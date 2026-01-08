from setuptools import setup, find_packages
import os

# 读取requirements.txt文件
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# 获取项目根目录
project_root = os.path.abspath(os.path.dirname(__file__))

# 获取tesseract目录的路径
tesseract_dir = os.path.join(project_root, 'tesseract')

# 收集tesseract目录下的所有文件
tesseract_files = []
if os.path.exists(tesseract_dir):
    for root, _, files in os.walk(tesseract_dir):
        for file in files:
            file_path = os.path.join(root, file)
            # 计算相对路径
            relative_path = os.path.relpath(file_path, project_root)
            tesseract_files.append(relative_path)

setup(
    name='autodoor-ocr',
    version='1.0.0',
    description='AutoDoor OCR 识别系统',
    author='AutoDoor Team',
    packages=find_packages(),
    install_requires=requirements,
    data_files=[
        ('tesseract', tesseract_files),
        ('voice', ['voice/alarm.mp3'])
    ],
    entry_points={
        'console_scripts': [
            'autodoor=autodoor:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)
