"""
导出路由
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from app.database import get_db, SessionLocal
from app.schemas.common import ResponseModel, ErrorCodes
from app.services.auth_service import get_current_user
from app.services.export_service import ExportService
from app.models.user import User
from app.models.export_history import ExportHistory
from app.models.export_job import ExportJob

router = APIRouter()


async def _run_export_job(job_id: str, user_id: int, options: dict) -> None:
    """在本地后台任务中执行导出，避免依赖系统级队列进程。"""
    db = SessionLocal()
    try:
        await ExportService(db).process_export_job(job_id, user_id, options)
    finally:
        db.close()


@router.post("/projects/{project_id}/export", response_model=ResponseModel)
async def submit_export_job(
    project_id: int,
    background_tasks: BackgroundTasks,
    export_options: dict = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提交导出任务"""
    try:
        export_service = ExportService(db)
        job = await export_service.submit_export_job(project_id, current_user.id, export_options)
        if not job:
            return ResponseModel(code=ErrorCodes.NOT_FOUND, message="项目不存在")
        background_tasks.add_task(_run_export_job, job["job_id"], current_user.id, export_options)
        return ResponseModel(code=ErrorCodes.OK, message="导出任务已提交", data=job)
    except Exception as e:
        return ResponseModel(code=ErrorCodes.EXPORT_FAILED, message=f"提交导出任务失败: {str(e)}")

@router.get("/history", response_model=ResponseModel)
async def get_export_history(
    project_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None, pattern="^(success|failed)$"),
    start_at: Optional[datetime] = Query(None, description="过滤起始时间，ISO8601"),
    end_at: Optional[datetime] = Query(None, description="过滤结束时间，ISO8601"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取导出历史"""
    try:
        query = db.query(ExportHistory).join(
            ExportHistory.project
        ).filter(
            ExportHistory.project.has(owner_id=current_user.id)
        )

        if project_id is not None:
            query = query.filter(ExportHistory.project_id == project_id)
        if status:
            query = query.filter(ExportHistory.status == status)
        if start_at:
            query = query.filter(ExportHistory.created_at >= start_at)
        if end_at:
            query = query.filter(ExportHistory.created_at <= end_at)

        total = query.count()
        histories = (
            query.order_by(ExportHistory.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return ResponseModel(
            code=ErrorCodes.OK,
            message="获取成功",
            data={
                "histories": [
                    {
                        "id": h.id,
                        "project_id": h.project_id,
                        "project_name": h.project.project_name,
                        "exporter": h.exporter,
                        "status": h.status,
                        "duration_ms": h.duration_ms,
                        "file_path": h.file_path,
                        "created_at": h.created_at
                    }
                    for h in histories
                ],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
            }
        )
    except Exception:
        return ResponseModel(code=ErrorCodes.SERVER_ERROR, message="获取导出历史失败")


@router.get("/jobs", response_model=ResponseModel)
async def list_export_jobs(
    status: Optional[str] = Query(None, pattern="^(queued|processing|success|failed)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户全部导出任务，可按状态过滤。"""
    try:
        export_service = ExportService(db)
        data = await export_service.list_jobs(
            user_id=current_user.id,
            status=status,
            page=page,
            page_size=page_size,
        )
        return ResponseModel(code=ErrorCodes.OK, message="获取成功", data=data)
    except Exception:
        return ResponseModel(code=ErrorCodes.SERVER_ERROR, message="获取导出任务失败")


@router.post("/{job_id}/retry", response_model=ResponseModel)
async def retry_export_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """根据已有任务重新提交一份带相同选项的导出任务。"""
    try:
        export_service = ExportService(db)
        result = await export_service.retry_export_job(job_id, current_user.id)
        if not result or not result["job"]:
            return ResponseModel(code=ErrorCodes.NOT_FOUND, message="导出任务不存在")
        background_tasks.add_task(
            _run_export_job,
            result["job"]["job_id"],
            current_user.id,
            result["options"],
        )
        return ResponseModel(code=ErrorCodes.OK, message="重试任务已提交", data=result["job"])
    except Exception:
        return ResponseModel(code=ErrorCodes.EXPORT_FAILED, message="重试导出失败")

@router.get("/download/{export_id}")
async def download_export(
    export_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """下载导出文件"""
    try:
        # 获取导出记录
        export_history = db.query(ExportHistory).join(
            ExportHistory.project
        ).filter(
            ExportHistory.id == export_id,
            ExportHistory.project.has(owner_id=current_user.id),
            ExportHistory.status == "success"
        ).first()

        if not export_history or not export_history.file_path:
            raise HTTPException(status_code=404, detail="文件不存在")

        if not os.path.exists(export_history.file_path):
            raise HTTPException(status_code=404, detail="文件已被删除")

        filename = os.path.basename(export_history.file_path)

        # 根据文件扩展名确定媒体类型
        if filename.endswith('.pdf'):
            media_type = 'application/pdf'
        elif filename.endswith('.html'):
            media_type = 'text/html'
        else:
            media_type = 'application/octet-stream'

        return FileResponse(
            path=export_history.file_path,
            filename=filename,
            media_type=media_type
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="下载失败")

@router.get("/{job_id}/download")
async def download_export_job_result(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """下载导出任务结果"""
    export_job = db.query(ExportJob).join(ExportJob.project).filter(
        ExportJob.job_id == job_id,
        ExportJob.project.has(owner_id=current_user.id),
        ExportJob.status == "success"
    ).first()

    if not export_job or not export_job.result_file_path:
        raise HTTPException(status_code=404, detail="导出文件不存在")

    if not os.path.exists(export_job.result_file_path):
        raise HTTPException(status_code=404, detail="导出文件已被删除")

    return FileResponse(
        path=export_job.result_file_path,
        filename=os.path.basename(export_job.result_file_path),
        media_type="application/pdf"
    )

@router.get("/{job_id}/log")
async def download_export_job_log(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """下载导出任务的 LaTeX 日志，便于排查失败原因。"""
    export_job = db.query(ExportJob).join(ExportJob.project).filter(
        ExportJob.job_id == job_id,
        ExportJob.project.has(owner_id=current_user.id),
    ).first()

    if not export_job or not export_job.error_log_path:
        raise HTTPException(status_code=404, detail="日志不存在")

    if not os.path.exists(export_job.error_log_path):
        raise HTTPException(status_code=404, detail="日志已被删除")

    return FileResponse(
        path=export_job.error_log_path,
        filename=os.path.basename(export_job.error_log_path),
        media_type="text/plain",
    )

@router.get("/{job_id}", response_model=ResponseModel)
async def get_export_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """查询导出任务状态"""
    export_service = ExportService(db)
    job = export_service.get_job_status(job_id, current_user.id)
    if not job:
        return ResponseModel(code=ErrorCodes.NOT_FOUND, message="导出任务不存在")
    return ResponseModel(code=ErrorCodes.OK, message="获取成功", data=job)
