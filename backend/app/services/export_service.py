"""
导出服务
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
# from weasyprint import HTML, CSS
# from weasyprint.text.fonts import FontConfiguration

from app.models.project import Project
from app.models.export_history import ExportHistory
from app.services.project_service import ProjectService
from app.services.highlight_service import HighlightService

class ExportService:
    def __init__(self, db: Session):
        self.db = db
        self.project_service = ProjectService(db)
        self.highlight_service = HighlightService(db)
        self.export_dir = Path("../exports")
        self.export_dir.mkdir(exist_ok=True)
    
    async def export_project_to_pdf(
        self, 
        project_id: int, 
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """导出项目为PDF"""
        start_time = datetime.now()
        
        try:
            # 获取项目信息
            project = await self.project_service.get_project_by_id(project_id, user_id)
            if not project:
                return None
            
            # 获取项目文件列表
            files = await self.project_service.get_project_files(project_id, user_id)
            if not files:
                return None
            
            # 生成HTML内容
            html_content = await self._generate_html_content(project, files, user_id)

            # 生成HTML文件（暂时替代PDF）
            html_filename = f"project_{project_id}_{uuid.uuid4().hex[:8]}.html"
            html_path = self.export_dir / html_filename

            # 保存HTML文件
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # 记录导出历史
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            export_history = ExportHistory(
                project_id=project_id,
                exporter="code",
                status="success",
                duration_ms=duration_ms,
                file_path=str(html_path)
            )
            
            self.db.add(export_history)
            self.db.commit()
            
            return {
                "export_id": export_history.id,
                "file_path": str(html_path),
                "filename": html_filename,
                "duration_ms": duration_ms
            }
            
        except Exception as e:
            # 记录失败历史
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            export_history = ExportHistory(
                project_id=project_id,
                exporter="code",
                status="failed",
                duration_ms=duration_ms
            )
            
            self.db.add(export_history)
            self.db.commit()
            
            return None
    
    async def _generate_html_content(
        self, 
        project: Project, 
        files: list, 
        user_id: int
    ) -> str:
        """生成HTML内容"""
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="zh-CN">',
            '<head>',
            '<meta charset="UTF-8">',
            '<title>软件著作权申请材料 - ' + project.project_name + '</title>',
            '<style>',
            self._generate_css_content(),
            '</style>',
            '</head>',
            '<body>',
            '<div class="document">',
            '<h1 class="title">软件著作权申请材料</h1>',
            f'<h2 class="project-name">{project.project_name}</h2>',
            '<div class="meta-info">',
            f'<p>项目类型：{project.project_type}</p>',
            f'<p>生成时间：{datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}</p>',
            f'<p>文件总数：{len(files)}</p>',
            '</div>',
            '<div class="toc">',
            '<h3>目录</h3>',
            '<ul>'
        ]
        
        # 生成目录
        for i, file_info in enumerate(files, 1):
            html_parts.append(
                f'<li><a href="#file-{file_info["file_id"]}">{i}. {file_info["original_filename"]}</a></li>'
            )
        
        html_parts.extend([
            '</ul>',
            '</div>',
            '<div class="content">'
        ])
        
        # 生成文件内容
        for i, file_info in enumerate(files, 1):
            # 获取高亮后的代码
            highlighted = await self.highlight_service.highlight_code(
                file_info["file_id"], 
                user_id, 
                file_info.get("language_override")
            )
            
            if highlighted:
                html_parts.extend([
                    f'<div class="file-section" id="file-{file_info["file_id"]}">',
                    f'<h3 class="file-title">{i}. {file_info["original_filename"]}</h3>',
                    '<div class="file-meta">',
                    f'<p>文件大小：{file_info["file_size"]} 字节</p>',
                    f'<p>编程语言：{highlighted["language"]}</p>',
                    f'<p>代码行数：{highlighted["line_count"]} 行</p>',
                    '</div>',
                    '<div class="file-content">',
                    highlighted["highlighted_html"],
                    '</div>',
                    '</div>'
                ])
        
        html_parts.extend([
            '</div>',
            '</div>',
            '</body>',
            '</html>'
        ])
        
        return '\n'.join(html_parts)
    
    def _generate_css_content(self) -> str:
        """生成CSS样式"""
        # 获取代码高亮CSS
        highlight_css = self.highlight_service.get_highlight_css()
        
        base_css = """
        @page {
            size: A4;
            margin: 2cm;
        }
        
        body {
            font-family: "SimSun", "宋体", serif;
            font-size: 12pt;
            line-height: 1.6;
            color: #333;
        }
        
        .document {
            max-width: 100%;
        }
        
        .title {
            text-align: center;
            font-size: 24pt;
            font-weight: bold;
            margin-bottom: 20pt;
            color: #000;
        }
        
        .project-name {
            text-align: center;
            font-size: 18pt;
            font-weight: bold;
            margin-bottom: 30pt;
            color: #333;
        }
        
        .meta-info {
            margin-bottom: 30pt;
            padding: 15pt;
            background-color: #f8f8f8;
            border: 1pt solid #ddd;
        }
        
        .meta-info p {
            margin: 5pt 0;
        }
        
        .toc {
            margin-bottom: 30pt;
            page-break-after: always;
        }
        
        .toc h3 {
            font-size: 16pt;
            font-weight: bold;
            margin-bottom: 15pt;
        }
        
        .toc ul {
            list-style-type: none;
            padding-left: 0;
        }
        
        .toc li {
            margin: 8pt 0;
            padding-left: 20pt;
        }
        
        .toc a {
            text-decoration: none;
            color: #333;
        }
        
        .file-section {
            margin-bottom: 40pt;
            page-break-before: always;
        }
        
        .file-title {
            font-size: 16pt;
            font-weight: bold;
            margin-bottom: 15pt;
            color: #000;
            border-bottom: 2pt solid #333;
            padding-bottom: 5pt;
        }
        
        .file-meta {
            margin-bottom: 15pt;
            padding: 10pt;
            background-color: #f0f0f0;
            border-left: 4pt solid #333;
        }
        
        .file-meta p {
            margin: 3pt 0;
            font-size: 10pt;
        }
        
        .file-content {
            margin-top: 15pt;
        }
        
        .highlight {
            font-family: "Consolas", "Monaco", "Courier New", monospace;
            font-size: 9pt;
            line-height: 1.4;
            background-color: #f8f8f8;
            border: 1pt solid #ddd;
            padding: 10pt;
            overflow: hidden;
        }
        
        .highlight table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .highlight .linenos {
            width: 40pt;
            text-align: right;
            padding-right: 10pt;
            border-right: 1pt solid #ddd;
            background-color: #f0f0f0;
            color: #666;
        }
        
        .highlight .code {
            padding-left: 10pt;
        }
        """
        
        return base_css + "\n" + highlight_css
