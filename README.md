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
- highlight.js (HTML 预览源码高亮)

### 后端
- FastAPI (Python 3.12+)
- Pydantic v2
- SQLAlchemy ORM
- SQLite 数据库
- bcrypt (密码哈希)
- JWT (认证)
- markdown-it-py + bleach (手册 Markdown 渲染与清洗)
- 数据库持久化导出任务 + FastAPI 后台任务

### PDF 生成
- Pygments (代码高亮)
- LaTeX→PDF（默认使用 XeLaTeX）
- PyTinyTeX（默认在项目内自动管理 TinyTeX/xelatex，不依赖系统级 TeX 安装）
- 后台 PDF 样式以 LaTeX 导言区、页眉、页脚等配置提交
- 中文字体默认使用 PingFang SC，可在系统设置中调整

## 项目结构

```
CodeWright/
├── frontend/          # Vue.js 前端项目
├── backend/           # FastAPI 后端项目
├── .test/            # 测试文件目录
├── upload/           # 运行时文件上传目录，自动创建，默认不纳入 Git
├── templates/        # 运行时模板目录，自动创建，默认不纳入 Git
├── exports/          # 运行时导出目录，自动创建，默认不纳入 Git
├── .runtime/         # 运行时工具目录，例如项目内 TinyTeX，默认不纳入 Git
├── DEVELOP_PLAN.md   # 开发计划文档
└── README.md         # 项目说明文档
```

## 快速开始

### 环境要求
- Python 3.12+
- Node.js 20.19+
- pnpm 10.x
- uv
- PDF 首次导出需要联网下载项目内 TinyTeX；也可设置 `CODEWRIGHT_TINYTEX_DIR` 指向已有 TinyTeX 目录

### 后端启动
```bash
cd backend
uv sync
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### 前端启动
```bash
cd frontend
pnpm install
pnpm run dev
```

默认从 `http://127.0.0.1:3000/` 访问前端；如果 3000 端口已被占用，以 Vite 终端输出的实际端口为准。

### 健康检查
- `GET /health` 与 `GET /healthz` 返回 `{"status":"healthy","version":"<APP_VERSION>"}`，便于负载均衡或运维探活。
- 版本号读取自 `backend/pyproject.toml`，可通过环境变量 `CODEWRIGHT_VERSION` 临时覆盖。

### 后端测试
```bash
cd backend
uv --cache-dir ../.uv-cache run pytest ../.test
```

### 前端验证
```bash
cd frontend
pnpm run type-check
pnpm run build
```

### 运行时目录

后端会自动创建运行时目录，默认位于项目根目录，且不纳入 Git：

- `upload/`：上传文件
- `templates/`：管理员上传的 HTML 模板
- `exports/`：导出的 PDF 文件
- `.runtime/`：项目内运行工具与下载缓存，例如 TinyTeX/xelatex

可通过环境变量覆盖路径：

- `CODEWRIGHT_UPLOAD_DIR`
- `CODEWRIGHT_TEMPLATES_DIR`
- `CODEWRIGHT_EXPORTS_DIR`
- `CODEWRIGHT_TINYTEX_DIR`
- `CODEWRIGHT_TINYTEX_VARIATION`：TinyTeX 下载变体，默认 `2`
- `CODEWRIGHT_USE_SYSTEM_XELATEX`：默认 `0`，仅显式设置为 `1` 时才允许使用系统 `xelatex`

### 导出任务

导出任务使用 SQLite 中的 `export_jobs` 表持久化状态，并通过 FastAPI `BackgroundTasks` 在后端进程内执行，接口保持提交任务、查询进度、下载结果的完整流程，无需额外启动队列服务。

## 开发状态

当前版本：V 0.1.1（本地开发版本，详见 [CHANGELOG.md](CHANGELOG.md)）

## 模板编写指南

管理员可在"模板管理"中上传 HTML 模板供导出使用，模板默认走前端模板引擎可识别的极简语法：

- 全局变量替换：`{{project_name}} / {{generated_time}} / {{file_count}} / {{software_name}} / {{version}} / {{developer}}`。
- 循环与索引：

  ```html
  {% for file in files %}
    <h2>{{loop.index}}. {{file.filename}}</h2>
    <pre>{{file.highlighted_content|safe}}</pre>
  {% endfor %}
  ```

- 默认管理员可在后台"模板管理"中点击"复制版本"，基于现有模板生成草稿后再做增量调整。
- 章节正文 Markdown 经 `markdown-it + DOMPurify` 渲染，前端预览与 LaTeX 导出共享同一全局变量。

## 功能特性

### 用户功能
- 用户注册/登录/登出
- 代码文件构建项目管理
- 操作文档构建项目管理
- 文件上传与排序
- 文件类型与大小限制
- HTML 预览
- PDF 导出（任务提交、状态查询、完成下载）
- 导出进度查询与下载
- 代码高亮语言识别与手动覆盖
- 代码导出格式选项（行号、连续行号、语法高亮、换行、布局、字号）
- 操作文档章节、截图、Markdown 内容
- 操作文档模板选择、软件名称/版本/开发者元信息、全局变量替换

### 管理员功能
- 启动时自动确保默认管理员账号 `admin/admin123`
- 用户管理
- 模板管理（HTML 模板上传、版本约束、草稿/发布状态）
- 系统设置（PDF 样式、上传限制、手册默认行为）
- 公告管理
- 高亮映射配置

## 当前范围说明

本地开发版本不包含 Docker、Nginx、备份、监控、CI、Playwright/Vitest 自动化；当前自动化验证以 `.test/` 中的后端 pytest 和前端 `type-check`/`build` 为准。

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request。

## 联系方式

如有问题，请通过 Issue 联系我们。
