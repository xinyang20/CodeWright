"""
文件相关模式
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class FileResponse(BaseModel):
    """文件响应模式"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    storage_path: str
    file_size: int
    file_type: str
    uploader_id: int
    created_at: datetime
