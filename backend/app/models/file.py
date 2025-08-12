"""
文件模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class UploadedFile(Base):
    """上传文件表"""
    __tablename__ = "uploaded_files"
    
    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # 文件大小（字节）
    file_type = Column(String(100))  # MIME类型
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    uploader = relationship("User", back_populates="uploaded_files")
    project_items = relationship("ProjectItem", back_populates="file", cascade="all, delete-orphan")
    manual_sections = relationship("ManualSection", back_populates="image_file")
    
    def __repr__(self):
        return f"<UploadedFile(id={self.id}, filename='{self.original_filename}')>"
