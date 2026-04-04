import os
import sys
from pathlib import Path


APP_IDS = ("cliente", "staff")
APP_DISPLAY_NAMES = {
    "cliente": "Inperia Cliente",
    "staff": "Inperia Staff",
}


def project_root():
    return Path(__file__).resolve().parents[2]


def runtime_root():
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass).resolve()
        return Path(sys.executable).resolve().parent / "_internal"
    return project_root()


def app_id():
    env_app_id = str(os.getenv("INPERIA_APP_ID", "")).strip().lower()
    if env_app_id in APP_IDS:
        return env_app_id

    executable_name = Path(sys.executable).stem.lower()
    if "cliente" in executable_name or "client" in executable_name:
        return "cliente"
    if "staff" in executable_name:
        return "staff"
    return "cliente"


def app_display_name():
    return APP_DISPLAY_NAMES[app_id()]


def app_install_root():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return project_root()


def shared_root():
    if getattr(sys, "frozen", False):
        return runtime_root() / "shared"
    return project_root() / "shared"


def shared_assets_root():
    return shared_root() / "assets"


def shared_asset_path(filename):
    return shared_assets_root() / filename


def qt_asset_path(filename):
    return f"assets:{filename}"


def shared_data_root():
    return shared_root() / "data"


def shared_data_file(filename):
    return shared_data_root() / filename


def _local_appdata_root():
    local_appdata = os.getenv("LOCALAPPDATA")
    if local_appdata:
        return Path(local_appdata)
    return Path.home() / "AppData" / "Local"


def app_user_root():
    return _local_appdata_root() / app_display_name()


def app_data_root():
    return app_user_root() / "data"


def app_cache_root():
    return app_user_root() / "cache"


def app_logs_root():
    return app_user_root() / "logs"


def audio_cache_root():
    return app_cache_root() / "audios_cache"


def grabaciones_root():
    return app_data_root() / "grabaciones"


def vosk_model_root(size="big"):
    return shared_root() / "utils" / "vosk-es" / size


def app_config_candidates():
    user_config = app_user_root() / "config.json"
    return [
        Path(os.getenv("INPERIA_CONFIG_PATH", "")).expanduser() if os.getenv("INPERIA_CONFIG_PATH") else None,
        user_config,
        shared_root() / "config.json",
    ]


def ensure_runtime_directories():
    from utils.app_config import ensure_user_config

    directories = [
        app_user_root(),
        app_data_root(),
        app_cache_root(),
        app_logs_root(),
        audio_cache_root(),
    ]
    if app_id() == "cliente":
        directories.append(grabaciones_root())

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    ensure_user_config()


def init_qt_search_paths():
    from PyQt5.QtCore import QDir

    QDir.addSearchPath("assets", str(shared_assets_root()))
