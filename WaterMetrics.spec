# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

# Добавляем ассеты и xlsx файлы в сборку
added_files = [
    ('assets', 'assets'),
]
for f in ['Душистая 45+.xlsx', 'душ 45 аркус.xlsx']:
    if os.path.exists(f):
        added_files.append((f, '.'))

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtOpenGL',
        'PySide6.QtOpenGLWidgets',
        'PySide6.QtSvg',
        'shiboken6',
        'OpenGL',
        'OpenGL.GL',
        'OpenGL.platform',
        'OpenGL.platform.win32',
        'OpenGL.arrays',
        'OpenGL.arrays.ctypesarrays',
        'OpenGL.arrays.numpymodule',
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.utils',
        'openpyxl.formatting',
        'openpyxl.comments',
        'et_xmlfile',
        'xml',
        'xml.etree',
        'xml.etree.ElementTree',
        'xml.parsers.expat',
        'numpy',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFilter',
        'config',
        'models',
        'core',
        'core.calculator',
        'core.excel_parser',
        'core.excel_validator',
        'services',
        'services.history_service',
        'services.i18n_service',
        'services.settings_service',
        'services.updater_service',
        'ui',
        'ui.about_page',
        'ui.dashboard_page',
        'ui.norms_page',
        'ui.logs_page',
        'ui.test_tab',
        'ui.main_window',
        'ui.styles',
        'ui.components',
        'ui.components.control_panel',
        'ui.components.glass_icon',
        'ui.components.interactive',
        'ui.components.onboarding_overlay',
        'ui.components.progress_overlay',
        'ui.components.toast',
        'ui.dialogs',
        'ui.dialogs.command_palette',
        'ui.dialogs.replacement_dialog',
        'ui.dialogs.update_dialog',
        'ui.dialogs.welcome_dialog',
        'ui.gl',
        'ui.gl.ocean_widget',
        'ui.gl.particle_system',
        'ui.gl.shaders',
        'ui.gl.wave_mesh_widget',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'pydoc'],
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
    name='WaterMetrics',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
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
    name='WaterMetrics',
)
