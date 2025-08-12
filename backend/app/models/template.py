"""
模板模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base

class Template(Base):
    """模板表"""
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    version = Column(String(20), nullable=False)
    description = Column(Text)
    storage_path = Column(String(500), nullable=False)
    status = Column(String(20), default="draft")  # draft, published
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Template(id={self.id}, name='{self.name}', version='{self.version}')>"
