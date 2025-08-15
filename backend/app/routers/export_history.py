"""
导出历史路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.common import ResponseModel
from app.services.auth_service import get_current_user
from app.services.export_history_service import ExportHistoryService
from app.models.user import User

router = APIRouter()


@router.get("/projects/{project_id}/exports", response_model=ResponseModel)
async def get_project_export_history(
    project_id: int,
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取项目导出历史"""
    try:
        export_service = ExportHistoryService(db)
        history = await export_service.get_project_export_history(
            project_id, current_user.id, limit, offset
        )
        
        if history is None:
            return ResponseModel(code=4001, message="项目不存在或无权限")
        
        return ResponseModel(
            code=0,
            message="获取导出历史成功",
            data={
                "exports": history,
                "total": len(history),
                "limit": limit,
                "offset": offset
            }
        )
    except Exception as e:
        return ResponseModel(code=5001, message="获取导出历史失败")


@router.get("/exports", response_model=ResponseModel)
async def get_user_export_history(
    limit: int = Query(50, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户导出历史"""
    try:
        export_service = ExportHistoryService(db)
        history = await export_service.get_user_export_history(
            current_user.id, limit, offset
        )
        
        return ResponseModel(
            code=0,
            message="获取导出历史成功",
            data={
                "exports": history,
                "total": len(history),
                "limit": limit,
                "offset": offset
            }
        )
    except Exception as e:
        return ResponseModel(code=5001, message="获取导出历史失败")


@router.get("/exports/statistics", response_model=ResponseModel)
async def get_export_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取导出统计信息"""
    try:
        export_service = ExportHistoryService(db)
        statistics = await export_service.get_export_statistics(current_user.id)
        
        return ResponseModel(
            code=0,
            message="获取导出统计成功",
            data=statistics
        )
    except Exception as e:
        return ResponseModel(code=5001, message="获取导出统计失败")


@router.delete("/exports/{export_id}", response_model=ResponseModel)
async def delete_export_record(
    export_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除导出记录"""
    try:
        export_service = ExportHistoryService(db)
        success = await export_service.delete_export_record(export_id, current_user.id)
        
        if not success:
            return ResponseModel(code=4001, message="导出记录不存在或无权限")
        
        return ResponseModel(
            code=0,
            message="导出记录删除成功"
        )
    except Exception as e:
        return ResponseModel(code=5001, message="删除导出记录失败")


@router.get("/exports/{export_id}", response_model=ResponseModel)
async def get_export_detail(
    export_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取导出记录详情"""
    try:
        from app.models.export_history import ExportHistory
        from sqlalchemy import and_
        
        export_record = db.query(ExportHistory).filter(
            and_(
                ExportHistory.id == export_id,
                ExportHistory.user_id == current_user.id
            )
        ).first()
        
        if not export_record:
            return ResponseModel(code=4001, message="导出记录不存在或无权限")
        
        import json
        export_data = {
            "id": export_record.id,
            "project_id": export_record.project_id,
            "project_name": export_record.project.project_name if export_record.project else "未知项目",
            "project_type": export_record.project.project_type if export_record.project else "unknown",
            "export_type": export_record.export_type,
            "export_format": export_record.export_format,
            "file_name": export_record.file_name,
            "file_size": export_record.file_size,
            "file_path": export_record.file_path,
            "status": export_record.status,
            "progress": export_record.progress,
            "error_message": export_record.error_message,
            "total_files": export_record.total_files,
            "total_sections": export_record.total_sections,
            "processing_time": export_record.processing_time,
            "created_at": export_record.created_at,
            "updated_at": export_record.updated_at,
            "completed_at": export_record.completed_at
        }
        
        # 解析导出选项
        if export_record.export_options:
            try:
                export_data["export_options"] = json.loads(export_record.export_options)
            except json.JSONDecodeError:
                export_data["export_options"] = {}
        else:
            export_data["export_options"] = {}
        
        return ResponseModel(
            code=0,
            message="获取导出记录详情成功",
            data=export_data
        )
    except Exception as e:
        return ResponseModel(code=5001, message="获取导出记录详情失败")
