"""
操作文档路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from app.database import get_db
from app.schemas.common import ResponseModel
from app.services.auth_service import get_current_user
from app.services.manual_service import ManualService
from app.models.user import User

router = APIRouter()

# Pydantic 模型
class SectionCreate(BaseModel):
    """章节创建模式"""
    title: str = Field(..., min_length=1, max_length=200, description="章节标题")
    body_markdown: str = Field(default="", description="章节内容（Markdown格式）")
    image_file_id: Optional[int] = Field(None, description="关联的图片文件ID")

class SectionUpdate(BaseModel):
    """章节更新模式"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="章节标题")
    body_markdown: Optional[str] = Field(None, description="章节内容（Markdown格式）")
    image_file_id: Optional[int] = Field(None, description="关联的图片文件ID")

class SectionOrder(BaseModel):
    """章节排序模式"""
    id: int = Field(..., description="章节ID")
    order_index: int = Field(..., description="排序索引")

class SectionReorder(BaseModel):
    """章节重排序模式"""
    sections: List[SectionOrder] = Field(..., description="章节排序列表")


@router.post("/projects/{project_id}/sections", response_model=ResponseModel)
async def create_section(
    project_id: int,
    section_data: SectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建章节"""
    try:
        manual_service = ManualService(db)
        section = await manual_service.create_section(
            project_id=project_id,
            user_id=current_user.id,
            title=section_data.title,
            body_markdown=section_data.body_markdown,
            image_file_id=section_data.image_file_id
        )
        
        if not section:
            return ResponseModel(code=4001, message="项目不存在或不是操作文档项目")
        
        return ResponseModel(
            code=0,
            message="章节创建成功",
            data={
                "id": section.id,
                "title": section.title,
                "body_markdown": section.body_markdown,
                "order_index": section.order_index,
                "created_at": section.created_at
            }
        )
    except Exception as e:
        return ResponseModel(code=5001, message=f"创建章节失败: {str(e)}")


@router.get("/projects/{project_id}/sections", response_model=ResponseModel)
async def get_project_sections(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取项目章节列表"""
    try:
        manual_service = ManualService(db)
        sections = await manual_service.get_project_sections(project_id, current_user.id)
        
        if sections is None:
            return ResponseModel(code=4001, message="项目不存在或不是操作文档项目")
        
        return ResponseModel(
            code=0,
            message="获取成功",
            data={"sections": sections}
        )
    except Exception as e:
        return ResponseModel(code=5001, message=f"获取章节列表失败: {str(e)}")


@router.put("/sections/{section_id}", response_model=ResponseModel)
async def update_section(
    section_id: int,
    section_data: SectionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新章节"""
    try:
        manual_service = ManualService(db)
        section = await manual_service.update_section(
            section_id=section_id,
            user_id=current_user.id,
            title=section_data.title,
            body_markdown=section_data.body_markdown,
            image_file_id=section_data.image_file_id
        )
        
        if not section:
            return ResponseModel(code=4001, message="章节不存在或无权限")
        
        return ResponseModel(
            code=0,
            message="章节更新成功",
            data={
                "id": section.id,
                "title": section.title,
                "body_markdown": section.body_markdown,
                "order_index": section.order_index,
                "updated_at": section.updated_at
            }
        )
    except Exception as e:
        return ResponseModel(code=5001, message=f"更新章节失败: {str(e)}")


@router.delete("/sections/{section_id}", response_model=ResponseModel)
async def delete_section(
    section_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除章节"""
    try:
        manual_service = ManualService(db)
        success = await manual_service.delete_section(section_id, current_user.id)
        
        if not success:
            return ResponseModel(code=4001, message="章节不存在或无权限")
        
        return ResponseModel(
            code=0,
            message="章节删除成功"
        )
    except Exception as e:
        return ResponseModel(code=5001, message=f"删除章节失败: {str(e)}")


@router.put("/projects/{project_id}/sections/reorder", response_model=ResponseModel)
async def reorder_sections(
    project_id: int,
    reorder_data: SectionReorder,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重新排序章节"""
    try:
        manual_service = ManualService(db)
        success = await manual_service.reorder_sections(
            project_id=project_id,
            user_id=current_user.id,
            section_orders=[section.dict() for section in reorder_data.sections]
        )
        
        if not success:
            return ResponseModel(code=4001, message="项目不存在或无权限")
        
        return ResponseModel(
            code=0,
            message="章节排序更新成功"
        )
    except Exception as e:
        return ResponseModel(code=5001, message=f"更新章节排序失败: {str(e)}")


@router.get("/sections/{section_id}", response_model=ResponseModel)
async def get_section(
    section_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取章节详情"""
    try:
        manual_service = ManualService(db)
        section = await manual_service.get_section_by_id(section_id, current_user.id)
        
        if not section:
            return ResponseModel(code=4001, message="章节不存在或无权限")
        
        return ResponseModel(
            code=0,
            message="获取成功",
            data={
                "id": section.id,
                "title": section.title,
                "body_markdown": section.body_markdown,
                "image_file_id": section.image_file_id,
                "order_index": section.order_index,
                "created_at": section.created_at,
                "updated_at": section.updated_at
            }
        )
    except Exception as e:
        return ResponseModel(code=5001, message=f"获取章节详情失败: {str(e)}")
