### **项目开发指南：CodeWright（代码版权工匠） V 1.0.0**

-----

#### **1. 项目概述**

CodeWright（代码版权工匠）是一个面向中国大陆用户、仅提供中文界面的在线 Web 平台，聚焦软件著作权申请材料的规范化准备。平台通过自动排版、语法高亮、模板化文档与 PDF 导出等能力，显著降低材料准备门槛并提升专业度，采用现代化的前后端分离架构，便于高效开发、部署与维护。

  * **核心价值**：节省时间，降低软著材料准备门槛，提升材料专业性与一致性。
  * **目标用户**：个人开发者、学生、及中小型研发团队（中国大陆）。
  * **语言与界面**：仅提供中文界面与中文导出内容（无多语言切换）。
  * **设计风格**：极简白色调 + 日式风格；简洁、清晰、用户友好。

-----

#### **2. 功能需求**

##### **2.1 用户故事 (User Stories)**

**用户角色：**

  * **普通用户 (User)**
  * **管理员 (Admin)**

**史诗：用户认证 (Authentication)**

  * **As a** 新用户, **I want to** 注册一个新账号, **so that** 我可以使用平台的功能。
  * **As a** 注册用户, **I want to** 登录我的账号, **so that** 我可以访问我的项目和文件。
  * **As a** 用户, **I want to** 登出我的账号, **so that** 保护我的账户安全。

**史诗：代码文件构建**

  * **As a** 登录用户, **I want to** 创建一个新的代码文件构建项目。
  * **As a** 登录用户, **I want to** 上传多个源代码文件（如 `.py`, `.java`, `.js` 等）。
  * **As a** 登录用户, **I want to** 看到系统根据文件后缀自动匹配语法高亮类型。
  * **As a** 登录用户, **I want to** 能手动修改某个文件的高亮类型，以防自动识别错误或对于无后缀文件进行指定。
  * **As a** 登录用户, **I want to** 拖动上传的文件列表来调整它们在最终文档中的顺序。
  * **As a** 登录用户, **I want to** 勾选一些格式化选项，如“代码行数跨文件连续编号”、“代码文件名加粗显示”。
  * **As a** 登录用户, **I want to** 将最终编辑好的代码文件导出为一个单独的PDF文档。
  * **As a** 登录用户, **I want to** 在导出前以 HTML 预览效果，以便检查排版与样式。
  * **As a** 登录用户, **I want to** 在提交导出任务后查看任务状态与进度，并在完成后获取下载链接。
  * **As a** 登录用户, **I want to** 在列表页看到我所有未完成和已完成的代码文件项目，并可以继续编辑或重新下载。

**史诗：操作文档构建**

  * **As a** 登录用户, **I want to** 创建一个新的操作文档构建项目。
  * **As a** 登录用户, **I want to** 从一个下拉列表中选择一个操作文档模板（由管理员上传）。
  * **As a** 登录用户, **I want to** 在文档的首页信息区填写软件名称、版本号、开发者等信息。
  * **As a** 登录用户, **I want to** 选择是否启用全局变量替换功能（如正文自动引用软件名称）。
  * **As a** 登录用户, **I want to** 添加一个个的图文章节，每个章节包含一张截图和一段描述文字。
  * **As a** 登录用户, **I want to** 使用Markdown或HTML语法来编写描述文字，以实现富文本格式。
  * **As a** 登录用户, **I want to** 将最终编辑好的操作文档导出为一个单独的PDF文档。
  * **As a** 登录用户, **I want to** 在导出前以 HTML 预览文档样式与排版，并修正问题。
  * **As a** 登录用户, **I want to** 在提交导出任务后查看任务状态与进度，并在完成后获取下载链接。
  * **As a** 登录用户, **I want to** 在列表页看到我所有未完成和已完成的操作文档项目，并可以继续编辑或重新下载。

**史诗：管理功能 (Admin)**

  * **As an** 管理员, **I want** 系统提供固定的初始管理员账户（用户名：admin，密码：admin123），该账号不可被删除。
  * **As an** 管理员, **I want to** 访问一个独立的“系统设置”页面。
  * **As an** 管理员, **I want to** 管理所有用户账号（如查看列表、禁用/启用账号）。
  * **As an** 管理员, **I want to** 发布和管理系统公告（支持草稿/发布/下线状态）。
  * **As an** 管理员, **I want to** 上传和管理操作文档的 `.template` 模板文件，并管理模板版本与发布状态（draft/published）。
  * **As an** 管理员, **I want to** 在系统设置中配置PDF的全局样式（如字体、字号、页眉页脚格式等）。
  * **As an** 管理员, **I want to** 编辑用于代码高亮的“后缀名-语言”匹配规则的配置文件。

-----

#### **3. 非功能需求**

  * **性能**：2000 行代码导出目标 < 10 秒（同步渲染基准）；异步模式下导出进入队列可见进度；单文件 ≤ 10MB、项目总量 ≤ 100MB（可配置）；导出阶段对图片按页宽自适应压缩。
  * **可用性**：在线率 99.9%；数据库、模板与上传目录均持久化；建议每日自动备份（数据库与上传目录）。
  * **安全性**：密码加密存储（bcrypt/Argon2）；前后端采用 JWT 鉴权；上传类型与大小校验；Markdown/HTML 清洗以防 XSS；接口鉴权中间件防止未授权访问。
  * **可伸缩性**：对象存储/文件系统可插拔；导出任务采用异步队列（Redis）便于横向扩展；前后端无状态便于容器弹性伸缩。
  * **可维护性**：统一编码规范与 CI 流水线；充分注释与文档；前后端分离利于独立演进。
  * **浏览器支持**：Chrome/Edge 最近两个大版本。

-----

#### **4. 技术选型**

  * **前端**：`Vue 3` + `TypeScript`（Composition API）, 构建使用 `Vite`，状态管理 `Pinia`，路由 `Vue Router`，UI 组件库采用 `Element Plus`（注意：Element UI 不兼容 Vue 3，必须使用 Element Plus）。预览链路：`markdown-it`（解析）+ `DOMPurify`（清洗）+ `highlight.js`（仅前端预览高亮）。
  * **后端**：`FastAPI`（Python 3.10+ 推荐）+ `Pydantic` v2；密码哈希 `bcrypt`/`Argon2`；鉴权 `JWT`。导出采用异步队列（`Redis` + `RQ`/`Celery`），任务可查询进度与结果。
  * **数据库**：`SQLite`（`SQLAlchemy` ORM）。
  * **PDF 生成**：
      * **代码高亮**：`Pygments`（代码→HTML，支持行号与样式）。
      * **HTML→PDF**：`WeasyPrint`（支持页眉页脚与样式定制），容器内置中文字体（思源黑体/宋体）。
  * **部署**：`Docker` & `Docker Compose`；生产推荐 `Nginx` 反向代理；引入 `Redis` 服务用于异步队列。

-----

#### **5. 系统架构设计**

采用经典的前后端分离架构。

  * **前端 (Vue3)**：负责所有用户界面的渲染和交互逻辑。通过HTTP请求与后端API进行数据交换。
  * **后端 (FastAPI)**：无状态的 API 服务。负责业务逻辑、用户认证、数据库操作、文件存储、异步导出队列（基于 Redis 的 RQ/Celery），以及调用 PDF 生成库创建最终文档。
  * **Nginx (反向代理)**：可选，但在生产环境中推荐。用于代理前端静态文件和后端API请求，便于配置HTTPS和负载均衡。

**高层架构图 (概念描述):**

```
+----------------+      (HTTPS)       +----------------------+      (API Calls)       +-----------------+
|   用户浏览器    | <----------------> |   Nginx (可选)       | <------------------>   |  FastAPI 后端    |
| (Vue.js App)   |                    |                      |                        |  (Python)       |
+----------------+                    +----------------------+                        +-------+---------+
                                                |                                        |      |
                                        (Serve Static Files)                             |      | (SQL)
                                                                                         |      v
                                                                             +-----------+-----------+
                                                                             |      SQLite 数据库     |
                                                                             +-----------------------+
                                                                                         |
                                                                                         | (File I/O)
                                                                                         v
                                                                             +-----------------------+
                                                                             |   服务器文件系统      |
                                                                             |   (./upload/ 目录)    |
                                                                             +-----------------------+
```

-----

#### **6. 数据模型设计 (SQLite)**

**User Table**

  * `id` (Integer, Primary Key, Auto Increment)
  * `username` (String, Unique, Not Null)
  * `password_hash` (String, Not Null)
  * `role` (String, 'user' or 'admin', Not Null, Default 'user')
  * `created_at` (DateTime)

**UploadedFile Table (用于代码文件和操作文档中的图片)**

  * `id` (Integer, Primary Key, Auto Increment)
  * `original_filename` (String, Not Null)
  * `storage_path` (String, Not Null, e.g., "upload/uuid-goes-here.py")
  * `uploader_id` (Integer, Foreign Key to User.id)
  * `created_at` (DateTime)

**Project Table (用于关联一次完整的文档构建任务)**

  * `id` (Integer, Primary Key, Auto Increment)
  * `project_name` (String, Not Null)
  * `project_type` (String, 'code' or 'manual', Not Null)
  * `owner_id` (Integer, Foreign Key to User.id)
  * `config_json` (Text, stores project-specific settings like file order, descriptions etc.)
  * `created_at` (DateTime)
  * `updated_at` (DateTime)


**ProjectItem Table (代码项目的文件项顺序与覆盖设置)**

  * `id` (Integer, Primary Key, Auto Increment)
  * `project_id` (Integer, Foreign Key to Project.id)
  * `file_id` (Integer, Foreign Key to UploadedFile.id)
  * `display_name` (String, Nullable)  // 显示名覆盖，默认取文件名
  * `language_override` (String, Nullable)  // 手动指定高亮语言
  * `include_in_export` (Boolean, Default true)
  * `order_index` (Integer, Not Null)

**ManualSection Table (操作文档的章节)**

  * `id` (Integer, Primary Key, Auto Increment)
  * `project_id` (Integer, Foreign Key to Project.id)
  * `title` (String, Not Null)
  * `image_file_id` (Integer, Foreign Key to UploadedFile.id, Nullable)
  * `body_markdown` (Text, Not Null)
  * `order_index` (Integer, Not Null)

**Template Table (模板与版本化)**

  * `id` (Integer, Primary Key, Auto Increment)
  * `name` (String, Not Null)
  * `version` (String, Not Null, e.g., "1.0.0")
  * `description` (String, Nullable)
  * `storage_path` (String, Not Null)
  * `status` (String, 'draft'|'published', Default 'draft')
  * `created_at` (DateTime)
  * `updated_at` (DateTime)

**Announcement Table (公告)**

  * `id` (Integer, Primary Key, Auto Increment)
  * `title` (String, Not Null)
  * `body_markdown` (Text, Not Null)
  * `status` (String, 'draft'|'published'|'archived', Default 'draft')
  * `published_at` (DateTime, Nullable)
  * `created_at` (DateTime)

**Setting Table (系统设置，KV)**

  * `id` (Integer, Primary Key, Auto Increment)
  * `key` (String, Unique, Not Null)
  * `value` (Text, JSON String, Not Null)
  * `updated_at` (DateTime)

**HighlightMapping Table (后缀-语言映射)**

  * `id` (Integer, Primary Key, Auto Increment)
  * `suffix` (String, Not Null)  // 例如 .py, .java
  * `language` (String, Not Null) // Pygments/前端预览用的语言标识
  * `enabled` (Boolean, Default true)
  * `updated_at` (DateTime)

**ExportHistory Table (导出历史记录)**

  * `id` (Integer, Primary Key, Auto Increment)
  * `project_id` (Integer, Foreign Key to Project.id)
  * `exporter` (String, 'code'|'manual', Not Null)
  * `status` (String, 'success'|'failed', Not Null)
  * `duration_ms` (Integer, Nullable)
  * `file_path` (String, Nullable)
  * `created_at` (DateTime)

**ExportJob Table (导出任务，异步队列)**

  * `id` (Integer, Primary Key, Auto Increment)
  * `project_id` (Integer, Foreign Key to Project.id)
  * `job_id` (String, Unique, Not Null) // 队列中的任务 ID
  * `status` (String, 'queued'|'processing'|'success'|'failed')
  * `progress` (Integer, 0-100)
  * `result_file_path` (String, Nullable)
  * `error_message` (String, Nullable)
  * `created_at` (DateTime)
  * `updated_at` (DateTime)

-----

#### **7. 关键接口定义（/api/v1）**

- 统一响应：
  - 成功：`{ code: 0, data: any, message: 'ok' }`
  - 失败：`{ code: <错误码>, message: <中文信息>, detail?: any }`
- 认证：Authorization: `Bearer <token>`

- 认证与用户
  * `POST /api/v1/users/register`：用户注册
  * `POST /api/v1/auth/token`：登录获取 JWT
  * `GET /api/v1/users/me`：当前用户信息

- 项目与上传
  * `POST /api/v1/projects`：创建项目（body：`{project_name, project_type: 'code'|'manual'}`）
  * `GET /api/v1/projects?type=&page=&page_size=`：项目列表
  * `PUT /api/v1/projects/{id}`：更新项目配置（如文件顺序、描述）
  * `POST /api/v1/projects/{id}/upload`：上传文件（multipart：file；限制类型与大小）
  * `GET /api/v1/projects/{id}/preview?format=html`：导出前预览（HTML）

- 导出与队列
  * `POST /api/v1/projects/{id}/export`：提交导出任务（返回 `job_id`）
  * `GET /api/v1/exports/{job_id}`：查询任务状态与进度
  * `GET /api/v1/exports/{job_id}/download`：下载生成的 PDF

- 管理（Admin）
  * `GET /api/v1/admin/users`：用户列表
  * `POST /api/v1/admin/templates`：上传模板（含元数据与文件）
  * `PUT /api/v1/admin/settings`：更新系统设置（PDF 样式、中文字体、上传限制等）
  * `GET /api/v1/settings/highlight-mapping`：获取后缀-语言映射
  * `PUT /api/v1/settings/highlight-mapping`：批量更新映射

- 错误码建议：
  * 0 成功；1001 参数错误；1002 认证失败；1003 权限不足；
  * 2001 非法文件（类型/大小）；3001 导出失败；4001 资源不存在；
  * 5001 服务器内部错误

-----

#### **8. 部署与运维建议**

1.  **Docker 化**：前端、后端分别编写 `Dockerfile`；镜像内置中文字体（思源黑体/宋体）与 WeasyPrint 依赖。
2.  **Docker Compose**：统一编排前端、后端、Redis、Nginx；暴露 API 与前端静态站点；为 Redis 设置持久化卷。
3.  **数据持久化**：将 SQLite 数据库文件与 `upload/`、`templates/`、`exports/` 目录通过 `volumes` 挂载，避免数据丢失。
4.  **环境变量**：`JWT_SECRET`、`TOKEN_EXPIRE_MINUTES`、`MAX_UPLOAD_SIZE_MB`、`ALLOWED_EXTENSIONS`、`PDF_DEFAULT_FONT_FAMILY` 等。
5.  **备份策略**：每日自动备份数据库与上传/模板/导出目录；保留最近 7 天快照。
6.  **Nginx**：反向代理与 HTTPS 终止；限流与基本安全头；静态资源缓存策略。
7.  **日志与监控**：Nginx 访问日志；后端结构化日志（JSON）；/healthz 健康检查；错误告警（可选 Sentry）。

-----

#### **9. 版本号规范（V A.B.C）**

- A（大版本）：里程碑式功能发布，包含重大能力或破坏性变更，由开发者评定。
- B（中版本）：每新增一个新功能时迭代，范围 0–7，由开发者评定。
- C（小版本）：每次发布时递增，无上限，由开发者评定。
- 标记示例：`V 1.3.12`
- 发布流程：

#### **10. 项目路线图**

- 当前版本：设定为 `V 0.0.1`（初始开发版本）。

- 到 `V 1.0.0` 里程碑前的开发约束与简化策略：
  1) 不构建 Docker 容器化部署，采用本地开发环境以降低复杂度（FastAPI 本地运行 + 前端本地 Vite 开发服务器）。
  2) 不部署在线演示环境，聚焦核心功能开发与本地验证。
  3) 采用极简设计语言与基础组件用法，避免深度 UI 设计/定制化工作量。
  4) 不对外暴露网络端口，所有测试在本地 Python 环境完成（含导出队列本地 Redis 实例）。
  5) 优先级：认证 → 项目/上传 → 预览 → 异步导出队列（提交/查询/下载）→ 模板基础 → 管理基础（公告/映射/设置）。

- `V 1.0.0` 阶段重点：
  - 基础功能闭环：用户注册登录、项目创建与管理、文件上传与排序、HTML 预览、异步导出 PDF（含进度查询与下载）、基础模板与公告、系统设置（中文字体/高亮映射）。
  - 基线性能：2000 行导出 < 10s（在本地环境）；文件与类型限制生效；Markdown/HTML 清洗安全链路打通。
  - 文档：完善开发指南、API 约定与验收用例，建立最小可行测试集（pytest/vitest/Playwright）。

- 到 `V 2.0.0` 前的功能优先级策略：
  1) 持续改进稳定性与功能性（导出鲁棒性、错误恢复、队列可观测性）。
  2) 便捷性提升（批量操作、导出历史、模板管理体验）。
  3) UI 深度优化延后（保留极简设计语言）。
  4) 仍不对外暴露网络端口，继续基于本地 Python 环境进行测试与验证。

- `V 2.0.0` 阶段重点：
  - 系统稳定性、功能性与便捷性全面提升：更完善的错误码与重试、导出历史可检索、模板版本化管理体验优化、后台操作审计（可选）。
  - 视情况引入容器化与演示环境筹备（不在本节强制要求，随实际进展评估）。

  1) main 分支保持稳定可发布；feature 分支合并需通过 CI（lint/test/build）。
  2) 更新 `CHANGELOG.md`，按 A.B.C 记录新增/修复/变更。
  3) 打 Git Tag 并产出发布物（前端构建包、后端镜像）。

#### **11. UI 设计规范（极简白色调 + 日式风格）**

- 颜色：
  - 文本主色：#111；背景：#FFFFFF/#FAFAFA；灰阶：#EDEDED/#D9D9D9/#BFBFBF；强调：#5C7CFA 或 #2F54EB（谨慎使用）。
- 字体：
  - 界面：Noto Sans SC / 思源黑体（优先），回退 PingFang SC、Microsoft YaHei。
  - PDF：思源黑体（正文）、思源宋体（手册/长文）。
- 间距与布局：8px 基准栅格；充分留白；统一圆角（如 6px）；极轻或无阴影。
- 组件：Element Plus；二次封装遵循最小化与对齐一致性；按钮动词前置，中文语境优化。

#### **12. 开发流程与质量保障**

- 分支策略：main（稳定）、feature/feat-xxx、fix/bug-xxx、chore/xxx。
- 提交规范：Conventional Commits（feat/fix/docs/style/refactor/test/chore）。
- 代码规范：
  - 前端：TypeScript、ESLint + Prettier、严格类型；Vitest 单测。
  - 后端：Black + isort + Ruff；pytest；可选 mypy。
- 测试：
  - 单元（前端/后端）、接口（pytest+httpx）、端到端（Playwright：注册/登录、上传、排序、预览、导出）。
- CI（可选后续接入）：lint → test → build → 镜像 → 扫描 → 部署。

#### **13. PDF 渲染与安全管线**

- 前端预览：markdown-it 解析 → DOMPurify 清洗 → highlight.js 仅用于浏览器侧高亮。
- 后端导出：Pygments（代码→HTML，行号/连续编号可选）→ WeasyPrint（HTML+CSS→PDF，中文字体内置）。
- 安全：上传白名单（.py .java .js .ts .md .png .jpg .jpeg .gif .txt .c .cpp）；大小限制；拒绝可执行二进制；清洗 Markdown/HTML 防 XSS。
- 性能：目标 2000 行 < 10s；图片导出按页宽压缩；异步队列可横向扩展。

#### **14. 错误码与响应约定**

- 返回结构统一：成功 `{ code:0, data, message:'ok' }`；失败 `{ code, message, detail? }`。
- 错误码：0 成功；1001 参数错误；1002 认证失败；1003 权限不足；2001 非法文件；3001 导出失败；4001 资源不存在；5001 服务器内部错误。
- 前端拦截：401→跳登录；403→提示权限不足；其余→Toast+错误页。

#### **15. 关键用例验收标准**

- 代码构建导出：顺序正确；连续行号选项生效；中文字体渲染正确；2000 行在 10s 内；下载文件可复核。
- 手册构建导出：目录层级正确；章节图文匹配；Markdown 标题与段落渲染正确；样式与全局设置一致。
- 管理：首个注册用户自动为管理员且不可删除；模板发布后不可直接覆盖（需新版本）。

#### **16. 技术问题解决记录**

**Element Plus 导入问题修复（2025-08-13）**
- **问题**：页面报错 `Failed to resolve import "element-plus/es"`，导致除首页和登录页外的所有页面无法加载
- **原因**：`unplugin-vue-components` 的 `ElementPlusResolver` 自动导入配置有问题
- **解决方案**：
  1. 在 `main.ts` 中手动全量导入 Element Plus：`import ElementPlus from 'element-plus'` 和 `app.use(ElementPlus)`
  2. 移除 Vite 配置中的 `ElementPlusResolver` 自动导入配置
  3. 保留 CSS 导入：`import 'element-plus/dist/index.css'`
- **注意**：Element UI 不兼容 Vue 3，必须使用 Element Plus

**登录跳转问题修复（2025-08-13）**
- **问题**：登录成功后不自动跳转到 dashboard 页面
- **原因**：
  1. `auth.ts` 中缺少 `readonly` 导入，导致状态管理异常
  2. `isAuthenticated` 计算属性同时检查 `token` 和 `user`，但 `getCurrentUser()` 是异步的
- **解决方案**：
  1. 添加 `readonly` 导入：`import { ref, computed, readonly } from 'vue'`
  2. 修改 `isAuthenticated` 逻辑为仅检查 `token`：`computed(() => !!token.value)`
- **验证**：登录后能正确跳转到 dashboard，所有需要认证的页面都能正常访问
