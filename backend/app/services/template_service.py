"""
模板服务
"""
import os
import uuid
import shutil
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.models.template import Template
from app.paths import TEMPLATES_DIR

class TemplateService:
    def __init__(self, db: Session):
        self.db = db
        self.template_dir = TEMPLATES_DIR
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

        existing = self.db.query(Template).filter(
            Template.name == name,
            Template.version == version
        ).first()
        if existing:
            raise ValueError("同名同版本模板已存在，请创建新版本")
        
        # 保存模板文件
        safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name)
        safe_version = "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in version)
        template_filename = f"{safe_name}_{safe_version}_{uuid.uuid4().hex[:8]}.html"
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

    async def clone_template(self, template_id: int, new_version: Optional[str] = None) -> Template:
        """复制一个现有模板，生成 draft 状态的新版本，便于增量改动。"""
        original = self.db.query(Template).filter(Template.id == template_id).first()
        if not original:
            raise ValueError("模板不存在")

        target_version = (new_version or self._next_version_string(original.version)).strip()
        if not target_version:
            raise ValueError("新版本号不能为空")

        existing = self.db.query(Template).filter(
            Template.name == original.name,
            Template.version == target_version,
        ).first()
        if existing:
            raise ValueError("同名同版本模板已存在，请输入新的版本号")

        source_path = original.storage_path
        safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in original.name)
        safe_version = "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in target_version)
        new_filename = f"{safe_name}_{safe_version}_{uuid.uuid4().hex[:8]}.html"
        new_path = self.template_dir / new_filename
        if source_path and os.path.exists(source_path):
            shutil.copyfile(source_path, new_path)
        else:
            new_path.write_text("", encoding="utf-8")

        clone = Template(
            name=original.name,
            version=target_version,
            description=original.description,
            storage_path=str(new_path),
            status="draft",
        )
        self.db.add(clone)
        self.db.commit()
        self.db.refresh(clone)
        return clone

    @staticmethod
    def _next_version_string(version: str) -> str:
        """Best-effort to bump the trailing numeric segment by 1."""
        if not version:
            return "1.0.1"
        parts = version.split(".")
        for index in range(len(parts) - 1, -1, -1):
            piece = parts[index]
            if piece.isdigit():
                parts[index] = str(int(piece) + 1)
                return ".".join(parts)
        return f"{version}.1"

    async def get_template_by_id(self, template_id: int) -> Optional[Template]:
        """根据ID获取模板"""
        return self.db.query(Template).filter(Template.id == template_id).first()
    
    async def get_published_templates(self) -> List[Template]:
        """获取已发布的模板"""
        return self.db.query(Template).filter(
            Template.status == "published"
        ).order_by(Template.created_at.desc()).all()
