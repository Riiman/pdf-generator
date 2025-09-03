# PyInstaller spec for LetterGen (Windows)
# Usage on Windows (from project root):
#   pyinstaller lettergen.spec

import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

app_name = 'LetterGen'

hiddenimports = collect_submodules('html2docx') + collect_submodules('jinja2')
datas = []

# Bundle assets (optional)
datas += collect_data_files('lettergen', include_py_files=False)
datas += [(os.path.join('assets', 'template_letter.html'), 'assets')]

# Bundle wkhtmltopdf.exe if placed in third_party/wkhtmltopdf/
if os.path.exists('third_party/wkhtmltopdf/wkhtmltopdf.exe'):
    datas += [('third_party/wkhtmltopdf/wkhtmltopdf.exe', 'third_party/wkhtmltopdf')]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
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
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)
