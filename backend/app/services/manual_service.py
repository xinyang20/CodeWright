"""
操作文档服务
"""
import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.manual_section import ManualSection
from app.models.project import Project
from app.models.file import UploadedFile


class ManualService:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_section(
        self,
        project_id: int,
        user_id: int,
        title: str,
        body_markdown: str,
        image_file_id: Optional[int] = None
    ) -> Optional[ManualSection]:
        """创建章节"""
        # 检查项目是否存在且属于用户
        project = self.db.query(Project).filter(
            and_(Project.id == project_id, Project.owner_id == user_id)
        ).first()
        
        if not project or project.project_type != 'manual':
            return None
        
        # 获取当前最大排序索引
        max_order = self.db.query(ManualSection).filter(
            ManualSection.project_id == project_id
        ).count()
        
        # 创建新章节
        section = ManualSection(
            project_id=project_id,
            title=title,
            body_markdown=body_markdown,
            image_file_id=image_file_id,
            order_index=max_order + 1
        )
        
        self.db.add(section)
        self.db.commit()
        self.db.refresh(section)
        
        return section
    
    async def get_project_sections(
        self,
        project_id: int,
        user_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """获取项目章节列表"""
        # 检查项目是否存在且属于用户
        project = self.db.query(Project).filter(
            and_(Project.id == project_id, Project.owner_id == user_id)
        ).first()
        
        if not project or project.project_type != 'manual':
            return None
        
        # 获取章节列表
        sections = self.db.query(ManualSection).filter(
            ManualSection.project_id == project_id
        ).order_by(ManualSection.order_index).all()
        
        result = []
        for section in sections:
            section_data = {
                "id": section.id,
                "title": section.title,
                "body_markdown": section.body_markdown,
                "order_index": section.order_index,
                "created_at": section.created_at,
                "updated_at": section.updated_at,
                "image_file": None
            }
            
            # 如果有关联的图片文件，获取文件信息
            if section.image_file_id:
                image_file = self.db.query(UploadedFile).filter(
                    UploadedFile.id == section.image_file_id
                ).first()
                if image_file:
                    section_data["image_file"] = {
                        "id": image_file.id,
                        "original_filename": image_file.original_filename,
                        "storage_path": image_file.storage_path,
                        "file_size": image_file.file_size
                    }
            
            result.append(section_data)
        
        return result
    
    async def update_section(
        self,
        section_id: int,
        user_id: int,
        title: Optional[str] = None,
        body_markdown: Optional[str] = None,
        image_file_id: Optional[int] = None
    ) -> Optional[ManualSection]:
        """更新章节"""
        # 获取章节并检查权限
        section = self.db.query(ManualSection).join(Project).filter(
            and_(
                ManualSection.id == section_id,
                Project.owner_id == user_id
            )
        ).first()
        
        if not section:
            return None
        
        # 更新字段
        if title is not None:
            section.title = title
        if body_markdown is not None:
            section.body_markdown = body_markdown
        if image_file_id is not None:
            section.image_file_id = image_file_id
        
        self.db.commit()
        self.db.refresh(section)
        
        return section
    
    async def delete_section(
        self,
        section_id: int,
        user_id: int
    ) -> bool:
        """删除章节"""
        # 获取章节并检查权限
        section = self.db.query(ManualSection).join(Project).filter(
            and_(
                ManualSection.id == section_id,
                Project.owner_id == user_id
            )
        ).first()
        
        if not section:
            return False
        
        project_id = section.project_id
        order_index = section.order_index
        
        # 删除章节
        self.db.delete(section)
        
        # 更新后续章节的排序索引
        self.db.query(ManualSection).filter(
            and_(
                ManualSection.project_id == project_id,
                ManualSection.order_index > order_index
            )
        ).update({
            ManualSection.order_index: ManualSection.order_index - 1
        })
        
        self.db.commit()
        
        return True
    
    async def reorder_sections(
        self,
        project_id: int,
        user_id: int,
        section_orders: List[Dict[str, int]]
    ) -> bool:
        """重新排序章节"""
        # 检查项目权限
        project = self.db.query(Project).filter(
            and_(Project.id == project_id, Project.owner_id == user_id)
        ).first()
        
        if not project or project.project_type != 'manual':
            return False
        
        # 更新章节排序
        for item in section_orders:
            section_id = item.get('id')
            new_order = item.get('order_index')
            
            if section_id and new_order is not None:
                self.db.query(ManualSection).filter(
                    and_(
                        ManualSection.id == section_id,
                        ManualSection.project_id == project_id
                    )
                ).update({
                    ManualSection.order_index: new_order
                })
        
        self.db.commit()
        
        return True
    
    async def get_section_by_id(
        self,
        section_id: int,
        user_id: int
    ) -> Optional[ManualSection]:
        """根据ID获取章节"""
        return self.db.query(ManualSection).join(Project).filter(
            and_(
                ManualSection.id == section_id,
                Project.owner_id == user_id
            )
        ).first()
