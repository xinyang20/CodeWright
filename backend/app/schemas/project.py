"""
项目相关模式
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List

class CodeOptions(BaseModel):
    """代码项目配置选项"""
    formatting: List[str] = Field(default_factory=list, description="格式化选项")
    layout: str = Field(default="single_column", description="页面布局")
    font_size: str = Field(default="14px", description="字体大小")
    export_options: List[str] = Field(default_factory=list, description="导出选项")

class ManualOptions(BaseModel):
    """操作文档项目配置选项"""
    template: str = Field(default="standard", description="文档模板")
    default_sections: List[str] = Field(default_factory=list, description="默认章节")

class ProjectCreate(BaseModel):
    """项目创建模式"""
    project_name: str = Field(..., min_length=1, max_length=100, description="项目名称")
    project_type: str = Field(..., pattern="^(code|manual)$", description="项目类型")
    code_options: Optional[CodeOptions] = Field(None, description="代码项目配置")
    manual_options: Optional[ManualOptions] = Field(None, description="操作文档配置")

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
