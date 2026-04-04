# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_dynamic_libs


project_root = Path.cwd()
app_root = project_root / "apps" / "cliente"

datas = [
    (str(project_root / "shared" / "config.json"), "shared"),
    (str(project_root / "shared" / "assets"), "shared/assets"),
    (str(project_root / "shared" / "data"), "shared/data"),
    (str(project_root / "shared" / "utils" / "vosk-es" / "big"), "shared/utils/vosk-es/big"),
]

hiddenimports = []

excludes = [
    "ia",
    "ollama_service",
]

binaries = collect_dynamic_libs("vosk")

a = Analysis(
    [str(app_root / "main.py")],
    pathex=[str(project_root), str(project_root / "shared"), str(app_root)],
    binaries=binaries,
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
    name="Inperia Cliente",
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
    name="Inperia Cliente",
)
