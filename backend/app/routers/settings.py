"""
设置路由
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, Body
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import ResponseModel, ErrorCodes
from app.services.auth_service import get_current_admin_user
from app.services.highlight_service import HighlightService
from app.services.settings_service import SettingsService
from app.services.template_service import TemplateService
from app.models.user import User

router = APIRouter()

@router.get("/templates/published", response_model=ResponseModel)
async def get_published_templates(db: Session = Depends(get_db)):
    """获取已发布模板，供普通用户选择"""
    try:
        template_service = TemplateService(db)
        templates = await template_service.get_published_templates()
        return ResponseModel(
            code=ErrorCodes.OK,
            message="获取成功",
            data={
                "templates": [
                    {
                        "id": template.id,
                        "name": template.name,
                        "version": template.version,
                        "description": template.description,
                        "status": template.status,
                        "created_at": template.created_at,
                        "updated_at": template.updated_at,
                    }
                    for template in templates
                ]
            }
        )
    except Exception:
        return ResponseModel(code=ErrorCodes.SERVER_ERROR, message="获取已发布模板失败")

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
            code=ErrorCodes.OK,
            message="获取成功",
            data={"templates": templates}
        )
    except Exception:
        return ResponseModel(code=ErrorCodes.SERVER_ERROR, message="获取模板列表失败")

@router.post("/templates", response_model=ResponseModel)
async def create_template(
    name: str = Form(...),
    version: str = Form(...),
    description: str = Form(""),
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
            code=ErrorCodes.OK,
            message="模板创建成功",
            data={
                "template_id": template.id,
                "name": template.name,
                "version": template.version
            }
        )
    except ValueError as e:
        return ResponseModel(code=ErrorCodes.PARAM, message=str(e))
    except Exception:
        return ResponseModel(code=ErrorCodes.SERVER_ERROR, message="创建模板失败")

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
            return ResponseModel(code=ErrorCodes.NOT_FOUND, message="模板不存在")

        return ResponseModel(code=ErrorCodes.OK, message="状态更新成功")
    except ValueError as e:
        return ResponseModel(code=ErrorCodes.PARAM, message=str(e))
    except Exception:
        return ResponseModel(code=ErrorCodes.SERVER_ERROR, message="更新模板状态失败")


@router.post("/templates/{template_id}/clone", response_model=ResponseModel)
async def clone_template(
    template_id: int,
    payload: dict = Body(default_factory=dict),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """复制现有模板生成新版本草稿。"""
    try:
        template_service = TemplateService(db)
        new_version = payload.get("version") if isinstance(payload, dict) else None
        cloned = await template_service.clone_template(template_id, new_version)
        return ResponseModel(
            code=ErrorCodes.OK,
            message="模板复制成功",
            data={
                "template_id": cloned.id,
                "name": cloned.name,
                "version": cloned.version,
                "status": cloned.status,
            }
        )
    except ValueError as e:
        return ResponseModel(code=ErrorCodes.PARAM, message=str(e))
    except Exception:
        return ResponseModel(code=ErrorCodes.SERVER_ERROR, message="模板复制失败")

@router.get("/system", response_model=ResponseModel)
async def get_system_settings(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """获取系统设置"""
    try:
        service = SettingsService(db)
        return ResponseModel(code=ErrorCodes.OK, message="获取成功", data=await service.get_settings())
    except Exception:
        return ResponseModel(code=ErrorCodes.SERVER_ERROR, message="获取系统设置失败")

@router.put("/system/{key}", response_model=ResponseModel)
async def update_system_setting(
    key: str,
    value: dict = Body(...),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """更新系统设置"""
    try:
        service = SettingsService(db)
        settings = await service.update_setting(key, value)
        return ResponseModel(code=ErrorCodes.OK, message="设置更新成功", data=settings)
    except ValueError as e:
        return ResponseModel(code=ErrorCodes.PARAM, message=str(e))
    except Exception:
        return ResponseModel(code=ErrorCodes.SERVER_ERROR, message="更新系统设置失败")

@router.get("/highlight-mapping", response_model=ResponseModel)
async def get_highlight_mapping(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """获取后缀名-语言映射"""
    try:
        service = HighlightService(db)
        return ResponseModel(
            code=ErrorCodes.OK,
            message="获取成功",
            data={"mappings": await service.get_mappings()}
        )
    except Exception:
        return ResponseModel(code=ErrorCodes.SERVER_ERROR, message="获取高亮映射失败")

@router.put("/highlight-mapping", response_model=ResponseModel)
async def update_highlight_mapping(
    mappings: list = Body(...),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """批量更新后缀名-语言映射"""
    try:
        service = HighlightService(db)
        return ResponseModel(
            code=ErrorCodes.OK,
            message="映射更新成功",
            data={"mappings": await service.update_mappings(mappings)}
        )
    except Exception:
        return ResponseModel(code=ErrorCodes.SERVER_ERROR, message="更新高亮映射失败")


@router.delete("/highlight-mapping/{suffix}", response_model=ResponseModel)
async def delete_highlight_mapping(
    suffix: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """删除一条后缀名-语言映射。"""
    try:
        service = HighlightService(db)
        deleted = await service.delete_mapping(suffix)
        if not deleted:
            return ResponseModel(code=ErrorCodes.NOT_FOUND, message="映射不存在")
        return ResponseModel(code=ErrorCodes.OK, message="映射已删除")
    except Exception:
        return ResponseModel(code=ErrorCodes.SERVER_ERROR, message="删除高亮映射失败")

@router.get("/announcements", response_model=ResponseModel)
async def get_announcements(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """获取公告列表"""
    try:
        service = SettingsService(db)
        return ResponseModel(
            code=ErrorCodes.OK,
            message="获取成功",
            data={"announcements": await service.get_announcements()}
        )
    except Exception:
        return ResponseModel(code=ErrorCodes.SERVER_ERROR, message="获取公告失败")

@router.get("/announcements/published", response_model=ResponseModel)
async def get_published_announcements(db: Session = Depends(get_db)):
    """获取已发布公告"""
    try:
        service = SettingsService(db)
        announcements = [
            item for item in await service.get_announcements(include_archived=False)
            if item["status"] == "published"
        ]
        return ResponseModel(
            code=ErrorCodes.OK,
            message="获取成功",
            data={"announcements": announcements}
        )
    except Exception:
        return ResponseModel(code=ErrorCodes.SERVER_ERROR, message="获取公告失败")

@router.post("/announcements", response_model=ResponseModel)
async def create_announcement(
    data: dict = Body(...),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """创建公告"""
    try:
        service = SettingsService(db)
        announcement = await service.create_announcement(data)
        return ResponseModel(code=ErrorCodes.OK, message="公告创建成功", data=announcement)
    except KeyError:
        return ResponseModel(code=ErrorCodes.PARAM, message="公告标题和正文不能为空")
    except ValueError as e:
        return ResponseModel(code=ErrorCodes.PARAM, message=str(e))
    except Exception:
        return ResponseModel(code=ErrorCodes.SERVER_ERROR, message="创建公告失败")

@router.put("/announcements/{announcement_id}", response_model=ResponseModel)
async def update_announcement(
    announcement_id: int,
    data: dict = Body(...),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """更新公告"""
    try:
        service = SettingsService(db)
        announcement = await service.update_announcement(announcement_id, data)
        if not announcement:
            return ResponseModel(code=ErrorCodes.NOT_FOUND, message="公告不存在")
        return ResponseModel(code=ErrorCodes.OK, message="公告更新成功", data=announcement)
    except ValueError as e:
        return ResponseModel(code=ErrorCodes.PARAM, message=str(e))
    except Exception:
        return ResponseModel(code=ErrorCodes.SERVER_ERROR, message="更新公告失败")

@router.delete("/announcements/{announcement_id}", response_model=ResponseModel)
async def delete_announcement(
    announcement_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """删除公告"""
    try:
        service = SettingsService(db)
        if not await service.delete_announcement(announcement_id):
            return ResponseModel(code=ErrorCodes.NOT_FOUND, message="公告不存在")
        return ResponseModel(code=ErrorCodes.OK, message="公告已删除")
    except Exception:
        return ResponseModel(code=ErrorCodes.SERVER_ERROR, message="删除公告失败")
