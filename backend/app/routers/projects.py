"""
项目路由
"""
from datetime import datetime
from urllib.parse import quote
from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, Query, UploadFile
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db, SessionLocal
from app.models.export_history import ExportHistory
from app.schemas.project import ProjectCreate, ProjectUpdate, ManualSectionCreate, ManualSectionUpdate
from app.schemas.common import ResponseModel, ErrorCodes
from app.services.auth_service import get_current_user
from app.services.export_service import ExportService
from app.services.file_service import FileService
from app.services.project_service import ProjectService
from app.models.user import User

router = APIRouter()


async def _run_export_job(job_id: str, user_id: int, options: dict) -> None:
    """在本地后台任务中执行导出，保持 /projects/{id}/export API 可查询。"""
    db = SessionLocal()
    try:
        await ExportService(db).process_export_job(job_id, user_id, options)
    finally:
        db.close()

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
    keyword: Optional[str] = Query(None, max_length=100),
    order: str = Query(
        "updated_desc",
        pattern="^(updated_desc|updated_asc|created_desc|created_asc|name_asc|name_desc)$",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取项目列表"""
    try:
        project_service = ProjectService(db)
        projects = await project_service.get_user_projects(
            current_user.id,
            project_type,
            page,
            page_size,
            keyword=keyword,
            order=order,
        )
        return ResponseModel(
            code=ErrorCodes.OK,
            message="获取成功",
            data=projects
        )
    except Exception:
        return ResponseModel(code=ErrorCodes.SERVER_ERROR, message="服务器内部错误")

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

@router.put("/{project_id}/files/reorder", response_model=ResponseModel)
async def reorder_project_files(
    project_id: int,
    file_orders: list = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重新排序项目文件"""
    try:
        project_service = ProjectService(db)
        success = await project_service.reorder_project_files(
            project_id, file_orders, current_user.id
        )

        if not success:
            return ResponseModel(code=4001, message="项目不存在或文件顺序无效")

        return ResponseModel(
            code=0,
            message="文件顺序更新成功"
        )
    except Exception as e:
        return ResponseModel(code=5001, message="更新文件顺序失败")

@router.post("/{project_id}/upload", response_model=ResponseModel)
async def upload_file_to_project(
    project_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传文件并直接加入项目"""
    try:
        project_service = ProjectService(db)
        project = await project_service.get_project_by_id(project_id, current_user.id)
        if not project:
            return ResponseModel(code=ErrorCodes.NOT_FOUND, message="项目不存在")

        file_service = FileService(db)
        file_content = await file.read()
        valid, message = file_service.validate_upload(file.filename or "", len(file_content))
        if not valid:
            return ResponseModel(code=ErrorCodes.INVALID_FILE, message=message)

        uploaded_file = await file_service.save_uploaded_file(file, current_user.id, file_content)
        success = await project_service.add_file_to_project(project_id, uploaded_file.id, current_user.id)
        if not success:
            await file_service.delete_file(uploaded_file.id, current_user.id)
            return ResponseModel(code=ErrorCodes.INVALID_FILE, message="项目总文件大小超过限制")

        return ResponseModel(
            code=ErrorCodes.OK,
            message="文件上传成功",
            data={
                "file_id": uploaded_file.id,
                "filename": uploaded_file.original_filename,
                "file_size": uploaded_file.file_size,
            }
        )
    except Exception:
        return ResponseModel(code=ErrorCodes.SERVER_ERROR, message="文件上传失败")

@router.get("/{project_id}/preview")
async def preview_project_html(
    project_id: int,
    format: str = Query("html", pattern="^html$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """导出前 HTML 预览"""
    try:
        from app.services.pdf_service import PdfService

        html = await PdfService(db).render_project_html(project_id, current_user.id)
        if not html:
            return ResponseModel(code=4001, message="项目不存在或无可预览内容")
        return HTMLResponse(content=html)
    except Exception as e:
        return ResponseModel(code=5001, message=f"生成预览失败: {str(e)}")

@router.post("/{project_id}/preview")
async def preview_project_html_with_options(
    project_id: int,
    preview_options: dict = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """按本次导出参数生成 HTML 预览，确保预览与导出使用同一组选项。"""
    try:
        from app.services.pdf_service import PdfService

        html = await PdfService(db).render_project_html(project_id, current_user.id, preview_options)
        if not html:
            return ResponseModel(code=4001, message="项目不存在或无可预览内容")
        return HTMLResponse(content=html)
    except Exception as e:
        return ResponseModel(code=5001, message=f"生成预览失败: {str(e)}")

@router.post("/{project_id}/preview/pdf")
async def preview_project_pdf(
    project_id: int,
    preview_options: dict = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """生成 PDF 预览，不写入导出历史，确保预览和下载使用同一条 LaTeX 链路。"""
    try:
        from app.services.pdf_service import PdfService
        from fastapi.responses import Response

        project_service = ProjectService(db)
        project = await project_service.get_project_by_id(project_id, current_user.id)
        if not project:
            return ResponseModel(code=4001, message="项目不存在")

        pdf_bytes = await PdfService(db).export_project_to_pdf(
            project_id=project_id,
            user_id=current_user.id,
            options=preview_options,
            use_cache=True,
        )
        if not pdf_bytes:
            return ResponseModel(code=4001, message="项目不存在或无文件可预览")

        filename = f"{project.project_name}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename*=UTF-8''{quote(filename)}"
            }
        )
    except RuntimeError as e:
        return ResponseModel(code=5001, message=str(e))
    except Exception:
        return ResponseModel(code=5001, message="PDF预览失败")

@router.post("/{project_id}/export", response_model=ResponseModel)
async def submit_project_export_job(
    project_id: int,
    background_tasks: BackgroundTasks,
    export_options: dict = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提交项目导出任务"""
    try:
        export_service = ExportService(db)
        job = await export_service.submit_export_job(project_id, current_user.id, export_options)
        if not job:
            return ResponseModel(code=ErrorCodes.NOT_FOUND, message="项目不存在")
        background_tasks.add_task(_run_export_job, job["job_id"], current_user.id, export_options)
        return ResponseModel(code=ErrorCodes.OK, message="导出任务已提交", data=job)
    except Exception:
        return ResponseModel(code=ErrorCodes.EXPORT_FAILED, message="提交导出任务失败")

@router.post("/{project_id}/export/pdf")
async def export_project_pdf(
    project_id: int,
    export_options: dict = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """导出项目为PDF"""
    start_time = datetime.now()
    try:
        from app.services.pdf_service import PdfService
        from fastapi.responses import Response

        project_service = ProjectService(db)
        project = await project_service.get_project_by_id(project_id, current_user.id)
        if not project:
            return ResponseModel(code=ErrorCodes.NOT_FOUND, message="项目不存在")

        pdf_service = PdfService(db)
        pdf_bytes = await pdf_service.export_project_to_pdf(
            project_id=project_id,
            user_id=current_user.id,
            options=export_options
        )

        if not pdf_bytes:
            db.add(ExportHistory(
                project_id=project_id,
                exporter=project.project_type,
                status="failed",
                duration_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            ))
            db.commit()
            return ResponseModel(code=ErrorCodes.NOT_FOUND, message="项目不存在或无文件可导出")

        db.add(ExportHistory(
            project_id=project_id,
            exporter=project.project_type,
            status="success",
            duration_ms=int((datetime.now() - start_time).total_seconds() * 1000)
        ))
        db.commit()

        filename = f"{project.project_name}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"
            }
        )

    except RuntimeError as e:
        db.add(ExportHistory(
            project_id=project_id,
            exporter=project.project_type if "project" in locals() and project else "unknown",
            status="failed",
            duration_ms=int((datetime.now() - start_time).total_seconds() * 1000)
        ))
        db.commit()
        return ResponseModel(code=ErrorCodes.EXPORT_FAILED, message=str(e))
    except Exception:
        return ResponseModel(code=ErrorCodes.EXPORT_FAILED, message="PDF导出失败")

@router.get("/{project_id}/sections", response_model=ResponseModel)
async def get_manual_sections(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取操作文档章节列表"""
    try:
        project_service = ProjectService(db)
        sections = await project_service.get_manual_sections(project_id, current_user.id)
        if sections is None:
            return ResponseModel(code=4001, message="项目不存在")

        return ResponseModel(code=0, message="获取成功", data={"sections": sections})
    except Exception:
        return ResponseModel(code=5001, message="获取章节失败")

@router.post("/{project_id}/sections", response_model=ResponseModel)
async def create_manual_section(
    project_id: int,
    section_data: ManualSectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建操作文档章节"""
    try:
        project_service = ProjectService(db)
        section = await project_service.create_manual_section(project_id, current_user.id, section_data)
        if not section:
            return ResponseModel(code=4001, message="项目不存在、类型不匹配或图片不存在")

        return ResponseModel(code=0, message="章节创建成功", data=section)
    except Exception:
        return ResponseModel(code=5001, message="创建章节失败")

@router.put("/{project_id}/sections/reorder", response_model=ResponseModel)
async def reorder_manual_sections(
    project_id: int,
    section_orders: list = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重新排序操作文档章节"""
    try:
        project_service = ProjectService(db)
        success = await project_service.reorder_manual_sections(
            project_id, section_orders, current_user.id
        )
        if not success:
            return ResponseModel(code=4001, message="项目不存在或章节顺序无效")

        return ResponseModel(code=0, message="章节顺序更新成功")
    except Exception:
        return ResponseModel(code=5001, message="更新章节顺序失败")

@router.put("/{project_id}/sections/{section_id}", response_model=ResponseModel)
async def update_manual_section(
    project_id: int,
    section_id: int,
    section_data: ManualSectionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新操作文档章节"""
    try:
        project_service = ProjectService(db)
        section = await project_service.update_manual_section(
            project_id, section_id, current_user.id, section_data
        )
        if not section:
            return ResponseModel(code=4001, message="章节不存在或图片不存在")

        return ResponseModel(code=0, message="章节更新成功", data=section)
    except Exception:
        return ResponseModel(code=5001, message="更新章节失败")

@router.delete("/{project_id}/sections/{section_id}", response_model=ResponseModel)
async def delete_manual_section(
    project_id: int,
    section_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除操作文档章节"""
    try:
        project_service = ProjectService(db)
        success = await project_service.delete_manual_section(project_id, section_id, current_user.id)
        if not success:
            return ResponseModel(code=4001, message="章节不存在")

        return ResponseModel(code=0, message="章节删除成功")
    except Exception:
        return ResponseModel(code=5001, message="删除章节失败")
