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
uv sync --extra postgres               # 数据库驱动，按 DATABASE_TYPE 选，见下
uv run main.py run --env=dev           # 首次启动自动迁移并导入种子数据
```

> 数据库驱动不随基础依赖安装，按 `DATABASE_TYPE` 选 extra：PostgreSQL `--extra postgres`（默认，含 `psycopg` + `asyncpg`）、MySQL `--extra mysql`、SQLite `--extra sqlite`、全部 `--extra all-db`。
> ⚠️ 不带 extra 的 `uv sync` 会把已装的驱动移除，之后启动会报 `No module named 'psycopg'` / `'asyncpg'`；固定用带 extra 的命令。

默认 `DATABASE_TYPE=postgres`（`localhost:5432`，库 `fastapiadmin` 需事先创建）。服务地址 `http://localhost:8001`，接口文档 `/docs`。

```bash
uv run main.py revision -m "说明"      # 生成迁移
uv run main.py upgrade --env=dev       # 应用迁移
uv run pytest -q                       # 测试
uv run ruff check                      # 代码检查
```

#### 配置向导（可选）

不想逐个文件手改 env，可以启动初始化向导：浏览器里填一次，保存后回写 `backend/env/.env.{dev,prod}`、`docker/.env`、`frontend/web/.env*` 和 `frontend/app/.env.*.local`。

```bash
cd backend
uv run main.py setup                   # 打开 http://127.0.0.1:9090
```

```bash
uv run main.py setup --port 9091 --host 127.0.0.1   # 端口被占用时
```

向导可以测试数据库 / Redis 连接，但不建库、不迁移；保存后用 `uv run main.py run --env=dev` 启动，首次启动仍会自动迁移并导入种子数据。

#### 本机开发：只在 Docker 里起依赖

后端跑在本机，Postgres 和 Redis 用容器。`docker/.env` 不存在时先 `cp .env.example .env` 并填 `POSTGRES_PASSWORD` / `REDIS_PASSWORD`；用过向导则已生成，且与 `backend/env/.env.dev` 口令一致。

```bash
cd docker && docker compose --env-file .env up -d postgres redis
```

用 SQLite 或外部数据库时只起 Redis：`cd docker && docker compose up -d redis`。等容器健康（`docker compose ps`）后再启动后端；否则后端启动时会因连不上数据库或 Redis 直接退出。

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

配置类改动（数据库名、口令、密钥、域名、端口、前端 API 地址等）用 `uv run main.py setup` 一次完成，会同步写后端、Docker、Web、小程序 env。下表只列向导改不到的部分。

**必改**

| 位置 | 改什么 |
| --- | --- |
| `docker/docker-compose.yaml` | 兜底默认值 `:-fastapiadmin`（`POSTGRES_DB`、健康检查、`DATABASE_NAME`）和 `OAUTH_ALLOWED_HOSTS` 默认域名。`docker/.env` 由向导写入，这些默认值只防漏配时回落到旧名 |
| `backend/app/config/setting.py` | 代码兜底默认值 `TITLE`、`DATABASE_NAME`、`ALLOWED_HOSTS`、`OAUTH_ALLOWED_HOSTS`（真实值以 `.env` 为准） |
| `backend/sql/sys_param.json`、`sys_user.json` | 种子数据里的 logo / favicon / 版权 / 文档 / 头像 URL（指向 `service.fastapiadmin.com`）。**首次启动导入后才生效**；已初始化的库到后台「参数管理」改 |
| `docker/nginx/nginx.conf`、`docker/nginx/ssl/` | `server_name` 与证书（仅 Nginx 部署时） |
| `deploy.sh` | `FA_REMOTE_ROOT` / `FA_BACKUP_DIR` 默认路径（`/home/FastapiAdmin`）和验证用的域名 |

**品牌与资源**

| 位置 | 改什么 |
| --- | --- |
| `frontend/web/public/`、`frontend/web/src/assets/fa_imgs/`、`backend/static/image/` | `logo.svg`、`favicon.ico`、背景图等图标 |
| `frontend/web/src/config/index.ts` | `name`（系统名称） |
| `frontend/web/package.json` | `name`、`author`、`repository`、`bugs`、`homepage` |
| `frontend/app/pages.config.ts`、`src/locales/langs/{zh,en}.json` | 导航栏标题、分享与欢迎文案（env 里的标题和接口地址由向导写入） |
| `backend/pyproject.toml`、`app/core/logger.py`、`app/utils/console.py`、`main.py` | 项目描述、日志文件名 `fastapiadmin.log`、启动标题、CLI 说明 |
| `README.md`、`docs/DESIGN-SPEC.md`、`docs/brand/`、`design/` | 项目名、品牌规范与资源 |

**注意**

- 数据库名只在**首次初始化**时生效：`docker/postgres/data/pgdata` 已存在时，向导改 `POSTGRES_DB` 不会重建库。要么删掉 `pgdata` 重新初始化（会清空数据），要么手动建库。
- Docker 容器名固定为 `postgres`、`redis`、`backend`、`nginx`，同一台机器上跑两个项目会冲突，需要改 `docker-compose.yaml` 里的 `container_name` 和端口。
- 全局检索遗漏项：`grep -rniE "fastapiadmin" --exclude-dir=node_modules --exclude-dir=.git .`。其中大量是代码注释里的 `@author`，不影响运行，可按需保留。
- 向导写入的 `backend/env/.env.*`、`docker/.env`、`frontend/web/.env*` 均已被 git 忽略；小程序配置写到 `frontend/app/.env.*.local`（`*.local` 已忽略），`frontend/app/.env.*` 本身仍保留仓库默认值。

## 📖 文档

- [AGENTS.md](AGENTS.md) — AI 协作入口与文档索引
- [docs/DEV-GUIDE.md](docs/DEV-GUIDE.md) — 开发约定与契约
- [docs/UI-ENGINEERING-SPEC.md](docs/UI-ENGINEERING-SPEC.md) · [docs/DESIGN-SPEC.md](docs/DESIGN-SPEC.md) — 界面与品牌规范
- [docs/DEPLOY-OPS.md](docs/DEPLOY-OPS.md) — 部署与运维
- [官网文档](https://service.fastapiadmin.com) · 子工程：[backend](backend/README.md) · [web](frontend/web/README.md) · [app](frontend/app/README.md) · [docker](docker/README.md)

协议：[MIT](LICENSE)
