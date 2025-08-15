"""
导出历史模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class ExportHistory(Base):
    """导出历史记录表"""
    __tablename__ = "export_histories"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 导出信息
    export_type = Column(String(20), nullable=False, comment="导出类型: pdf, html, docx")
    export_format = Column(String(20), default="pdf", comment="导出格式")
    file_name = Column(String(255), nullable=False, comment="导出文件名")
    file_size = Column(Integer, comment="文件大小(字节)")
    file_path = Column(String(500), comment="文件存储路径")

    # 导出状态
    status = Column(String(20), default="pending", comment="导出状态: pending, processing, completed, failed")
    progress = Column(Float, default=0.0, comment="导出进度(0-100)")
    error_message = Column(Text, comment="错误信息")

    # 导出配置
    export_options = Column(Text, comment="导出选项(JSON)")

    # 统计信息
    total_files = Column(Integer, default=0, comment="总文件数")
    total_sections = Column(Integer, default=0, comment="总章节数")
    processing_time = Column(Float, comment="处理时间(秒)")

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), comment="完成时间")

    # 关系
    project = relationship("Project", back_populates="export_histories")
    user = relationship("User", back_populates="export_histories")

    def __repr__(self):
        return f"<ExportHistory(id={self.id}, project_id={self.project_id}, status='{self.status}')>"
