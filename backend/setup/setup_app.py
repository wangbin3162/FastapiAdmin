"""FastapiAdmin 系统初始化配置向导。

启动：
    cd backend && uv run main.py setup
访问：
    http://127.0.0.1:9090

向导只负责「测试连接 + 回写 env 配置」，不建库、不迁移；首次启动
`uv run main.py run --env=dev` 时会自动迁移并导入 sql/*.json 种子数据。
"""

from __future__ import annotations

import secrets
from pathlib import Path
from typing import Literal

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.engine import URL

from setup import writer

TEMPLATE_DIR = Path(__file__).parent / "templates"

setup_app = FastAPI(
    title="FastapiAdmin 初始化向导",
    description="填写配置后回写 backend / docker / frontend 的 env 文件",
    docs_url=None,
    redoc_url=None,
)


# ================================================= #
# ******************* 请求模型 ******************** #
# ================================================= #
class AppConfig(BaseModel):
    """应用运行参数"""

    environment: Literal["dev", "prod"] = "dev"
    server_host: str = "localhost"
    server_port: int = Field(default=8001, ge=1, le=65535)
    logger_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "DEBUG"
    demo_enable: bool = False


class DatabaseConfig(BaseModel):
    """数据库参数"""

    type: Literal["postgres", "mysql", "sqlite"] = "postgres"
    host: str = "localhost"
    port: int = Field(default=5432, ge=0, le=65535)
    user: str = "postgres"
    password: str = ""
    name: str = "fastapiadmin"


class RedisConfig(BaseModel):
    """Redis 参数"""

    host: str = "localhost"
    port: int = Field(default=6379, ge=1, le=65535)
    user: str = ""
    password: str = ""
    db: int = Field(default=1, ge=0, le=15)


class SecurityConfig(BaseModel):
    """安全参数"""

    secret_key: str = ""
    data_encryption_key: str = ""
    prod_domain: str = ""
    forwarded_allow_ips: str = ""
    allow_localhost_hosts: bool = True
    cors_strict_startup: bool = False
    scheduler_allow_code_exec: bool = False


class FrontendConfig(BaseModel):
    """前端参数"""

    app_title: str = "FastapiAdmin"
    web_port: int = Field(default=5180, ge=1, le=65535)
    app_port: int = Field(default=5180, ge=1, le=65535)


class DockerConfig(BaseModel):
    """Docker 部署参数"""

    write: bool = True
    project_name: str = "FastapiAdmin"
    http_port: int = Field(default=80, ge=1, le=65535)
    https_port: int = Field(default=443, ge=1, le=65535)


class SetupConfig(BaseModel):
    """完整配置"""

    app: AppConfig = AppConfig()
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    security: SecurityConfig = SecurityConfig()
    frontend: FrontendConfig = FrontendConfig()
    docker: DockerConfig = DockerConfig()


# ================================================= #
# ******************* 工具函数 ******************** #
# ================================================= #
def _as_bool(raw: str, default: bool = False) -> bool:
    if not raw.strip():
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(raw: str, default: int) -> int:
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        return default


def _split_domains(raw: str) -> list[str]:
    """拆分域名输入；裸域名补 https:// 作为跨域来源。"""
    items = [item.strip() for item in raw.replace("，", ",").split(",") if item.strip()]
    return [item if "://" in item else f"https://{item}" for item in items]


def _host_only(origin: str) -> str:
    return origin.split("://", 1)[-1].split("/", 1)[0].strip()


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(writer.PROJECT_ROOT))
    except ValueError:
        return str(path)


def get_setup_html() -> str:
    html_path = TEMPLATE_DIR / "setup.html"
    if html_path.is_file():
        return html_path.read_text(encoding="utf-8")
    return "<h1>初始化页面模板不存在</h1>"


def build_state(environment: str) -> dict:
    """汇总各 env 文件的当前值，供页面回填。"""
    backend = writer.read_env(writer.backend_env_path(environment), writer.BACKEND_ENV_EXAMPLE)
    docker = writer.read_env(writer.DOCKER_ENV, writer.DOCKER_ENV_EXAMPLE)
    web_common = writer.read_env(writer.WEB_DIR / ".env")
    web_mode = writer.read_env(writer.web_env_path(environment), writer.web_env_example_path(environment))
    app_mode = writer.read_env(writer.app_env_path(environment), writer.app_env_template_path(environment))

    origins = _split_domains(backend.get("PROD_CORS_ORIGINS") or docker.get("PROD_CORS_ORIGINS", ""))
    domain = _host_only(origins[0]) if origins else ""
    title = web_common.get("VITE_APP_TITLE") or web_mode.get("VITE_APP_TITLE") or docker.get("PROJECT_NAME") or "FastapiAdmin"
    logger_level = backend.get("LOGGER_LEVEL", "DEBUG").strip().upper()
    if logger_level not in {"DEBUG", "INFO", "WARNING", "ERROR"}:
        logger_level = "INFO"

    files = [
        ("后端环境", writer.backend_env_path(environment)),
        ("Docker 部署", writer.DOCKER_ENV),
        ("Web 通用", writer.WEB_DIR / ".env"),
        ("Web 模式", writer.web_env_path(environment)),
        ("小程序本地", writer.app_env_path(environment)),
    ]

    return {
        "app": {
            "environment": environment,
            "server_host": backend.get("SERVER_HOST", "localhost"),
            "server_port": _as_int(backend.get("SERVER_PORT", ""), 8001),
            "logger_level": logger_level,
            "demo_enable": _as_bool(backend.get("DEMO_ENABLE", ""), False),
        },
        "database": {
            "type": backend.get("DATABASE_TYPE", "postgres"),
            "host": backend.get("DATABASE_HOST", "localhost"),
            "port": _as_int(backend.get("DATABASE_PORT", ""), 5432),
            "user": backend.get("DATABASE_USER", "postgres"),
            "password": backend.get("DATABASE_PASSWORD", ""),
            "name": backend.get("DATABASE_NAME", "fastapiadmin"),
        },
        "redis": {
            "host": backend.get("REDIS_HOST", "localhost"),
            "port": _as_int(backend.get("REDIS_PORT", ""), 6379),
            "user": backend.get("REDIS_USER", ""),
            "password": backend.get("REDIS_PASSWORD", ""),
            "db": _as_int(backend.get("REDIS_DB_NAME", ""), 1),
        },
        "security": {
            "secret_key": backend.get("SECRET_KEY") or docker.get("SECRET_KEY", ""),
            "data_encryption_key": backend.get("DATA_ENCRYPTION_KEY") or docker.get("DATA_ENCRYPTION_KEY", ""),
            "prod_domain": domain,
            "forwarded_allow_ips": backend.get("FORWARDED_ALLOW_IPS") or docker.get("FORWARDED_ALLOW_IPS", ""),
            "allow_localhost_hosts": _as_bool(backend.get("ALLOW_LOCALHOST_HOSTS", ""), True),
            "cors_strict_startup": _as_bool(backend.get("CORS_STRICT_STARTUP", ""), False),
            "scheduler_allow_code_exec": _as_bool(backend.get("SCHEDULER_ALLOW_CODE_EXEC", ""), False),
        },
        "frontend": {
            "app_title": title,
            "web_port": _as_int(web_common.get("VITE_PORT", ""), 5180),
            "app_port": _as_int(app_mode.get("VITE_APP_PORT", ""), 5180),
        },
        "docker": {
            "write": True,
            "project_name": docker.get("PROJECT_NAME") or title,
            "http_port": _as_int(docker.get("HTTP_PORT", ""), 80),
            "https_port": _as_int(docker.get("HTTPS_PORT", ""), 443),
        },
        "files": [
            {"label": label, "path": _relative(path), "exists": path.is_file()}
            for label, path in files
        ],
    }


def save_config(config: SetupConfig) -> dict:
    """按表单回写 env 文件，返回写入 / 跳过清单。"""
    environment = config.app.environment
    generated_secret = not config.security.secret_key.strip()
    secret_key = config.security.secret_key.strip() or secrets.token_hex(32)
    data_key = config.security.data_encryption_key.strip()
    origins = _split_domains(config.security.prod_domain)
    host_names = [_host_only(origin) for origin in origins]
    forwarded = config.security.forwarded_allow_ips.strip()

    written: list[str] = []
    skipped: list[str] = []
    notes: list[str] = []

    # ---------- 1. 后端 env ----------
    backend_updates: dict[str, object] = {
        "ENVIRONMENT": environment,
        "SERVER_HOST": config.app.server_host.strip() or "localhost",
        "SERVER_PORT": config.app.server_port,
        "DEBUG": writer.as_bool(environment == "dev"),
        "LOGGER_LEVEL": config.app.logger_level,
        "DEMO_ENABLE": writer.as_bool(config.app.demo_enable),
        "DATABASE_TYPE": config.database.type,
        "DATABASE_HOST": config.database.host.strip(),
        "DATABASE_PORT": config.database.port,
        "DATABASE_USER": config.database.user.strip(),
        "DATABASE_PASSWORD": config.database.password,
        "DATABASE_NAME": config.database.name.strip(),
        "REDIS_HOST": config.redis.host.strip(),
        "REDIS_PORT": config.redis.port,
        "REDIS_USER": config.redis.user.strip(),
        "REDIS_PASSWORD": config.redis.password,
        "REDIS_DB_NAME": config.redis.db,
        "SECRET_KEY": secret_key,
        "CORS_STRICT_STARTUP": writer.as_bool(config.security.cors_strict_startup),
        "ALLOW_LOCALHOST_HOSTS": writer.as_bool(config.security.allow_localhost_hosts),
        "SCHEDULER_ALLOW_CODE_EXEC": writer.as_bool(config.security.scheduler_allow_code_exec),
    }
    if data_key:
        backend_updates["DATA_ENCRYPTION_KEY"] = data_key
    if forwarded:
        backend_updates["FORWARDED_ALLOW_IPS"] = forwarded
    if origins:
        backend_updates["PROD_CORS_ORIGINS"] = ",".join(origins)
        backend_updates["ALLOWED_HOSTS"] = writer.as_json_list(host_names)
        backend_updates["OAUTH_ALLOWED_HOSTS"] = writer.as_json_list(host_names)
    elif environment == "prod":
        notes.append("未填写生产域名：PROD_CORS_ORIGINS 为空时浏览器跨域请求会被拒绝（同源部署不受影响）")

    backend_file = writer.write_env(
        writer.backend_env_path(environment),
        backend_updates,
        template=writer.BACKEND_ENV_EXAMPLE,
    )
    written.append(_relative(backend_file))

    # ---------- 2. Docker env ----------
    if config.docker.write:
        # compose 的后端固定 PostgreSQL；SQLite 只用于本地，别把端口 0 写进 compose
        postgres_port = config.database.port if config.database.type != "sqlite" else 5432
        docker_updates: dict[str, object] = {
            "POSTGRES_DB": config.database.name.strip() or "fastapiadmin",
            "POSTGRES_USER": config.database.user.strip() or "postgres",
            "POSTGRES_PASSWORD": config.database.password,
            "POSTGRES_PORT": postgres_port,
            "REDIS_PASSWORD": config.redis.password,
            "REDIS_PORT": config.redis.port,
            "BACKEND_PORT": config.app.server_port,
            "LOGGER_LEVEL": config.app.logger_level,
            "DEPLOY_ENV": environment,
            "SECRET_KEY": secret_key,
            "DEMO_ENABLE": writer.as_bool(config.app.demo_enable),
            "ALLOW_LOCALHOST_HOSTS": writer.as_bool(config.security.allow_localhost_hosts),
            "CORS_STRICT_STARTUP": writer.as_bool(config.security.cors_strict_startup),
            "SCHEDULER_ALLOW_CODE_EXEC": writer.as_bool(config.security.scheduler_allow_code_exec),
            "HTTP_PORT": config.docker.http_port,
            "HTTPS_PORT": config.docker.https_port,
            "PROJECT_NAME": config.docker.project_name.strip() or config.frontend.app_title.strip(),
        }
        if data_key:
            docker_updates["DATA_ENCRYPTION_KEY"] = data_key
        if forwarded:
            docker_updates["FORWARDED_ALLOW_IPS"] = forwarded
        if origins:
            docker_updates["PROD_CORS_ORIGINS"] = ",".join(origins)
            docker_updates["OAUTH_ALLOWED_HOSTS"] = writer.as_json_list(host_names)
        docker_file = writer.write_env(
            writer.DOCKER_ENV,
            docker_updates,
            template=writer.DOCKER_ENV_EXAMPLE,
        )
        written.append(_relative(docker_file))
    else:
        skipped.append("docker/.env")

    # ---------- 3. Web env ----------
    title = config.frontend.app_title.strip() or "FastapiAdmin"
    if environment == "dev":
        api_base = f"http://127.0.0.1:{config.app.server_port}"
        ws_base = f"ws://127.0.0.1:{config.app.server_port}"
        web_mode_updates: dict[str, object] = {
            "VITE_APP_ENV": "dev",
            "VITE_APP_TITLE": title,
            "VITE_API_URL": "/",
            "VITE_API_BASE_URL": api_base,
            "VITE_APP_WS_ENDPOINT": ws_base,
            "VITE_DROP_CONSOLE": "false",
        }
        app_updates: dict[str, object] = {
            "VITE_ENV_NAME": "development",
            "VITE_APP_TITLE": title,
            "VITE_API_BASE_URL": api_base,
            "VITE_APP_WS_ENDPOINT": ws_base,
            "VITE_APP_PORT": config.frontend.app_port,
        }
    elif host_names:
        domain = host_names[0]
        api_url = origins[0].rstrip("/")
        web_mode_updates = {
            "VITE_APP_ENV": "prod",
            "VITE_APP_TITLE": title,
            "VITE_API_BASE_URL": api_url,
            "VITE_APP_WS_ENDPOINT": f"wss://{domain}",
            "VITE_DROP_CONSOLE": "true",
        }
        app_updates = {
            "VITE_ENV_NAME": "production",
            "VITE_APP_TITLE": title,
            "VITE_API_BASE_URL": api_url,
            "VITE_APP_WS_ENDPOINT": f"wss://{domain}",
            "VITE_APP_PORT": config.frontend.app_port,
        }
    else:
        web_mode_updates = {}
        app_updates = {}
        skipped.extend(["frontend/web 生产 env", "frontend/app 生产 env"])
        notes.append("生产环境未填写域名，已跳过前端生产 env 的写入")

    if web_mode_updates:
        web_common_file = writer.write_env(
            writer.WEB_DIR / ".env",
            {"VITE_APP_TITLE": title, "VITE_PORT": config.frontend.web_port},
            header="# 【通用】环境变量 - 所有环境共享\n",
        )
        written.append(_relative(web_common_file))
        web_file = writer.write_env(
            writer.web_env_path(environment),
            web_mode_updates,
            template=writer.web_env_example_path(environment),
        )
        written.append(_relative(web_file))

        app_file = writer.write_env(
            writer.app_env_path(environment),
            app_updates,
            template=writer.app_env_template_path(environment),
        )
        written.append(_relative(app_file))

    if config.database.type == "sqlite":
        notes.append("SQLite：DATABASE_NAME 会被展开为 <name>.db，启动时自动建库建表")
        notes.append("Docker 部署固定 PostgreSQL；当前选择的 SQLite 只在本地生效")

    return {
        "success": True,
        "msg": "配置已保存，首次启动后端会自动迁移并导入种子数据",
        "data": {
            "written": written,
            "skipped": skipped,
            "notes": notes,
            "environment": environment,
            "secret_key_generated": generated_secret,
            "secret_key": secret_key if generated_secret else "",
            "backend_url": f"http://localhost:{config.app.server_port}",
            "login_hint": "默认账号 super / admin / user，密码均为 123456（登录后请立即修改）",
        },
    }


# ================================================= #
# ******************** 路由 ********************** #
# ================================================= #
@setup_app.get("/", response_class=HTMLResponse)
async def setup_page() -> str:
    """初始化页面。"""
    return get_setup_html()


@setup_app.get("/api/setup/state")
async def get_setup_state(environment: Literal["dev", "prod"] = "dev") -> dict:
    """读取各 env 文件当前值。"""
    return build_state(environment)


@setup_app.post("/api/setup/test-database")
async def test_database(config: DatabaseConfig) -> dict:
    """测试数据库连接（sqlite 仅校验文件名，不落盘）。"""
    if config.type == "sqlite":
        name = config.name.strip() or "fastapiadmin"
        db_file = name if name.endswith(".db") else f"{name}.db"
        return {"success": True, "msg": f"SQLite 无需连接测试，启动时会自动创建 {db_file}"}

    drivername = "postgresql+asyncpg" if config.type == "postgres" else "mysql+aiomysql"
    url = URL.create(
        drivername=drivername,
        username=config.user.strip() or None,
        password=config.password or None,
        host=config.host.strip() or None,
        port=config.port or None,
        database=config.name.strip() or None,
        query={"charset": "utf8mb4"} if config.type == "mysql" else {},
    ).render_as_string(hide_password=False)

    try:
        from sqlalchemy.ext.asyncio import create_async_engine
    except ImportError as exc:  # pragma: no cover - 依赖缺失时给出明确指引
        return {"success": False, "msg": f"SQLAlchemy 异步引擎不可用：{exc}"}

    engine = create_async_engine(url, pool_pre_ping=True)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except ModuleNotFoundError:
        driver = "asyncpg" if config.type == "postgres" else "aiomysql"
        extra = "postgres" if config.type == "postgres" else "mysql"
        return {
            "success": False,
            "msg": f"缺少数据库驱动 {driver}：请在 backend 目录执行 uv sync --extra {extra}",
        }
    except Exception as exc:  # noqa: BLE001 - 原样回显给向导页面
        hint = ""
        if config.type == "postgres":
            hint = f"；数据库不存在时请先创建：createdb -h {config.host} -p {config.port} -U {config.user} {config.name}"
        return {
            "success": False,
            "msg": f"连接失败：{type(exc).__name__}: {exc}{hint}",
            "detail": str(exc),
        }
    finally:
        await engine.dispose()

    return {"success": True, "msg": "数据库连接成功"}


@setup_app.post("/api/setup/test-redis")
async def test_redis(config: RedisConfig) -> dict:
    """测试 Redis 连接。"""
    try:
        from redis.asyncio import Redis
    except ImportError as exc:  # pragma: no cover
        return {"success": False, "msg": f"redis 客户端不可用：{exc}"}

    client = Redis(
        host=config.host.strip() or "localhost",
        port=config.port,
        username=config.user.strip() or None,
        password=config.password or None,
        db=config.db,
        socket_timeout=5,
        socket_connect_timeout=5,
    )
    try:
        await client.ping()
    except Exception as exc:  # noqa: BLE001 - 原样回显给向导页面
        return {"success": False, "msg": f"连接失败：{type(exc).__name__}: {exc}"}
    finally:
        await client.aclose()
    return {"success": True, "msg": "Redis 连接成功"}


@setup_app.post("/api/setup/save")
async def initialize_system(config: SetupConfig) -> dict:
    """回写全部 env 配置。"""
    try:
        return save_config(config)
    except Exception as exc:  # noqa: BLE001 - 返回堆栈摘要，便于定位是权限还是路径问题
        import traceback

        return {
            "success": False,
            "msg": f"保存失败：{type(exc).__name__}: {exc}",
            "detail": traceback.format_exc(),
        }


def run_setup_server(host: str = "127.0.0.1", port: int = 9090) -> None:
    """运行初始化服务器。"""
    print("\n" + "=" * 62)
    print("  🚀 FastapiAdmin 初始化配置向导")
    print("=" * 62)
    print("\n  打开下面的地址填写配置，保存后会回写：")
    print("    - backend/env/.env.{dev,prod}")
    print("    - docker/.env")
    print("    - frontend/web/.env 与 .env.{development,production}")
    print("    - frontend/app/.env.{development,production}.local")
    print(f"\n  ➜  http://{host}:{port}")
    print("\n  提示：本页面会显示与保存口令，默认只监听本机。")
    print("  保存后执行 uv run main.py run --env=dev 启动后端。")
    print("\n" + "=" * 62 + "\n")

    uvicorn.run(setup_app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    run_setup_server()
