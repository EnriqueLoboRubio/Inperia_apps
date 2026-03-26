import os
import sys
from pathlib import Path


def _bootstrap():
    os.environ["INPERIA_APP_ID"] = "staff"
    app_root = Path(__file__).resolve().parent
    project_root = app_root.parent.parent

    for path in (str(project_root), str(project_root / "shared"), str(app_root)):
        if path not in sys.path:
            sys.path.insert(0, path)

    from utils.runtime_paths import ensure_runtime_directories, init_qt_search_paths

    ensure_runtime_directories()
    init_qt_search_paths()


_bootstrap()

from controllers.main_controller import StaffMainController 


if __name__ == "__main__":
    controller = StaffMainController()
    controller.ejecutar()
