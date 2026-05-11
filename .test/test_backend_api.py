import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'codewright_test.db'}")
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


def register_and_login(client: TestClient, username: str = "admin_user"):
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
    assert login.json()["code"] == 0
    token = login.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def login_default_admin(client: TestClient):
    login = client.post(
        "/api/v1/auth/token",
        json={"username": "admin", "password": "admin123"},
    )
    assert login.status_code == 200
    assert login.json()["code"] == 0
    assert login.json()["data"]["user"]["role"] == "admin"
    token = login.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_project(client: TestClient, headers: dict, project_type: str):
    response = client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "project_name": f"{project_type} project",
            "project_type": project_type,
        },
    )
    assert response.status_code == 200
    assert response.json()["code"] == 0
    return response.json()["data"]["project_id"]


def assert_pdf_response(response):
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF-")
    assert len(response.content) > 500


def test_default_admin_seeded_and_registered_users_are_regular(client):
    admin_headers = login_default_admin(client)

    me = client.get("/api/v1/users/me", headers=admin_headers)
    assert me.json()["code"] == 0
    assert me.json()["data"]["username"] == "admin"
    assert me.json()["data"]["role"] == "admin"

    user_headers = register_and_login(client, "normal_user")
    user_me = client.get("/api/v1/users/me", headers=user_headers)
    assert user_me.json()["code"] == 0
    assert user_me.json()["data"]["role"] == "user"


def test_code_project_upload_preview_export_and_history(client):
    headers = register_and_login(client)
    project_id = create_project(client, headers, "code")

    upload = client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("hello.py", b'print("hello")\n', "text/x-python")},
    )
    assert upload.status_code == 200
    assert upload.json()["code"] == 0
    file_id = upload.json()["data"]["file_id"]

    add_file = client.post(f"/api/v1/projects/{project_id}/files/{file_id}", headers=headers)
    assert add_file.json()["code"] == 0

    preview = client.get(f"/api/v1/files/{file_id}/preview", headers=headers)
    assert preview.json()["code"] == 0
    assert preview.json()["data"]["language"] == "python"
    assert "highlighted_html" in preview.json()["data"]

    project_preview = client.post(
        f"/api/v1/projects/{project_id}/preview",
        headers=headers,
        json={"include_toc": True, "include_summary": True},
    )
    assert project_preview.status_code == 200
    assert "hello.py" in project_preview.text

    pdf_preview = client.post(
        f"/api/v1/projects/{project_id}/preview/pdf",
        headers=headers,
        json={"include_toc": True, "include_summary": True, "watermark": False},
    )
    assert_pdf_response(pdf_preview)

    history_before_export = client.get("/api/v1/exports/history", headers=headers, params={"project_id": project_id})
    assert history_before_export.json()["code"] == 0
    assert history_before_export.json()["data"]["histories"] == []

    config = client.put(
        f"/api/v1/projects/{project_id}",
        headers=headers,
        json={
            "config_json": {
                "code_options": {
                    "formatting": ["line_numbers", "highlight_syntax"],
                    "layout": "single_column",
                    "font_size": "14px",
                    "export_options": ["include_toc", "include_summary"],
                },
                "export_options": ["include_toc", "include_summary"],
            }
        },
    )
    assert config.json()["code"] == 0

    export = client.post(
        f"/api/v1/projects/{project_id}/export/pdf",
        headers=headers,
        json={"include_toc": True, "include_summary": True, "watermark": False},
    )
    assert_pdf_response(export)

    history = client.get("/api/v1/exports/history", headers=headers, params={"project_id": project_id})
    assert history.json()["code"] == 0
    assert history.json()["data"]["histories"][0]["status"] == "success"


def test_manual_sections_reorder_preview_export_and_history(client):
    headers = register_and_login(client)
    project_id = create_project(client, headers, "manual")

    upload = client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("screen.png", b"\x89PNG\r\n\x1a\n", "image/png")},
    )
    assert upload.json()["code"] == 0
    image_file_id = upload.json()["data"]["file_id"]

    first = client.post(
        f"/api/v1/projects/{project_id}/sections",
        headers=headers,
        json={
            "title": "安装说明",
            "body_markdown": "## 安装\n运行安装程序。",
            "image_file_id": image_file_id,
        },
    )
    assert first.json()["code"] == 0
    first_id = first.json()["data"]["id"]

    second = client.post(
        f"/api/v1/projects/{project_id}/sections",
        headers=headers,
        json={"title": "使用说明", "body_markdown": "打开软件并登录。"},
    )
    assert second.json()["code"] == 0
    second_id = second.json()["data"]["id"]

    reorder = client.put(
        f"/api/v1/projects/{project_id}/sections/reorder",
        headers=headers,
        json=[
            {"section_id": second_id, "order_index": 1},
            {"section_id": first_id, "order_index": 2},
        ],
    )
    assert reorder.json()["code"] == 0

    sections = client.get(f"/api/v1/projects/{project_id}/sections", headers=headers)
    assert sections.json()["code"] == 0
    assert sections.json()["data"]["sections"][0]["id"] == second_id

    update = client.put(
        f"/api/v1/projects/{project_id}/sections/{first_id}",
        headers=headers,
        json={"title": "安装与启动"},
    )
    assert update.json()["code"] == 0
    assert update.json()["data"]["title"] == "安装与启动"

    export = client.post(
        f"/api/v1/projects/{project_id}/export/pdf",
        headers=headers,
        json={"include_toc": True, "include_summary": True, "watermark": False},
    )
    assert_pdf_response(export)

    history = client.get("/api/v1/exports/history", headers=headers, params={"project_id": project_id})
    assert history.json()["code"] == 0
    assert history.json()["data"]["histories"][0]["exporter"] == "manual"


def test_admin_user_status_stats_and_templates(client):
    admin_headers = login_default_admin(client)

    user_register = client.post(
        "/api/v1/auth/register",
        json={"username": "normal_user", "password": "123456"},
    )
    assert user_register.json()["code"] == 0
    user_id = user_register.json()["data"]["user_id"]

    stats = client.get("/api/v1/admin/stats", headers=admin_headers)
    assert stats.json()["code"] == 0
    assert stats.json()["data"]["users"]["total"] == 2
    assert stats.json()["data"]["users"]["admin"] == 1

    users = client.get("/api/v1/admin/users", headers=admin_headers)
    assert users.json()["code"] == 0
    assert users.json()["data"]["total"] == 2

    disable = client.put(
        f"/api/v1/admin/users/{user_id}/status",
        headers=admin_headers,
        params={"is_active": False},
    )
    assert disable.json()["code"] == 0

    disable_admin = client.put(
        "/api/v1/admin/users/1/status",
        headers=admin_headers,
        params={"is_active": False},
    )
    assert disable_admin.json()["code"] != 0

    template = client.post(
        "/api/v1/settings/templates",
        headers=admin_headers,
        data={"name": "测试模板", "version": "1.0.0", "description": "pytest"},
        files={"file": ("template.html", b"<html><body>{{project_name}}</body></html>", "text/html")},
    )
    assert template.json()["code"] == 0
    template_id = template.json()["data"]["template_id"]

    update_status = client.put(
        f"/api/v1/settings/templates/{template_id}/status",
        headers=admin_headers,
        params={"status": "published"},
    )
    assert update_status.json()["code"] == 0

    templates = client.get("/api/v1/settings/templates", headers=admin_headers)
    assert templates.json()["code"] == 0
    assert any(item["id"] == template_id for item in templates.json()["data"]["templates"])

    duplicate = client.post(
        "/api/v1/settings/templates",
        headers=admin_headers,
        data={"name": "测试模板", "version": "1.0.0", "description": "duplicate"},
        files={"file": ("template.html", b"<html><body>duplicate</body></html>", "text/html")},
    )
    assert duplicate.json()["code"] != 0


def test_settings_announcements_highlight_mapping_and_project_upload(client):
    admin_headers = login_default_admin(client)

    settings = client.get("/api/v1/settings/system", headers=admin_headers)
    assert settings.json()["code"] == 0
    assert settings.json()["data"]["pdf_style"]["latex_engine"] == "xelatex"
    upload_settings = settings.json()["data"]["upload"]
    upload_settings["allowed_extensions"].append(".foo")

    update_upload = client.put(
        "/api/v1/settings/system/upload",
        headers=admin_headers,
        json=upload_settings,
    )
    assert update_upload.json()["code"] == 0

    update_pdf = client.put(
        "/api/v1/settings/system/pdf_style",
        headers=admin_headers,
        json={
            "latex_engine": "xelatex",
            "document_class": "article",
            "font_size": "12pt",
            "page_geometry": "a4paper,margin=1.8cm",
            "main_font": "PingFang SC",
            "mono_font": "Menlo",
            "line_stretch": "1.2",
            "header_latex": r"CodeWright 测试",
            "footer_latex": r"\thepage",
            "preamble_latex": r"\setlength{\parindent}{0pt}",
        },
    )
    assert update_pdf.json()["code"] == 0

    mapping = client.put(
        "/api/v1/settings/highlight-mapping",
        headers=admin_headers,
        json=[{"suffix": ".foo", "language": "python", "enabled": True}],
    )
    assert mapping.json()["code"] == 0
    assert any(item["suffix"] == ".foo" for item in mapping.json()["data"]["mappings"])

    project_id = create_project(client, admin_headers, "code")
    upload = client.post(
        f"/api/v1/projects/{project_id}/upload",
        headers=admin_headers,
        files={"file": ("sample.foo", b"print('mapped')\n", "text/plain")},
    )
    assert upload.json()["code"] == 0
    file_id = upload.json()["data"]["file_id"]

    preview = client.get(f"/api/v1/files/{file_id}/preview", headers=admin_headers)
    assert preview.json()["code"] == 0
    assert preview.json()["data"]["language"] == "python"

    announcement = client.post(
        "/api/v1/settings/announcements",
        headers=admin_headers,
        json={"title": "维护通知", "body_markdown": "今晚发布新版本", "status": "published"},
    )
    assert announcement.json()["code"] == 0
    announcement_id = announcement.json()["data"]["id"]

    published = client.get("/api/v1/settings/announcements/published")
    assert published.json()["code"] == 0
    assert any(item["id"] == announcement_id for item in published.json()["data"]["announcements"])

    archive = client.put(
        f"/api/v1/settings/announcements/{announcement_id}",
        headers=admin_headers,
        json={"status": "archived"},
    )
    assert archive.json()["code"] == 0


def test_export_job_preview_template_and_manual_variables(client):
    headers = login_default_admin(client)

    template = client.post(
        "/api/v1/settings/templates",
        headers=headers,
        data={"name": "手册模板", "version": "1.0.0", "description": "manual"},
        files={
            "file": (
                "manual.html",
                b"<html><body><h1>{{software_name}}</h1><main>{{sections|safe}}</main></body></html>",
                "text/html",
            )
        },
    )
    assert template.json()["code"] == 0
    template_id = template.json()["data"]["template_id"]
    publish = client.put(
        f"/api/v1/settings/templates/{template_id}/status",
        headers=headers,
        params={"status": "published"},
    )
    assert publish.json()["code"] == 0

    project = client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "project_name": "manual project",
            "project_type": "manual",
            "manual_options": {
                "template": str(template_id),
                "template_id": template_id,
                "default_sections": ["overview"],
                "software_name": "测试软件",
                "version": "V1.2.3",
                "developer": "测试团队",
                "enable_global_variables": True,
            },
        },
    )
    assert project.json()["code"] == 0
    project_id = project.json()["data"]["project_id"]

    sections = client.get(f"/api/v1/projects/{project_id}/sections", headers=headers)
    assert sections.json()["code"] == 0
    assert len(sections.json()["data"]["sections"]) == 1

    preview = client.get(f"/api/v1/projects/{project_id}/preview", headers=headers)
    assert preview.status_code == 200
    assert "测试软件" in preview.text
    assert "{{软件名称}}" not in preview.text

    job_response = client.post(
        f"/api/v1/projects/{project_id}/export",
        headers=headers,
        json={"include_toc": True, "include_summary": True},
    )
    assert job_response.json()["code"] == 0
    job_id = job_response.json()["data"]["job_id"]

    status = client.get(f"/api/v1/exports/{job_id}", headers=headers)
    assert status.json()["code"] == 0
    assert status.json()["data"]["status"] == "success"
    assert status.json()["data"]["download_url"].endswith(f"/{job_id}/download")

    download = client.get(f"/api/v1/exports/{job_id}/download", headers=headers)
    assert_pdf_response(download)
