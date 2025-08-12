"""
模板服务
"""
import os
import uuid
import shutil
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.models.template import Template

class TemplateService:
    def __init__(self, db: Session):
        self.db = db
        self.template_dir = Path("../templates")
        self.template_dir.mkdir(exist_ok=True)
        self._init_default_template()
    
    def _init_default_template(self):
        """初始化默认模板"""
        existing = self.db.query(Template).filter(
            Template.name == "基础代码模板"
        ).first()
        
        if not existing:
            # 创建基础模板文件
            template_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{{project_name}} - 软件著作权申请材料</title>
    <style>
        body { font-family: "SimSun", serif; font-size: 12pt; line-height: 1.6; }
        .title { text-align: center; font-size: 24pt; font-weight: bold; margin-bottom: 20pt; }
        .project-name { text-align: center; font-size: 18pt; margin-bottom: 30pt; }
        .file-section { margin-bottom: 40pt; page-break-before: always; }
        .file-title { font-size: 16pt; font-weight: bold; margin-bottom: 15pt; }
        .highlight { font-family: "Consolas", monospace; font-size: 9pt; }
    </style>
</head>
<body>
    <div class="title">软件著作权申请材料</div>
    <div class="project-name">{{project_name}}</div>
    
    <div class="meta-info">
        <p>项目类型：{{project_type}}</p>
        <p>生成时间：{{generated_time}}</p>
        <p>文件总数：{{file_count}}</p>
    </div>
    
    <div class="content">
        {% for file in files %}
        <div class="file-section">
            <div class="file-title">{{loop.index}}. {{file.filename}}</div>
            <div class="file-content">{{file.highlighted_content|safe}}</div>
        </div>
        {% endfor %}
    </div>
</body>
</html>"""
            
            template_filename = f"basic_template_{uuid.uuid4().hex[:8]}.html"
            template_path = self.template_dir / template_filename
            
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            template = Template(
                name="基础代码模板",
                version="1.0.0",
                description="默认的代码文档模板，适用于大多数软件著作权申请",
                storage_path=str(template_path),
                status="published"
            )
            
            self.db.add(template)
            self.db.commit()
    
    async def get_templates(self) -> List[dict]:
        """获取模板列表"""
        templates = self.db.query(Template).order_by(Template.created_at.desc()).all()
        
        return [
            {
                "id": t.id,
                "name": t.name,
                "version": t.version,
                "description": t.description,
                "status": t.status,
                "created_at": t.created_at,
                "updated_at": t.updated_at
            }
            for t in templates
        ]
    
    async def create_template(
        self, 
        name: str, 
        version: str, 
        description: str, 
        file: UploadFile
    ) -> Template:
        """创建模板"""
        # 检查文件类型
        if not file.filename.endswith('.html'):
            raise ValueError("模板文件必须是HTML格式")
        
        # 保存模板文件
        template_filename = f"{name}_{version}_{uuid.uuid4().hex[:8]}.html"
        template_path = self.template_dir / template_filename
        
        with open(template_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 创建模板记录
        template = Template(
            name=name,
            version=version,
            description=description,
            storage_path=str(template_path),
            status="draft"
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        return template
    
    async def update_template_status(self, template_id: int, status: str) -> bool:
        """更新模板状态"""
        if status not in ["draft", "published"]:
            raise ValueError("状态必须是 draft 或 published")
        
        template = self.db.query(Template).filter(Template.id == template_id).first()
        if not template:
            return False
        
        template.status = status
        self.db.commit()
        
        return True
    
    async def get_template_by_id(self, template_id: int) -> Optional[Template]:
        """根据ID获取模板"""
        return self.db.query(Template).filter(Template.id == template_id).first()
    
    async def get_published_templates(self) -> List[Template]:
        """获取已发布的模板"""
        return self.db.query(Template).filter(
            Template.status == "published"
        ).order_by(Template.created_at.desc()).all()
