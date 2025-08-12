"""
管理员路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.common import ResponseModel
from app.services.auth_service import get_current_admin_user
from app.services.admin_service import AdminService
from app.models.user import User

router = APIRouter()

@router.get("/users", response_model=ResponseModel)
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """获取用户列表"""
    try:
        admin_service = AdminService(db)
        users = await admin_service.get_users(page, page_size, search)

        return ResponseModel(
            code=0,
            message="获取成功",
            data=users
        )
    except Exception as e:
        return ResponseModel(code=5001, message="获取用户列表失败")

@router.put("/users/{user_id}/status", response_model=ResponseModel)
async def update_user_status(
    user_id: int,
    is_active: bool,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """更新用户状态"""
    try:
        admin_service = AdminService(db)
        success = await admin_service.update_user_status(user_id, is_active)

        if not success:
            return ResponseModel(code=4001, message="用户不存在")

        return ResponseModel(
            code=0,
            message="更新成功"
        )
    except Exception as e:
        return ResponseModel(code=5001, message="更新用户状态失败")

@router.get("/stats", response_model=ResponseModel)
async def get_system_stats(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """获取系统统计信息"""
    try:
        admin_service = AdminService(db)
        stats = await admin_service.get_system_stats()

        return ResponseModel(
            code=0,
            message="获取成功",
            data=stats
        )
    except Exception as e:
        return ResponseModel(code=5001, message="获取统计信息失败")
