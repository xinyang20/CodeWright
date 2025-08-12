"""
认证路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, TokenResponse
from app.schemas.common import ResponseModel
from app.services.auth_service import AuthService

router = APIRouter()

@router.post("/register", response_model=ResponseModel)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
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
    except Exception as e:
        return ResponseModel(code=5001, message="服务器内部错误")

@router.post("/token", response_model=ResponseModel)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    try:
        auth_service = AuthService(db)
        token_data = await auth_service.authenticate_user(user_data)
        return ResponseModel(
            code=0,
            message="登录成功",
            data=token_data
        )
    except ValueError as e:
        return ResponseModel(code=1002, message=str(e))
    except Exception as e:
        return ResponseModel(code=5001, message="服务器内部错误")
