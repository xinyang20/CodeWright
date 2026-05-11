"""
CodeWright 后端主应用
"""
import os
import tomllib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from sqlalchemy import inspect, text

from app.paths import BACKEND_DIR, EXPORTS_DIR, UPLOAD_DIR, ensure_runtime_dirs


def _resolve_app_version() -> str:
    """Read the application version from pyproject.toml or env override."""
    override = os.getenv("CODEWRIGHT_VERSION")
    if override:
        return override.strip()
    pyproject_path = BACKEND_DIR / "pyproject.toml"
    if pyproject_path.exists():
        try:
            data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
            version = data.get("project", {}).get("version")
            if version:
                return str(version)
        except Exception:
            pass
    return "0.0.0"


APP_VERSION = _resolve_app_version()

# 加载环境变量
load_dotenv(BACKEND_DIR / ".env")

from app.database import engine, Base, SessionLocal
from app.routers import auth, users, projects, files, exports, admin, settings
from app.services.auth_service import AuthService
from app.services.highlight_service import HighlightService
from app.services.settings_service import SettingsService


def _apply_lightweight_migrations() -> None:
    """Apply small additive migrations that SQLite cannot infer from metadata."""
    inspector = inspect(engine)
    if "export_jobs" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("export_jobs")}
    pending = [
        ("error_log_path", "VARCHAR(500)"),
        ("options_json", "TEXT"),
    ]
    with engine.begin() as connection:
        for column_name, column_type in pending:
            if column_name in existing_columns:
                continue
            connection.execute(
                text(f"ALTER TABLE export_jobs ADD COLUMN {column_name} {column_type}")
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    Base.metadata.create_all(bind=engine)
    _apply_lightweight_migrations()

    db = SessionLocal()
    try:
        AuthService(db).ensure_default_admin()
        HighlightService.bootstrap_default_mappings(db)
        SettingsService(db).ensure_defaults()
    finally:
        db.close()

    ensure_runtime_dirs()

    yield

    # 关闭时的清理工作
    pass

# 创建FastAPI应用
ensure_runtime_dirs()

app = FastAPI(
    title="CodeWright API",
    description="代码版权工匠 - 软件著作权申请材料准备平台",
    version=APP_VERSION,
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/exports", StaticFiles(directory=str(EXPORTS_DIR)), name="exports")

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/v1/users", tags=["用户"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["项目"])
app.include_router(files.router, prefix="/api/v1/files", tags=["文件"])
app.include_router(exports.router, prefix="/api/v1/exports", tags=["导出"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["管理"])
app.include_router(settings.router, prefix="/api/v1/settings", tags=["设置"])

@app.get("/")
async def root():
    """根路径"""
    return {"message": f"CodeWright API v{APP_VERSION}"}


async def _health_payload() -> dict[str, str]:
    return {"status": "healthy", "version": APP_VERSION}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """健康检查"""
    return await _health_payload()


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    """与运维约定的别名健康检查端点。"""
    return await _health_payload()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
