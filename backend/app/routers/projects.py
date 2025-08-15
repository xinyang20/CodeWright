"""
项目路由
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from app.database import get_db
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.schemas.common import ResponseModel
from app.services.auth_service import get_current_user
from app.services.project_service import ProjectService
from app.services.project_settings_service import ProjectSettingsService
from app.models.user import User

# 文件排序模型
class FileOrderItem(BaseModel):
    file_id: int
    order_index: int

class FileReorderRequest(BaseModel):
    file_orders: List[FileOrderItem] = []

router = APIRouter()

@router.post("", response_model=ResponseModel)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建项目"""
    try:
        project_service = ProjectService(db)
        project = await project_service.create_project(project_data, current_user.id)
        return ResponseModel(
            code=0,
            message="项目创建成功",
            data={"project_id": project.id, "project_name": project.project_name}
        )
    except Exception as e:
        return ResponseModel(code=5001, message="服务器内部错误")

@router.get("", response_model=ResponseModel)
async def get_projects(
    project_type: Optional[str] = Query(None, pattern="^(code|manual)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取项目列表"""
    try:
        project_service = ProjectService(db)
        projects = await project_service.get_user_projects(
            current_user.id, project_type, page, page_size
        )
        return ResponseModel(
            code=0,
            message="获取成功",
            data=projects
        )
    except Exception as e:
        return ResponseModel(code=5001, message="服务器内部错误")

@router.get("/{project_id}", response_model=ResponseModel)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取项目详情"""
    try:
        project_service = ProjectService(db)
        project = await project_service.get_project_by_id(project_id, current_user.id)
        if not project:
            return ResponseModel(code=4001, message="项目不存在")

        return ResponseModel(
            code=0,
            message="获取成功",
            data={
                "id": project.id,
                "project_name": project.project_name,
                "project_type": project.project_type,
                "config_json": project.config_json,
                "created_at": project.created_at,
                "updated_at": project.updated_at
            }
        )
    except Exception as e:
        return ResponseModel(code=5001, message="服务器内部错误")

@router.put("/{project_id}", response_model=ResponseModel)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新项目"""
    try:
        project_service = ProjectService(db)
        project = await project_service.update_project(project_id, current_user.id, project_data)
        if not project:
            return ResponseModel(code=4001, message="项目不存在")

        return ResponseModel(
            code=0,
            message="更新成功",
            data={
                "id": project.id,
                "project_name": project.project_name,
                "project_type": project.project_type,
                "config_json": project.config_json,
                "updated_at": project.updated_at
            }
        )
    except Exception as e:
        return ResponseModel(code=5001, message="服务器内部错误")

@router.delete("/{project_id}", response_model=ResponseModel)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除项目"""
    try:
        project_service = ProjectService(db)
        success = await project_service.delete_project(project_id, current_user.id)
        if not success:
            return ResponseModel(code=4001, message="项目不存在")

        return ResponseModel(
            code=0,
            message="删除成功"
        )
    except Exception as e:
        return ResponseModel(code=5001, message="服务器内部错误")

@router.post("/{project_id}/files/{file_id}", response_model=ResponseModel)
async def add_file_to_project(
    project_id: int,
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """将文件添加到项目"""
    try:
        project_service = ProjectService(db)
        success = await project_service.add_file_to_project(
            project_id, file_id, current_user.id
        )

        if not success:
            return ResponseModel(code=4001, message="项目或文件不存在")

        return ResponseModel(
            code=0,
            message="文件添加成功"
        )
    except Exception as e:
        return ResponseModel(code=5001, message="添加文件失败")

@router.get("/{project_id}/files", response_model=ResponseModel)
async def get_project_files(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取项目文件列表"""
    try:
        project_service = ProjectService(db)
        files = await project_service.get_project_files(project_id, current_user.id)

        if files is None:
            return ResponseModel(code=4001, message="项目不存在")

        return ResponseModel(
            code=0,
            message="获取成功",
            data={"files": files}
        )
    except Exception as e:
        return ResponseModel(code=5001, message="获取项目文件失败")

@router.delete("/{project_id}/files/{file_id}", response_model=ResponseModel)
async def remove_file_from_project(
    project_id: int,
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """从项目中移除文件"""
    try:
        project_service = ProjectService(db)
        success = await project_service.remove_file_from_project(
            project_id, file_id, current_user.id
        )

        if not success:
            return ResponseModel(code=4001, message="项目或文件不存在")

        return ResponseModel(
            code=0,
            message="文件移除成功"
        )
    except Exception as e:
        return ResponseModel(code=5001, message="移除文件失败")

@router.put("/{project_id}/files/{file_id}", response_model=ResponseModel)
async def update_project_file(
    project_id: int,
    file_id: int,
    update_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新项目文件信息"""
    try:
        project_service = ProjectService(db)
        success = await project_service.update_project_file(
            project_id, file_id, current_user.id, update_data
        )

        if not success:
            return ResponseModel(code=4001, message="项目或文件不存在")

        return ResponseModel(
            code=0,
            message="文件信息更新成功"
        )
    except Exception as e:
        return ResponseModel(code=5001, message="更新文件信息失败")

@router.put("/{project_id}/reorder-files", response_model=ResponseModel)
async def reorder_project_files(
    project_id: int,
    file_orders: List[FileOrderItem],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重新排序项目文件"""
    try:
        project_service = ProjectService(db)
        # 转换为字典列表
        file_orders_dict = [{"file_id": item.file_id, "order_index": item.order_index} for item in file_orders]
        success = await project_service.reorder_project_files(
            project_id, file_orders_dict, current_user.id
        )

        if not success:
            return ResponseModel(code=4001, message="项目不存在或文件顺序无效")

        return ResponseModel(
            code=0,
            message="文件顺序更新成功"
        )
    except Exception as e:
        return ResponseModel(code=5001, message="更新文件顺序失败")

@router.post("/{project_id}/export/pdf")
async def export_project_pdf(
    project_id: int,
    export_options: dict = {},
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """导出项目为PDF"""
    try:
        from app.services.pdf_service import PdfService
        from fastapi.responses import Response

        pdf_service = PdfService(db)
        pdf_bytes = await pdf_service.export_project_to_pdf(
            project_id=project_id,
            user_id=current_user.id,
            options=export_options
        )

        if not pdf_bytes:
            return ResponseModel(code=4001, message="项目不存在或无文件可导出")

        # 获取项目名称用于文件名
        project_service = ProjectService(db)
        project = await project_service.get_project_by_id(project_id, current_user.id)

        if project:
            # 对中文文件名进行URL编码
            import urllib.parse
            encoded_filename = urllib.parse.quote(f"{project.project_name}.pdf", safe='')
            filename_header = f"attachment; filename*=UTF-8''{encoded_filename}"
        else:
            filename_header = "attachment; filename=export.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": filename_header
            }
        )

    except Exception as e:
        print(f"PDF导出错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return ResponseModel(code=5001, message=f"PDF导出失败: {str(e)}")


@router.get("/{project_id}/settings", response_model=ResponseModel)
async def get_project_settings(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取项目配置"""
    try:
        settings_service = ProjectSettingsService(db)
        settings = await settings_service.get_project_settings(project_id, current_user.id)

        if settings is None:
            return ResponseModel(code=4001, message="项目不存在或无权限")

        return ResponseModel(
            code=0,
            message="获取项目配置成功",
            data=settings
        )
    except Exception as e:
        return ResponseModel(code=5001, message="获取项目配置失败")


@router.put("/{project_id}/settings", response_model=ResponseModel)
async def update_project_settings(
    project_id: int,
    settings_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新项目配置"""
    try:
        settings_service = ProjectSettingsService(db)
        settings = await settings_service.update_project_settings(
            project_id, current_user.id, settings_data
        )

        if settings is None:
            return ResponseModel(code=4001, message="项目不存在或无权限")

        return ResponseModel(
            code=0,
            message="项目配置更新成功",
            data=settings
        )
    except Exception as e:
        return ResponseModel(code=5001, message="更新项目配置失败")


@router.post("/{project_id}/settings/reset", response_model=ResponseModel)
async def reset_project_settings(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重置项目配置为默认值"""
    try:
        settings_service = ProjectSettingsService(db)
        settings = await settings_service.reset_project_settings(project_id, current_user.id)

        if settings is None:
            return ResponseModel(code=4001, message="项目不存在或无权限")

        return ResponseModel(
            code=0,
            message="项目配置重置成功",
            data=settings
        )
    except Exception as e:
        return ResponseModel(code=5001, message="重置项目配置失败")
