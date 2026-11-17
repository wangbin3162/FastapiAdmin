# 开发约定与契约

> 工程地图、前后端约定、已验证契约。命令与红线见 [`AGENTS.md`](../AGENTS.md)；验收见 [`CODE-STANDARDS.md`](./CODE-STANDARDS.md)。
> 本文由原根目录 `SKILL.md` 迁移而来（§1、§3–5、§7–9、§12、§14），章节号沿用原编号（缺号的章节已迁入 `AGENTS.md`、`CODE-STANDARDS.md`、`DEPLOY-OPS.md`）。

## 1. 工程地图

| 目录 | 说明 | 技术栈 |
| --- | --- | --- |
| `backend/` | 后端服务（入口 `main.py`，本地端口见 `app/config/setting.py` 的 SERVER_PORT，通常 8001） | FastAPI + SQLAlchemy + Alembic + Redis + uv |
| `frontend/web/` | 管理后台（pnpm 包，Node >= 20） | Vue3 + Vite + TS + Element Plus + Tailwind4 + Pinia |
| `frontend/app/` | 小程序/移动端 | uni-app（有独立约定，见 `frontend/app/.agents/skills/wot-ui-*`） |
| `frontend/docs/` | 项目文档站（中英双语 `src/guide` 与 `src/en/guide`） | VitePress |
| `docker/` | 部署（backend/mysql/nginx/redis） | docker-compose |
| 根目录 | `README.md`、`CONTRIBUTING.md` | 项目总览、贡献规范与部署说明，做大功能前先读 |

### backend/app 关键位置

| 位置 | 说明 |
| --- | --- |
| `modules/<模块>/<功能>/` | 业务模块：controller/service/crud/model/schema + 模块根 `plugin.toml` |
| `plugin/` | 独立插件目录（如 `plugin/module_example/demo`），与 modules 同构、可插拔 |
| `api/v1/routers.py` | 全部路由的注册处 |
| `core/` | 基建：database、base_crud、base_model、security、permission、dependencies、exceptions、ap_scheduler（定时任务）、sse_manager、middlewares |
| `scripts/initialize.py` | 启动时自动执行迁移并导入 `sql/*.json` 种子数据 |
| `sql/*.json` | 菜单/角色/用户/部门/字典/参数等种子数据 |
| `templates/{python,ts,vue}/` | 代码生成器 jinja2 模板 |
| `tests/` | pytest（conftest 自建临时库并初始化数据） |
| `utils/` | crypto/password/excel/upload/xss 等工具函数 |

### frontend/web/src 关键位置

| 位置 | 说明 |
| --- | --- |
| `api/module_x/` | API 层，与后端模块一一对应 |
| `views/module_x/` | 业务页面；页面私有组件放同目录 `components/` |
| `components/` | 公共组件 FaXxx（forms/tables/charts/modal/display 等）——写页面前先找现成的 |
| `hooks/core/` | 开发套件：useTable、useCrudForm、useCrudDialog、useTableColumns、useAuth、useImportExport、useConfirm |
| `directives/permission/` | `v-hasPerm` 按钮权限指令 |
| `router/` | `routes.ts` 静态壳 + guards/MenuProcessor/RouteRegistry 动态路由管道 |
| `store/modules/` | pinia stores（user/worktab/menu/setting/dict…），持久化用 pinia-plugin-persistedstate |
| `locales/langs/` | i18n 词条（zh.json / en.json） |
| `utils/` | http(request 封装)、auth、storage、navigation、download、sse 等 |


## 3. 后端约定（backend/app）

- 模块结构：`app/modules/<模块>/<功能>/`，固定文件划分
  - `controller.py` 路由层、`service.py` 业务层、`crud.py` 数据层、`model.py` ORM、`schema.py` Pydantic
  - 模块根放 `plugin.toml`（name/title/version/description）
- 路由统一在 `app/api/v1/routers.py` 注册；路由类用 `OperationLogRoute`（自动操作日志）
- 权限：`Security(AuthPermission(["模块:资源:操作"]))`，如 `module_ai:chat:query`
- 响应：`SuccessResponse(data=..., msg=...)` + `response_model=ResponseSchema[T]`；业务错误抛 `CustomException`
- 基建都在 `app/core/`：`base_crud.py`、`base_model.py`、`base_schema.py`、`redis_crud.py`、`dependencies.py`、`exceptions.py`、`logger.py`（loguru，占位符用 `{}`)
- 配置：`app/config/setting.py` + `backend/env/.env`（模板见 `env/.env.example`）
- 改了 model 必须生成并执行 Alembic 迁移；初始菜单/角色等数据在 `backend/sql/*.json`
- 新模块两种放法：常规业务放 `app/modules/`，可插拔/示例性质放 `app/plugin/`（结构相同，都有 `plugin.toml`）
- 代码生成：`backend/templates/{python,ts,vue}/*.jinja2` 配合 generator 模块（后台「代码生成」功能可视化生成）；**生成/修改代码后必须重启后端**——dev reload 只在文件变更时重载，动态路由发现（`app/core/discover.py`）只在启动时执行，不重启新模块不生效且会静默失败

## 4. 前端 web 约定（frontend/web/src）

- API 层：`api/module_x/xxx.ts`，对象字面量方法 + `request`（来自 `@utils`），泛型用全局 `ApiResponse<T>` / `PageResult<T>`；URL 与后端 controller 对齐（如 `/system/dict/type/list`）
- 页面：`views/module_x/...`；页面私有子组件放同目录 `components/` 下，公共组件命名 `FaXxx`
- CRUD 页面优先复用现成套件：列表用 `useTable` + `FaTable` + `FaSearchBar`，弹窗表单用 `useCrudDialog`/`useCrudForm` + `FaDialog`，列定义用 `useTableColumns`，导入导出用 `useImportExport`——参考已有 `views/module_system/` 页面写法，不要手写 ElTable/ElDialog
- 权限控制：按钮级用 `v-hasPerm="'sys:user:add'"`（支持数组）；代码内判断用 `useAuth().hasAuth(...)`；后端标识 `模块:资源:操作` 三段式，前后端保持一致
- i18n：文案用 `$t('key')`，词条加到 `locales/langs/zh.json` 与 `en.json` 两份
- 自动导入：vue API（`ref`/`computed`/`watch`/`onMounted` 等）无需 import；Element Plus 组件模板内直接用；`ElMessage` 等按现有文件习惯可显式 import
- 路由：静态壳路由在 `router/routes.ts`；业务路由来自后端菜单（`guards.ts` → `MenuProcessor` → `RouteRegistry` 动态 addRoute）。新增页面要在「菜单管理」配置 route_path/route_name/component_path/keep_alive
- KeepAlive 与工作栏按「组件名」匹配：`defineOptions({ name })` 必须与菜单的 route_name 一致，否则页面缓存/缓存排除（exclude）会失灵
- 有副作用页面（WebSocket/定时器/全局事件监听）必须实现 `onActivated`/`onDeactivated`：deactivated 时释放资源，activated 时按需恢复。`onUnmounted` 只在缓存被驱逐时触发，不能作为唯一清理点（详见第 7 节）
- 路由视图缓存为**单层**：目录路由不挂组件，`KeepAlive` 只存在于 `layouts/fa-page-content/index.vue` 一处，缓存键是叶子路由 `path`（query 变化不重挂载，改键逻辑见同文件 `routeViewCacheKey`）
- 环境变量：公共 `.env`（`VITE_APP_BASE_API=/api/v1` 请求前缀、`VITE_PORT=5180`）；`.env.development`（`VITE_API_BASE_URL=http://127.0.0.1:8001` 代理目标；AI WebSocket `VITE_APP_WS_ENDPOINT=ws://localhost:8001` 直连）
- WebSocket 鉴权（AI chat）：token 经 `Sec-WebSocket-Protocol` 传 `["access_token", "access_token." + jwt]`，后端在握手阶段 `websocket_authenticate` 校验
- 图标：`FaSvgIcon` + iconify（`ri:` / `ep:` / `line-md:`）；i18n 用 `$t(...)`

## 5. 新增一个业务功能（全栈流程）

1. 后端建模块（参考 `app/modules/system/dict/`；标准 CRUD 表可先用后台「代码生成」可视化产出，再调整）
2. `app/api/v1/routers.py` 注册路由
3. `uv run main.py revision` + `upgrade` 做迁移；菜单/按钮权限写入 sys_menu（后台「菜单管理」配置 route_path/route_name/component_path/keep_alive/按钮权限）
4. 前端新建 `api/module_x/xxx.ts` 与 `views/module_x/` 页面（复用 useTable/FaTable 套件）
5. 前后端权限标识保持一致（`模块:资源:操作`），页面按钮加 `v-hasPerm`
6. 验证：后端 `uv run pytest`；前端 `pnpm ts:check`、`pnpm lint`、`pnpm test`


## 7. KeepAlive 缓存与连接类资源（踩过坑，勿回退）

- KeepAlive 的 `include` 来自 worktab `opened`（`layouts/fa-page-content/index.vue`），`opened` 为空时 include 为 `undefined`——KeepAlive 对 undefined include **不做 prune**，不要以为「标签清了缓存就没了」
- KeepAlive 内部缓存无法从外部直接清空，唯一手段是改变 `include`/`exclude` 触发内部 prune。登出场景由 `worktab.store.ts` 的 `clearAll()` 把待删标签组件名写入 `keepAliveExclude` 驱逐旧实例（下次 `openTab` 的 `removeKeepAliveExclude` 自动移出），改 store 时勿删这段
- WebSocket 守卫必须覆盖握手期：`if (ws && ws.readyState !== WebSocket.CLOSED) return`。只挡 `OPEN` 会在 CONNECTING 期间重入时创建新连接并覆盖旧引用，泄漏的连接照样握手成功并弹提示（AI chat 曾因此登出→登录后出现多条 ws + 多条「连接成功」）
- 主动断开先摘 `onopen/onmessage/onerror/onclose` 回调再 `close()`，避免关闭竞态触发提示或状态回调
- 路由出口 KeepAlive **只能有一层**，且不要给它加 `:max`：动态目录路由的 `component` 必须保持 `undefined`（`MenuProcessor.mapMenuNode` / `RouteTransformer.handleNormalRoute`），靠 vue-router 的 RouterView 深度跳级直达叶子页面。历史上给目录挂过壳组件（`NestedRouterParent`），壳实例会随缓存同时存活多份、同一页面被重复挂载，导致切换菜单时接口重复请求；`:max` 的 LRU 则会在标签仍打开时挤掉最早的页面，切回时同样无谓重挂载。缓存集合只由 `include`/`exclude` 表达
- 排查「重复弹窗/重复连接/重复请求」类 bug 的路径：先 grep 提示文案定位全库唯一来源（N 次弹窗 = N 个实例或 N 次重入）→ 查 KeepAlive include/exclude 计算与登出→登录导航链（登录守卫 404→replace 重定向会叠加竞态窗口）→ 菜单配置查 `backend/sql/sys_menu.json`（确认 route_name 唯一、keep_alive）排除后端

## 8. 已知注意点

- 静态前端托管：`register_frontend`（`app/__init__.py`）检查与挂载必须用同一个 `path_conf.FRONTEND_DIST_DIR`（backend/dist）。曾因检查用 path_conf、挂载硬编码 `frontend/web/dist` 导致 500：`check_dir=False` 时启动不报错，**首次请求才炸**，必须看 loguru 日志（`backend/logs/fastapiadmin.log`）才能定位
- 模板/脚本里不要用 `{% for %}` + `{% set %}` 累计布尔标志：Jinja2 for 块作用域隔离，循环外读到的仍是初值。用过滤器一次性计算，如 `{% set has_x = columns | selectattr('python_type', 'equalto', 'date') | list | length > 0 %}`（代码生成器 schema.py.jinja2 曾因此漏生成 validator import，生成产物 NameError、后端起不来）
- 跨端需求（web + 小程序）要同时评估 `frontend/web` 与 `frontend/app` 两套代码，API 层各自维护
- 小程序侧有自己的 skills（`frontend/app/.agents/skills/`），改小程序 UI 时遵循 wot-ui 约定
- 文档站改动记得中英两份（`src/guide/` 与 `src/en/guide/`）

## 9. 前端产物验证（dist）

**源码已修 ≠ 部署已修。** dist 是生成物、不入库（`.gitignore`），但仓库内存在多份预构建副本并直接被打进部署，改完前端源码必须重建并同步，否则线上仍跑旧行为（AI chat 重复「连接成功」就因此漏判过一轮：源码 `e39a369b` 已修，三份 dist 仍停在修复前）。

**三份产物与各自的服务入口**

| 产物 | 服务入口 |
| --- | --- |
| `frontend/web/dist` | 构建输出（`pnpm build:prod` 的 outDir） |
| `docker/nginx/web/dist` | docker 部署的 `/web`（`nginx.conf` 的 `alias /usr/share/nginx/html/web/dist`） |
| `backend/dist` | 一体化部署时 `app.frontend("/")` 托管（`path_conf.FRONTEND_DIST_DIR`） |

移动端同理：`docker/nginx/app/dist/build/h5`（nginx 的 `/app`）。

**重建 + 同步**

```bash
cd frontend/web && pnpm build:prod          # 输出 frontend/web/dist
cd ../.. && rsync -a --delete frontend/web/dist/ docker/nginx/web/dist/ \
              && rsync -a --delete frontend/web/dist/ backend/dist/
```

必须带 `--delete`：产物文件名带 content hash，不带会把旧 chunk 留在目录里。

**验证要核到产物，不能只看 `src/`**（minify 后函数名/注释会丢，但 `WebSocket.CLOSED` 这类属性访问、以及提示文案字符串会保留）：

```bash
grep -l "ai/chat/ws" docker/nginx/web/dist/js/*.js                    # 定位 chunk
grep -oE '.{0,60}readyState.{0,60}' <chunk> | grep -i websocket       # 核守卫（-oE 重复上限 255）
```

例：旧包 `if (ws?.readyState === WebSocket.OPEN) return;`（`CLOSED` 命中 0 次）；修复后 `if (ws && ws.readyState !== WebSocket.CLOSED) return;`。

**收到「源码没改好」的线上反馈时，第一步先核 dist 产物特征字符串**，再回源码；docker 部署还要重新打镜像/重传 `docker` 目录才算生效。


## 12. 时间、消息与调度契约（已验证，勿回退）

- 数据库统一存 UTC；接口/页面统一按 `settings.TIMEZONE`（默认 `Asia/Shanghai`）展示。
- 时间输出统一走 `app/core/validator.py::to_local_datetime` 或响应编码器；裸 `datetime` 在响应层也要做时区转换。
- 用户导入导出：
  - Excel 导出前必须把 aware datetime 转成 naive（openpyxl 不支持时区）；
  - 导入模板中文性别映射：男→0、女→1、未知→2；
  - 空/损坏 Excel 返回 400，不允许 500。
- SQL 控制台：多语句、未确认写操作、超 200 行、敏感列都有既有约束；不要为了“显示方便”强行给裸 DATETIME 加 8 小时。
- 全局消息：`frontend/web/src/utils/message.ts` 对 success/error 做短时合并；新增页面不要再叠加多条同义提示。
- 调度器：`reconcile_node_jobs` 启动时会刷新已存在 job；改 node.func/trigger 后必须确认旧 job 参数被替换，否则会出现“数据库已改、调度器仍报旧原因”。


## 14. 当前统一契约

- 用户账号：**3–32 位**，字母开头，仅字母/数字/`_ . -`；
- 角色编码：**2–64 位**，字母开头，仅字母/数字/下划线；
- 角色数据权限：1/2/3；状态：0/1；
- 菜单类型：1 目录、2 菜单、3 按钮、4 外链；
- 公告类型：1 通知、2 公告；状态 0/1/2；
- 存储对象 key 不接受 `..`；对象存储绝对路径会被规范化为桶内路径。


## 2. 首次启动要点

- 复制 `backend/env/.env.example` 为 `.env.dev`，必改项：`DATABASE_PASSWORD` / `REDIS_PASSWORD` / `OPENAI_API_KEY`；`DATABASE_TYPE` 默认 postgres，也支持 mysql / sqlite（本地体验用 sqlite 可零配置）。
- 启动时自动执行迁移并导入 `sql/*.json` 种子数据，无需手动建表；dev 环境检测到模型变更还会自动生成并应用迁移。
- 默认账号 `super` / `admin` / `user`，密码均为 `123456`，部署后立即修改。
- 地址：Web `http://localhost:{VITE_PORT}`（`frontend/web/.env` 为 5180）；后端 `http://localhost:8001`，Swagger `/docs`，API 前缀 `/api/v1`。
- 前端代理：vite 把 `VITE_APP_BASE_API` 前缀代理到 `VITE_API_BASE_URL`（`vite.config.ts`），本地无 CORS 问题；AI WebSocket 用 `VITE_APP_WS_ENDPOINT` 直连后端，不走代理。
- 小程序/App H5 调试用 `frontend/app` 内 `pnpm dev:h5`。

## 15. AI 协作流程

1. 先读 `AGENTS.md` 与 `docs/COVERAGE-PLAN.md`，确认现有覆盖和已知缺口；
2. 修改前先查现有组件/套件，避免重复造轮子；
3. 改完执行对应验证，至少「单元/接口 + 类型/构建」两类；
4. 涉及生产写操作、部署、master、凭据时先获得当次明确确认；
5. 不把「页面能打开」当成「功能通过」；写操作要真实提交并清理测试数据；
6. 交付时说明：改了什么、验证了什么、未覆盖什么。
