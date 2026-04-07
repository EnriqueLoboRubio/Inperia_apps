import json
import os
from pathlib import Path

from utils.runtime_paths import app_config_candidates, app_config_path


DEFAULT_CONFIG = {
    "server_host": "192.168.1.200",
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


def _load_from_candidates():
    for config_path in app_config_candidates():
        if config_path is None:
            continue
        path = Path(config_path)
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
    ensure_app_config()
    return _load_from_candidates()


def ensure_app_config():
    config_path = app_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if config_path.exists():
        return config_path

    config_path.write_text(
        json.dumps(DEFAULT_CONFIG, ensure_ascii=True, indent=2) + "\n",
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
    config = load_app_config()
    host = str(
        _config_value(config, "server_host", default="")
        or os.getenv("INPERIA_SERVER_HOST")
        or DEFAULT_CONFIG["server_host"]
    ).strip()
    return host or DEFAULT_CONFIG["server_host"]


def get_api_base_url():
    config = load_app_config()

    explicit_url = _config_value(config, "inperiaudio_api_url", default=None)
    if explicit_url in (None, ""):
        # Compatibilidad con ambas variantes del nombre de la variable de entorno.
        explicit_url = os.getenv("INPERIAUDIO_API_URL") or os.getenv("INPERAUDIO_API_URL")
    explicit_url = str(explicit_url or "").strip()
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
        "host": str(database.get("host") or os.getenv("PGHOST") or get_server_host()).strip()
        or DEFAULT_CONFIG["server_host"],
        "port": int(database.get("port") or os.getenv("PGPORT") or DEFAULT_CONFIG["database"]["port"]),
        "dbname": str(database.get("name") or os.getenv("PGDATABASE") or DEFAULT_CONFIG["database"]["name"]).strip(),
        "user": str(database.get("user") or os.getenv("PGUSER") or DEFAULT_CONFIG["database"]["user"]).strip(),
        "password": str(
            database.get("password") or os.getenv("PGPASSWORD") or DEFAULT_CONFIG["database"]["password"]
        ),
    }
