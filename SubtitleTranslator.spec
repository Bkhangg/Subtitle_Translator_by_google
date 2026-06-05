# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

a = Analysis(
    ['subtitle_translator_gui.py'],
    pathex=[],
    binaries=[],
    datas=collect_data_files('googletrans') + collect_data_files('openai') + collect_data_files('httpx'),
    hiddenimports=[
        'Mux_Subtitle', 'Subtitle_Translator',
        'googletrans', 'googletrans.client', 'googletrans.gtoken', 'googletrans.models', 'googletrans.constants',
        'httpx', 'httpcore', 'h2', 'sniffio', 'certifi', 'charset_normalizer',
        'openai', 'openai._client', 'openai._base_client', 'openai._streaming',
        'pydantic', 'anyio', 'anyio._backends._asyncio',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'pandas', 'scipy', 'PIL', 'cv2',
        'tensorflow', 'torch', 'notebook', 'jupyter', 'ipython',
        'openai.helpers', 'openai.lib.azure', 'openai.cli',
        'setuptools._vendor', 'setuptools.extern',
        'packaging', 'pkg_resources',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SubtitleTranslator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
