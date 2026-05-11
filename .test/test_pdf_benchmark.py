"""Performance benchmark for the LaTeX PDF export pipeline.

This test only runs locally where a real LaTeX toolchain is available.  In CI
or when ``CODEWRIGHT_ALLOW_IMAGE_PDF_FALLBACK`` is set the benchmark is
skipped because the image fallback does not reflect real performance.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"

LARGE_FILE_LINES = 2000
LATENCY_BUDGET_SECONDS = 10.0


pytestmark = pytest.mark.skipif(
    os.getenv("CODEWRIGHT_ALLOW_IMAGE_PDF_FALLBACK") == "1"
    or os.getenv("CODEWRIGHT_RUN_BENCHMARK") != "1",
    reason=(
        "PDF benchmark is opt-in; export CODEWRIGHT_RUN_BENCHMARK=1 in a local "
        "environment with TinyTeX/xelatex to run it (and disable the image fallback)."
    ),
)


def _build_python_source(line_count: int) -> str:
    lines: list[str] = []
    for index in range(line_count):
        lines.append(
            f"def function_{index:04d}(value):\n"
            f"    \"\"\"Auto-generated benchmark line {index}.\"\"\"\n"
            f"    return value + {index}"
        )
    return "\n".join(lines).encode().decode()


@pytest.fixture()
def benchmark_client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'codewright_bench.db'}")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("CODEWRIGHT_UPLOAD_DIR", str(tmp_path / "upload"))
    monkeypatch.setenv("CODEWRIGHT_TEMPLATES_DIR", str(tmp_path / "templates"))
    monkeypatch.setenv("CODEWRIGHT_EXPORTS_DIR", str(tmp_path / "exports"))
    monkeypatch.delenv("CODEWRIGHT_ALLOW_IMAGE_PDF_FALLBACK", raising=False)

    for name in list(sys.modules):
        if name == "main" or name.startswith("app."):
            del sys.modules[name]

    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))

    from main import app

    with TestClient(app) as test_client:
        yield test_client


def _login_admin(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/token",
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def test_pdf_export_2000_lines_under_budget(benchmark_client):
    headers = _login_admin(benchmark_client)

    project = benchmark_client.post(
        "/api/v1/projects",
        headers=headers,
        json={"project_name": "benchmark-2000", "project_type": "code"},
    )
    project_id = project.json()["data"]["project_id"]

    payload = _build_python_source(LARGE_FILE_LINES // 3 + 1).encode("utf-8")
    upload = benchmark_client.post(
        f"/api/v1/projects/{project_id}/upload",
        headers=headers,
        files={"file": ("large_module.py", payload, "text/x-python")},
    )
    assert upload.json()["code"] == 0

    start = time.perf_counter()
    response = benchmark_client.post(
        f"/api/v1/projects/{project_id}/export/pdf",
        headers=headers,
        json={"include_toc": True, "include_summary": True},
    )
    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert elapsed < LATENCY_BUDGET_SECONDS, (
        f"PDF benchmark took {elapsed:.2f}s, budget {LATENCY_BUDGET_SECONDS}s"
    )
