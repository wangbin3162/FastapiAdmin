"""env 配置文件读写：按 KEY 就地更新，保留注释与表单未涉及的配置项。"""

from __future__ import annotations

import json
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

BACKEND_ENV_DIR = BACKEND_DIR / "env"
BACKEND_ENV_EXAMPLE = BACKEND_ENV_DIR / ".env.example"

DOCKER_ENV = PROJECT_ROOT / "docker" / ".env"
DOCKER_ENV_EXAMPLE = PROJECT_ROOT / "docker" / ".env.example"

WEB_DIR = PROJECT_ROOT / "frontend" / "web"
APP_DIR = PROJECT_ROOT / "frontend" / "app"

_KEY_LINE = re.compile(r"^(\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*=\s*)(.*)$")


def backend_env_path(environment: str) -> Path:
    """后端环境文件：backend/env/.env.{dev,prod}（不入库）。"""
    return BACKEND_ENV_DIR / f".env.{environment}"


def web_mode(environment: str) -> str:
    return "development" if environment == "dev" else "production"


def web_env_path(environment: str) -> Path:
    """Web 模式文件：.env.development / .env.production（不入库）。"""
    return WEB_DIR / f".env.{web_mode(environment)}"


def web_env_example_path(environment: str) -> Path:
    return WEB_DIR / f".env.{web_mode(environment)}.example"


def app_env_path(environment: str) -> Path:
    """小程序写入 .local 文件：优先生效且被 *.local 忽略规则排除，不污染已跟踪的 .env.*。"""
    return APP_DIR / f".env.{web_mode(environment)}.local"


def app_env_template_path(environment: str) -> Path:
    return APP_DIR / f".env.{web_mode(environment)}"


def _parse_env_text(text: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        if key:
            data[key] = value.strip().strip("'\"")
    return data


def read_env(path: Path | None, fallback: Path | None = None) -> dict[str, str]:
    """读取 env 文件；path 不存在时回退到 fallback（通常是 *.example）。"""
    for candidate in (path, fallback):
        if candidate is None or not candidate.is_file():
            continue
        try:
            from dotenv import dotenv_values

            values = dotenv_values(candidate, encoding="utf-8")
        except Exception:
            return _parse_env_text(candidate.read_text(encoding="utf-8"))
        return {key: (value or "") for key, value in values.items() if key}
    return {}


def format_value(value: object) -> str:
    """按 .env 语法格式化值；含空白或注释符时加双引号。"""
    text = str(value).replace("\n", " ").strip()
    if not text:
        return ""
    # JSON 数组（ALLOWED_HOSTS 等）本身含引号，原样写入才能被 pydantic-settings 解析
    if text.startswith("[") and text.endswith("]"):
        return text
    if re.search(r"""[\s#'"]""", text):
        return '"' + text.replace('"', '\\"') + '"'
    return text


def upsert_env_text(text: str, updates: dict[str, object]) -> str:
    """就地替换已有 KEY 的值；不存在的 KEY 追加到文件末尾。"""
    lines = text.splitlines()
    seen: set[str] = set()
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        match = _KEY_LINE.match(line)
        if not match:
            continue
        key = match.group(2)
        if key in updates:
            lines[index] = f"{match.group(1)}{key}{match.group(3)}{format_value(updates[key])}"
            seen.add(key)

    missing = [key for key in updates if key not in seen]
    if missing:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append("# 由 setup 向导写入")
        lines.extend(f"{key} = {format_value(updates[key])}" for key in missing)
    return "\n".join(lines) + "\n"


def write_env(
    path: Path,
    updates: dict[str, object],
    *,
    template: Path | None = None,
    header: str = "",
) -> Path:
    """以已有文件（其次模板）为基底，写入更新项。"""
    if path.is_file():
        text = path.read_text(encoding="utf-8")
    elif template is not None and template.is_file():
        text = template.read_text(encoding="utf-8")
    else:
        text = header
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(upsert_env_text(text, updates), encoding="utf-8")
    return path


def as_bool(value: bool) -> str:
    return "True" if value else "False"


def as_json_list(items: list[str]) -> str:
    return json.dumps(items, ensure_ascii=False, separators=(",", ":"))
