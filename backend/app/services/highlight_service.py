"""
代码高亮服务
"""
from html import escape
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer_for_filename
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

from app.models.highlight_mapping import HighlightMapping
from app.services.file_service import FileService

DEFAULT_HIGHLIGHT_MAPPINGS: tuple[tuple[str, str], ...] = (
    ('.py', 'python'),
    ('.java', 'java'),
    ('.js', 'javascript'),
    ('.ts', 'typescript'),
    ('.c', 'c'),
    ('.cpp', 'cpp'),
    ('.h', 'c'),
    ('.hpp', 'cpp'),
    ('.css', 'css'),
    ('.html', 'html'),
    ('.xml', 'xml'),
    ('.json', 'json'),
    ('.yml', 'yaml'),
    ('.yaml', 'yaml'),
    ('.sql', 'sql'),
    ('.sh', 'bash'),
    ('.bat', 'batch'),
    ('.md', 'markdown'),
    ('.txt', 'text'),
)


class HighlightService:
    """Default mappings are seeded at app startup, see ``bootstrap_default_mappings``."""

    _bootstrap_done = False

    def __init__(self, db: Session):
        self.db = db
        self.file_service = FileService(db)

    @classmethod
    def bootstrap_default_mappings(cls, db: Session, force: bool = False) -> None:
        """Insert any missing default suffix→language rows once per process."""
        if cls._bootstrap_done and not force:
            return

        added = False
        for suffix, language in DEFAULT_HIGHLIGHT_MAPPINGS:
            existing = db.query(HighlightMapping).filter(
                HighlightMapping.suffix == suffix
            ).first()
            if not existing:
                db.add(HighlightMapping(
                    suffix=suffix,
                    language=language,
                    enabled=True,
                ))
                added = True

        if added:
            db.commit()
        cls._bootstrap_done = True
    
    def get_language_for_file(self, filename: str, language_override: Optional[str] = None) -> str:
        """获取文件对应的语言标识"""
        if language_override:
            return language_override
        
        # 从文件扩展名获取语言
        file_ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
        
        mapping = self.db.query(HighlightMapping).filter(
            HighlightMapping.suffix == file_ext,
            HighlightMapping.enabled == True
        ).first()
        
        if mapping:
            return mapping.language
        
        # 默认返回text
        return 'text'
    
    async def highlight_code(
        self, 
        file_id: int, 
        user_id: int, 
        language_override: Optional[str] = None,
        line_numbers: bool = True,
        highlight_syntax: bool = True,
        line_start: int = 1
    ) -> Optional[Dict[str, Any]]:
        """高亮代码文件"""
        # 获取文件记录
        file_record = await self.file_service.get_file_by_id(file_id, user_id)
        if not file_record:
            return None
        
        # 读取文件内容
        content = await self.file_service.read_file_content(file_id, user_id)
        if content is None:
            return None
        
        # 获取语言标识
        language = self.get_language_for_file(
            file_record.original_filename, 
            language_override
        )
        
        try:
            # 使用Pygments进行高亮
            if language == 'text' or not highlight_syntax:
                # 纯文本，不进行高亮
                if line_numbers:
                    numbered_lines = []
                    for offset, line in enumerate(content.splitlines() or [""]):
                        number = line_start + offset
                        numbered_lines.append(
                            f'<span class="linenos">{number}</span> {escape(line)}'
                        )
                    numbered_content = "\n".join(numbered_lines)
                    highlighted_html = f'<pre><code>{numbered_content}</code></pre>'
                else:
                    highlighted_html = f'<pre><code>{escape(content)}</code></pre>'
            else:
                lexer = get_lexer_by_name(language)
                formatter = HtmlFormatter(
                    style='default',
                    linenos=line_numbers,
                    linenostart=line_start,
                    cssclass='highlight'
                )
                highlighted_html = highlight(content, lexer, formatter)
            
            return {
                'file_id': file_id,
                'filename': file_record.original_filename,
                'language': language,
                'content': content,
                'highlighted_html': highlighted_html,
                'line_count': len(content.splitlines())
            }
            
        except ClassNotFound:
            # 语言不支持，使用纯文本
            if line_numbers:
                numbered_lines = []
                for offset, line in enumerate(content.splitlines() or [""]):
                    number = line_start + offset
                    numbered_lines.append(
                        f'<span class="linenos">{number}</span> {escape(line)}'
                    )
                numbered_content = "\n".join(numbered_lines)
                highlighted_html = f'<pre><code>{numbered_content}</code></pre>'
            else:
                highlighted_html = f'<pre><code>{escape(content)}</code></pre>'
            return {
                'file_id': file_id,
                'filename': file_record.original_filename,
                'language': 'text',
                'content': content,
                'highlighted_html': highlighted_html,
                'line_count': len(content.splitlines())
            }
        except Exception:
            return None
    
    def get_highlight_css(self) -> str:
        """获取高亮样式CSS"""
        formatter = HtmlFormatter(style='default')
        return formatter.get_style_defs('.highlight')

    async def get_mappings(self) -> list[dict]:
        """获取后缀名到语言的映射列表"""
        HighlightService.bootstrap_default_mappings(self.db)
        mappings = self.db.query(HighlightMapping).order_by(HighlightMapping.suffix).all()
        return [
            {
                "id": mapping.id,
                "suffix": mapping.suffix,
                "language": mapping.language,
                "enabled": mapping.enabled,
                "updated_at": mapping.updated_at,
            }
            for mapping in mappings
        ]

    async def update_mappings(self, mappings: list[dict]) -> list[dict]:
        """批量更新后缀名到语言的映射"""
        for item in mappings:
            suffix = item.get("suffix", "").strip().lower()
            language = item.get("language", "").strip()
            if not suffix or not language:
                continue
            if not suffix.startswith("."):
                suffix = f".{suffix}"

            mapping = self.db.query(HighlightMapping).filter(
                HighlightMapping.suffix == suffix
            ).first()
            if not mapping:
                mapping = HighlightMapping(suffix=suffix, language=language)
                self.db.add(mapping)

            mapping.language = language
            mapping.enabled = bool(item.get("enabled", True))

        self.db.commit()
        return await self.get_mappings()

    async def delete_mapping(self, suffix: str) -> bool:
        """删除指定后缀的映射；当 suffix 不存在时返回 False。"""
        normalized = (suffix or "").strip().lower()
        if not normalized:
            return False
        if not normalized.startswith("."):
            normalized = f".{normalized}"

        mapping = self.db.query(HighlightMapping).filter(
            HighlightMapping.suffix == normalized
        ).first()
        if not mapping:
            return False
        self.db.delete(mapping)
        self.db.commit()
        return True
