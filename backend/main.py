import os
from typing import Annotated

import typer
import uvicorn
from alembic import command
from alembic.config import Config
from typer.main import Typer

from app.common.enums import EnvironmentEnum

fastapiadmin_cli: Typer = typer.Typer()
alembic_cfg: Config = Config(file_="alembic.ini")


@fastapiadmin_cli.command(
    name="run",
    help="启动 FastapiAdmin 服务, 运行 python(或uv run) main.py run --env=dev 不加参数默认 dev 环境",
)
def run(
    env: Annotated[EnvironmentEnum, typer.Option("--env", help="运行环境 (dev, prod)")] = EnvironmentEnum.DEV,
) -> None:
    """按指定环境加载配置并启动 Uvicorn（dev 环境 DEBUG=True 自动开启 reload）。

    参数:
    - env (EnvironmentEnum): 运行环境，对应 `--env`。

    返回:
    - None
    """
    os.environ["ENVIRONMENT"] = env.value

    from app.utils.banner import worship
    typer.secho(message=f"{worship()}", fg=typer.colors.GREEN)
    from app.config.setting import settings

    uvicorn.run(
        app="app:create_app",
        factory=True,
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS,
        log_config=None,
        timeout_graceful_shutdown=5,
    )


@fastapiadmin_cli.command(
    name="revision",
    help="生成新的 Alembic 迁移脚本, 运行 python(或uv run) main.py revision --env=dev",
)
def revision(
    env: Annotated[EnvironmentEnum, typer.Option("--env", help="运行环境 (dev, prod)")] = EnvironmentEnum.DEV,
    message: Annotated[str, typer.Option("--message", "-m", help="迁移说明（进入迁移文件名 slug）")] = "迁移脚本",
) -> None:
    """使用 Alembic 自动生成迁移脚本（autogenerate）。

    参数:
    - env (EnvironmentEnum): 运行环境，用于加载对应数据库模型元数据。
    - message (str): 迁移说明，写入迁移文件 message 与文件名 slug。

    返回:
    - None
    """
    os.environ["ENVIRONMENT"] = env.value
    command.revision(config=alembic_cfg, autogenerate=True, message=message)
    typer.echo(message="迁移脚本已生成")


@fastapiadmin_cli.command(
    name="setup",
    help="启动系统初始化配置向导（浏览器填写后回写 env 配置）, 运行 uv run main.py setup",
)
def setup(
    host: Annotated[str, typer.Option("--host", help="监听地址，默认仅本机可访问")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port", help="向导监听端口")] = 9090,
) -> None:
    """启动初始化向导，按表单回写后端 / Docker / Web / 小程序 env 文件。

    参数:
    - host (str): 监听地址，默认 127.0.0.1（页面会显示口令，勿随意暴露）。
    - port (int): 向导端口，默认 9090。

    返回:
    - None
    """
    from setup.setup_app import run_setup_server

    run_setup_server(host=host, port=port)


@fastapiadmin_cli.command(
    name="upgrade",
    help="应用最新的 Alembic 迁移, 运行 python(或uv run) main.py upgrade --env=dev",
)
def upgrade(
    env: Annotated[EnvironmentEnum, typer.Option("--env", help="运行环境 (dev, prod)")] = EnvironmentEnum.DEV,
) -> None:
    """将数据库升级到 Alembic 最新版本（head）。

    参数:
    - env (EnvironmentEnum): 运行环境。

    返回:
    - None
    """
    os.environ["ENVIRONMENT"] = env.value
    command.upgrade(config=alembic_cfg, revision="head")
    typer.echo(message="所有迁移已应用。")


if __name__ == "__main__":
    fastapiadmin_cli()
