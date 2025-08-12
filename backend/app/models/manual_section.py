"""
操作文档章节模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class ManualSection(Base):
    """操作文档章节表"""
    __tablename__ = "manual_sections"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(200), nullable=False)
    image_file_id = Column(Integer, ForeignKey("uploaded_files.id"))
    body_markdown = Column(Text, nullable=False)
    order_index = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    project = relationship("Project", back_populates="manual_sections")
    image_file = relationship("UploadedFile", back_populates="manual_sections")
    
    def __repr__(self):
        return f"<ManualSection(id={self.id}, title='{self.title}', order={self.order_index})>"
