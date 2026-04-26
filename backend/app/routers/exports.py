"""
导出路由
"""
from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from app.database import get_db, SessionLocal
from app.schemas.common import ResponseModel
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

@router.post("/projects/{project_id}/pdf", response_model=ResponseModel)
async def export_project_pdf(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """导出项目为PDF"""
    try:
        export_service = ExportService(db)
        result = await export_service.export_project_to_pdf(project_id, current_user.id)

        if not result:
            return ResponseModel(code=4001, message="项目不存在或导出失败")

        return ResponseModel(
            code=0,
            message="导出成功",
            data=result
        )
    except Exception as e:
        return ResponseModel(code=5001, message=f"导出失败: {str(e)}")

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
            return ResponseModel(code=4001, message="项目不存在")
        background_tasks.add_task(_run_export_job, job["job_id"], current_user.id, export_options)
        return ResponseModel(code=0, message="导出任务已提交", data=job)
    except Exception as e:
        return ResponseModel(code=5001, message=f"提交导出任务失败: {str(e)}")

@router.get("/history", response_model=ResponseModel)
async def get_export_history(
    project_id: int | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取导出历史"""
    try:
        # 获取用户的导出历史
        query = db.query(ExportHistory).join(
            ExportHistory.project
        ).filter(
            ExportHistory.project.has(owner_id=current_user.id)
        )

        if project_id is not None:
            query = query.filter(ExportHistory.project_id == project_id)

        histories = query.order_by(ExportHistory.created_at.desc()).limit(50).all()

        return ResponseModel(
            code=0,
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
                ]
            }
        )
    except Exception as e:
        return ResponseModel(code=5001, message="获取导出历史失败")

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
        return ResponseModel(code=4001, message="导出任务不存在")
    return ResponseModel(code=0, message="获取成功", data=job)
