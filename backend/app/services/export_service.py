"""
导出服务
"""
import json
import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.export_history import ExportHistory
from app.models.export_job import ExportJob
from app.paths import EXPORTS_DIR
from app.services.project_service import ProjectService


def _job_log_path(job_id: str) -> str:
    return str(EXPORTS_DIR / "logs" / f"{job_id}.log")


class ExportService:
    def __init__(self, db: Session):
        self.db = db
        self.project_service = ProjectService(db)
        self.export_dir = EXPORTS_DIR
        self.export_dir.mkdir(exist_ok=True)
        (self.export_dir / "logs").mkdir(parents=True, exist_ok=True)

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
            progress=0,
            options_json=json.dumps(options or {}, ensure_ascii=False),
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
        from pathlib import Path
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
        if options is not None:
            export_job.options_json = json.dumps(options, ensure_ascii=False)
        self.db.commit()

        log_path = Path(_job_log_path(job_id))

        try:
            pdf_bytes = await PdfService(self.db).export_project_to_pdf(
                project_id=export_job.project_id,
                user_id=user_id,
                options=options or {},
                log_path=log_path,
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
            export_job.error_log_path = None

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
            export_job.error_log_path = str(log_path) if log_path.exists() else None
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

        return self._serialize_job(export_job)

    def _serialize_job(self, export_job: ExportJob) -> Dict[str, Any]:
        return {
            "id": export_job.id,
            "project_id": export_job.project_id,
            "project_name": export_job.project.project_name if export_job.project else None,
            "job_id": export_job.job_id,
            "status": export_job.status,
            "progress": export_job.progress,
            "result_file_path": export_job.result_file_path,
            "error_message": export_job.error_message,
            "created_at": export_job.created_at,
            "updated_at": export_job.updated_at,
            "download_url": f"/api/v1/exports/{export_job.job_id}/download" if export_job.result_file_path else None,
            "error_log_url": f"/api/v1/exports/{export_job.job_id}/log" if export_job.error_log_path else None,
        }

    async def list_jobs(
        self,
        user_id: int,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """List export jobs owned by ``user_id`` with optional filters."""
        query = self.db.query(ExportJob).join(ExportJob.project).filter(
            ExportJob.project.has(owner_id=user_id)
        )
        if status:
            query = query.filter(ExportJob.status == status)

        total = query.count()
        jobs = (
            query.order_by(ExportJob.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "jobs": [self._serialize_job(job) for job in jobs],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    async def retry_export_job(
        self,
        job_id: str,
        user_id: int,
    ) -> Optional[Dict[str, Any]]:
        """Create a new job that mirrors the options of an earlier failed job."""
        original = self.db.query(ExportJob).join(ExportJob.project).filter(
            ExportJob.job_id == job_id,
            ExportJob.project.has(owner_id=user_id)
        ).first()
        if not original:
            return None

        try:
            options = json.loads(original.options_json or "{}")
        except (TypeError, json.JSONDecodeError):
            options = {}

        new_job = ExportJob(
            project_id=original.project_id,
            job_id=uuid.uuid4().hex,
            status="queued",
            progress=0,
            options_json=json.dumps(options, ensure_ascii=False),
        )
        self.db.add(new_job)
        self.db.commit()
        self.db.refresh(new_job)
        return {
            "job": self.get_job_status(new_job.job_id, user_id),
            "options": options,
        }
