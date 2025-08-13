"""
PDF导出服务
"""
import os
import tempfile
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
import weasyprint
from weasyprint import HTML, CSS

from app.models.project import Project, ProjectItem
from app.models.uploaded_file import UploadedFile
from app.services.highlight_service import HighlightService

class PdfService:
    """PDF导出服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.highlight_service = HighlightService(db)
        
        # 默认CSS样式
        self.default_css = """
        @page {
            size: A4;
            margin: 2cm;
            @bottom-center {
                content: counter(page);
                font-size: 10px;
                color: #666;
            }
        }
        
        body {
            font-family: "SimSun", "Microsoft YaHei", "PingFang SC", "Hiragino Sans GB", sans-serif;
            font-size: 12px;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
        }
        
        .document-header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #5c7cfa;
        }
        
        .document-title {
            font-size: 24px;
            font-weight: bold;
            color: #5c7cfa;
            margin: 0 0 10px 0;
        }
        
        .document-meta {
            font-size: 10px;
            color: #666;
            margin: 5px 0;
        }
        
        .toc {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 25px;
            page-break-inside: avoid;
        }
        
        .toc-title {
            font-size: 16px;
            font-weight: bold;
            color: #5c7cfa;
            margin: 0 0 10px 0;
        }
        
        .toc-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .toc-item {
            margin: 5px 0;
            padding: 2px 0;
        }
        
        .toc-link {
            color: #5c7cfa;
            text-decoration: none;
            font-size: 11px;
        }
        
        .file-section {
            margin-bottom: 25px;
            page-break-inside: avoid;
            break-inside: avoid;
        }
        
        .file-header {
            background-color: #5c7cfa;
            color: white;
            padding: 8px 12px;
            font-weight: bold;
            font-size: 14px;
            margin: 0;
            border-radius: 3px 3px 0 0;
        }
        
        .file-content {
            border: 1px solid #e4e7ed;
            border-top: none;
            border-radius: 0 0 3px 3px;
            overflow: hidden;
        }
        
        .file-content pre {
            margin: 0;
            padding: 10px;
            font-family: "Consolas", "Monaco", "Courier New", monospace;
            font-size: 9px;
            line-height: 1.4;
            background-color: #f8f9fa;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        .highlight {
            background-color: transparent;
        }
        
        .linenos {
            color: #666;
            background-color: #f0f0f0;
            padding-right: 5px;
            border-right: 1px solid #ddd;
            user-select: none;
            display: inline-block;
            width: 30px;
            text-align: right;
        }
        
        .stats-section {
            margin-top: 30px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
            page-break-inside: avoid;
        }
        
        .stats-title {
            font-size: 14px;
            font-weight: bold;
            color: #5c7cfa;
            margin: 0 0 10px 0;
        }
        
        .stats-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 10px;
        }
        
        .stats-table th,
        .stats-table td {
            border: 1px solid #ddd;
            padding: 5px 8px;
            text-align: left;
        }
        
        .stats-table th {
            background-color: #f0f0f0;
            font-weight: bold;
        }
        
        .watermark {
            position: fixed;
            bottom: 10px;
            right: 10px;
            font-size: 8px;
            color: #ccc;
            z-index: 1000;
        }
        """
    
    async def export_project_to_pdf(
        self,
        project_id: int,
        user_id: int,
        options: Dict[str, Any] = None
    ) -> Optional[bytes]:
        """导出项目为PDF"""
        try:
            # 获取项目信息
            project = self.db.query(Project).filter(
                Project.id == project_id,
                Project.owner_id == user_id
            ).first()
            
            if not project:
                return None
            
            # 获取项目文件
            project_items = self.db.query(ProjectItem).join(UploadedFile).filter(
                ProjectItem.project_id == project_id,
                ProjectItem.include_in_export == True
            ).order_by(ProjectItem.order_index).all()
            
            if not project_items:
                return None
            
            # 生成HTML内容
            html_content = await self._generate_html_content(project, project_items, options)
            
            # 生成PDF
            pdf_bytes = self._html_to_pdf(html_content, options)
            
            return pdf_bytes
            
        except Exception as e:
            print(f"PDF导出失败: {str(e)}")
            return None
    
    async def _generate_html_content(
        self,
        project: Project,
        project_items: List[ProjectItem],
        options: Dict[str, Any] = None
    ) -> str:
        """生成HTML内容"""
        if not options:
            options = {}
        
        html_parts = []
        
        # HTML头部
        html_parts.append(f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{project.project_name}</title>
</head>
<body>""")
        
        # 文档头部
        html_parts.append(f"""
    <div class="document-header">
        <h1 class="document-title">{project.project_name}</h1>
        <div class="document-meta">生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</div>
        <div class="document-meta">项目类型：{'代码文件' if project.project_type == 'code' else '操作文档'}</div>
        <div class="document-meta">文件数量：{len(project_items)} 个</div>
    </div>""")
        
        # 目录（如果启用）
        if options.get('include_toc', True) and len(project_items) > 1:
            html_parts.append("""
    <div class="toc">
        <h2 class="toc-title">目录</h2>
        <ul class="toc-list">""")
            
            for i, item in enumerate(project_items):
                file_name = item.display_name or item.file.original_filename
                html_parts.append(f'            <li class="toc-item"><a href="#file-{i}" class="toc-link">{file_name}</a></li>')
            
            html_parts.append("""        </ul>
    </div>""")
        
        # 文件内容
        for i, item in enumerate(project_items):
            file_name = item.display_name or item.file.original_filename
            
            # 获取文件高亮内容
            highlight_result = await self.highlight_service.highlight_code(
                file_id=item.file_id,
                user_id=project.owner_id,
                language_override=item.language_override
            )
            
            html_parts.append(f"""
    <div class="file-section" id="file-{i}">
        <h3 class="file-header">{file_name}</h3>
        <div class="file-content">""")
            
            if highlight_result and highlight_result.get('highlighted_html'):
                html_parts.append(highlight_result['highlighted_html'])
            elif highlight_result and highlight_result.get('content'):
                html_parts.append(f'<pre><code>{highlight_result["content"]}</code></pre>')
            else:
                html_parts.append('<pre><code>无法加载文件内容</code></pre>')
            
            html_parts.append("""        </div>
    </div>""")
        
        # 统计信息（如果启用）
        if options.get('include_summary', True):
            total_lines = sum(
                item.get('line_count', 0) for item in [
                    await self.highlight_service.highlight_code(
                        file_id=pi.file_id,
                        user_id=project.owner_id,
                        language_override=pi.language_override
                    ) for pi in project_items
                ] if item
            )
            
            html_parts.append(f"""
    <div class="stats-section">
        <h2 class="stats-title">统计信息</h2>
        <table class="stats-table">
            <tr><th>项目名称</th><td>{project.project_name}</td></tr>
            <tr><th>文件数量</th><td>{len(project_items)} 个</td></tr>
            <tr><th>总行数</th><td>{total_lines} 行</td></tr>
            <tr><th>生成时间</th><td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
        </table>
    </div>""")
        
        # 水印（如果启用）
        if options.get('watermark', False):
            html_parts.append("""
    <div class="watermark">
        Generated by CodeWright
    </div>""")
        
        # HTML尾部
        html_parts.append("""
</body>
</html>""")
        
        return ''.join(html_parts)
    
    def _html_to_pdf(self, html_content: str, options: Dict[str, Any] = None) -> bytes:
        """将HTML转换为PDF"""
        if not options:
            options = {}
        
        # 创建HTML对象
        html_doc = HTML(string=html_content)
        
        # 创建CSS对象
        css_doc = CSS(string=self.default_css)
        
        # 生成PDF
        pdf_bytes = html_doc.write_pdf(stylesheets=[css_doc])
        
        return pdf_bytes
    
    def get_export_options(self) -> Dict[str, Any]:
        """获取导出选项说明"""
        return {
            'include_toc': {
                'name': '包含目录',
                'description': '在PDF中包含文件目录',
                'default': True
            },
            'include_summary': {
                'name': '包含统计信息',
                'description': '在PDF末尾包含项目统计信息',
                'default': True
            },
            'watermark': {
                'name': '添加水印',
                'description': '在PDF中添加生成工具水印',
                'default': False
            }
        }
