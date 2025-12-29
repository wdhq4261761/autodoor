# AutoDoor OCR 识别系统

一个自动化的OCR文字识别系统，用于监控屏幕特定区域并执行相应操作。

## 功能特性

- ✅ 直观的屏幕区域选择GUI
- ✅ 支持多显示器区域选择
- ✅ 可自定义OCR识别间隔（1-30秒）
- ✅ 支持自定义关键词列表
- ✅ 支持中英文识别切换（英文/简体中文/繁体中文）
- ✅ 自动化鼠标点击和键盘操作
- ✅ 可配置暂停时长（30-300秒）
- ✅ 实时状态显示和日志记录
- ✅ 日志文件输出（autodoor.log）
- ✅ 配置自动保存/加载
- ✅ 内置Tesseract OCR引擎支持
- ✅ Windows/macOS平台打包支持
- ✅ 自动检测和设置Tesseract路径
- ✅ 错误处理机制

## 安装要求

### 方法一：直接运行打包好的可执行文件（推荐）

#### Windows系统：
1. 从发布页面下载`autodoor-windows.zip`文件
2. 解压到任意目录
3. 运行`autodoor.exe`文件

#### macOS系统：
1. 从发布页面下载`autodoor-macos.zip`文件
2. 解压到任意目录
3. 运行`autodoor`可执行文件

### 方法二：从源码运行

#### 1. Python环境
- Python 3.8+ 版本

#### 2. 安装Python依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 3. Tesseract OCR引擎（可选）

系统会优先使用内置的Tesseract引擎，也可以使用外部安装的Tesseract：

##### Windows系统：
1. 下载Tesseract安装包：[Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
2. 安装时记住安装路径

##### Linux系统：
```bash
sudo apt-get install tesseract-ocr
```

##### macOS系统：
```bash
brew install tesseract
```

## 使用方法

### 从源码运行
```bash
python autodoor.py
```

### 从可执行文件运行
- Windows：双击`autodoor.exe`文件
- macOS：双击`autodoor`可执行文件

## 界面功能说明

### 基本设置标签页

1. **Tesseract配置**
   - 显示当前Tesseract路径
   - 可手动设置Tesseract路径

2. **时间间隔设置**
   - **识别间隔**：1-30秒，拖动滑块或直接输入数值
   - **暂停时长**：30-300秒，检测到关键词后的暂停时间

3. **关键词设置**
   - 输入多个关键词，用英文逗号分隔
   - 支持实时应用和恢复默认设置

4. **语言设置**
   - 选择OCR识别语言：英文、简体中文、繁体中文

### 高级设置标签页

1. **坐标轴选取**
   - **区域中心**：点击选择区域的中心位置
   - **自定义坐标**：设置相对于选择区域左上角的自定义坐标

2. **键位自定义**
   - 选择检测到关键词后自动按下的按键
   - 支持预览按键效果和恢复默认设置

### 日志标签页

- 显示程序运行的实时日志
- 包含时间戳和详细的操作记录
- 支持清除日志

### 控制按钮

- **选择区域**：开始选择要监控的屏幕区域
- **开始监控**：开始OCR识别和监控
- **停止监控**：停止监控
- **退出程序**：退出应用

## 操作流程

1. 运行程序
2. 点击"选择区域"按钮，拖动鼠标选择要监控的屏幕区域
3. 根据需要调整设置：
   - 设置识别间隔和暂停时长
   - 输入自定义关键词
   - 选择识别语言
   - 设置点击模式和按键
4. 点击"开始监控"按钮开始OCR识别
5. 当检测到关键词时，系统会自动执行以下操作：
   - 点击指定位置（区域中心或自定义坐标）
   - 等待0.5秒后按下指定按键
   - 暂停设定的时长后继续监控
6. 点击"停止监控"按钮可停止识别

## 配置文件说明

程序会自动生成和加载配置文件`autodoor_config.json`，包含以下配置项：

- `tesseract_path`：Tesseract OCR引擎路径
- `ocr_interval`：OCR识别间隔（秒）
- `pause_duration`：暂停时长（秒）
- `selected_region`：选择的监控区域坐标
- `custom_key`：自定义按键
- `custom_keywords`：自定义关键词列表
- `ocr_language`：OCR识别语言

## 日志文件

程序会生成日志文件`autodoor.log`，包含：
- 程序启动和退出记录
- 配置加载和保存记录
- Tesseract检测结果
- OCR识别结果
- 操作执行记录
- 错误和异常信息

## 打包说明

### Windows平台打包
使用批处理脚本进行打包：
```cmd
./build_windows.bat
```

### macOS平台打包
使用Shell脚本进行打包：
```bash
./build_mac.sh
```

打包后的可执行文件位于`dist/autodoor/`目录下，包含所有必要的依赖文件和内置的Tesseract引擎。

## 注意事项

1. 选择的监控区域应包含清晰可见的文字
2. 运行脚本时请确保目标区域保持可见
3. Windows系统可能需要管理员权限才能正常模拟鼠标和键盘操作
4. macOS系统可能需要在"安全性与隐私"中允许程序控制电脑
5. 程序会自动检测和使用内置的Tesseract引擎，无需额外安装

## 故障排除

### 问题：Tesseract未检测到
- 检查配置文件中的Tesseract路径是否正确
- 程序会自动尝试使用内置的Tesseract引擎

### 问题：OCR识别结果为空
- 检查选择的区域是否包含清晰的文字
- 尝试调整选择区域大小
- 尝试切换识别语言

### 问题：无法模拟鼠标/键盘操作
- Windows：尝试以管理员身份运行程序
- macOS：检查"安全性与隐私"设置，允许程序控制电脑
- 检查是否有其他软件阻止了自动化操作

### 问题：程序崩溃
- 检查Python版本是否符合要求（3.8+）
- 查看日志文件`autodoor.log`中的错误信息
- 重新安装依赖包：`pip install -r requirements.txt`

## 开发说明

### 项目结构

```
autodoor/
├── autodoor.py          # 主程序文件
├── autodoor_config.json # 配置文件
├── autodoor.log         # 日志文件
├── autodoor.spec        # PyInstaller配置文件
├── build_windows.bat    # Windows打包脚本
├── build_mac.sh         # macOS打包脚本
├── requirements.txt     # Python依赖
├── README.md            # 说明文档
└── tesseract/           # 内置Tesseract引擎目录
    └── ...
```

### 依赖包

- pyautogui >= 0.9.54
- pytesseract >= 0.3.10
- Pillow >= 10.0.0
- opencv-python >= 4.8.0
- numpy >= 1.24.0
- screeninfo >= 0.8.1
- pyinstaller (用于打包)

## 许可证

MIT License
