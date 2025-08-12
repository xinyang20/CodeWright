"""
设置路由
"""
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import ResponseModel
from app.services.auth_service import get_current_admin_user
from app.services.template_service import TemplateService
from app.models.user import User

router = APIRouter()

@router.get("/templates", response_model=ResponseModel)
async def get_templates(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """获取模板列表"""
    try:
        template_service = TemplateService(db)
        templates = await template_service.get_templates()

        return ResponseModel(
            code=0,
            message="获取成功",
            data={"templates": templates}
        )
    except Exception as e:
        return ResponseModel(code=5001, message="获取模板列表失败")

@router.post("/templates", response_model=ResponseModel)
async def create_template(
    name: str,
    version: str,
    description: str = "",
    file: UploadFile = File(...),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """创建模板"""
    try:
        template_service = TemplateService(db)
        template = await template_service.create_template(
            name, version, description, file
        )

        return ResponseModel(
            code=0,
            message="模板创建成功",
            data={
                "template_id": template.id,
                "name": template.name,
                "version": template.version
            }
        )
    except Exception as e:
        return ResponseModel(code=5001, message=f"创建模板失败: {str(e)}")

@router.put("/templates/{template_id}/status", response_model=ResponseModel)
async def update_template_status(
    template_id: int,
    status: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """更新模板状态"""
    try:
        template_service = TemplateService(db)
        success = await template_service.update_template_status(template_id, status)

        if not success:
            return ResponseModel(code=4001, message="模板不存在")

        return ResponseModel(
            code=0,
            message="状态更新成功"
        )
    except Exception as e:
        return ResponseModel(code=5001, message="更新模板状态失败")
