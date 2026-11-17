# FastapiAdmin — AI 协作说明

FastAPI + Vue3 全栈后台底座（RBAC、代码生成、Web / H5 / 小程序三端）。Monorepo：`backend/`（FastAPI + SQLAlchemy + Alembic + Redis，uv）、`frontend/web/`（Vue3 + Vite + TS + Element Plus + Tailwind4 + Pinia，pnpm，Node ≥ 20）、`frontend/app/`（uni-app）、`frontend/docs/`（VitePress）、`docker/`（部署）。

## 改代码之前

按顺序读，别跳：

1. **[`LESSONS.md`](LESSONS.md)** — 近期踩过的坑。**修改代码前阅读相关条目**，再动手。
2. **[`docs/CODE-STANDARDS.md`](docs/CODE-STANDARDS.md)** — 什么算「做完了」、提交信息、测试数据规范、复盘节奏。
3. **[`docs/DEV-GUIDE.md`](docs/DEV-GUIDE.md)** — 工程地图、前后端约定、新增功能流程、已验证契约。写代码/建模块/排查前读。
4. 改 Web 界面 → 先读 [`docs/UI-ENGINEERING-SPEC.md`](docs/UI-ENGINEERING-SPEC.md)（工程契约，冲突时以它为准）与 [`docs/DESIGN-SPEC.md`](docs/DESIGN-SPEC.md)（品牌与视觉）。
5. 部署、备份、凭据、巡检 → [`docs/DEPLOY-OPS.md`](docs/DEPLOY-OPS.md)。
6. 改测试 / 看覆盖基线 → [`docs/COVERAGE-PLAN.md`](docs/COVERAGE-PLAN.md)。
7. 改小程序 UI → `frontend/app/.agents/skills/wot-ui-*`。

## 构建与测试

后端（`cd backend`）：

- `uv sync` — 安装依赖
- `uv run main.py run --env=dev` — 启动（默认 `http://localhost:8001`，`/docs`；首次启动自动迁移并导入 `sql/*.json` 种子数据）
- `uv run main.py revision -m "说明"` / `uv run main.py upgrade --env=dev` — 生成 / 应用 Alembic 迁移
> 默认库为 PostgreSQL，但驱动不随 `uv sync` 安装：使用 postgres 需手动执行 `uv sync --extra postgres`（MySQL 用 `--extra mysql`，全部用 `--extra all-db`）。

- `uv run pytest -q` — 全部测试；`uv run pytest path::case` 可按用例筛选
- `uv run ruff check` — 后端 lint

前端 web（`cd frontend/web`）：

- `pnpm i` · `pnpm dev`（端口 5180，以输出为准）
- `pnpm ts:check`（改 TS/Vue 必跑）· `pnpm lint` · `pnpm test` · `pnpm build`

测试环境：后端测试默认用临时 SQLite，与开发库隔离；涉及迁移或 PG 特有语义时设 `TEST_DB_TYPE=postgres` 并配 `TEST_DB_*`（默认库 `fastapiadmin_test` 需事先创建）（见 `backend/tests/conftest.py`）。

## 硬性规矩

- **凭据**：未经当次明确确认，不得改服务器口令与 SSH 认证方式，不得轮换任何凭据（`SECRET_KEY`、`DATA_ENCRYPTION_KEY`、数据库/Redis 口令、第三方 Key）。变更时同一条消息写清：改了什么、旧凭据何时失效、新凭据如何获得、回滚办法。口令、私钥不进仓库、文档、提交信息。
- **不可逆动作**：部署/重建镜像、合并 `master`、`git push`、删除服务器数据、重启服务器、清理历史提交，一律先说明影响并取得当次确认。
- **登录/连接排障顺序**：先实测能否连接 → 再查服务端认证日志 → 再查客户端认证方式/密钥 → 最后才考虑重启。
- **生成物不手改**：`dist/`（`frontend/web/dist`、`docker/nginx/web/dist`、`backend/dist`、`docker/nginx/app/dist`）靠重建同步，规程见 `docs/DEV-GUIDE.md`「前端产物验证」。
- **代码生成后必须重启后端**：动态路由只在启动时发现。
- **范围**：只改本次目标相关的内容；顺手重构另开提交。
- **不改既有状态机/契约**：时间、账号/角色编码、菜单类型等契约见 `docs/DEV-GUIDE.md`，勿回退。

## 约定

- **语言**：中文（文档、注释、提交说明）。
- **格式**：后端 `ruff`；前端 `pnpm lint`；提交走 husky + commitlint（`pnpm commit`），不绕过 hook。
- **依赖**：新增第三方依赖前先说明用途与影响。
- **跨端**：需求涉及 web + 小程序时两套都评估；文档站改动同步 `src/guide/` 与 `src/en/guide/`。
- **日志**：loguru，占位符用 `{}`；500 类问题先看 `backend/logs/fastapiadmin.log`。

## 提交与复盘

提交信息、验证披露、复盘触发条件和错题毕业规则，统一遵循 [`docs/CODE-STANDARDS.md`](docs/CODE-STANDARDS.md)。

## 文档索引

| 文档 | 什么时候读 |
| --- | --- |
| [`LESSONS.md`](LESSONS.md) | **修改代码前阅读相关条目** |
| [`docs/CODE-STANDARDS.md`](docs/CODE-STANDARDS.md) | 提交前、复盘时、写测试时 |
| [`docs/DEV-GUIDE.md`](docs/DEV-GUIDE.md) | 写代码、建模块、排查 KeepAlive/WebSocket/dist 问题 |
| [`docs/UI-ENGINEERING-SPEC.md`](docs/UI-ENGINEERING-SPEC.md) | 改 Web 页面、组件、表单、表格 |
| [`docs/DESIGN-SPEC.md`](docs/DESIGN-SPEC.md) | 涉及品牌、Logo、色彩、字体、文案 |
| [`docs/DEPLOY-OPS.md`](docs/DEPLOY-OPS.md) | 部署、备份、凭据轮换、巡检 |
| [`docs/COVERAGE-PLAN.md`](docs/COVERAGE-PLAN.md) | 覆盖基线与剩余缺口 |
| [`docker/README.md`](docker/README.md) | Docker 部署细节 |
