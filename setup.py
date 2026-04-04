from setuptools import setup, find_packages
import os
import re

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

project_root = os.path.abspath(os.path.dirname(__file__))

def get_version():
    """从autodoor.py中读取版本号"""
    version_file = os.path.join(project_root, 'autodoor.py')
    with open(version_file, encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', content)
    if match:
        return match.group(1)
    return '0.0.0'

version = get_version()

tesseract_dir = os.path.join(project_root, 'tesseract')

tesseract_files = []
if os.path.exists(tesseract_dir):
    for root, _, files in os.walk(tesseract_dir):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, project_root)
            tesseract_files.append(relative_path)

voice_files = []
voice_dir = os.path.join(project_root, 'voice')
if os.path.exists(voice_dir):
    for file in os.listdir(voice_dir):
        if file.endswith('.mp3'):
            voice_files.append(os.path.join('voice', file))

setup(
    name='autodoor-ocr',
    version=version,
    description='AutoDoor OCR 识别系统 - 模块化架构版本',
    author='AutoDoor Team',
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=requirements,
    package_data={
        '': ['*.mp3'],
    },
    data_files=[
        ('tesseract', tesseract_files) if tesseract_files else (),
        ('voice', [os.path.join('voice', f) for f in os.listdir('voice') if f.endswith('.mp3')]) if os.path.exists('voice') else (),
    ],
    entry_points={
        'console_scripts': [
            'autodoor=autodoor:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Microsoft :: Windows',
    ],
    python_requires='>=3.10',
)
