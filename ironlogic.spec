# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec: сборка IronLogic.app (macOS).

Сборка: .venv/bin/pyinstaller ironlogic.spec --noconfirm
Результат: dist/IronLogic.app
"""

from PyInstaller.utils.hooks import collect_submodules

datas = [
    ("examples", "examples"),
    ("ironlogic/template_bot.py", "."),
    ("ironlogic_api.py", "."),
]

hiddenimports = collect_submodules("ironlogic")

a = Analysis(
    ["ironlogic/app/main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "PySide6.QtMultimedia"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="IronLogic",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="IronLogic",
)
app = BUNDLE(
    coll,
    name="IronLogic.app",
    icon=None,
    bundle_identifier="ru.ironlogic.game",
    info_plist={
        "CFBundleName": "IronLogic",
        "CFBundleDisplayName": "IronLogic — Битва интеллектов",
        "NSHighResolutionCapable": True,
    },
)
