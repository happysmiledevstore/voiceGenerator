# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all data files needed by librosa (audio models, etc.)
librosa_datas = collect_data_files('librosa')
matplotlib_datas = collect_data_files('matplotlib')
scipy_datas = collect_data_files('scipy')

hidden_imports = [
    # librosa internals
    'librosa',
    'librosa.core',
    'librosa.feature',
    'librosa.effects',
    'librosa.util',
    'librosa.filters',
    'librosa.display',
    'librosa.beat',
    'librosa.onset',
    'librosa.decompose',
    'librosa.segment',
    'librosa.sequence',
    'numba',
    'numba.core',
    'llvmlite',
    'audioread',
    'soxr',
    'lazy_loader',
    'pooch',
    # scipy
    'scipy',
    'scipy.signal',
    'scipy.fft',
    'scipy.io',
    'scipy.io.wavfile',
    'scipy._lib.array_api_compat',
    'scipy._lib.array_api_compat.numpy',
    'scipy._lib.array_api_compat.numpy.fft',
    # sounddevice / soundfile
    'sounddevice',
    'soundfile',
    'cffi',
    # gTTS / pyttsx3
    'gtts',
    'gtts.tts',
    'gtts.lang',
    'pyttsx3',
    'pyttsx3.drivers',
    'pyttsx3.drivers.sapi5',
    'comtypes',
    'comtypes.client',
    # matplotlib
    'matplotlib',
    'matplotlib.backends.backend_qt5agg',
    'matplotlib.backends.backend_agg',
    # PyQt5
    'PyQt5',
    'PyQt5.QtWidgets',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.sip',
    # audio
    'pydub',
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=librosa_datas + matplotlib_datas + scipy_datas + [
        ('assets', 'assets'),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'test',
        '_pytest',
        'IPython',
        'jupyter',
        'notebook',
    ],
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
    name='VoiceGenerator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # no black terminal window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/app_icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VoiceGenerator',
)
