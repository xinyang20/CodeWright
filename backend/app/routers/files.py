"""
文件路由
"""
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.common import ResponseModel
from app.services.auth_service import get_current_user
from app.services.file_service import FileService
from app.services.highlight_service import HighlightService
from app.models.user import User

router = APIRouter()

@router.post("/upload", response_model=ResponseModel)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传文件"""
    try:
        file_service = FileService(db)
        file_content = await file.read()
        valid, message = file_service.validate_upload(file.filename or "", len(file_content))
        if not valid:
            return ResponseModel(
                code=2001,
                message=message
            )

        # 重置文件指针
        await file.seek(0)

        uploaded_file = await file_service.save_uploaded_file(
            file, current_user.id, file_content
        )

        return ResponseModel(
            code=0,
            message="文件上传成功",
            data={
                "file_id": uploaded_file.id,
                "filename": uploaded_file.original_filename,
                "file_size": uploaded_file.file_size
            }
        )
    except Exception as e:
        return ResponseModel(code=5001, message=f"文件上传失败: {str(e)}")

@router.get("", response_model=ResponseModel)
async def get_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户文件列表"""
    try:
        file_service = FileService(db)
        files = await file_service.get_user_files(current_user.id)

        return ResponseModel(
            code=0,
            message="获取成功",
            data={
                "files": [
                    {
                        "id": f.id,
                        "original_filename": f.original_filename,
                        "file_size": f.file_size,
                        "file_type": f.file_type,
                        "created_at": f.created_at
                    }
                    for f in files
                ]
            }
        )
    except Exception as e:
        return ResponseModel(code=5001, message="获取文件列表失败")

@router.delete("/{file_id}", response_model=ResponseModel)
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除文件"""
    try:
        file_service = FileService(db)
        success = await file_service.delete_file(file_id, current_user.id)

        if not success:
            return ResponseModel(code=4001, message="文件不存在")

        return ResponseModel(
            code=0,
            message="文件删除成功"
        )
    except Exception as e:
        return ResponseModel(code=5001, message="删除文件失败")

@router.get("/{file_id}/preview", response_model=ResponseModel)
async def preview_file(
    file_id: int,
    language: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """预览文件（带语法高亮）"""
    try:
        highlight_service = HighlightService(db)
        result = await highlight_service.highlight_code(
            file_id, current_user.id, language
        )

        if not result:
            return ResponseModel(code=4001, message="文件不存在或无法读取")

        return ResponseModel(
            code=0,
            message="预览成功",
            data=result
        )
    except Exception as e:
        return ResponseModel(code=5001, message="预览失败")

@router.get("/highlight/css")
async def get_highlight_css(db: Session = Depends(get_db)):
    """获取代码高亮CSS样式"""
    try:
        highlight_service = HighlightService(db)
        css = highlight_service.get_highlight_css()

        return ResponseModel(
            code=0,
            message="获取成功",
            data={"css": css}
        )
    except Exception as e:
        return ResponseModel(code=5001, message="获取CSS失败")
