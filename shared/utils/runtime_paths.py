import sys
from pathlib import Path


def project_root():
    return Path(__file__).resolve().parents[2]


def runtime_root():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return project_root()


def shared_root():
    if getattr(sys, "frozen", False):
        return runtime_root() / "shared"
    return project_root() / "shared"


def shared_assets_root():
    return shared_root() / "assets"


def shared_data_root():
    return shared_root() / "data"


def app_data_root():
    return runtime_root() / "data"


def grabaciones_root():
    return app_data_root() / "grabaciones"


def vosk_model_root(size):
    return shared_root() / "utils" / "vosk-es" / size
