"""
项目配置服务
"""
import json
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.project import Project
from app.models.project_settings import ProjectSettings


class ProjectSettingsService:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_project_settings(
        self,
        project_id: int,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """获取项目配置"""
        # 检查项目是否存在且属于用户
        project = self.db.query(Project).filter(
            and_(Project.id == project_id, Project.owner_id == user_id)
        ).first()
        
        if not project:
            return None
        
        # 获取项目配置
        settings = self.db.query(ProjectSettings).filter(
            ProjectSettings.project_id == project_id
        ).first()
        
        if not settings:
            # 如果没有配置，创建默认配置
            settings = await self.create_default_settings(project_id)
        
        return self._settings_to_dict(settings)
    
    async def update_project_settings(
        self,
        project_id: int,
        user_id: int,
        settings_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """更新项目配置"""
        # 检查项目是否存在且属于用户
        project = self.db.query(Project).filter(
            and_(Project.id == project_id, Project.owner_id == user_id)
        ).first()
        
        if not project:
            return None
        
        # 获取或创建项目配置
        settings = self.db.query(ProjectSettings).filter(
            ProjectSettings.project_id == project_id
        ).first()
        
        if not settings:
            settings = ProjectSettings(project_id=project_id)
            self.db.add(settings)
        
        # 更新配置字段
        if 'enable_syntax_highlight' in settings_data:
            settings.enable_syntax_highlight = settings_data['enable_syntax_highlight']
        if 'show_line_numbers' in settings_data:
            settings.show_line_numbers = settings_data['show_line_numbers']
        if 'code_theme' in settings_data:
            settings.code_theme = settings_data['code_theme']
        if 'file_sort_order' in settings_data:
            settings.file_sort_order = settings_data['file_sort_order']
        
        if 'auto_save' in settings_data:
            settings.auto_save = settings_data['auto_save']
        if 'auto_save_interval' in settings_data:
            settings.auto_save_interval = settings_data['auto_save_interval']
        if 'editor_mode' in settings_data:
            settings.editor_mode = settings_data['editor_mode']
        if 'show_section_numbers' in settings_data:
            settings.show_section_numbers = settings_data['show_section_numbers']
        
        if 'export_include_toc' in settings_data:
            settings.export_include_toc = settings_data['export_include_toc']
        if 'export_include_summary' in settings_data:
            settings.export_include_summary = settings_data['export_include_summary']
        if 'export_watermark' in settings_data:
            settings.export_watermark = settings_data['export_watermark']
        if 'export_page_format' in settings_data:
            settings.export_page_format = settings_data['export_page_format']
        
        # 处理扩展配置
        if 'extra_settings' in settings_data:
            settings.extra_settings = json.dumps(settings_data['extra_settings'])
        
        self.db.commit()
        self.db.refresh(settings)
        
        return self._settings_to_dict(settings)
    
    async def create_default_settings(
        self,
        project_id: int
    ) -> ProjectSettings:
        """创建默认项目配置"""
        settings = ProjectSettings(
            project_id=project_id,
            enable_syntax_highlight=True,
            show_line_numbers=True,
            code_theme="default",
            file_sort_order="manual",
            auto_save=True,
            auto_save_interval=30,
            editor_mode="split",
            show_section_numbers=True,
            export_include_toc=True,
            export_include_summary=True,
            export_watermark=False,
            export_page_format="A4"
        )
        
        self.db.add(settings)
        self.db.commit()
        self.db.refresh(settings)
        
        return settings
    
    def _settings_to_dict(self, settings: ProjectSettings) -> Dict[str, Any]:
        """将配置对象转换为字典"""
        result = {
            "id": settings.id,
            "project_id": settings.project_id,
            
            # 代码文件配置
            "enable_syntax_highlight": settings.enable_syntax_highlight,
            "show_line_numbers": settings.show_line_numbers,
            "code_theme": settings.code_theme,
            "file_sort_order": settings.file_sort_order,
            
            # 操作文档配置
            "auto_save": settings.auto_save,
            "auto_save_interval": settings.auto_save_interval,
            "editor_mode": settings.editor_mode,
            "show_section_numbers": settings.show_section_numbers,
            
            # 导出配置
            "export_include_toc": settings.export_include_toc,
            "export_include_summary": settings.export_include_summary,
            "export_watermark": settings.export_watermark,
            "export_page_format": settings.export_page_format,
            
            # 时间戳
            "created_at": settings.created_at,
            "updated_at": settings.updated_at
        }
        
        # 解析扩展配置
        if settings.extra_settings:
            try:
                result["extra_settings"] = json.loads(settings.extra_settings)
            except json.JSONDecodeError:
                result["extra_settings"] = {}
        else:
            result["extra_settings"] = {}
        
        return result
    
    async def reset_project_settings(
        self,
        project_id: int,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """重置项目配置为默认值"""
        # 检查项目是否存在且属于用户
        project = self.db.query(Project).filter(
            and_(Project.id == project_id, Project.owner_id == user_id)
        ).first()
        
        if not project:
            return None
        
        # 删除现有配置
        self.db.query(ProjectSettings).filter(
            ProjectSettings.project_id == project_id
        ).delete()
        
        # 创建默认配置
        settings = await self.create_default_settings(project_id)
        
        return self._settings_to_dict(settings)
