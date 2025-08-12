"""
项目模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Project(Base):
    """项目表"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(100), nullable=False)
    project_type = Column(String(20), nullable=False)  # code, manual
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    config_json = Column(Text, default="{}")  # 项目配置JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    owner = relationship("User", back_populates="projects")
    project_items = relationship("ProjectItem", back_populates="project", cascade="all, delete-orphan")
    manual_sections = relationship("ManualSection", back_populates="project", cascade="all, delete-orphan")
    export_histories = relationship("ExportHistory", back_populates="project", cascade="all, delete-orphan")
    export_jobs = relationship("ExportJob", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.project_name}', type='{self.project_type}')>"

class ProjectItem(Base):
    """项目文件项表"""
    __tablename__ = "project_items"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    file_id = Column(Integer, ForeignKey("uploaded_files.id"), nullable=False)
    display_name = Column(String(255))  # 显示名覆盖
    language_override = Column(String(50))  # 手动指定高亮语言
    include_in_export = Column(Boolean, default=True)
    order_index = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    project = relationship("Project", back_populates="project_items")
    file = relationship("UploadedFile", back_populates="project_items")
    
    def __repr__(self):
        return f"<ProjectItem(id={self.id}, project_id={self.project_id}, order={self.order_index})>"
