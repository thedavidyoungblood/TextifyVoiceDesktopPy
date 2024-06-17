# main.spec

# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['C:\\Users\\lfmdsantos\\Desktop\\pyfiles'],
    binaries=[],
    datas=[
        ('C:\\Users\\lfmdsantos\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\whisper', 'whisper'),
        ('C:\\Users\\lfmdsantos\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\plyer', 'plyer')

    ],
    hiddenimports=['plyer.platforms','plyer'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)