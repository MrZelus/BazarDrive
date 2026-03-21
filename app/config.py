import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


DEFAULT_ENV_PATH = ".env"


@dataclass(frozen=True)
class BotSettings:
    bot_token: str
    admin_chat_id: int
    group_chat_id: int
    admin_ids: set[int]


@dataclass(frozen=True)
class ApiSettings:
    host: str
    port: int


@lru_cache(maxsize=1)
def load_env_file(env_path: str = DEFAULT_ENV_PATH) -> None:
    path = Path(env_path)
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key:
            os.environ.setdefault(key, value)


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise ValueError(f"Environment variable {name} is required")
    return value.strip()


def _get_required_int_env(name: str) -> int:
    raw_value = _get_required_env(name)
    try:
        return int(raw_value)
    except ValueError as error:
        raise ValueError(f"Environment variable {name} must be an integer") from error


@lru_cache(maxsize=1)
def get_bot_settings() -> BotSettings:
    load_env_file()
    admin_ids_raw = os.getenv("ADMIN_IDS", "")
    return BotSettings(
        bot_token=_get_required_env("BOT_TOKEN"),
        admin_chat_id=_get_required_int_env("ADMIN_CHAT_ID"),
        group_chat_id=_get_required_int_env("GROUP_CHAT_ID"),
        admin_ids={int(uid.strip()) for uid in admin_ids_raw.split(",") if uid.strip()},
    )


@lru_cache(maxsize=1)
def get_api_settings() -> ApiSettings:
    load_env_file()
    host = os.getenv("FEED_API_HOST", "0.0.0.0")
    port_raw = os.getenv("FEED_API_PORT", "8001")
    try:
        port = int(port_raw)
    except ValueError as error:
        raise ValueError("Environment variable FEED_API_PORT must be an integer") from error
    return ApiSettings(host=host, port=port)


def get_feed_upload_dir() -> str:
    load_env_file()
    return os.getenv("FEED_UPLOAD_DIR", "storage/feed_images")
