"""
项目服务
"""
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.project import Project, ProjectItem
from app.models.file import UploadedFile
from app.models.manual_section import ManualSection
from app.schemas.project import ProjectCreate, ProjectUpdate, ManualSectionCreate, ManualSectionUpdate
from app.services.file_service import FileService

class ProjectService:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_project(self, project_data: ProjectCreate, owner_id: int) -> Project:
        """创建项目"""
        import json

        # 准备配置数据
        config = {}
        if project_data.code_options:
            config['code_options'] = project_data.code_options.model_dump()
        if project_data.manual_options:
            config['manual_options'] = project_data.manual_options.model_dump()

        new_project = Project(
            project_name=project_data.project_name,
            project_type=project_data.project_type,
            owner_id=owner_id,
            config_json=json.dumps(config, ensure_ascii=False)
        )
        
        self.db.add(new_project)
        self.db.commit()
        self.db.refresh(new_project)

        if new_project.project_type == "manual" and project_data.manual_options:
            await self._create_default_manual_sections(
                new_project.id,
                project_data.manual_options.default_sections
            )
        
        return new_project

    async def _create_default_manual_sections(self, project_id: int, section_keys: list[str]) -> None:
        """根据创建配置生成操作文档默认章节。"""
        section_templates = {
            "overview": ("软件概述", "介绍 {{软件名称}} 的用途、目标用户和主要能力。"),
            "installation": ("安装说明", "说明 {{软件名称}} 的安装环境、安装步骤和启动方式。"),
            "usage": ("使用说明", "描述 {{软件名称}} 的常用操作流程。"),
            "features": ("功能介绍", "列出 {{软件名称}} 的核心功能，并说明每个功能的使用方法。"),
            "troubleshooting": ("常见问题", "整理用户可能遇到的问题及处理方法。"),
        }
        for index, key in enumerate(section_keys, start=1):
            title, body = section_templates.get(key, (key, "请补充本章节内容。"))
            self.db.add(ManualSection(
                project_id=project_id,
                title=title,
                body_markdown=body,
                order_index=index
            ))
        self.db.commit()
    
    async def get_user_projects(
        self,
        user_id: int,
        project_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        keyword: Optional[str] = None,
        order: str = "updated_desc",
    ) -> Dict[str, Any]:
        """获取用户项目列表，可按名称关键词与排序方式过滤。"""
        query = self.db.query(Project).filter(Project.owner_id == user_id)

        if project_type:
            query = query.filter(Project.project_type == project_type)

        if keyword:
            cleaned = keyword.strip()
            if cleaned:
                query = query.filter(Project.project_name.contains(cleaned))

        order_map = {
            "updated_desc": Project.updated_at.desc(),
            "updated_asc": Project.updated_at.asc(),
            "created_desc": Project.created_at.desc(),
            "created_asc": Project.created_at.asc(),
            "name_asc": Project.project_name.asc(),
            "name_desc": Project.project_name.desc(),
        }
        order_clause = order_map.get(order, Project.updated_at.desc())
        query = query.order_by(order_clause)

        total = query.count()
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
            "total_pages": (total + page_size - 1) // page_size,
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

        policy = FileService(self.db).get_upload_policy()
        current_size = (
            self.db.query(func.coalesce(func.sum(UploadedFile.file_size), 0))
            .join(ProjectItem, ProjectItem.file_id == UploadedFile.id)
            .filter(ProjectItem.project_id == project_id)
            .scalar()
            or 0
        )
        if current_size + file_record.file_size > policy["max_project_size_bytes"]:
            return False

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

    def _manual_section_to_dict(self, section: ManualSection) -> Dict[str, Any]:
        """Convert a manual section model into API response data."""
        image = section.image_file
        return {
            "id": section.id,
            "project_id": section.project_id,
            "title": section.title,
            "image_file_id": section.image_file_id,
            "image_filename": image.original_filename if image else None,
            "image_url": f"/uploads/{Path(image.storage_path).name}" if image else None,
            "body_markdown": section.body_markdown,
            "order_index": section.order_index,
            "created_at": section.created_at,
            "updated_at": section.updated_at,
        }

    async def get_manual_sections(self, project_id: int, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """获取操作文档章节列表"""
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            return None

        sections = self.db.query(ManualSection).filter(
            ManualSection.project_id == project_id
        ).order_by(ManualSection.order_index, ManualSection.id).all()

        return [self._manual_section_to_dict(section) for section in sections]

    async def create_manual_section(
        self,
        project_id: int,
        user_id: int,
        section_data: ManualSectionCreate
    ) -> Optional[Dict[str, Any]]:
        """创建操作文档章节"""
        project = await self.get_project_by_id(project_id, user_id)
        if not project or project.project_type != "manual":
            return None

        if section_data.image_file_id:
            image = self.db.query(UploadedFile).filter(
                UploadedFile.id == section_data.image_file_id,
                UploadedFile.uploader_id == user_id
            ).first()
            if not image:
                return None

        order_index = section_data.order_index
        if order_index is None:
            order_index = self.db.query(ManualSection).filter(
                ManualSection.project_id == project_id
            ).count() + 1

        section = ManualSection(
            project_id=project_id,
            title=section_data.title,
            image_file_id=section_data.image_file_id,
            body_markdown=section_data.body_markdown,
            order_index=order_index
        )

        self.db.add(section)
        self.db.commit()
        self.db.refresh(section)

        return self._manual_section_to_dict(section)

    async def update_manual_section(
        self,
        project_id: int,
        section_id: int,
        user_id: int,
        section_data: ManualSectionUpdate
    ) -> Optional[Dict[str, Any]]:
        """更新操作文档章节"""
        project = await self.get_project_by_id(project_id, user_id)
        if not project or project.project_type != "manual":
            return None

        section = self.db.query(ManualSection).filter(
            ManualSection.id == section_id,
            ManualSection.project_id == project_id
        ).first()
        if not section:
            return None

        if section_data.image_file_id:
            image = self.db.query(UploadedFile).filter(
                UploadedFile.id == section_data.image_file_id,
                UploadedFile.uploader_id == user_id
            ).first()
            if not image:
                return None

        update_data = section_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(section, key, value)

        self.db.commit()
        self.db.refresh(section)

        return self._manual_section_to_dict(section)

    async def delete_manual_section(self, project_id: int, section_id: int, user_id: int) -> bool:
        """删除操作文档章节"""
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            return False

        section = self.db.query(ManualSection).filter(
            ManualSection.id == section_id,
            ManualSection.project_id == project_id
        ).first()
        if not section:
            return False

        self.db.delete(section)
        self.db.commit()
        return True

    async def reorder_manual_sections(
        self,
        project_id: int,
        section_orders: list,
        user_id: int
    ) -> bool:
        """重新排序操作文档章节"""
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            return False

        try:
            for order_data in section_orders:
                section_id = order_data.get("section_id")
                order_index = order_data.get("order_index")
                if section_id is None or order_index is None:
                    continue

                section = self.db.query(ManualSection).filter(
                    ManualSection.id == section_id,
                    ManualSection.project_id == project_id
                ).first()
                if section:
                    section.order_index = order_index

            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False
