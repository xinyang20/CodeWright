"""
代码高亮服务
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer_for_filename
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

from app.models.highlight_mapping import HighlightMapping
from app.services.file_service import FileService

class HighlightService:
    def __init__(self, db: Session):
        self.db = db
        self.file_service = FileService(db)
        self._init_default_mappings()
    
    def _init_default_mappings(self):
        """初始化默认的文件扩展名到语言的映射"""
        default_mappings = [
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
        ]
        
        for suffix, language in default_mappings:
            existing = self.db.query(HighlightMapping).filter(
                HighlightMapping.suffix == suffix
            ).first()
            
            if not existing:
                mapping = HighlightMapping(
                    suffix=suffix,
                    language=language,
                    enabled=True
                )
                self.db.add(mapping)
        
        self.db.commit()
    
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
        language_override: Optional[str] = None
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
            if language == 'text':
                # 纯文本，不进行高亮
                highlighted_html = f'<pre><code>{content}</code></pre>'
            else:
                lexer = get_lexer_by_name(language)
                formatter = HtmlFormatter(
                    style='default',
                    linenos=True,
                    linenostart=1,
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
            highlighted_html = f'<pre><code>{content}</code></pre>'
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
