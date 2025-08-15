"""
CodeWright 后端主应用
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from app.database import engine, Base
from app.routers import auth, users, projects, files, exports, admin, settings, manual
from app.routers import export_history as export_history_router

# 导入所有模型以确保表被创建
from app.models import user, project, file, manual_section, highlight_mapping, project_settings
from app.models import export_history as export_history_model

# 加载环境变量
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时创建数据库表
    Base.metadata.create_all(bind=engine)

    # 创建必要的目录
    os.makedirs("../upload", exist_ok=True)
    os.makedirs("../templates", exist_ok=True)
    os.makedirs("../exports", exist_ok=True)

    # 初始化数据库数据
    from app.services.init_service import InitService
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        init_service = InitService(db)
        init_service.init_all()
    finally:
        db.close()

    yield

    # 关闭时的清理工作
    pass

# 创建FastAPI应用
app = FastAPI(
    title="CodeWright API",
    description="代码版权工匠 - 软件著作权申请材料准备平台",
    version="0.0.2",
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
app.mount("/uploads", StaticFiles(directory="../upload"), name="uploads")
app.mount("/exports", StaticFiles(directory="../exports"), name="exports")

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/v1/users", tags=["用户"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["项目"])
app.include_router(files.router, prefix="/api/v1/files", tags=["文件"])
app.include_router(exports.router, prefix="/api/v1/exports", tags=["导出"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["管理"])
app.include_router(settings.router, prefix="/api/v1/settings", tags=["设置"])
app.include_router(manual.router, prefix="/api/v1/manual", tags=["操作文档"])
app.include_router(export_history_router.router, prefix="/api/v1", tags=["导出历史"])

@app.get("/")
async def root():
    """根路径"""
    return {"message": "CodeWright API v0.0.2"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "version": "0.0.2"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
