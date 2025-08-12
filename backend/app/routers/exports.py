"""
导出路由
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from app.database import get_db
from app.schemas.common import ResponseModel
from app.services.auth_service import get_current_user
from app.services.export_service import ExportService
from app.models.user import User
from app.models.export_history import ExportHistory

router = APIRouter()

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

@router.get("/history", response_model=ResponseModel)
async def get_export_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取导出历史"""
    try:
        # 获取用户的导出历史
        histories = db.query(ExportHistory).join(
            ExportHistory.project
        ).filter(
            ExportHistory.project.has(owner_id=current_user.id)
        ).order_by(ExportHistory.created_at.desc()).limit(50).all()

        return ResponseModel(
            code=0,
            message="获取成功",
            data={
                "histories": [
                    {
                        "id": h.id,
                        "project_id": h.project_id,
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
