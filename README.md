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

## 📖 文档

- [AGENTS.md](AGENTS.md) — AI 协作入口与文档索引
- [docs/DEV-GUIDE.md](docs/DEV-GUIDE.md) — 开发约定与契约
- [docs/UI-ENGINEERING-SPEC.md](docs/UI-ENGINEERING-SPEC.md) · [docs/DESIGN-SPEC.md](docs/DESIGN-SPEC.md) — 界面与品牌规范
- [docs/DEPLOY-OPS.md](docs/DEPLOY-OPS.md) — 部署与运维
- [官网文档](https://service.fastapiadmin.com) · 子工程：[backend](backend/README.md) · [web](frontend/web/README.md) · [app](frontend/app/README.md) · [docker](docker/README.md)

协议：[MIT](LICENSE)
