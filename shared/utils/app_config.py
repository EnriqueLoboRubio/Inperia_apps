import json
import os
from pathlib import Path

from utils.runtime_paths import app_config_candidates, app_user_root


DEFAULT_CONFIG = {
    "server_host": "127.0.0.1",
    "api_scheme": "http",
    "api_port": 8000,
    "api_base_path": "/api",
    "database": {
        "port": 5432,
        "name": "Inperia_db",
        "user": "postgres",
        "password": "1234",
    },
}


def _load_from_candidates(skip_user_config=False):
    user_config_path = (app_user_root() / "config.json").resolve()
    for config_path in app_config_candidates():
        if config_path is None:
            continue
        path = Path(config_path)
        if skip_user_config and path.resolve() == user_config_path:
            continue
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}


def load_app_config():
    return _load_from_candidates()


def ensure_user_config():
    config_path = app_user_root() / "config.json"
    if config_path.exists():
        return config_path

    initial_config = _load_from_candidates(skip_user_config=True) or DEFAULT_CONFIG
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(initial_config, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    return config_path


def _config_value(data, *keys, default=None):
    current = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def get_server_host():
    host = str(
        os.getenv("INPERIA_SERVER_HOST")
        or _config_value(load_app_config(), "server_host", default=DEFAULT_CONFIG["server_host"])
    ).strip()
    return host or DEFAULT_CONFIG["server_host"]


def get_api_base_url():
    config = load_app_config()

    explicit_url = str(
        os.getenv("INPERAUDIO_API_URL")
        or _config_value(config, "inperiaudio_api_url", default="")
    ).strip()
    if explicit_url:
        return explicit_url.rstrip("/")

    scheme = str(_config_value(config, "api_scheme", default=DEFAULT_CONFIG["api_scheme"])).strip() or "http"
    port = int(_config_value(config, "api_port", default=DEFAULT_CONFIG["api_port"]))
    base_path = str(
        _config_value(config, "api_base_path", default=DEFAULT_CONFIG["api_base_path"])
    ).strip() or "/api"
    if not base_path.startswith("/"):
        base_path = f"/{base_path}"

    return f"{scheme}://{get_server_host()}:{port}{base_path}".rstrip("/")


def get_database_settings():
    config = load_app_config()
    database = _config_value(config, "database", default={}) or {}

    return {
        "host": str(os.getenv("PGHOST") or get_server_host()).strip() or DEFAULT_CONFIG["server_host"],
        "port": int(os.getenv("PGPORT") or database.get("port", DEFAULT_CONFIG["database"]["port"])),
        "dbname": str(os.getenv("PGDATABASE") or database.get("name", DEFAULT_CONFIG["database"]["name"])).strip(),
        "user": str(os.getenv("PGUSER") or database.get("user", DEFAULT_CONFIG["database"]["user"])).strip(),
        "password": str(
            os.getenv("PGPASSWORD") or database.get("password", DEFAULT_CONFIG["database"]["password"])
        ),
    }
