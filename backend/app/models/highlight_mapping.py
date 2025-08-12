"""
高亮映射模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base

class HighlightMapping(Base):
    """后缀-语言映射表"""
    __tablename__ = "highlight_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    suffix = Column(String(20), nullable=False)  # 例如 .py, .java
    language = Column(String(50), nullable=False)  # Pygments/前端预览用的语言标识
    enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<HighlightMapping(id={self.id}, suffix='{self.suffix}', language='{self.language}')>"
