# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 获取项目根目录 - 修复PyInstaller执行时__file__未定义的问题
import os
import sys
project_root = os.path.abspath('.')

# 收集tesseract目录下的必要文件（排除训练工具和文档）
tesseract_files = []
tesseract_dir = os.path.join(project_root, 'tesseract')
if os.path.exists(tesseract_dir):
    for root, _, files in os.walk(tesseract_dir):
        # 排除训练工具和文档
        # 对于Windows，保留tesseract.exe，排除其他.exe文件
        # 对于macOS/Linux，保留tesseract可执行文件
        for file in files:
            file_path = os.path.join(root, file)
            dest_dir = os.path.join('tesseract', os.path.relpath(root, tesseract_dir))
            
            # 保留主要的tesseract可执行文件，无论平台
            if (file == 'tesseract' or file == 'tesseract.exe'):
                tesseract_files.append((file_path, dest_dir))
                continue
            # 排除其他.exe文件（Windows训练工具）
            if file.endswith('.exe'):
                continue
            # 排除HTML文档
            if file.endswith('.html'):
                continue
            # 排除不必要的配置文件
            if root.endswith('tessdata/configs') or root.endswith('tessdata/tessconfigs'):
                continue
            
            tesseract_files.append((file_path, dest_dir))

# 配置文件
data_files = [
    (os.path.join(project_root, 'autodoor_config.json'), '.'),
] + tesseract_files

a = Analysis(
    ['autodoor.py'],
    pathex=[project_root],
    binaries=[],
    datas=data_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},

    runtime_hooks=[],
    excludes=[
        # 大型深度学习框架
        'torch', 'tensorflow', 'keras', 'scipy', 'pandas', 'matplotlib',
        'sklearn', 'xgboost', 'lightgbm', 'catboost', 'seaborn',
        'statsmodels', 'plotly', 'bokeh', 'networkx', 'nltk',
        'spacy', 'transformers', 'torchvision', 'torchaudio', 'onnx',
        'onnxruntime', 'jax', 'jaxlib', 'timm', 'diffusers', 'peft',
        'gradio', 'streamlit', 'dash',
        
        # Web框架和网络库
        'flask', 'django', 'fastapi', 'uvicorn', 'gunicorn',
        'requests', 'urllib3', 'beautifulsoup4', 'selenium', 'webdriver_manager',
        
        # GUI库
        'pyqt5', 'pyside6', 'wxpython', 'tkinterdnd2',
        
        # PIL扩展
        'pillow_heif', 'PIL._imagingtk', 'PIL._tkinter_finder', 'PIL.ImageQt', 'PIL.ImageTk',
        
        # 完全排除OpenCV
        'cv2',
        
        # 完全排除NumPy
        'numpy',
        
        # NumPy扩展
        'numpy.testing', 'numpy.f2py', 'numpy.distutils',
        
        # 其他不必要的库
        'pkg_resources',
        'pycparser', 'cffi', 'six',
        'platformdirs', 'pyparsing', 'colorama', 'chardet',
        'idna', 'certifi', 'charset_normalizer'
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
    name='autodoor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='',  # 如果有图标文件，可以在这里设置
)

import platform
if platform.system() == 'Darwin':
    # macOS平台：创建.app应用程序包
    app = BUNDLE(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        name='AutoDoor.app',
        icon='',  # 如果有图标文件，可以在这里设置
        bundle_identifier=None,
        info_plist={
            'CFBundleName': 'AutoDoor',
            'CFBundleDisplayName': 'AutoDoor OCR',
            'CFBundleIdentifier': 'com.autodoor.ocr',
            'CFBundleVersion': '1.0',
            'CFBundleShortVersionString': '1.0',
            'NSHighResolutionCapable': True,
        },
    )
else:
    # Windows/Linux平台：使用COLLECT创建目录结构
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='autodoor',
    )
