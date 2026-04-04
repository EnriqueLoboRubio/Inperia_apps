# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


project_root = Path.cwd()
app_root = project_root / "apps" / "staff"

datas = [
    (str(project_root / "shared" / "config.json"), "shared"),
    (str(project_root / "shared" / "assets"), "shared/assets"),
    (str(project_root / "shared" / "data"), "shared/data"),
]

hiddenimports = []
for package_name in ("ia", "gui", "controllers"):
    hiddenimports += collect_submodules(package_name)

excludes = [
    "utils.transcripcionVosk",
    "utils.vosk_model_manager",
    "vosk",
    "pyaudio",
    "sounddevice",
]

a = Analysis(
    [str(app_root / "main.py")],
    pathex=[str(project_root), str(project_root / "shared"), str(app_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Inperia Staff",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(project_root / "shared" / "assets" / "inperia.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="Inperia Staff",
)
