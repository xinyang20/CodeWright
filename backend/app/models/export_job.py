"""
导出任务模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class ExportJob(Base):
    """导出任务表（异步队列）"""
    __tablename__ = "export_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    job_id = Column(String(100), unique=True, nullable=False)  # 队列中的任务ID
    status = Column(String(20), default="queued")  # queued, processing, success, failed
    progress = Column(Integer, default=0)  # 0-100
    result_file_path = Column(String(500))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    project = relationship("Project", back_populates="export_jobs")
    
    def __repr__(self):
        return f"<ExportJob(id={self.id}, job_id='{self.job_id}', status='{self.status}')>"
