"""Validation, edge-case and refactor regression tests for the backend API."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'codewright_validation.db'}")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("CODEWRIGHT_UPLOAD_DIR", str(tmp_path / "upload"))
    monkeypatch.setenv("CODEWRIGHT_TEMPLATES_DIR", str(tmp_path / "templates"))
    monkeypatch.setenv("CODEWRIGHT_EXPORTS_DIR", str(tmp_path / "exports"))
    monkeypatch.setenv("CODEWRIGHT_ALLOW_IMAGE_PDF_FALLBACK", "1")

    for name in list(sys.modules):
        if name == "main" or name.startswith("app."):
            del sys.modules[name]

    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))

    from main import app

    with TestClient(app) as test_client:
        yield test_client


def _register_login(client: TestClient, username: str = "validator_user") -> dict[str, str]:
    register = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": "123456"},
    )
    assert register.status_code == 200
    assert register.json()["code"] == 0

    login = client.post(
        "/api/v1/auth/token",
        json={"username": username, "password": "123456"},
    )
    assert login.status_code == 200
    token = login.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _login_admin(client: TestClient) -> dict[str, str]:
    login = client.post(
        "/api/v1/auth/token",
        json={"username": "admin", "password": "admin123"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['data']['access_token']}"}


def _create_project(client: TestClient, headers: dict[str, str], project_type: str = "code") -> int:
    response = client.post(
        "/api/v1/projects",
        headers=headers,
        json={"project_name": f"{project_type} pytest", "project_type": project_type},
    )
    assert response.status_code == 200
    return response.json()["data"]["project_id"]


def test_health_endpoints_expose_app_version(client):
    health = client.get("/health")
    healthz = client.get("/healthz")
    assert health.status_code == healthz.status_code == 200
    assert health.json()["status"] == healthz.json()["status"] == "healthy"
    assert health.json()["version"] == healthz.json()["version"]


def test_oversized_upload_returns_invalid_file_code(client):
    admin_headers = _login_admin(client)
    settings = client.get("/api/v1/settings/system", headers=admin_headers).json()["data"]
    upload_settings = settings["upload"]
    upload_settings["max_upload_size_mb"] = 1
    update = client.put(
        "/api/v1/settings/system/upload",
        headers=admin_headers,
        json=upload_settings,
    )
    assert update.json()["code"] == 0

    user_headers = _register_login(client, "size_user")
    too_big = b"a" * (2 * 1024 * 1024)
    response = client.post(
        "/api/v1/files/upload",
        headers=user_headers,
        files={"file": ("payload.py", too_big, "text/x-python")},
    )
    assert response.json()["code"] == 2001


def test_disallowed_extension_blocks_upload(client):
    headers = _register_login(client, "ext_user")
    response = client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("malware.exe", b"binary", "application/octet-stream")},
    )
    assert response.json()["code"] == 2001


def test_admin_only_route_blocks_normal_user(client):
    headers = _register_login(client, "regular_user")
    response = client.get("/api/v1/admin/stats", headers=headers)
    assert response.status_code == 403


def test_template_status_invalid_value_returns_param_code(client):
    admin_headers = _login_admin(client)
    template = client.post(
        "/api/v1/settings/templates",
        headers=admin_headers,
        data={"name": "状态校验模板", "version": "1.0.0", "description": "validate"},
        files={"file": ("validate.html", b"<html><body>{{project_name}}</body></html>", "text/html")},
    )
    template_id = template.json()["data"]["template_id"]

    response = client.put(
        f"/api/v1/settings/templates/{template_id}/status",
        headers=admin_headers,
        params={"status": "wip"},
    )
    assert response.json()["code"] == 1001


def test_announcement_with_blank_title_returns_param_code(client):
    admin_headers = _login_admin(client)
    response = client.post(
        "/api/v1/settings/announcements",
        headers=admin_headers,
        json={"title": "", "body_markdown": "正文", "status": "draft"},
    )
    assert response.json()["code"] == 1001


def test_template_clone_creates_new_draft(client):
    admin_headers = _login_admin(client)

    create = client.post(
        "/api/v1/settings/templates",
        headers=admin_headers,
        data={"name": "克隆测试模板", "version": "1.0.0", "description": "clone"},
        files={"file": ("clone_seed.html", b"<html><body>{{project_name}}</body></html>", "text/html")},
    )
    template_id = create.json()["data"]["template_id"]

    clone = client.post(
        f"/api/v1/settings/templates/{template_id}/clone",
        headers=admin_headers,
        json={"version": "1.0.1"},
    )
    assert clone.json()["code"] == 0
    assert clone.json()["data"]["version"] == "1.0.1"
    assert clone.json()["data"]["status"] == "draft"


def test_delete_highlight_mapping(client):
    admin_headers = _login_admin(client)
    client.put(
        "/api/v1/settings/highlight-mapping",
        headers=admin_headers,
        json=[{"suffix": ".widget", "language": "html", "enabled": True}],
    )
    response = client.delete("/api/v1/settings/highlight-mapping/.widget", headers=admin_headers)
    assert response.json()["code"] == 0

    after = client.get("/api/v1/settings/highlight-mapping", headers=admin_headers)
    assert all(item["suffix"] != ".widget" for item in after.json()["data"]["mappings"])


def test_project_size_limit_uses_aggregate_query(client):
    admin_headers = _login_admin(client)
    project_id = _create_project(client, admin_headers, "code")

    one_mb = b"x" * (1024 * 1024)
    for index in range(11):
        upload = client.post(
            f"/api/v1/projects/{project_id}/upload",
            headers=admin_headers,
            files={"file": (f"chunk_{index}.txt", one_mb, "text/plain")},
        )
        assert upload.json()["code"] == 0


def test_options_for_project_isolated_from_manual_fields(client):
    headers = _login_admin(client)
    project_id = _create_project(client, headers, "code")

    from app.database import SessionLocal
    from app.models.project import Project
    from app.services.pdf_service import PdfService

    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).one()
        merged = PdfService(db)._options_for_project(
            project,
            {
                "include_toc": True,
                "software_name": "should_not_apply",
                "version": "9.9.9",
                "developer": "ghost",
                "template": "标题污染",
                "layout": "double_column",
                "font_size": "12px",
                "file_name_bold": False,
            },
        )
    finally:
        db.close()

    assert merged["layout"] == "double_column"
    assert merged["font_size"] == "12px"
    assert merged["file_name_bold"] is False
    assert merged.get("include_toc") is True
    assert "software_name" not in merged or not merged.get("software_name")
    assert "developer" not in merged or not merged.get("developer")


def test_export_history_pagination_and_status_filter(client):
    headers = _login_admin(client)
    project_id = _create_project(client, headers, "code")

    upload = client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("hello.py", b"print('hi')\n", "text/x-python")},
    )
    file_id = upload.json()["data"]["file_id"]
    add_file = client.post(f"/api/v1/projects/{project_id}/files/{file_id}", headers=headers)
    assert add_file.json()["code"] == 0

    for _ in range(2):
        response = client.post(
            f"/api/v1/projects/{project_id}/export/pdf",
            headers=headers,
            json={"include_toc": True},
        )
        assert response.status_code == 200

    history = client.get(
        "/api/v1/exports/history",
        headers=headers,
        params={"status": "success", "page": 1, "page_size": 1},
    )
    payload = history.json()["data"]
    assert payload["total"] >= 2
    assert payload["page"] == 1
    assert payload["page_size"] == 1
    assert len(payload["histories"]) == 1
    assert payload["histories"][0]["status"] == "success"


def test_export_retry_creates_new_job_with_same_options(client):
    headers = _login_admin(client)
    project_id = _create_project(client, headers, "code")

    upload = client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("retry.py", b"print('retry')\n", "text/x-python")},
    )
    file_id = upload.json()["data"]["file_id"]
    add_file = client.post(f"/api/v1/projects/{project_id}/files/{file_id}", headers=headers)
    assert add_file.json()["code"] == 0

    submit = client.post(
        f"/api/v1/projects/{project_id}/export",
        headers=headers,
        json={"include_toc": True, "include_summary": True},
    )
    assert submit.json()["code"] == 0
    job_id = submit.json()["data"]["job_id"]

    retry = client.post(f"/api/v1/exports/{job_id}/retry", headers=headers)
    assert retry.json()["code"] == 0
    new_job_id = retry.json()["data"]["job_id"]
    assert new_job_id != job_id

    from app.database import SessionLocal
    from app.models.export_job import ExportJob

    db = SessionLocal()
    try:
        original = db.query(ExportJob).filter(ExportJob.job_id == job_id).one()
        retried = db.query(ExportJob).filter(ExportJob.job_id == new_job_id).one()
        original_options = json.loads(original.options_json or "{}")
        retried_options = json.loads(retried.options_json or "{}")
        assert original_options == retried_options
    finally:
        db.close()


def test_project_list_keyword_filter(client):
    headers = _login_admin(client)

    for name in ("alpha-keep", "beta-skip", "alpha-second"):
        client.post(
            "/api/v1/projects",
            headers=headers,
            json={"project_name": name, "project_type": "code"},
        )

    response = client.get(
        "/api/v1/projects",
        headers=headers,
        params={"keyword": "alpha", "order": "name_asc", "page": 1, "page_size": 10},
    )
    payload = response.json()["data"]
    names = [item["project_name"] for item in payload["projects"]]
    assert names == sorted(names)
    assert all(name.startswith("alpha") for name in names)
    assert payload["total"] == len(names)
