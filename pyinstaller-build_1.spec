# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path
import cffi

import streamlit

from PyInstaller.utils.hooks import copy_metadata
from PyInstaller.utils.hooks import collect_submodules


platform = sys.platform

if platform == 'win32':
    icon_path = 'src/science_parser/desktop/st_app/static/logo.ico'
elif platform == 'darwin':
    icon_path = 'src/science_parser/desktop/st_app/static/logo.icns'
else:
    icon_path = 'src/science_parser/desktop/st_app/static/logo.png'

if platform == "win32":
    cffi_path = Path(cffi.__file__).parent
    cffi_binaries = []
    if cffi_path.exists():
        for pyd in cffi_path.glob('_cffi_backend*.pyd'):
            cffi_binaries.append((str(pyd), 'cffi'))

    win_hiddenimports = [
        'webview.platforms.winforms',
        'cffi',
        '_cffi_backend',
        'cffi.api',
        'cffi.lock',
        'cffi.cparser',
        'cffi.model',
        'pythonnet',
        'clr',
        'clr_loader',
        'clr_loader.ffi',
        'clr_loader.hostfxr',
        'clr_loader.netfx',
        'webview.platforms.edgechromium',  
        'python-certifi-win32'
    ]
    binaries = cffi_binaries
else:
    win_hiddenimports = ['webview.platforms.gtk']
    binaries = []

block_cipher = None

sys.path.insert(0, str(Path(SPECPATH) / 'src'))
all_science_parser_modules = collect_submodules('science_parser')

metadatas = [] 
metadatas += copy_metadata('streamlit')
metadatas += copy_metadata('pywebview')
streamlit_static_path = os.path.dirname(streamlit.__file__) # os.path.join(os.path.dirname(streamlit.__file__), 'static')

datas = [
        # (источник, куда положить внутри пакета)
        # ('src/science_parser/core/licenses/licenses.json', 'science_parser/core/licenses'),
        ('src/science_parser', 'science_parser'),
        (streamlit_static_path, 'streamlit')
    ]

a = Analysis(
    ['src/science_parser/desktop/main.py'],
    pathex=['src'],
    binaries=binaries,
    datas= datas + metadatas,
    hiddenimports=[
        'webview',
        'webview.guilib',
        'webview.platforms',
        'webview.platforms.qt',
        'webview.platforms.gtk',
        'streamlit',
        'streamlit.web',
        'streamlit.web.cli',
        'streamlit.runtime',
        'streamlit.runtime.scriptrunner',
        'streamlit.components.v1',
        'streamlit.elements',
        'tornado',                  
        'watchdog',                
        'altair',                
        'pandas', 
        'jmespath',
        'yarl',
        'tenacity',
        'filetype',
        'science_parser',
        'science_parser.agregators',
        'science_parser.agregators.crossref',
        'science_parser.core',
        'science_parser.core.licenses',
        'science_parser.desktop',
        'science_parser.desktop.utils',
        'science_parser.desktop.st_app',
        'pip-system-certs',
        'certifi',
        'truststore'
    ] + win_hiddenimports + all_science_parser_modules,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ScienceIndexer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=(platform != 'win32'),
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,             
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,   
)

#coll = COLLECT(
#    exe,
#    a.binaries,
#    a.zipfiles,
#    a.datas,
#    strip=False,
#    upx=True,
#    upx_exclude=[],
#    name='ScienceIndexer',
#)