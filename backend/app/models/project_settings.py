"""
项目配置模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ProjectSettings(Base):
    """项目配置表"""
    __tablename__ = "project_settings"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # 代码文件配置
    enable_syntax_highlight = Column(Boolean, default=True, comment="启用语法高亮")
    show_line_numbers = Column(Boolean, default=True, comment="显示行号")
    code_theme = Column(String(50), default="default", comment="代码主题")
    file_sort_order = Column(String(20), default="manual", comment="文件排序方式")
    
    # 操作文档配置
    auto_save = Column(Boolean, default=True, comment="自动保存")
    auto_save_interval = Column(Integer, default=30, comment="自动保存间隔(秒)")
    editor_mode = Column(String(20), default="split", comment="编辑器模式")
    show_section_numbers = Column(Boolean, default=True, comment="显示章节编号")
    
    # 导出配置
    export_include_toc = Column(Boolean, default=True, comment="导出包含目录")
    export_include_summary = Column(Boolean, default=True, comment="导出包含统计")
    export_watermark = Column(Boolean, default=False, comment="导出添加水印")
    export_page_format = Column(String(20), default="A4", comment="导出页面格式")
    
    # 其他配置（JSON格式存储扩展配置）
    extra_settings = Column(Text, comment="扩展配置(JSON)")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    project = relationship("Project", back_populates="settings")
