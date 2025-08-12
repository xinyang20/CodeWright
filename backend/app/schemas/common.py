"""
通用响应模式
"""
from pydantic import BaseModel
from typing import Any, Optional

class ResponseModel(BaseModel):
    """统一响应模型"""
    code: int = 0
    message: str = "ok"
    data: Optional[Any] = None
    detail: Optional[Any] = None
