# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — skymeshx gcs (SkyMeshX ground control station).

Full graphical build: PySide6 + QtQuick + QtWebEngine +
the entire QML tree under tools/ui/qml/ (including 3D mesh assets).

Build with:
    pyinstaller tools/installer/specs/skymeshx_gcs.spec --noconfirm
Output:
    dist/SkyMeshXGCS/skymeshx gcs.exe   (+ _internal/ folder)

Notes
-----
- One-folder mode is intentional: one-file would re-extract ~280 MB
  to %TEMP% on every launch (slow and flaky on locked-down machines).
- console=False → no flickering cmd.exe window when launching from
  the Start Menu shortcut.
- QML files are bundled under ``tools/ui/qml/`` to mirror the source
  layout; ``tools/ui/app.py:_resolve_qml_root()`` understands both
  frozen and source layouts.
- ``optimize=1`` strips ``assert`` statements while keeping ``__doc__`` strings
  from all bundled .pyc files. Casual code-protection only; bytecode
  can still be decompiled with public tools.
"""

import os
import sys
from pathlib import Path

# Apply the Python 3.10.0-3.10.3 dis._get_const_info workaround
# (bpo-45757) before PyInstaller starts scanning bytecode.
sys.path.insert(0, str(Path(SPECPATH).resolve()))
import _dis_patch  # noqa: F401
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

PROJECT_ROOT = Path(SPECPATH).resolve().parent.parent.parent
ASSETS_DIR = PROJECT_ROOT / "tools" / "installer" / "assets"
QML_ROOT = PROJECT_ROOT / "tools" / "ui" / "qml"

block_cipher = None


# ── Data: QML + 3D assets ────────────────────────────────────────────
def _collect_qml() -> list[tuple[str, str]]:
    """Mirror tools/ui/qml/** into the bundle, preserving directory layout."""
    out: list[tuple[str, str]] = []
    for path in QML_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix == ".bak":
            continue
        rel_dir = path.parent.relative_to(PROJECT_ROOT)
        out.append((str(path), str(rel_dir).replace(os.sep, "/")))
    return out


qml_datas = _collect_qml()
print(f"[gcs.spec] bundling {len(qml_datas)} QML / asset files")


# ── Hidden imports ───────────────────────────────────────────────────
hidden = (
    collect_submodules("skymeshx")
    + collect_submodules("tools.ui")
    + collect_submodules("pymavlink")
    + [
        "serial",
        "serial.tools.list_ports",
        # PySide6 modules - WebEngine bits PyInstaller occasionally misses
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineQuick",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtQuick3D",
        "PySide6.QtPositioning",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtQml",
        "PySide6.QtQuick",
    ]
)


a = Analysis(
    [str(PROJECT_ROOT / "tools" / "ui" / "__main__.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=qml_datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PyQt5",
        "PyQt6",
        "PySide2",
        "tkinter",
        "matplotlib",
        "scipy",
        "pandas",
        "IPython",
        "test",
        "unittest",
        # See skymeshx_cli.spec for the rationale.
        "lxml",
        "cv2",
        "google",
        "grpc",
        "cryptography",
        "pkg_resources",
        "setuptools._vendor",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    optimize=1,  # -O: strip asserts, keep docstrings for legacy widgets
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="skymeshx",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # GUI app — no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ASSETS_DIR / "skymeshx_icon.ico"),
    version=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="SkyMeshXGCS",
)
