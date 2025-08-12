# CodeWright（代码版权工匠）

CodeWright 是一个面向中国大陆用户的在线 Web 平台，专注于软件著作权申请材料的规范化准备。通过自动排版、语法高亮、模板化文档与 PDF 导出等能力，显著降低材料准备门槛并提升专业度。

## 项目概述

- **核心价值**：节省时间，降低软著材料准备门槛，提升材料专业性与一致性
- **目标用户**：个人开发者、学生、及中小型研发团队（中国大陆）
- **语言与界面**：仅提供中文界面与中文导出内容
- **设计风格**：极简白色调 + 日式风格；简洁、清晰、用户友好

## 技术栈

### 前端
- Vue 3 + TypeScript (Composition API)
- Vite (构建工具)
- Pinia (状态管理)
- Vue Router (路由)
- Element Plus (UI组件库)
- markdown-it + DOMPurify + highlight.js (预览链路)

### 后端
- FastAPI (Python 3.10+)
- Pydantic v2
- SQLAlchemy ORM
- SQLite 数据库
- bcrypt/Argon2 (密码哈希)
- JWT (认证)
- Redis + RQ/Celery (异步队列)

### PDF 生成
- Pygments (代码高亮)
- WeasyPrint (HTML→PDF)
- 内置中文字体（思源黑体/宋体）

## 项目结构

```
CodeWright/
├── frontend/          # Vue.js 前端项目
├── backend/           # FastAPI 后端项目
├── .test/            # 测试文件目录
├── .docs/            # 项目文档目录
├── upload/           # 文件上传目录
├── templates/        # 模板文件目录
├── exports/          # 导出文件目录
├── DEVELOP_PLAN.md   # 开发计划文档
└── README.md         # 项目说明文档
```

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 16+
- Redis (用于异步队列)

### 后端启动
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 前端启动
```bash
cd frontend
npm install
npm run dev
```

### Redis 启动
```bash
redis-server
```

## 开发状态

当前版本：V 0.0.1（初始开发版本）

## 功能特性

### 用户功能
- 用户注册/登录/登出
- 代码文件构建项目管理
- 操作文档构建项目管理
- 文件上传与排序
- HTML 预览
- PDF 导出（异步队列）
- 导出进度查询与下载

### 管理员功能
- 用户管理
- 模板管理
- 系统设置
- 公告管理
- 高亮映射配置

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request。

## 联系方式

如有问题，请通过 Issue 联系我们。
