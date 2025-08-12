"""
用户相关模式
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    """用户创建模式"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")

class UserLogin(BaseModel):
    """用户登录模式"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")

class UserResponse(BaseModel):
    """用户响应模式"""
    id: int
    username: str
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    """令牌响应模式"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
