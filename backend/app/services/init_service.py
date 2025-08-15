"""
数据库初始化服务
"""
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.models.user import User
from app.models.highlight_mapping import HighlightMapping

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class InitService:
    def __init__(self, db: Session):
        self.db = db
    
    def init_admin_user(self):
        """初始化管理员用户"""
        # 检查是否已存在管理员用户
        admin_user = self.db.query(User).filter(User.username == "admin").first()
        
        if not admin_user:
            # 创建固定的管理员账户
            hashed_password = pwd_context.hash("admin123")
            
            admin_user = User(
                username="admin",
                password_hash=hashed_password,
                role="admin",
                is_active=True
            )
            
            self.db.add(admin_user)
            self.db.commit()
            print("✅ 初始管理员账户创建成功: admin / admin123")
        else:
            print("ℹ️  管理员账户已存在")
    
    def init_highlight_mappings(self):
        """初始化语言高亮映射"""
        # 检查是否已有映射数据
        existing_count = self.db.query(HighlightMapping).count()
        
        if existing_count == 0:
            # 默认的语言映射
            default_mappings = [
                # Python
                ('.py', 'python'),
                ('.pyw', 'python'),
                
                # JavaScript/TypeScript
                ('.js', 'javascript'),
                ('.jsx', 'javascript'),
                ('.ts', 'typescript'),
                ('.tsx', 'typescript'),
                ('.mjs', 'javascript'),
                
                # Java
                ('.java', 'java'),
                ('.class', 'java'),
                
                # C/C++
                ('.c', 'c'),
                ('.h', 'c'),
                ('.cpp', 'cpp'),
                ('.cxx', 'cpp'),
                ('.cc', 'cpp'),
                ('.hpp', 'cpp'),
                ('.hxx', 'cpp'),
                
                # C#
                ('.cs', 'csharp'),
                
                # Go
                ('.go', 'go'),
                
                # Rust
                ('.rs', 'rust'),
                
                # PHP
                ('.php', 'php'),
                ('.php3', 'php'),
                ('.php4', 'php'),
                ('.php5', 'php'),
                
                # Ruby
                ('.rb', 'ruby'),
                ('.rbw', 'ruby'),
                
                # Swift
                ('.swift', 'swift'),
                
                # Kotlin
                ('.kt', 'kotlin'),
                ('.kts', 'kotlin'),
                
                # Scala
                ('.scala', 'scala'),
                
                # R
                ('.r', 'r'),
                ('.R', 'r'),
                
                # MATLAB
                ('.m', 'matlab'),
                
                # Shell
                ('.sh', 'bash'),
                ('.bash', 'bash'),
                ('.zsh', 'zsh'),
                ('.fish', 'fish'),
                
                # Batch
                ('.bat', 'batch'),
                ('.cmd', 'batch'),
                
                # PowerShell
                ('.ps1', 'powershell'),
                
                # Web
                ('.html', 'html'),
                ('.htm', 'html'),
                ('.xhtml', 'html'),
                ('.css', 'css'),
                ('.scss', 'scss'),
                ('.sass', 'sass'),
                ('.less', 'less'),
                
                # Data formats
                ('.json', 'json'),
                ('.xml', 'xml'),
                ('.yaml', 'yaml'),
                ('.yml', 'yaml'),
                ('.toml', 'toml'),
                ('.ini', 'ini'),
                ('.cfg', 'ini'),
                ('.conf', 'ini'),
                
                # SQL
                ('.sql', 'sql'),
                
                # Markdown
                ('.md', 'markdown'),
                ('.markdown', 'markdown'),
                
                # Text
                ('.txt', 'text'),
                ('.log', 'text'),
                
                # Docker
                ('Dockerfile', 'dockerfile'),
                ('.dockerfile', 'dockerfile'),
                
                # Makefile
                ('Makefile', 'makefile'),
                ('.mk', 'makefile'),
                
                # Git
                ('.gitignore', 'gitignore'),
                ('.gitattributes', 'gitattributes'),
                
                # Other
                ('.vim', 'vim'),
                ('.lua', 'lua'),
                ('.pl', 'perl'),
                ('.pm', 'perl'),
                ('.tcl', 'tcl'),
                ('.awk', 'awk'),
                ('.sed', 'sed'),
            ]
            
            for suffix, language in default_mappings:
                mapping = HighlightMapping(
                    suffix=suffix,
                    language=language,
                    enabled=True
                )
                self.db.add(mapping)
            
            self.db.commit()
            print(f"✅ 初始化了 {len(default_mappings)} 个语言高亮映射")
        else:
            print(f"ℹ️  语言高亮映射已存在 ({existing_count} 个)")
    
    def init_all(self):
        """初始化所有数据"""
        print("🚀 开始初始化数据库...")
        self.init_admin_user()
        self.init_highlight_mappings()
        print("✅ 数据库初始化完成")
