"""
通用响应模式
"""
from pydantic import BaseModel
from typing import Any, Optional


class ErrorCodes:
    """Centralized error codes used by the API responses."""

    OK = 0
    PARAM = 1001  # 参数错误
    AUTH_FAILED = 1002  # 认证失败
    PERMISSION_DENIED = 1003  # 权限不足
    INVALID_FILE = 2001  # 非法文件（类型/大小/项目超量）
    EXPORT_FAILED = 3001  # 导出失败
    NOT_FOUND = 4001  # 资源不存在
    SERVER_ERROR = 5001  # 服务器内部错误


class ResponseModel(BaseModel):
    """统一响应模型"""
    code: int = ErrorCodes.OK
    message: str = "ok"
    data: Optional[Any] = None
    detail: Optional[Any] = None
