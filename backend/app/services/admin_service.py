"""
管理员服务
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.user import User
from app.models.project import Project
from app.models.file import UploadedFile
from app.models.export_history import ExportHistory

class AdminService:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_users(
        self, 
        page: int = 1, 
        page_size: int = 10, 
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取用户列表"""
        query = self.db.query(User)
        
        if search:
            query = query.filter(User.username.contains(search))
        
        # 计算总数
        total = query.count()
        
        # 分页查询
        offset = (page - 1) * page_size
        users = query.offset(offset).limit(page_size).all()
        
        return {
            "users": [
                {
                    "id": u.id,
                    "username": u.username,
                    "role": u.role,
                    "is_active": u.is_active,
                    "created_at": u.created_at
                }
                for u in users
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    
    async def update_user_status(self, user_id: int, is_active: bool) -> bool:
        """更新用户状态"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.is_active = is_active
        self.db.commit()
        
        return True
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        # 用户统计
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.is_active == True).count()
        admin_users = self.db.query(User).filter(User.role == "admin").count()
        
        # 项目统计
        total_projects = self.db.query(Project).count()
        code_projects = self.db.query(Project).filter(Project.project_type == "code").count()
        manual_projects = self.db.query(Project).filter(Project.project_type == "manual").count()
        
        # 文件统计
        total_files = self.db.query(UploadedFile).count()
        total_file_size = self.db.query(func.sum(UploadedFile.file_size)).scalar() or 0
        
        # 导出统计
        total_exports = self.db.query(ExportHistory).count()
        successful_exports = self.db.query(ExportHistory).filter(
            ExportHistory.status == "success"
        ).count()
        failed_exports = self.db.query(ExportHistory).filter(
            ExportHistory.status == "failed"
        ).count()
        
        # 最近活动统计（最近7天）
        from datetime import datetime, timedelta
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        recent_users = self.db.query(User).filter(
            User.created_at >= seven_days_ago
        ).count()
        
        recent_projects = self.db.query(Project).filter(
            Project.created_at >= seven_days_ago
        ).count()
        
        recent_exports = self.db.query(ExportHistory).filter(
            ExportHistory.created_at >= seven_days_ago
        ).count()
        
        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "admin": admin_users,
                "recent": recent_users
            },
            "projects": {
                "total": total_projects,
                "code": code_projects,
                "manual": manual_projects,
                "recent": recent_projects
            },
            "files": {
                "total": total_files,
                "total_size": total_file_size,
                "average_size": total_file_size // total_files if total_files > 0 else 0
            },
            "exports": {
                "total": total_exports,
                "successful": successful_exports,
                "failed": failed_exports,
                "success_rate": (successful_exports / total_exports * 100) if total_exports > 0 else 0,
                "recent": recent_exports
            }
        }
