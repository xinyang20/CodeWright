"""
导出服务
"""
import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.export_history import ExportHistory
from app.models.export_job import ExportJob
from app.paths import EXPORTS_DIR
from app.services.project_service import ProjectService

class ExportService:
    def __init__(self, db: Session):
        self.db = db
        self.project_service = ProjectService(db)
        self.export_dir = EXPORTS_DIR
        self.export_dir.mkdir(exist_ok=True)

    async def submit_export_job(
        self,
        project_id: int,
        user_id: int,
        options: Dict[str, Any] | None = None
    ) -> Optional[Dict[str, Any]]:
        """提交导出任务并返回任务状态。"""
        project = await self.project_service.get_project_by_id(project_id, user_id)
        if not project:
            return None

        export_job = ExportJob(
            project_id=project_id,
            job_id=uuid.uuid4().hex,
            status="queued",
            progress=0
        )
        self.db.add(export_job)
        self.db.commit()
        self.db.refresh(export_job)

        return self.get_job_status(export_job.job_id, user_id)

    async def process_export_job(
        self,
        job_id: str,
        user_id: int,
        options: Dict[str, Any] | None = None
    ) -> None:
        """执行导出任务。"""
        from app.services.pdf_service import PdfService

        export_job = self.db.query(ExportJob).join(ExportJob.project).filter(
            ExportJob.job_id == job_id,
            ExportJob.project.has(owner_id=user_id)
        ).first()
        if not export_job:
            return

        start_time = datetime.now()
        export_job.status = "processing"
        export_job.progress = 20
        self.db.commit()

        try:
            pdf_bytes = await PdfService(self.db).export_project_to_pdf(
                project_id=export_job.project_id,
                user_id=user_id,
                options=options or {}
            )

            if not pdf_bytes:
                raise ValueError("项目不存在或无可导出内容")

            filename = f"project_{export_job.project_id}_{export_job.job_id[:8]}.pdf"
            file_path = self.export_dir / filename
            with open(file_path, "wb") as pdf_file:
                pdf_file.write(pdf_bytes)

            export_job.status = "success"
            export_job.progress = 100
            export_job.result_file_path = str(file_path)
            export_job.error_message = None

            self.db.add(ExportHistory(
                project_id=export_job.project_id,
                exporter=export_job.project.project_type,
                status="success",
                duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                file_path=str(file_path)
            ))
            self.db.commit()
        except Exception as e:
            export_job.status = "failed"
            export_job.progress = 100
            export_job.error_message = str(e)
            self.db.add(ExportHistory(
                project_id=export_job.project_id,
                exporter=export_job.project.project_type,
                status="failed",
                duration_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            ))
            self.db.commit()

    def get_job_status(self, job_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """查询导出任务状态。"""
        export_job = self.db.query(ExportJob).join(ExportJob.project).filter(
            ExportJob.job_id == job_id,
            ExportJob.project.has(owner_id=user_id)
        ).first()
        if not export_job:
            return None

        return {
            "id": export_job.id,
            "project_id": export_job.project_id,
            "job_id": export_job.job_id,
            "status": export_job.status,
            "progress": export_job.progress,
            "result_file_path": export_job.result_file_path,
            "error_message": export_job.error_message,
            "created_at": export_job.created_at,
            "updated_at": export_job.updated_at,
            "download_url": f"/api/v1/exports/{export_job.job_id}/download" if export_job.result_file_path else None,
        }
    
    async def export_project_to_pdf(
        self, 
        project_id: int, 
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """导出项目为PDF"""
        from app.services.pdf_service import PdfService

        start_time = datetime.now()
        
        try:
            # 获取项目信息
            project = await self.project_service.get_project_by_id(project_id, user_id)
            if not project:
                return None
            
            pdf_bytes = await PdfService(self.db).export_project_to_pdf(
                project_id=project_id,
                user_id=user_id,
                options={}
            )
            if not pdf_bytes:
                return None

            pdf_filename = f"project_{project_id}_{uuid.uuid4().hex[:8]}.pdf"
            pdf_path = self.export_dir / pdf_filename

            with open(pdf_path, "wb") as pdf_file:
                pdf_file.write(pdf_bytes)
            
            # 记录导出历史
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            export_history = ExportHistory(
                project_id=project_id,
                exporter=project.project_type,
                status="success",
                duration_ms=duration_ms,
                file_path=str(pdf_path)
            )
            
            self.db.add(export_history)
            self.db.commit()
            
            return {
                "export_id": export_history.id,
                "file_path": str(pdf_path),
                "filename": pdf_filename,
                "duration_ms": duration_ms
            }
            
        except RuntimeError:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self.db.add(ExportHistory(
                project_id=project_id,
                exporter=project.project_type if "project" in locals() and project else "unknown",
                status="failed",
                duration_ms=duration_ms
            ))
            self.db.commit()
            raise
        except Exception as e:
            # 记录失败历史
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            export_history = ExportHistory(
                project_id=project_id,
                exporter=project.project_type if "project" in locals() and project else "unknown",
                status="failed",
                duration_ms=duration_ms
            )
            
            self.db.add(export_history)
            self.db.commit()
            
            return None
