import os
import sys
from pathlib import Path


def _bootstrap():
    app_root = Path(__file__).resolve().parent
    project_root = app_root.parent.parent
    runtime_root = (
        Path(sys.executable).resolve().parent / "shared"
        if getattr(sys, "frozen", False)
        else project_root / "shared"
    )

    for path in (str(project_root), str(project_root / "shared"), str(app_root)):
        if path not in sys.path:
            sys.path.insert(0, path)

    os.chdir(runtime_root)


_bootstrap()

from controllers.main_controller import StaffMainController 


if __name__ == "__main__":
    controller = StaffMainController()
    controller.ejecutar()
