"""
项目相关模式
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any

class ProjectCreate(BaseModel):
    """项目创建模式"""
    project_name: str = Field(..., min_length=1, max_length=100, description="项目名称")
    project_type: str = Field(..., pattern="^(code|manual)$", description="项目类型")

class ProjectUpdate(BaseModel):
    """项目更新模式"""
    project_name: Optional[str] = Field(None, min_length=1, max_length=100, description="项目名称")
    config_json: Optional[Dict[str, Any]] = Field(None, description="项目配置")

class ProjectResponse(BaseModel):
    """项目响应模式"""
    id: int
    project_name: str
    project_type: str
    owner_id: int
    config_json: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
