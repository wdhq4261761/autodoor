# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 获取项目根目录 - 修复PyInstaller执行时__file__未定义的问题
import os
import sys
project_root = os.path.abspath('.')

# 收集tesseract目录下的必要文件（只在项目自带tesseract存在时）
tesseract_files = []
tesseract_dir = os.path.join(project_root, 'tesseract')
import platform
# 当项目自带tesseract存在时，包含项目自带的tesseract
if os.path.exists(tesseract_dir) and platform.system() == 'Windows':
    # 只在Windows平台上包含项目自带的tesseract
    for root, _, files in os.walk(tesseract_dir):
        # 排除训练工具和文档
        for file in files:
            file_path = os.path.join(root, file)
            dest_dir = os.path.join('tesseract', os.path.relpath(root, tesseract_dir))
            
            # 保留主要的tesseract可执行文件
            if (file == 'tesseract' or file == 'tesseract.exe'):
                tesseract_files.append((file_path, dest_dir))
                continue
            # 排除其他.exe文件（Windows训练工具）
            if file.endswith('.exe') and file != 'tesseract.exe':
                continue
            # 排除HTML文档
            if file.endswith('.html'):
                continue
            # 排除不必要的配置文件
            if root.endswith('tessdata/configs') or root.endswith('tessdata/tessconfigs'):
                continue
            
            tesseract_files.append((file_path, dest_dir))
    print(f"Collected {len(tesseract_files)} tesseract files for Windows")

# 配置文件 - 移除本地配置文件，使用应用程序生成的默认配置
data_files = [
    (os.path.join(project_root, 'voice/alarm.mp3'), 'voice'),
    (os.path.join(project_root, 'voice/temp_reversed.mp3'), 'voice'),
] + tesseract_files

# 检查平台并添加必要的二进制文件
binaries = []
import platform
if platform.system() == 'Darwin':
    # 对于macOS，添加cliclick二进制文件
    # 检查不同架构下的cliclick路径
    cliclick_paths = ['/usr/local/bin/cliclick', '/opt/homebrew/bin/cliclick']
    for cliclick_path in cliclick_paths:
        if os.path.exists(cliclick_path):
            binaries.append((cliclick_path, '.'))
            break
    # 对于macOS，添加tesseract二进制文件
    # 检查不同架构下的tesseract路径
    tesseract_paths = ['/usr/local/bin/tesseract', '/opt/homebrew/bin/tesseract']
    for tesseract_path in tesseract_paths:
        if os.path.exists(tesseract_path):
            binaries.append((tesseract_path, 'tesseract'))
            break
# 对于Windows平台，直接使用项目自带的tesseract文件夹
if platform.system() == 'Windows':
    # 检查项目自带的tesseract文件夹
    tesseract_dir = os.path.join(project_root, 'tesseract')
    if os.path.exists(tesseract_dir):
        print(f"Using project-provided tesseract directory: {tesseract_dir}")

# 对于macOS平台，添加语言包
try:
    if platform.system() == 'Darwin':
        import subprocess
        import os
        # 查找tessdata目录路径
        result = subprocess.run(['tesseract', '--list-langs'], capture_output=True, text=True)
        tessdata_path = None
        if result.returncode == 0:
            import re
            match = re.search(r'\/.*tessdata', result.stdout)
            if match:
                tessdata_path = match.group(0)
        # 尝试默认路径
        if not tessdata_path:
            tessdata_paths = ['/usr/local/share/tessdata', '/opt/homebrew/share/tessdata']
            for path in tessdata_paths:
                if os.path.exists(path):
                    tessdata_path = path
                    break
        # 添加语言包
        if tessdata_path and os.path.exists(tessdata_path):
            import glob
            lang_files = glob.glob(os.path.join(tessdata_path, '*.traineddata'))
            for lang_file in lang_files:
                lang_filename = os.path.basename(lang_file)
                data_files.append((lang_file, os.path.join('tesseract', 'tessdata')))
except Exception as e:
    pass

a = Analysis(
    ['autodoor.py'],
    pathex=[project_root],
    binaries=binaries,
    datas=data_files,
    hiddenimports=[
        # 核心模块
        'core',
        'core.config',
        'core.controller',
        'core.events',
        'core.logging',
        'core.platform',
        'core.proxy',
        'core.threading',
        'core.utils',
        
        # UI模块
        'ui',
        'ui.basic_tab',
        'ui.builder',
        'ui.home',
        'ui.image_tab',
        'ui.number_tab',
        'ui.ocr_tab',
        'ui.script_tab',
        'ui.styles',
        'ui.timed_tab',
        'ui.utils',
        'ui.validators',
        
        # 功能模块
        'modules',
        'modules.alarm',
        'modules.color',
        'modules.image',
        'modules.input',
        'modules.number',
        'modules.ocr',
        'modules.recorder',
        'modules.script',
        'modules.timed',
        
        # 输入控制模块
        'input',
        'input.controller',
        'input.keyboard',
        'input.permissions',
        
        # 工具模块
        'utils',
        'utils.image',
        'utils.keyboard',
        'utils.region',
        'utils.tesseract',
        'utils.version',
        
        # 第三方库
        'pygame',
        'pygame.mixer',
        'pygame.mixer.music',
        'pygame._sdl2.mixer',
        'tkinter',
        'tkinter.ttk',
        'PIL',
        'PIL.Image',
        'PIL.ImageGrab',
        'pytesseract',
        'screeninfo',
        'screeninfo.common',
        'screeninfo.monitors',
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
    ],
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
        'beautifulsoup4', 'selenium', 'webdriver_manager',
        
        # GUI库
        'pyqt5', 'pyside6', 'wxpython', 'tkinterdnd2',
        
        # PIL扩展
        'pillow_heif', 'PIL._tkinter_finder', 'PIL.ImageQt',
        
        # NumPy扩展（保留核心numpy）
        'numpy.testing', 'numpy.f2py', 'numpy.distutils',
        
        # 其他不必要的库
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
        bundle_identifier='com.autodoor.ocr',
        info_plist={
            'CFBundleName': 'AutoDoor',
            'CFBundleDisplayName': 'AutoDoor OCR',
            'CFBundleIdentifier': 'com.autodoor.ocr',
            'CFBundleVersion': '1.0',
            'CFBundleShortVersionString': '1.0',
            'NSHighResolutionCapable': True,
            'NSAppleEventsUsageDescription': 'AutoDoor需要访问系统事件以执行自动化操作',
            'NSMicrophoneUsageDescription': 'AutoDoor可能需要使用音频功能进行报警',
            'NSCameraUsageDescription': 'AutoDoor可能需要访问屏幕截图功能',
            'NSScreenCaptureUsageDescription': 'AutoDoor需要访问屏幕截图功能以进行OCR识别和颜色识别',
            'NSAccessibilityUsageDescription': 'AutoDoor需要访问辅助功能以执行自动化操作',
            'LSBackgroundOnly': False,
            'LSMinimumSystemVersion': '10.14',
        },
        # 确保tesseract有执行权限
        strip=False,
        upx=False,  # 禁用UPX压缩，避免macOS安全问题
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
