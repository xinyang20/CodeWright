"""
项目相关模式
"""
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Dict, Any, List

class CodeOptions(BaseModel):
    """代码项目配置选项"""
    formatting: List[str] = Field(default_factory=list, description="格式化选项")
    layout: str = Field(default="single_column", description="页面布局")
    font_size: str = Field(default="14px", description="字体大小")
    export_options: List[str] = Field(default_factory=list, description="导出选项")
    template_id: Optional[int] = Field(None, description="代码导出模板ID")

class ManualOptions(BaseModel):
    """操作文档项目配置选项"""
    template: str = Field(default="standard", description="文档模板")
    template_id: Optional[int] = Field(None, description="操作文档模板ID")
    default_sections: List[str] = Field(default_factory=list, description="默认章节")
    software_name: str = Field(default="", max_length=100, description="软件名称")
    version: str = Field(default="", max_length=50, description="版本号")
    developer: str = Field(default="", max_length=100, description="开发者")
    enable_global_variables: bool = Field(default=True, description="启用全局变量替换")

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

class ManualSectionCreate(BaseModel):
    """操作文档章节创建模式"""
    title: str = Field(..., min_length=1, max_length=200, description="章节标题")
    body_markdown: str = Field(..., min_length=1, description="章节正文 Markdown")
    image_file_id: Optional[int] = Field(None, description="章节截图文件ID")
    order_index: Optional[int] = Field(None, ge=1, description="章节排序")

class ManualSectionUpdate(BaseModel):
    """操作文档章节更新模式"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="章节标题")
    body_markdown: Optional[str] = Field(None, min_length=1, description="章节正文 Markdown")
    image_file_id: Optional[int] = Field(None, description="章节截图文件ID")
    order_index: Optional[int] = Field(None, ge=1, description="章节排序")

class ProjectResponse(BaseModel):
    """项目响应模式"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_name: str
    project_type: str
    owner_id: int
    config_json: str
    created_at: datetime
    updated_at: datetime
