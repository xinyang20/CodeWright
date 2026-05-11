# 更新日志

本仓库遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范，时间格式为 `YYYY-MM-DD`。

## [0.1.1] - 2026-05-11

### 新增
- 代码项目导出 PDF 现在真实生效字体大小、文件名加粗与双列布局选项 (`pdf_service`)。
- LaTeX 编译失败时自动留存 `.log` 至 `runtime/exports/logs/`，前端"查看 LaTeX 日志"按钮可下载。
- 异步导出任务支持重试 (`POST /api/v1/exports/{job_id}/retry`) 与按状态/时间过滤的历史检索。
- 管理员后台新增"模板复制版本"、"高亮映射删除"、公告 Markdown 编辑弹窗、用户列表分页大小切换。
- 仪表盘公告渲染 Markdown，操作文档章节正文具备实时富文本预览。
- 项目列表支持名称关键字搜索与多种排序，列表内点击项目改用 SPA 路由跳转。
- 操作文档导出图片自动按页宽压缩到 1600px。
- 错误码集中维护：`1001/1003/2001/3001/4001/5001` 在 routers 层全面落地。

### 变更
- 删除遗留的 `POST /api/v1/exports/projects/{project_id}/pdf` 同步导出接口，统一使用 `/projects/{id}/export` 等新链路。
- `HighlightService` 默认映射只在应用启动一次性写入，避免每个请求都触发 `commit`。
- `add_file_to_project` 的体积统计改为聚合查询，避免 N+1。
- 后端版本号读取自 `pyproject.toml` 或 `CODEWRIGHT_VERSION`，不再硬编码。

### 修复
- `HtmlPreview.vue` 使用 `renderToken` 隔离重复触发的预览请求，连续刷新不再错位。
- 路由守卫在 `getCurrentUser()` 失败时清除 token 并跳转登录，刷新管理员页面不再误跳仪表盘。
- 修正 `_options_for_project` 中 manual 字段会污染 code 项目导出选项的问题。

### 文档
- 同步 `README.md` 与 `DEVELOP_PLAN.md`：PDF 渲染从 WeasyPrint 切换为 LaTeX，并补全 `/healthz` 与模板变量说明。
- 新增 `CHANGELOG.md` 记录后续版本演进。

## [0.0.1] - 2026-04-01

- 项目首版：用户认证、代码 / 文档项目管理、HTML & PDF 预览、PDF 同步与异步导出、管理员控制台。
