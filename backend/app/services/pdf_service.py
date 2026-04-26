"""
PDF导出服务
"""
import base64
import json
import os
import re
import shutil
import subprocess
import tempfile
from io import BytesIO
from html import escape
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import bleach
from markdown_it import MarkdownIt
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.orm import Session

from app.models.manual_section import ManualSection
from app.models.project import Project, ProjectItem
from app.models.file import UploadedFile
from app.models.setting import Setting
from app.models.template import Template
from app.paths import TINYTEX_DIR, TINYTEX_DOWNLOAD_DIR
from app.services.highlight_service import HighlightService


class PdfService:
    """PDF导出服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.highlight_service = HighlightService(db)
        self.markdown = MarkdownIt("commonmark", {"html": False})
    
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
            
            options = self._options_for_project(project, options)
            manual_sections: list[ManualSection] | None = None
            code_items: list[ProjectItem] | None = None

            if project.project_type == "manual":
                sections = self.db.query(ManualSection).filter(
                    ManualSection.project_id == project_id
                ).order_by(ManualSection.order_index, ManualSection.id).all()

                if not sections:
                    return None

                manual_sections = sections
            else:
                # 获取项目文件
                project_items = self.db.query(ProjectItem).join(UploadedFile).filter(
                    ProjectItem.project_id == project_id,
                    ProjectItem.include_in_export == True
                ).order_by(ProjectItem.order_index).all()
                
                if not project_items:
                    return None

                code_items = project_items
            
            # PDF 导出固定走 LaTeX 链路，避免 HTML 引擎缺失时生成乱码 PDF。
            try:
                pdf_bytes = await self._generate_latex_pdf(
                    project=project,
                    options=options,
                    project_items=code_items,
                    sections=manual_sections,
                )
            except RuntimeError as e:
                if not self._image_pdf_fallback_enabled():
                    raise
                print(f"LaTeX PDF 不可用，测试环境使用图片型PDF降级: {str(e)}")
                pdf_bytes = await self._generate_image_pdf_fallback(
                    project=project,
                    options=options,
                    project_items=code_items,
                    sections=manual_sections,
                )
            
            return pdf_bytes
            
        except RuntimeError:
            raise
        except Exception as e:
            print(f"PDF导出失败: {str(e)}")
            return None

    async def render_project_html(
        self,
        project_id: int,
        user_id: int,
        options: Dict[str, Any] = None
    ) -> Optional[str]:
        """生成项目 HTML，用于预览或 PDF 渲染。"""
        project = self.db.query(Project).filter(
            Project.id == project_id,
            Project.owner_id == user_id
        ).first()
        if not project:
            return None

        options = self._options_for_project(project, options)
        if project.project_type == "manual":
            sections = self.db.query(ManualSection).filter(
                ManualSection.project_id == project_id
            ).order_by(ManualSection.order_index, ManualSection.id).all()
            if not sections:
                return None
            return self._generate_manual_html_content(project, sections, options)

        project_items = self.db.query(ProjectItem).join(UploadedFile).filter(
            ProjectItem.project_id == project_id,
            ProjectItem.include_in_export == True
        ).order_by(ProjectItem.order_index).all()
        if not project_items:
            return None
        return await self._generate_html_content(project, project_items, options)
    
    async def _generate_html_content(
        self,
        project: Project,
        project_items: List[ProjectItem],
        options: Dict[str, Any] = None
    ) -> str:
        """生成HTML内容"""
        options = self._normalize_options(options)
        project_name = escape(project.project_name)
        body_class = "code-layout-double" if options.get("layout") == "double_column" else "code-layout-single"
        total_lines = 0
        next_line_number = 1
        file_contexts: list[dict[str, Any]] = []
        content_parts: list[str] = []
        
        # HTML头部
        html_parts = [f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{project_name}</title>
</head>
<body class="{body_class}">"""]
        
        # 文档头部
        html_parts.append(f"""
    <div class="document-header">
        <h1 class="document-title">{project_name}</h1>
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
                file_name = escape(item.display_name or item.file.original_filename)
                html_parts.append(f'            <li class="toc-item"><a href="#file-{i}" class="toc-link">{file_name}</a></li>')
            
            html_parts.append("""        </ul>
    </div>""")
        
        content_parts.append('<div class="content-sections">')
        for i, item in enumerate(project_items):
            file_name = escape(item.display_name or item.file.original_filename)
            
            # 获取文件高亮内容
            highlight_result = await self.highlight_service.highlight_code(
                file_id=item.file_id,
                user_id=project.owner_id,
                language_override=item.language_override,
                line_numbers=bool(options.get("line_numbers", True)),
                highlight_syntax=bool(options.get("highlight_syntax", True)),
                line_start=next_line_number
            )

            if highlight_result:
                total_lines += int(highlight_result.get("line_count") or 0)
                if options.get("continuous_line_numbers", False) and options.get("line_numbers", True):
                    next_line_number += int(highlight_result.get("line_count") or 0)
            
            content_parts.append(f"""
    <div class="file-section" id="file-{i}">
        <h3 class="file-header">{file_name}</h3>
        <div class="file-content">""")
            
            if highlight_result and highlight_result.get('highlighted_html'):
                highlighted_html = highlight_result['highlighted_html']
                content_parts.append(highlighted_html)
            elif highlight_result and highlight_result.get('content'):
                highlighted_html = f'<pre><code>{escape(highlight_result["content"])}</code></pre>'
                content_parts.append(highlighted_html)
            else:
                highlighted_html = '<pre><code>无法加载文件内容</code></pre>'
                content_parts.append(highlighted_html)
            
            content_parts.append("""        </div>
    </div>""")
            file_contexts.append({
                "filename": item.display_name or item.file.original_filename,
                "language": highlight_result.get("language") if highlight_result else "text",
                "line_count": highlight_result.get("line_count") if highlight_result else 0,
                "highlighted_content": highlighted_html,
            })

        content_parts.append("</div>")
        html_parts.append("".join(content_parts))
        
        # 统计信息（如果启用）
        if options.get('include_summary', True):
            html_parts.append(f"""
    <div class="stats-section">
        <h2 class="stats-title">统计信息</h2>
        <table class="stats-table">
            <tr><th>项目名称</th><td>{project_name}</td></tr>
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

        default_html = ''.join(html_parts)
        return self._render_selected_template(
            options,
            default_html,
            {
                "project_name": project.project_name,
                "project_type": "代码文件",
                "generated_time": datetime.now().strftime("%Y年%m月%d日 %H:%M:%S"),
                "file_count": len(project_items),
                "total_lines": total_lines,
                "content": "".join(content_parts),
                "files": file_contexts,
            }
        )

    def _generate_manual_html_content(
        self,
        project: Project,
        sections: List[ManualSection],
        options: Dict[str, Any] = None
    ) -> str:
        """生成操作文档HTML内容"""
        options = self._normalize_options(options)
        project_name = escape(project.project_name)
        software_name = escape(options.get("software_name") or project.project_name)
        version = escape(options.get("version") or "")
        developer = escape(options.get("developer") or "")
        variables = {
            "project_name": project.project_name,
            "software_name": options.get("software_name") or project.project_name,
            "version": options.get("version") or "",
            "developer": options.get("developer") or "",
        }
        section_contexts: list[dict[str, Any]] = []
        section_parts: list[str] = []

        html_parts = [f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{project_name}</title>
</head>
<body>
    <div class="document-header">
        <h1 class="document-title">{project_name}</h1>
        <div class="document-meta">软件名称：{software_name}</div>
        {f'<div class="document-meta">版本号：{version}</div>' if version else ''}
        {f'<div class="document-meta">开发者：{developer}</div>' if developer else ''}
        <div class="document-meta">生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</div>
        <div class="document-meta">项目类型：操作文档</div>
        <div class="document-meta">章节数量：{len(sections)} 个</div>
    </div>"""]

        if options.get("include_toc", True) and len(sections) > 1:
            html_parts.append("""
    <div class="toc">
        <h2 class="toc-title">目录</h2>
        <ul class="toc-list">""")
            for index, section in enumerate(sections):
                html_parts.append(
                    f'            <li class="toc-item"><a href="#section-{index}" class="toc-link">{escape(section.title)}</a></li>'
                )
            html_parts.append("""        </ul>
    </div>""")

        for index, section in enumerate(sections):
            image_html = ""
            image_uri = self._image_data_uri(section.image_file)
            if image_uri:
                image_html = f'<img src="{image_uri}" alt="{escape(section.title)}" />'
            body_html = self._render_markdown(
                section.body_markdown,
                variables if options.get("enable_global_variables", True) else None
            )

            section_html = f"""
    <section class="manual-section" id="section-{index}">
        <h2>{index + 1}. {escape(section.title)}</h2>
        {image_html}
        <div class="manual-body">
            {body_html}
        </div>
    </section>"""
            html_parts.append(section_html)
            section_parts.append(section_html)
            section_contexts.append({
                "title": section.title,
                "body_html": body_html,
                "image_html": image_html,
                "order_index": index + 1,
            })

        if options.get("include_summary", True):
            html_parts.append(f"""
    <div class="stats-section">
        <h2 class="stats-title">统计信息</h2>
        <table class="stats-table">
            <tr><th>项目名称</th><td>{project_name}</td></tr>
            <tr><th>章节数量</th><td>{len(sections)} 个</td></tr>
            <tr><th>生成时间</th><td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
        </table>
    </div>""")

        if options.get("watermark", False):
            html_parts.append("""
    <div class="watermark">
        Generated by CodeWright
    </div>""")

        html_parts.append("""
</body>
</html>""")
        default_html = "".join(html_parts)
        return self._render_selected_template(
            options,
            default_html,
            {
                "project_name": project.project_name,
                "software_name": options.get("software_name") or project.project_name,
                "version": options.get("version") or "",
                "developer": options.get("developer") or "",
                "project_type": "操作文档",
                "generated_time": datetime.now().strftime("%Y年%m月%d日 %H:%M:%S"),
                "section_count": len(sections),
                "sections": "".join(section_parts),
                "content": "".join(section_parts),
                "section_items": section_contexts,
            }
        )

    def _render_markdown(self, markdown: str, variables: Optional[dict[str, str]] = None) -> str:
        """Render and sanitize manual section markdown."""
        if variables:
            markdown = self._apply_global_variables(markdown, variables)
        html = self.markdown.render(markdown)
        allowed_tags = [
            "p", "br", "strong", "em", "ul", "ol", "li", "blockquote",
            "code", "pre", "h1", "h2", "h3", "h4", "table", "thead",
            "tbody", "tr", "th", "td", "a"
        ]
        allowed_attrs = {
            "a": ["href", "title"],
            "th": ["align"],
            "td": ["align"],
        }
        return bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs, strip=True)

    def _apply_global_variables(self, value: str, variables: dict[str, str]) -> str:
        """替换手册正文中的全局变量。"""
        aliases = {
            "project_name": variables.get("project_name", ""),
            "项目名称": variables.get("project_name", ""),
            "software_name": variables.get("software_name", ""),
            "软件名称": variables.get("software_name", ""),
            "version": variables.get("version", ""),
            "版本号": variables.get("version", ""),
            "developer": variables.get("developer", ""),
            "开发者": variables.get("developer", ""),
        }
        for key, replacement in aliases.items():
            value = value.replace("{{" + key + "}}", replacement)
            value = value.replace("{{ " + key + " }}", replacement)
        return value

    def _render_selected_template(
        self,
        options: dict[str, Any],
        default_html: str,
        context: dict[str, Any]
    ) -> str:
        """使用已发布模板渲染 HTML；无匹配模板时返回默认 HTML。"""
        template = self._resolve_template(options)
        if not template:
            return default_html

        try:
            template_content = Path(template.storage_path).read_text(encoding="utf-8")
        except Exception:
            return default_html

        render_context = {
            **context,
            "html": default_html,
            "summary": context.get("content", ""),
        }
        loop_collections = {
            "files": context.get("files", []),
            "sections": context.get("section_items", []),
        }
        return self._render_template_string(template_content, render_context, loop_collections)

    def _resolve_template(self, options: dict[str, Any]) -> Optional[Template]:
        template_id = options.get("template_id")
        template_key = str(options.get("template") or "").strip()
        if not template_id and template_key.isdigit():
            template_id = int(template_key)

        query = self.db.query(Template).filter(Template.status == "published")
        if template_id:
            return query.filter(Template.id == int(template_id)).first()

        if not template_key or template_key in {"standard", "detailed", "simple"}:
            return None

        return query.filter(Template.name == template_key).order_by(
            Template.updated_at.desc(),
            Template.created_at.desc()
        ).first()

    def _render_template_string(
        self,
        template: str,
        context: dict[str, Any],
        loop_collections: dict[str, list[dict[str, Any]]]
    ) -> str:
        safe_fields = {"content", "html", "summary", "sections", "highlighted_content", "body_html", "image_html"}

        def resolve_expr(expr: str, item: Optional[dict[str, Any]] = None, index: int = 0, var_name: str = "") -> tuple[Any, bool]:
            expr = expr.strip()
            safe = expr.endswith("|safe")
            expr = expr.replace("|safe", "").strip()

            if expr == "loop.index":
                return index + 1, safe

            if item is not None and var_name and expr.startswith(f"{var_name}."):
                key = expr.split(".", 1)[1]
                return item.get(key, ""), safe or key in safe_fields

            return context.get(expr, ""), safe or expr in safe_fields

        def render_vars(fragment: str, item: Optional[dict[str, Any]] = None, index: int = 0, var_name: str = "") -> str:
            def replace_var(match: re.Match[str]) -> str:
                value, safe = resolve_expr(match.group(1), item, index, var_name)
                return str(value) if safe else escape(str(value))

            return re.sub(r"{{\s*([^}]+?)\s*}}", replace_var, fragment)

        def replace_loop(match: re.Match[str]) -> str:
            var_name = match.group(1)
            collection_name = match.group(2)
            fragment = match.group(3)
            items = loop_collections.get(collection_name, [])
            return "".join(
                render_vars(fragment, item=item, index=index, var_name=var_name)
                for index, item in enumerate(items)
            )

        rendered = re.sub(
            r"{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%}(.*?){%\s*endfor\s*%}",
            replace_loop,
            template,
            flags=re.DOTALL,
        )
        return render_vars(rendered)

    def _image_data_uri(self, image_file: Optional[UploadedFile]) -> Optional[str]:
        """Read an uploaded image as a data URI for PDF rendering."""
        if not image_file or not image_file.file_type.startswith("image/"):
            return None

        try:
            with open(image_file.storage_path, "rb") as image:
                encoded = base64.b64encode(image.read()).decode("ascii")
                return f"data:{image_file.file_type};base64,{encoded}"
        except Exception:
            return None

    def _image_pdf_fallback_enabled(self) -> bool:
        """Only tests may opt into the old non-LaTeX fallback."""
        return os.getenv("CODEWRIGHT_ALLOW_IMAGE_PDF_FALLBACK") == "1"

    async def _generate_latex_pdf(
        self,
        project: Project,
        options: dict[str, Any],
        project_items: Optional[list[ProjectItem]] = None,
        sections: Optional[list[ManualSection]] = None,
    ) -> bytes:
        """Generate a PDF by writing LaTeX first and compiling it with XeLaTeX."""
        style = self._get_latex_style()
        with tempfile.TemporaryDirectory(prefix="codewright-latex-") as temp_dir:
            work_dir = Path(temp_dir)
            tex_path = work_dir / "codewright_export.tex"
            tex_content = await self._build_latex_document(
                project=project,
                options=options,
                style=style,
                asset_dir=work_dir,
                project_items=project_items,
                sections=sections,
            )
            tex_path.write_text(tex_content, encoding="utf-8")
            return self._compile_latex_to_pdf(tex_path, style)

    async def _build_latex_document(
        self,
        project: Project,
        options: dict[str, Any],
        style: dict[str, Any],
        asset_dir: Path,
        project_items: Optional[list[ProjectItem]] = None,
        sections: Optional[list[ManualSection]] = None,
    ) -> str:
        """Build the full LaTeX source from semantic project data."""
        generated_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        project_type = "代码文件" if project.project_type == "code" else "操作文档"
        parts = [
            self._build_latex_preamble(project.project_name, generated_time, style),
            r"\begin{document}",
            r"\maketitle",
            r"\thispagestyle{fancy}",
            r"\begin{center}",
            r"\begin{tabular}{rl}",
            f"生成时间 & {self._latex_escape(generated_time)} \\\\",
            f"项目类型 & {self._latex_escape(project_type)} \\\\",
        ]

        if project.project_type == "manual":
            section_list = sections or []
            software_name = options.get("software_name") or project.project_name
            parts.extend([
                f"软件名称 & {self._latex_escape(str(software_name))} \\\\",
            ])
            if options.get("version"):
                parts.append(f"版本号 & {self._latex_escape(str(options.get('version')))} \\\\")
            if options.get("developer"):
                parts.append(f"开发者 & {self._latex_escape(str(options.get('developer')))} \\\\")
            parts.append(f"章节数量 & {len(section_list)} 个 \\\\")
        else:
            item_list = project_items or []
            parts.append(f"文件数量 & {len(item_list)} 个 \\\\")

        parts.extend([
            r"\end{tabular}",
            r"\end{center}",
            "",
        ])

        if options.get("include_toc", True):
            parts.extend([r"\tableofcontents", r"\newpage", ""])

        if project.project_type == "manual":
            body, total_count = self._manual_sections_to_latex(
                sections or [],
                project,
                options,
                asset_dir,
            )
            summary_label = "章节数量"
        else:
            body, total_count = await self._code_items_to_latex(
                project_items or [],
                project,
                options,
            )
            summary_label = "总行数"

        parts.append(body)

        if options.get("include_summary", True):
            parts.extend([
                r"\newpage",
                r"\section*{统计信息}",
                r"\addcontentsline{toc}{section}{统计信息}",
                r"\begin{tabular}{ll}",
                f"项目名称 & {self._latex_escape(project.project_name)} \\\\",
                f"{summary_label} & {total_count} \\\\",
                f"生成时间 & {self._latex_escape(generated_time)} \\\\",
                r"\end{tabular}",
            ])

        if options.get("watermark", False):
            parts.extend([
                "",
                r"\vfill",
                r"\begin{center}\footnotesize Generated by CodeWright\end{center}",
            ])

        parts.append(r"\end{document}")
        return "\n".join(parts)

    def _build_latex_preamble(self, title: str, generated_time: str, style: dict[str, Any]) -> str:
        document_class = str(style.get("document_class") or "article").strip() or "article"
        font_size = str(style.get("font_size") or "12pt").strip() or "12pt"
        geometry = str(style.get("page_geometry") or "a4paper,margin=2cm").strip() or "a4paper,margin=2cm"
        main_font = str(style.get("main_font") or "PingFang SC").strip()
        mono_font = str(style.get("mono_font") or "Menlo").strip()
        line_stretch = str(style.get("line_stretch") or "1.25").strip() or "1.25"
        header_latex = str(style.get("header_latex") or "").strip()
        footer_latex = str(style.get("footer_latex") or r"\thepage").strip() or r"\thepage"
        preamble_latex = str(style.get("preamble_latex") or "").strip()

        parts = [
            f"\\documentclass[{font_size}]{{{document_class}}}",
            r"\usepackage{fontspec}",
            r"\usepackage{xeCJK}",
            r"\usepackage{xcolor}",
            r"\usepackage{geometry}",
            r"\usepackage{graphicx}",
            r"\usepackage{fancyhdr}",
            r"\usepackage{hyperref}",
            r"\usepackage{booktabs}",
            r"\usepackage{array}",
            r"\usepackage{longtable}",
            r"\usepackage{fvextra}",
            r"\usepackage{setspace}",
            f"\\geometry{{{geometry}}}",
            f"\\setstretch{{{line_stretch}}}",
            r"\definecolor{codewrightBlue}{HTML}{147ED6}",
            r"\definecolor{codewrightText}{HTML}{102033}",
            r"\definecolor{codewrightMuted}{HTML}{667587}",
            r"\hypersetup{colorlinks=true,linkcolor=codewrightBlue,urlcolor=codewrightBlue}",
            r"\pagestyle{fancy}",
            r"\fancyhf{}",
            f"\\fancyhead[C]{{{header_latex}}}",
            f"\\fancyfoot[C]{{{footer_latex}}}",
            r"\setlength{\headheight}{15pt}",
            r"\fvset{breaklines=true,breakanywhere=true,fontsize=\small,frame=single,framesep=2mm,tabsize=2}",
        ]

        parts.append(self._latex_font_setup(main_font, mono_font))

        if preamble_latex:
            parts.extend(["", "% Custom PDF style from admin settings", preamble_latex])

        parts.extend([
            "",
            f"\\title{{{self._latex_escape(title)}}}",
            r"\author{CodeWright}",
            f"\\date{{{self._latex_escape(generated_time)}}}",
        ])
        return "\n".join(parts)

    def _latex_font_setup(self, main_font: str, mono_font: str) -> str:
        cjk_candidates = [
            main_font,
            "PingFang SC",
            "Songti SC",
            "Heiti SC",
            "Noto Sans CJK SC",
            "Noto Serif CJK SC",
            "Microsoft YaHei",
            "SimSun",
        ]
        mono_candidates = [
            mono_font,
            "Menlo",
            "Monaco",
            "Consolas",
            "Courier New",
        ]

        def unique(values: list[str]) -> list[str]:
            seen: set[str] = set()
            result: list[str] = []
            for value in values:
                normalized = str(value or "").strip()
                if normalized and normalized not in seen:
                    seen.add(normalized)
                    result.append(normalized)
            return result

        def fallback_chain(candidates: list[str], command_builder, fallback: str = "") -> str:
            chain = fallback
            for font in reversed(unique(candidates)):
                chain = f"\\IfFontExistsTF{{{font}}}{{{command_builder(font)}}}{{{chain}}}"
            return chain

        cjk_chain = fallback_chain(
            cjk_candidates,
            lambda font: f"\\setmainfont{{{font}}}\\setCJKmainfont{{{font}}}\\setCJKmonofont{{{font}}}",
        )
        mono_chain = fallback_chain(
            mono_candidates,
            lambda font: f"\\setmonofont{{{font}}}",
            r"\setmonofont{Latin Modern Mono}",
        )
        return "\n".join([cjk_chain, mono_chain])

    async def _code_items_to_latex(
        self,
        project_items: list[ProjectItem],
        project: Project,
        options: dict[str, Any],
    ) -> tuple[str, int]:
        parts: list[str] = []
        total_lines = 0
        next_line_number = 1

        for index, item in enumerate(project_items, 1):
            file_name = item.display_name or item.file.original_filename
            highlight_result = await self.highlight_service.highlight_code(
                file_id=item.file_id,
                user_id=project.owner_id,
                language_override=item.language_override,
                line_numbers=False,
                highlight_syntax=False,
            )
            content = highlight_result.get("content") if highlight_result else "无法加载文件内容"
            line_count = len(str(content).splitlines()) or 1
            total_lines += line_count

            parts.extend([
                f"\\section{{{self._latex_escape(file_name)}}}",
                self._latex_code_block(
                    str(content),
                    options=options,
                    first_number=next_line_number,
                ),
                "",
            ])
            if options.get("continuous_line_numbers", False) and options.get("line_numbers", True):
                next_line_number += line_count

        return "\n".join(parts), total_lines

    def _manual_sections_to_latex(
        self,
        sections: list[ManualSection],
        project: Project,
        options: dict[str, Any],
        asset_dir: Path,
    ) -> tuple[str, int]:
        parts: list[str] = []
        variables = {
            "project_name": project.project_name,
            "software_name": options.get("software_name") or project.project_name,
            "version": options.get("version") or "",
            "developer": options.get("developer") or "",
        }

        for index, section in enumerate(sections, 1):
            parts.append(f"\\section{{{self._latex_escape(section.title)}}}")
            image_path = self._copy_latex_image(section.image_file, asset_dir, index)
            if image_path:
                parts.extend([
                    r"\begin{figure}[htbp]",
                    r"\centering",
                    f"\\includegraphics[width=0.92\\linewidth]{{{image_path.name}}}",
                    r"\end{figure}",
                    "",
                ])
            parts.append(self._markdown_to_latex(
                section.body_markdown,
                variables if options.get("enable_global_variables", True) else None
            ))
            parts.append("")

        return "\n".join(parts), len(sections)

    def _markdown_to_latex(self, value: str, variables: Optional[dict[str, str]] = None) -> str:
        if variables:
            value = self._apply_global_variables(value, variables)

        lines = value.splitlines()
        parts: list[str] = []
        in_code = False
        list_type: Optional[str] = None

        def close_list() -> None:
            nonlocal list_type
            if list_type:
                parts.append(r"\end{" + list_type + "}")
                list_type = None

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("```"):
                close_list()
                if in_code:
                    parts.append(r"\end{Verbatim}")
                    in_code = False
                else:
                    parts.append(r"\begin{Verbatim}[breaklines=true,breakanywhere=true,fontsize=\small,frame=single]")
                    in_code = True
                continue

            if in_code:
                parts.append(self._sanitize_verbatim(line))
                continue

            if not stripped:
                close_list()
                parts.append("")
                continue

            heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
            if heading:
                close_list()
                level = len(heading.group(1))
                command = "subsection" if level <= 2 else "subsubsection"
                parts.append(f"\\{command}*{{{self._latex_escape(heading.group(2))}}}")
                continue

            unordered = re.match(r"^[-*]\s+(.+)$", stripped)
            ordered = re.match(r"^\d+[.)]\s+(.+)$", stripped)
            if unordered or ordered:
                target_list = "itemize" if unordered else "enumerate"
                if list_type != target_list:
                    close_list()
                    parts.append(r"\begin{" + target_list + "}")
                    list_type = target_list
                item_text = (unordered or ordered).group(1)
                parts.append(r"\item " + self._latex_escape(item_text))
                continue

            close_list()
            parts.append(self._latex_escape(stripped) + r"\par")

        close_list()
        if in_code:
            parts.append(r"\end{Verbatim}")
        return "\n".join(parts)

    def _latex_code_block(self, content: str, options: dict[str, Any], first_number: int = 1) -> str:
        block_options = [
            "breaklines=true" if options.get("wrap_lines", True) else "breaklines=false",
            "breakanywhere=true",
            "fontsize=\\small",
            "frame=single",
            "framesep=2mm",
            "tabsize=2",
        ]
        if options.get("line_numbers", True):
            block_options.extend(["numbers=left", "numbersep=6pt"])
            if options.get("continuous_line_numbers", False):
                block_options.append(f"firstnumber={first_number}")

        return (
            "\\begin{Verbatim}[" + ",".join(block_options) + "]\n"
            + self._sanitize_verbatim(content)
            + "\n\\end{Verbatim}"
        )

    def _sanitize_verbatim(self, value: str) -> str:
        return value.replace(r"\end{Verbatim}", r"\\end{Verbatim}")

    def _copy_latex_image(
        self,
        image_file: Optional[UploadedFile],
        asset_dir: Path,
        index: int,
    ) -> Optional[Path]:
        if not image_file or not image_file.file_type.startswith("image/"):
            return None

        source = Path(image_file.storage_path)
        if not source.exists():
            return None

        suffix = source.suffix.lower() or ".png"
        target = asset_dir / f"manual_image_{index}{suffix}"
        try:
            shutil.copyfile(source, target)
            return target
        except Exception:
            return None

    def _compile_latex_to_pdf(self, tex_path: Path, style: dict[str, Any]) -> bytes:
        engine = str(style.get("latex_engine") or "xelatex").strip() or "xelatex"
        if engine != "xelatex":
            raise RuntimeError("当前仅支持 xelatex 作为 LaTeX PDF 引擎")

        if os.getenv("CODEWRIGHT_USE_SYSTEM_XELATEX", "0") == "1":
            engine_path = shutil.which(engine)
            if engine_path:
                return self._compile_latex_with_subprocess(tex_path, engine_path)

        if self._image_pdf_fallback_enabled():
            raise RuntimeError("测试环境跳过 PyTinyTeX 自动下载")

        return self._compile_latex_with_pytinytex(tex_path, engine)

    def _compile_latex_with_subprocess(self, tex_path: Path, engine_path: str) -> bytes:
        command = [
            engine_path,
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-file-line-error",
            "-no-shell-escape",
            tex_path.name,
        ]
        last_result: subprocess.CompletedProcess[str] | None = None
        for _ in range(2):
            last_result = subprocess.run(
                command,
                cwd=tex_path.parent,
                capture_output=True,
                text=True,
                timeout=90,
                check=False,
            )
            if last_result.returncode != 0:
                break

        pdf_path = tex_path.with_suffix(".pdf")
        if last_result is None or last_result.returncode != 0 or not pdf_path.exists():
            log_path = tex_path.with_suffix(".log")
            log_text = ""
            if log_path.exists():
                log_text = log_path.read_text(encoding="utf-8", errors="replace")
            output = "\n".join(filter(None, [last_result.stdout if last_result else "", last_result.stderr if last_result else "", log_text]))
            error_tail = "\n".join(output.splitlines()[-20:]).strip()
            raise RuntimeError(f"LaTeX PDF 生成失败{': ' + error_tail if error_tail else ''}")

        return pdf_path.read_bytes()

    def _compile_latex_with_pytinytex(self, tex_path: Path, engine: str) -> bytes:
        """Use PyTinyTeX-managed TinyTeX when no system xelatex exists."""
        try:
            import pytinytex
        except ImportError as e:
            raise RuntimeError("未安装 PyTinyTeX，无法在项目内初始化 xelatex") from e

        self._ensure_pytinytex_engine(pytinytex, engine)
        self._ensure_pytinytex_latex_packages(pytinytex)

        result = pytinytex.compile(
            str(tex_path),
            engine=engine,
            output_dir=str(tex_path.parent),
            num_runs=2,
            auto_install=True,
            extra_args=["-halt-on-error", "-file-line-error", "-no-shell-escape"],
        )
        pdf_path = Path(result.pdf_path)
        if result.success and pdf_path.exists():
            return pdf_path.read_bytes()

        error_messages = []
        for error in getattr(result, "errors", []) or []:
            line = f"line {error.line}: " if getattr(error, "line", None) else ""
            error_messages.append(f"{line}{error.message}")
        if not error_messages:
            error_messages = (getattr(result, "output", "") or "").splitlines()[-20:]
        error_tail = "\n".join(str(item) for item in error_messages if str(item).strip()).strip()
        raise RuntimeError(f"LaTeX PDF 生成失败{': ' + error_tail if error_tail else ''}")

    def _ensure_pytinytex_engine(self, pytinytex: Any, engine: str) -> str:
        TINYTEX_DIR.mkdir(parents=True, exist_ok=True)
        TINYTEX_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        os.environ["PYTINYTEX_TINYTEX"] = str(TINYTEX_DIR)
        pytinytex.clear_path_cache()

        try:
            return pytinytex.get_engine(engine)
        except RuntimeError:
            try:
                pytinytex.download_tinytex(
                    variation=int(os.getenv("CODEWRIGHT_TINYTEX_VARIATION", "2")),
                    target_folder=TINYTEX_DIR,
                    download_folder=TINYTEX_DOWNLOAD_DIR,
                )
                pytinytex.clear_path_cache()
                return pytinytex.get_engine(engine)
            except Exception as e:
                raise RuntimeError(
                    "项目内 TinyTeX 初始化失败。首次 PDF 导出需要联网下载 TinyTeX；"
                    "也可设置 CODEWRIGHT_TINYTEX_DIR 指向已有 TinyTeX 目录。"
                ) from e

    def _ensure_pytinytex_latex_packages(self, pytinytex: Any) -> None:
        if os.getenv("CODEWRIGHT_TINYTEX_AUTO_INSTALL_PACKAGES", "1") == "0":
            return

        marker = TINYTEX_DIR / ".codewright_latex_packages_ready"
        if marker.exists():
            return

        # TinyTeX variation 2 on macOS may still omit xeCJK/fvextra; install
        # the LaTeX packages required by CodeWright's generated preamble.
        required_packages = [
            "xecjk",
            "fvextra",
            "fontspec",
            "xcolor",
            "geometry",
            "graphicx",
            "fancyhdr",
            "hyperref",
            "booktabs",
            "longtable",
            "setspace",
        ]
        failures: list[str] = []
        for package in required_packages:
            try:
                exit_code, output = pytinytex.install(package)
                if exit_code != 0:
                    failures.append(f"{package}: {output}")
            except Exception as e:
                failures.append(f"{package}: {str(e)}")

        if failures:
            raise RuntimeError("TinyTeX 宏包安装失败: " + "; ".join(failures[:3]))
        marker.write_text(datetime.now().isoformat(), encoding="utf-8")

    def _get_latex_style(self) -> dict[str, Any]:
        defaults = {
            "latex_engine": "xelatex",
            "document_class": "article",
            "font_size": "12pt",
            "page_geometry": "a4paper,margin=2cm",
            "main_font": "PingFang SC",
            "mono_font": "Menlo",
            "line_stretch": "1.25",
            "header_latex": "",
            "footer_latex": r"\thepage",
            "preamble_latex": "",
        }
        setting = self.db.query(Setting).filter(Setting.key == "pdf_style").first()
        if not setting:
            return defaults
        try:
            value = json.loads(setting.value)
            return {**defaults, **self._migrate_legacy_pdf_style(value)}
        except json.JSONDecodeError:
            return defaults

    def _migrate_legacy_pdf_style(self, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            return {}

        migrated = dict(value)
        if "page_margin" in value and "page_geometry" not in value:
            migrated["page_geometry"] = f"a4paper,margin={value.get('page_margin') or '2cm'}"
        if "font_family" in value and "main_font" not in value:
            migrated["main_font"] = str(value.get("font_family") or "PingFang SC").split(",")[0].strip()
        if "font_size" in value and str(value.get("font_size") or "").endswith("px"):
            migrated["font_size"] = str(value.get("font_size") or "12px").replace("px", "pt")
        if "header_text" in value and "header_latex" not in value:
            migrated["header_latex"] = self._latex_escape(str(value.get("header_text") or ""))
        if "footer_text" in value and "footer_latex" not in value:
            footer_text = str(value.get("footer_text") or "").strip()
            migrated["footer_latex"] = r"\thepage" if footer_text in {"", "页码", "page", "counter(page)"} else self._latex_escape(footer_text)

        for legacy_key in ("font_family", "page_margin", "header_text", "footer_text"):
            migrated.pop(legacy_key, None)
        return migrated

    def _latex_escape(self, value: str) -> str:
        replacements = {
            "\\": r"\textbackslash{}",
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
            "^": r"\textasciicircum{}",
        }
        return "".join(replacements.get(char, char) for char in str(value))
    
    def _normalize_options(self, options: Any = None) -> Dict[str, Any]:
        """Normalize options from either API JSON objects or saved form arrays."""
        defaults = {
            "include_toc": True,
            "include_summary": True,
            "watermark": False,
            "line_numbers": True,
            "highlight_syntax": True,
            "wrap_lines": True,
            "continuous_line_numbers": False,
            "file_name_bold": True,
            "layout": "single_column",
            "font_size": "14px",
            "template": "standard",
            "template_id": None,
            "software_name": "",
            "version": "",
            "developer": "",
            "enable_global_variables": True,
        }

        if isinstance(options, dict):
            return {**defaults, **options}

        if isinstance(options, list):
            return {
                **defaults,
                "include_toc": "include_toc" in options,
                "include_summary": "include_summary" in options,
                "watermark": "watermark" in options,
            }

        return defaults

    def _options_for_project(self, project: Project, requested_options: Any = None) -> dict[str, Any]:
        """合并项目保存配置与本次请求导出配置。"""
        try:
            config = json.loads(project.config_json or "{}")
        except json.JSONDecodeError:
            config = {}

        options = self._normalize_options(None)
        project_export_options = config.get("export_options")
        if project_export_options:
            options.update(self._normalize_options(project_export_options))

        code_options = config.get("code_options") or {}
        manual_options = config.get("manual_options") or {}

        if project.project_type == "code":
            formatting = code_options.get("formatting") or []
            has_formatting_config = "formatting" in code_options
            options.update({
                "line_numbers": "line_numbers" in formatting if has_formatting_config else options["line_numbers"],
                "highlight_syntax": "highlight_syntax" in formatting if has_formatting_config else options["highlight_syntax"],
                "wrap_lines": "wrap_lines" in formatting if has_formatting_config else options["wrap_lines"],
                "continuous_line_numbers": "continuous_line_numbers" in formatting,
                "file_name_bold": "file_name_bold" in formatting if has_formatting_config else options["file_name_bold"],
                "layout": code_options.get("layout", options["layout"]),
                "font_size": code_options.get("font_size", options["font_size"]),
                "template_id": code_options.get("template_id"),
            })
            if code_options.get("export_options"):
                options.update(self._normalize_options(code_options.get("export_options")))

        if project.project_type == "manual":
            options.update({
                "template": manual_options.get("template", options["template"]),
                "template_id": manual_options.get("template_id"),
                "software_name": manual_options.get("software_name", project.project_name),
                "version": manual_options.get("version", ""),
                "developer": manual_options.get("developer", ""),
                "enable_global_variables": manual_options.get("enable_global_variables", True),
            })

        if isinstance(requested_options, list):
            options.update(self._normalize_options(requested_options))
        elif isinstance(requested_options, dict) and requested_options:
            if "export_options" in requested_options:
                options.update(self._normalize_options(requested_options["export_options"]))
            if "formatting" in requested_options:
                formatting = requested_options.get("formatting") or []
                options.update({
                    "line_numbers": "line_numbers" in formatting,
                    "highlight_syntax": "highlight_syntax" in formatting,
                    "wrap_lines": "wrap_lines" in formatting,
                    "continuous_line_numbers": "continuous_line_numbers" in formatting,
                    "file_name_bold": "file_name_bold" in formatting,
                })
            options.update({
                key: value
                for key, value in requested_options.items()
                if value is not None and key != "export_options"
            })

        return self._normalize_options(options)

    def _get_font_path(self) -> Optional[str]:
        candidates = [
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
            "/System/Library/Fonts/PingFang.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for candidate in candidates:
            if Path(candidate).exists():
                return candidate
        return None

    def _load_font(self, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        font_path = self._get_font_path()
        if font_path:
            try:
                return ImageFont.truetype(font_path, size=size)
            except Exception:
                pass
        return ImageFont.load_default()

    def _wrap_text_for_image(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
        max_width: int
    ) -> list[str]:
        if text == "":
            return [""]

        lines: list[str] = []
        current = ""
        for char in text:
            candidate = current + char
            if current and draw.textlength(candidate, font=font) > max_width:
                lines.append(current)
                current = char
            else:
                current = candidate
        lines.append(current)
        return lines

    def _plain_markdown_text(self, value: str, variables: Optional[dict[str, str]] = None) -> str:
        if variables:
            value = self._apply_global_variables(value, variables)
        value = re.sub(r"```.*?```", lambda match: match.group(0).strip("`"), value, flags=re.DOTALL)
        value = re.sub(r"^#{1,6}\s*", "", value, flags=re.MULTILINE)
        value = re.sub(r"[*_`>#-]+", "", value)
        value = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", value)
        return value.strip()

    async def _generate_image_pdf_fallback(
        self,
        project: Project,
        options: dict[str, Any],
        project_items: Optional[list[ProjectItem]] = None,
        sections: Optional[list[ManualSection]] = None,
    ) -> bytes:
        """Generate a readable image-based PDF for tests when LaTeX is unavailable."""
        page_width, page_height = 1240, 1754
        margin = 86
        max_text_width = page_width - margin * 2
        colors = {
            "text": (16, 32, 51),
            "muted": (102, 117, 135),
            "blue": (20, 126, 214),
            "border": (218, 229, 240),
            "code_bg": (248, 251, 255),
        }
        fonts = {
            "title": self._load_font(38),
            "heading": self._load_font(26),
            "body": self._load_font(20),
            "meta": self._load_font(17),
            "code": self._load_font(17),
        }
        pages: list[Image.Image] = []

        def new_page() -> tuple[Image.Image, ImageDraw.ImageDraw, int]:
            page = Image.new("RGB", (page_width, page_height), "white")
            pages.append(page)
            return page, ImageDraw.Draw(page), margin

        page, draw, y = new_page()

        def ensure_space(required: int) -> None:
            nonlocal page, draw, y
            if y + required > page_height - margin:
                page, draw, y = new_page()

        def add_text(text: str, style: str = "body", fill: tuple[int, int, int] | None = None, top: int = 0, bottom: int = 8) -> None:
            nonlocal y
            font = fonts.get(style, fonts["body"])
            fill = fill or colors["text"]
            y += top
            line_height = max(font.size + 10 if hasattr(font, "size") else 28, 24)
            for source_line in str(text).splitlines() or [""]:
                for line in self._wrap_text_for_image(draw, source_line, font, max_text_width):
                    ensure_space(line_height)
                    draw.text((margin, y), line, font=font, fill=fill)
                    y += line_height
            y += bottom

        def add_rule(space: int = 18) -> None:
            nonlocal y
            ensure_space(space + 2)
            y += space // 2
            draw.line((margin, y, page_width - margin, y), fill=colors["border"], width=2)
            y += space // 2

        def add_image(path: str) -> None:
            nonlocal y
            try:
                image = Image.open(path).convert("RGB")
            except Exception:
                return
            max_width = page_width - margin * 2
            max_height = 620
            scale = min(max_width / image.width, max_height / image.height, 1)
            width = max(1, int(image.width * scale))
            height = max(1, int(image.height * scale))
            ensure_space(height + 24)
            image = image.resize((width, height))
            page.paste(image, (margin, y))
            y += height + 18

        add_text(project.project_name, "title", colors["blue"], bottom=10)
        add_text(f"生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}", "meta", colors["muted"], bottom=4)
        add_text(f"项目类型：{'代码文件' if project.project_type == 'code' else '操作文档'}", "meta", colors["muted"], bottom=10)
        add_rule()

        if project.project_type == "manual":
            section_list = sections or []
            variables = {
                "project_name": project.project_name,
                "software_name": options.get("software_name") or project.project_name,
                "version": options.get("version") or "",
                "developer": options.get("developer") or "",
            }
            if options.get("include_toc", True) and len(section_list) > 1:
                add_text("目录", "heading", colors["blue"], bottom=8)
                for index, section in enumerate(section_list, 1):
                    add_text(f"{index}. {section.title}", "meta", colors["text"], bottom=2)
                add_rule()

            for index, section in enumerate(section_list, 1):
                add_text(f"{index}. {section.title}", "heading", colors["blue"], top=10, bottom=8)
                if section.image_file:
                    add_image(section.image_file.storage_path)
                body = self._plain_markdown_text(
                    section.body_markdown,
                    variables if options.get("enable_global_variables", True) else None
                )
                add_text(body, "body", colors["text"], bottom=14)
        else:
            item_list = project_items or []
            if options.get("include_toc", True) and len(item_list) > 1:
                add_text("目录", "heading", colors["blue"], bottom=8)
                for index, item in enumerate(item_list, 1):
                    add_text(f"{index}. {item.display_name or item.file.original_filename}", "meta", colors["text"], bottom=2)
                add_rule()

            next_line_number = 1
            for index, item in enumerate(item_list, 1):
                file_name = item.display_name or item.file.original_filename
                add_text(f"{index}. {file_name}", "heading", colors["blue"], top=10, bottom=8)
                highlight_result = await self.highlight_service.highlight_code(
                    file_id=item.file_id,
                    user_id=project.owner_id,
                    language_override=item.language_override,
                    line_numbers=False,
                    highlight_syntax=False,
                )
                content = highlight_result.get("content") if highlight_result else "无法加载文件内容"
                code_lines = content.splitlines() or [""]
                for offset, line in enumerate(code_lines):
                    if options.get("line_numbers", True):
                        number = next_line_number + offset if options.get("continuous_line_numbers", False) else offset + 1
                        line = f"{number:>4}  {line}"
                    add_text(line, "code", colors["text"], bottom=0)
                if options.get("continuous_line_numbers", False) and options.get("line_numbers", True):
                    next_line_number += len(code_lines)
                add_rule()

        if not pages:
            page, draw, y = new_page()
            add_text("CodeWright export", "title", colors["blue"])

        output = BytesIO()
        pages[0].save(
            output,
            format="PDF",
            save_all=True,
            append_images=pages[1:],
            resolution=150,
        )
        return output.getvalue()

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
