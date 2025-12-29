# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 获取项目根目录 - 修复PyInstaller执行时__file__未定义的问题
import os
import sys
project_root = os.path.abspath('.')

# 收集tesseract目录下的所有文件
tesseract_files = []
tesseract_dir = os.path.join(project_root, 'tesseract')
if os.path.exists(tesseract_dir):
    for root, _, files in os.walk(tesseract_dir):
        for file in files:
            file_path = os.path.join(root, file)
            dest_dir = os.path.join('tesseract', os.path.relpath(root, tesseract_dir))
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
    excludes=[],
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
