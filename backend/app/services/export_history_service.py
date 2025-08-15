"""
导出历史服务
"""
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models.project import Project
from app.models.export_history import ExportHistory


class ExportHistoryService:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_export_record(
        self,
        project_id: int,
        user_id: int,
        export_type: str = "pdf",
        file_name: str = "",
        export_options: Dict[str, Any] = None
    ) -> Optional[ExportHistory]:
        """创建导出记录"""
        # 检查项目是否存在且属于用户
        project = self.db.query(Project).filter(
            and_(Project.id == project_id, Project.owner_id == user_id)
        ).first()
        
        if not project:
            return None
        
        # 统计项目内容
        total_files = 0
        total_sections = 0
        
        if project.project_type == 'code':
            total_files = len(project.project_items)
        elif project.project_type == 'manual':
            total_sections = len(project.manual_sections)
        
        # 创建导出记录
        export_record = ExportHistory(
            project_id=project_id,
            user_id=user_id,
            export_type=export_type,
            export_format=export_type,
            file_name=file_name or f"{project.project_name}.{export_type}",
            status="pending",
            progress=0.0,
            export_options=json.dumps(export_options or {}),
            total_files=total_files,
            total_sections=total_sections
        )
        
        self.db.add(export_record)
        self.db.commit()
        self.db.refresh(export_record)
        
        return export_record
    
    async def update_export_progress(
        self,
        export_id: int,
        progress: float,
        status: str = None
    ) -> bool:
        """更新导出进度"""
        export_record = self.db.query(ExportHistory).filter(
            ExportHistory.id == export_id
        ).first()
        
        if not export_record:
            return False
        
        export_record.progress = progress
        if status:
            export_record.status = status
        
        self.db.commit()
        return True
    
    async def complete_export(
        self,
        export_id: int,
        file_path: str = None,
        file_size: int = None,
        processing_time: float = None,
        error_message: str = None
    ) -> bool:
        """完成导出"""
        export_record = self.db.query(ExportHistory).filter(
            ExportHistory.id == export_id
        ).first()
        
        if not export_record:
            return False
        
        export_record.completed_at = datetime.utcnow()
        export_record.progress = 100.0
        
        if error_message:
            export_record.status = "failed"
            export_record.error_message = error_message
        else:
            export_record.status = "completed"
            export_record.file_path = file_path
            export_record.file_size = file_size
        
        if processing_time:
            export_record.processing_time = processing_time
        
        self.db.commit()
        return True
    
    async def get_project_export_history(
        self,
        project_id: int,
        user_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> Optional[List[Dict[str, Any]]]:
        """获取项目导出历史"""
        # 检查项目是否存在且属于用户
        project = self.db.query(Project).filter(
            and_(Project.id == project_id, Project.owner_id == user_id)
        ).first()
        
        if not project:
            return None
        
        # 获取导出历史
        export_records = self.db.query(ExportHistory).filter(
            ExportHistory.project_id == project_id
        ).order_by(desc(ExportHistory.created_at)).offset(offset).limit(limit).all()
        
        result = []
        for record in export_records:
            record_data = {
                "id": record.id,
                "export_type": record.export_type,
                "export_format": record.export_format,
                "file_name": record.file_name,
                "file_size": record.file_size,
                "file_path": record.file_path,
                "status": record.status,
                "progress": record.progress,
                "error_message": record.error_message,
                "total_files": record.total_files,
                "total_sections": record.total_sections,
                "processing_time": record.processing_time,
                "created_at": record.created_at,
                "updated_at": record.updated_at,
                "completed_at": record.completed_at
            }
            
            # 解析导出选项
            if record.export_options:
                try:
                    record_data["export_options"] = json.loads(record.export_options)
                except json.JSONDecodeError:
                    record_data["export_options"] = {}
            else:
                record_data["export_options"] = {}
            
            result.append(record_data)
        
        return result
    
    async def get_user_export_history(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取用户导出历史"""
        export_records = self.db.query(ExportHistory).filter(
            ExportHistory.user_id == user_id
        ).order_by(desc(ExportHistory.created_at)).offset(offset).limit(limit).all()
        
        result = []
        for record in export_records:
            record_data = {
                "id": record.id,
                "project_id": record.project_id,
                "project_name": record.project.project_name if record.project else "未知项目",
                "project_type": record.project.project_type if record.project else "unknown",
                "export_type": record.export_type,
                "export_format": record.export_format,
                "file_name": record.file_name,
                "file_size": record.file_size,
                "status": record.status,
                "progress": record.progress,
                "error_message": record.error_message,
                "total_files": record.total_files,
                "total_sections": record.total_sections,
                "processing_time": record.processing_time,
                "created_at": record.created_at,
                "completed_at": record.completed_at
            }
            
            result.append(record_data)
        
        return result
    
    async def delete_export_record(
        self,
        export_id: int,
        user_id: int
    ) -> bool:
        """删除导出记录"""
        export_record = self.db.query(ExportHistory).filter(
            and_(
                ExportHistory.id == export_id,
                ExportHistory.user_id == user_id
            )
        ).first()
        
        if not export_record:
            return False
        
        self.db.delete(export_record)
        self.db.commit()
        
        return True
    
    async def get_export_statistics(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """获取导出统计信息"""
        # 总导出次数
        total_exports = self.db.query(ExportHistory).filter(
            ExportHistory.user_id == user_id
        ).count()
        
        # 成功导出次数
        successful_exports = self.db.query(ExportHistory).filter(
            and_(
                ExportHistory.user_id == user_id,
                ExportHistory.status == "completed"
            )
        ).count()
        
        # 失败导出次数
        failed_exports = self.db.query(ExportHistory).filter(
            and_(
                ExportHistory.user_id == user_id,
                ExportHistory.status == "failed"
            )
        ).count()
        
        # 最近7天导出次数
        from datetime import datetime, timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_exports = self.db.query(ExportHistory).filter(
            and_(
                ExportHistory.user_id == user_id,
                ExportHistory.created_at >= seven_days_ago
            )
        ).count()
        
        return {
            "total_exports": total_exports,
            "successful_exports": successful_exports,
            "failed_exports": failed_exports,
            "recent_exports": recent_exports,
            "success_rate": round(successful_exports / total_exports * 100, 2) if total_exports > 0 else 0
        }
