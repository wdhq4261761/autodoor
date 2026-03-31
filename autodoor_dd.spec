# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import os
import sys
project_root = os.path.abspath('.')

tesseract_files = []
tesseract_dir = os.path.join(project_root, 'tesseract')

if os.path.exists(tesseract_dir):
    for root, _, files in os.walk(tesseract_dir):
        for file in files:
            file_path = os.path.join(root, file)
            dest_dir = os.path.join('tesseract', os.path.relpath(root, tesseract_dir))
            
            if (file == 'tesseract' or file == 'tesseract.exe'):
                tesseract_files.append((file_path, dest_dir))
                continue
            if file.endswith('.exe') and file != 'tesseract.exe':
                continue
            if file.endswith('.html'):
                continue
            if root.endswith('tessdata/configs') or root.endswith('tessdata/tessconfigs'):
                continue
            
            tesseract_files.append((file_path, dest_dir))
    print(f"Collected {len(tesseract_files)} tesseract files")

data_files = [
    (os.path.join(project_root, 'voice/alarm.mp3'), 'voice'),
    (os.path.join(project_root, 'voice/temp_reversed.mp3'), 'voice'),
    (os.path.join(project_root, 'icon/autodoor.ico'), 'icon'),
    (os.path.join(project_root, 'icon/autodoor.png'), 'icon'),
    (os.path.join(project_root, 'drivers/DD64.dll'), 'drivers'),
] + tesseract_files

binaries = []

a = Analysis(
    ['autodoor.py'],
    pathex=[project_root],
    binaries=binaries,
    datas=data_files,
    hiddenimports=[
        'core',
        'core.config',
        'core.controller',
        'core.events',
        'core.logging',
        'core.platform',
        'core.proxy',
        'core.threading',
        'core.utils',
        
        'ui',
        'ui.background_tab',
        'ui.basic_tab',
        'ui.bt_editor',
        'ui.bt_editor.canvas',
        'ui.bt_editor.connection',
        'ui.bt_editor.editor',
        'ui.bt_editor.palette',
        'ui.bt_editor.property',
        'ui.bt_editor.toolbar',
        'ui.bt_editor.undo_redo',
        'ui.home',
        'ui.image_tab',
        'ui.number_tab',
        'ui.ocr_tab',
        'ui.script_tab',
        'ui.theme',
        'ui.timed_tab',
        'ui.utils',
        'ui.widgets',
        
        'modules',
        'modules.alarm',
        'modules.background',
        'modules.behavior_tree',
        'modules.behavior_tree.blackboard',
        'modules.behavior_tree.context',
        'modules.behavior_tree.engine',
        'modules.behavior_tree.nodes',
        'modules.behavior_tree.serializer',
        'modules.bt_adapters',
        'modules.bt_adapters.action_adapters',
        'modules.bt_adapters.color_adapter',
        'modules.bt_adapters.image_adapter',
        'modules.bt_adapters.number_adapter',
        'modules.bt_adapters.ocr_adapter',
        'modules.bt_adapters.variable_adapter',
        'modules.color',
        'modules.image',
        'modules.input',
        'modules.number',
        'modules.ocr',
        'modules.persistence',
        'modules.persistence.auto_save',
        'modules.persistence.crash_recovery',
        'modules.persistence.data_version',
        'modules.persistence.file_recovery',
        'modules.recorder',
        'modules.script',
        'modules.timed',
        
        'input',
        'input.base',
        'input.controller',
        'input.dd_input',
        'input.pyautogui_input',
        'input.key_mapping',
        'input.keyboard',
        'input.permissions',
        
        'utils',
        'utils.image',
        'utils.keyboard',
        'utils.region',
        'utils.tesseract',
        'utils.version',
        
        'pygame',
        'pygame.mixer',
        'tkinter',
        'tkinter.ttk',
        'PIL',
        'PIL.Image',
        'PIL.ImageGrab',
        'pytesseract',
        'screeninfo',
        'screeninfo.common',
        'pynput',
        'pynput.keyboard',
        'pynput.mouse',
        'pydub',
        'requests',
        'numpy',
        'numpy.core',
        'numpy.core.multiarray',
        'six',
        'imagehash',
        'cv2',
        
        'win32gui',
        'win32ui',
        'win32con',
        'win32api',
        'win32process',
        'pywintypes',
        'pythoncom',
        'ctypes',
    ],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=['hooks/hook_dd_input.py'],
    excludes=[
        'torch', 'tensorflow', 'keras', 'scipy', 'pandas', 'matplotlib',
        'sklearn', 'xgboost', 'lightgbm', 'catboost', 'seaborn',
        'statsmodels', 'plotly', 'bokeh', 'networkx', 'nltk',
        'spacy', 'transformers', 'torchvision', 'torchaudio', 'onnx',
        'onnxruntime', 'jax', 'jaxlib', 'timm', 'diffusers', 'peft',
        'gradio', 'streamlit', 'dash',
        
        'flask', 'django', 'fastapi', 'uvicorn', 'gunicorn',
        'beautifulsoup4', 'selenium', 'webdriver_manager',
        
        'pyqt5', 'pyside6', 'wxpython', 'tkinterdnd2',
        
        'pillow_heif', 'PIL._tkinter_finder', 'PIL.ImageQt',
        
        'numpy.testing', 'numpy.f2py', 'numpy.distutils',
        
        'pkg_resources',
        'pycparser', 'cffi',
        'platformdirs', 'pyparsing', 'colorama', 'chardet'
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
    name='autodoor_dd',
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
    icon=os.path.join(project_root, 'icon', 'autodoor.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='autodoor_dd',
)
