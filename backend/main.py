"""
CodeWright 后端主应用
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from app.paths import BACKEND_DIR, EXPORTS_DIR, UPLOAD_DIR, ensure_runtime_dirs

# 加载环境变量
load_dotenv(BACKEND_DIR / ".env")

from app.database import engine, Base, SessionLocal
from app.routers import auth, users, projects, files, exports, admin, settings
from app.services.auth_service import AuthService

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时创建数据库表
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        AuthService(db).ensure_default_admin()
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
    version="0.0.1",
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
    return {"message": "CodeWright API v0.0.1"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "version": "0.0.1"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
