"""
公告模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base

class Announcement(Base):
    """公告表"""
    __tablename__ = "announcements"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    body_markdown = Column(Text, nullable=False)
    status = Column(String(20), default="draft")  # draft, published, archived
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Announcement(id={self.id}, title='{self.title}', status='{self.status}')>"
