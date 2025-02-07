# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['vbapp.py'],
    pathex=[],
    binaries=[],
    datas=[('client_secret_888683576335-ea5h2tct2s2eclkjnqt3spe06ro2afba.apps.googleusercontent.com.json', '.'), ('clientes.txt', '.'), ('ZIP.ico', '.')],
    hiddenimports=['babel.numbers'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='vbapp',
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
