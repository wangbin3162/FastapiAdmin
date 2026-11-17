## 📦 工程结构

```
FastapiAdmin/
├─ backend/        # FastAPI 后端（Pydantic 2 + SQLAlchemy + Alembic），入口 main.py
│   ├─ app/        # modules/ 业务模块、plugin/ 插件、core/ 基建、api/v1/ 路由
│   ├─ env/        # 环境配置（.env.example → .env.dev / .env.prod）
│   ├─ sql/        # 初始化种子数据（JSON）
│   └─ tests/      # pytest
├─ frontend/
│   ├─ web/        # Vue3 管理后台（Element Plus + TypeScript）
│   ├─ app/        # uni-app 移动端（H5 / 小程序 / App）
│   └─ docs/       # VitePress 文档站
├─ docker/         # Docker Compose 部署（Nginx + SSL）
├─ docs/           # 开发约定、UI 规范、部署运维
├─ deploy.sh       # 部署脚本
└─ AGENTS.md       # AI 协作入口
```

## 🧱 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | FastAPI · Pydantic 2 · SQLAlchemy 2 · Alembic · Redis · uv |
| 数据库 | PostgreSQL（默认）· MySQL · SQLite |
| Web | Vue 3 · TypeScript · Vite · Element Plus · Pinia · Tailwind 4 |
| 移动端 | uni-app · Vue 3 · Wot Design Uni |
| AI | Agno |
| 部署 | Docker Compose · Nginx |

环境要求：Python ≥ 3.12、[uv](https://docs.astral.sh/uv/)、Node.js ≥ 20 + pnpm、PostgreSQL 14+（或 MySQL 8.0+）、Redis 7。

## 🚀 启动

### 后端

```bash
cd backend
cp env/.env.example env/.env.dev       # 修改 DATABASE_PASSWORD / REDIS_PASSWORD / SECRET_KEY 等
uv sync
uv run main.py run --env=dev           # 首次启动自动迁移并导入种子数据
```

> 如果使用 postgres（默认库），需手动安装驱动：`uv sync --extra postgres`（MySQL 用 `--extra mysql`，全部驱动用 `--extra all-db`）。

默认 `DATABASE_TYPE=postgres`（`localhost:5432`，库 `fastapiadmin` 需事先创建）。服务地址 `http://localhost:8001`，接口文档 `/docs`。

```bash
uv run main.py revision -m "说明"      # 生成迁移
uv run main.py upgrade --env=dev       # 应用迁移
uv run pytest -q                       # 测试
uv run ruff check                      # 代码检查
```

### 前端

```bash
cd frontend/web
cp .env.development.example .env.development
pnpm install && pnpm dev               # http://localhost:5180
```

浏览器打开后用 `admin` / `123456` 登录（部署后请立即修改）。

### 后端打包

后端以 Docker 镜像交付，`DB` 构建参数选择数据库驱动（Dockerfile 默认 `postgres`）：

```bash
docker build --build-arg DB=postgres -f docker/backend/Dockerfile -t fastapiadmin-backend .
```

前端构建：`cd frontend/web && pnpm build:prod`。完整部署流程见 [docs/DEPLOY-OPS.md](docs/DEPLOY-OPS.md) 与 [docker/README.md](docker/README.md)。

## 🔁 基于本工程新建项目：改名清单

以「系统名改为 `Eco`、数据库改为 `eco`」为例。按层列出，**必改**是不改就跑不起来或会串环境，**建议**是品牌与文案。

**必改**

| 位置 | 改什么 |
| --- | --- |
| `backend/env/.env.dev`、`.env.prod`（由 `.env.example` 复制） | `DATABASE_NAME=eco`、数据库/Redis 口令、`SECRET_KEY`、`DATA_ENCRYPTION_KEY`（均用 `openssl rand -hex 32`）；生产再改 `PROD_CORS_ORIGINS`、`ALLOWED_HOSTS`、`OAUTH_ALLOWED_HOSTS` 为你的域名 |
| `docker/.env`（由 `.env.example` 复制） | `POSTGRES_DB=eco`、`POSTGRES_PASSWORD`、`REDIS_PASSWORD`、`SECRET_KEY`、`DATA_ENCRYPTION_KEY`、`PROJECT_NAME`、`PROD_CORS_ORIGINS`、`OAUTH_ALLOWED_HOSTS` |
| `docker/docker-compose.yaml` | 三处默认值 `:-fastapiadmin`（`POSTGRES_DB`、健康检查、`DATABASE_NAME`）和 `OAUTH_ALLOWED_HOSTS` 默认域名；`.env` 已设置时可不改，但建议一并改，避免回落到旧名 |
| `backend/app/config/setting.py` | 默认值：`TITLE`、`DATABASE_NAME`、`ALLOWED_HOSTS`、`OAUTH_ALLOWED_HOSTS`（只是兜底，真实值以 `.env` 为准） |
| `backend/sql/sys_param.json`、`sys_user.json` | 种子数据里的 logo / favicon / 版权 / 文档 / 头像 URL（指向 `service.fastapiadmin.com`）。**首次启动导入后才生效**，已初始化的库要到后台「参数管理」里改 |
| `docker/nginx/nginx.conf`、`docker/nginx/ssl/` | `server_name` 与证书（仅用到 Nginx 部署时） |
| `deploy.sh` | `REMOTE_ROOT`、`BACKUP_DIR` 默认路径（`/home/FastapiAdmin`）和验证用的域名 |

**建议（品牌与文案）**

| 位置 | 改什么 |
| --- | --- |
| `frontend/web/.env.development`、`.env.production` | `VITE_APP_TITLE` |
| `frontend/web/src/config/index.ts` | `name`（系统名称） |
| `frontend/web/package.json` | `name`、`author`、`repository`、`bugs`、`homepage` |
| `frontend/web/public/`、`frontend/web/src/assets/fa_imgs/`、`backend/static/image/` | `logo.svg`、favicon 等图标 |
| `frontend/app/.env.*`、`pages.config.ts`、`src/locales/langs/{zh,en}.json` | `VITE_APP_TITLE`、`VITE_API_BASE_URL`、导航栏标题、分享与欢迎文案 |
| `backend/pyproject.toml`、`app/core/logger.py`、`app/utils/console.py`、`main.py` | 项目描述、日志文件名 `fastapiadmin.log`、启动标题、CLI 说明 |
| `README.md`、`docs/DESIGN-SPEC.md`、`docs/brand/`、`design/` | 项目名、品牌规范与资源 |

**注意**

- 数据库名只在**首次初始化**时生效：`docker/postgres/data/pgdata` 已存在时，改 `POSTGRES_DB` 不会重建库。要么删掉 `pgdata` 重新初始化（会清空数据），要么手动 `createdb eco`。
- Docker 容器名固定为 `postgres`、`redis`、`backend`、`nginx`，同一台机器上跑两个项目会冲突，需要改 `docker-compose.yaml` 里的 `container_name` 和端口。
- 全局检索遗漏项：`grep -rniE "fastapiadmin" --exclude-dir=node_modules --exclude-dir=.git .`。其中大量是代码注释里的 `@author`，不影响运行，可按需保留。
- `.env`、`.env.dev`、`.env.prod` 不提交到 git。

## 📖 文档

- [AGENTS.md](AGENTS.md) — AI 协作入口与文档索引
- [docs/DEV-GUIDE.md](docs/DEV-GUIDE.md) — 开发约定与契约
- [docs/UI-ENGINEERING-SPEC.md](docs/UI-ENGINEERING-SPEC.md) · [docs/DESIGN-SPEC.md](docs/DESIGN-SPEC.md) — 界面与品牌规范
- [docs/DEPLOY-OPS.md](docs/DEPLOY-OPS.md) — 部署与运维
- [官网文档](https://service.fastapiadmin.com) · 子工程：[backend](backend/README.md) · [web](frontend/web/README.md) · [app](frontend/app/README.md) · [docker](docker/README.md)

协议：[MIT](LICENSE)
