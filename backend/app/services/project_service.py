"""
项目服务
"""
import json
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.project import Project, ProjectItem
from app.models.file import UploadedFile
from app.schemas.project import ProjectCreate, ProjectUpdate

class ProjectService:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_project(self, project_data: ProjectCreate, owner_id: int) -> Project:
        """创建项目"""
        import json

        # 准备配置数据
        config = {}
        if project_data.code_options:
            config['code_options'] = project_data.code_options.dict()
        if project_data.manual_options:
            config['manual_options'] = project_data.manual_options.dict()

        new_project = Project(
            project_name=project_data.project_name,
            project_type=project_data.project_type,
            owner_id=owner_id,
            config_json=json.dumps(config, ensure_ascii=False)
        )
        
        self.db.add(new_project)
        self.db.commit()
        self.db.refresh(new_project)
        
        return new_project
    
    async def get_user_projects(
        self, 
        user_id: int, 
        project_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """获取用户项目列表"""
        query = self.db.query(Project).filter(Project.owner_id == user_id)
        
        if project_type:
            query = query.filter(Project.project_type == project_type)
        
        # 计算总数
        total = query.count()
        
        # 分页查询
        offset = (page - 1) * page_size
        projects = query.offset(offset).limit(page_size).all()
        
        return {
            "projects": [
                {
                    "id": p.id,
                    "project_name": p.project_name,
                    "project_type": p.project_type,
                    "config_json": p.config_json,
                    "created_at": p.created_at,
                    "updated_at": p.updated_at
                }
                for p in projects
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    
    async def get_project_by_id(self, project_id: int, user_id: int) -> Optional[Project]:
        """根据ID获取项目"""
        return self.db.query(Project).filter(
            and_(Project.id == project_id, Project.owner_id == user_id)
        ).first()
    
    async def update_project(
        self,
        project_id: int,
        user_id: int,
        project_data: ProjectUpdate
    ) -> Optional[Project]:
        """更新项目"""
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            return None

        if project_data.project_name is not None:
            project.project_name = project_data.project_name

        if project_data.config_json is not None:
            project.config_json = json.dumps(project_data.config_json, ensure_ascii=False)

        self.db.commit()
        self.db.refresh(project)

        return project

    async def delete_project(self, project_id: int, user_id: int) -> bool:
        """删除项目"""
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            return False

        self.db.delete(project)
        self.db.commit()

        return True

    async def add_file_to_project(
        self,
        project_id: int,
        file_id: int,
        user_id: int
    ) -> bool:
        """将文件添加到项目"""
        # 检查项目是否存在且属于用户
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            return False

        # 检查文件是否存在且属于用户
        file_record = self.db.query(UploadedFile).filter(
            UploadedFile.id == file_id,
            UploadedFile.uploader_id == user_id
        ).first()
        if not file_record:
            return False

        # 检查文件是否已经在项目中
        existing_item = self.db.query(ProjectItem).filter(
            ProjectItem.project_id == project_id,
            ProjectItem.file_id == file_id
        ).first()
        if existing_item:
            return True  # 已存在，返回成功

        # 获取当前项目中文件的最大顺序
        max_order = self.db.query(ProjectItem).filter(
            ProjectItem.project_id == project_id
        ).count()

        # 创建项目文件关联
        project_item = ProjectItem(
            project_id=project_id,
            file_id=file_id,
            order_index=max_order + 1
        )

        self.db.add(project_item)
        self.db.commit()

        return True

    async def get_project_files(
        self,
        project_id: int,
        user_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """获取项目文件列表"""
        # 检查项目是否存在且属于用户
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            return None

        # 获取项目文件列表
        project_items = self.db.query(ProjectItem).join(UploadedFile).filter(
            ProjectItem.project_id == project_id
        ).order_by(ProjectItem.order_index).all()

        return [
            {
                "id": item.id,
                "file_id": item.file_id,
                "display_name": item.display_name or item.file.original_filename,
                "original_filename": item.file.original_filename,
                "file_size": item.file.file_size,
                "file_type": item.file.file_type,
                "language_override": item.language_override,
                "include_in_export": item.include_in_export,
                "order_index": item.order_index,
                "created_at": item.created_at
            }
            for item in project_items
        ]

    async def remove_file_from_project(
        self,
        project_id: int,
        file_id: int,
        user_id: int
    ) -> bool:
        """从项目中移除文件"""
        # 检查项目是否存在且属于用户
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            return False

        # 查找项目文件关联
        project_item = self.db.query(ProjectItem).filter(
            ProjectItem.project_id == project_id,
            ProjectItem.file_id == file_id
        ).first()

        if not project_item:
            return False

        # 删除项目文件关联
        self.db.delete(project_item)
        self.db.commit()

        return True

    async def update_project_file(
        self,
        project_id: int,
        file_id: int,
        user_id: int,
        update_data: dict
    ) -> bool:
        """更新项目文件信息"""
        # 检查项目是否存在且属于用户
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            return False

        # 查找项目文件关联
        project_item = self.db.query(ProjectItem).filter(
            ProjectItem.project_id == project_id,
            ProjectItem.file_id == file_id
        ).first()

        if not project_item:
            return False

        # 更新文件信息
        if 'display_name' in update_data:
            project_item.display_name = update_data['display_name']

        if 'language_override' in update_data:
            project_item.language_override = update_data['language_override']

        if 'include_in_export' in update_data:
            project_item.include_in_export = update_data['include_in_export']

        self.db.commit()
        return True

    async def reorder_project_files(
        self,
        project_id: int,
        file_orders: list,
        user_id: int
    ) -> bool:
        """重新排序项目文件"""
        # 检查项目是否存在且属于用户
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            return False

        try:
            # 批量更新文件顺序
            for order_data in file_orders:
                file_id = order_data.get('file_id')
                order_index = order_data.get('order_index')

                if file_id is None or order_index is None:
                    continue

                # 查找项目文件关联
                project_item = self.db.query(ProjectItem).filter(
                    ProjectItem.project_id == project_id,
                    ProjectItem.file_id == file_id
                ).first()

                if project_item:
                    project_item.order_index = order_index

            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            return False
