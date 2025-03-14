# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('D:/vscode/_qgis_bundled_apps/flowbot_v4_qgis/resources', 'resources')],
    hiddenimports=['PyQt5.QtPositioning', 'PyQt5.QtPrintSupport', 'PyQt5.QtSql', 'PyQt5.QtNetwork', 'PyQt5.QtXml', 'PyQt5.sip', 'PyQt5.Qsci', 'PyQt5.QtMultimedia', 'PyQt5.QtXml', 'PyQt5.QtSerialPort'],
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
    [],
    exclude_binaries=True,
    name='Flowbot v4.2.1 Beta',
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
    icon=['D:\\vscode\\_qgis_bundled_apps\\flowbot_v4_qgis\\resources\\Flowbot.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Flowbot v4.2.1 Beta',
)
