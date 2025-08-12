"""
导出历史模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class ExportHistory(Base):
    """导出历史记录表"""
    __tablename__ = "export_histories"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    exporter = Column(String(20), nullable=False)  # code, manual
    status = Column(String(20), nullable=False)  # success, failed
    duration_ms = Column(Integer)  # 导出耗时（毫秒）
    file_path = Column(String(500))  # 导出文件路径
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    project = relationship("Project", back_populates="export_histories")
    
    def __repr__(self):
        return f"<ExportHistory(id={self.id}, project_id={self.project_id}, status='{self.status}')>"
