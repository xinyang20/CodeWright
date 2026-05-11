"""
用户路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.common import ResponseModel
from app.schemas.user import UserCreate
from app.services.auth_service import get_current_user
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter()

@router.post("/register", response_model=ResponseModel)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册接口别名"""
    try:
        auth_service = AuthService(db)
        user = await auth_service.register_user(user_data)
        return ResponseModel(
            code=0,
            message="注册成功",
            data={"user_id": user.id, "username": user.username}
        )
    except ValueError as e:
        return ResponseModel(code=1001, message=str(e))
    except Exception:
        return ResponseModel(code=5001, message="服务器内部错误")

@router.get("/me", response_model=ResponseModel)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户信息"""
    return ResponseModel(
        code=0,
        message="获取成功",
        data={
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at
        }
    )
