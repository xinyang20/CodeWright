"""
项目路由
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.schemas.common import ResponseModel
from app.services.auth_service import get_current_user
from app.services.project_service import ProjectService
from app.models.user import User

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
