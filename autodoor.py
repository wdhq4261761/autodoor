import tkinter as tk
from tkinter import messagebox, ttk
import pyautogui
import pytesseract
from PIL import Image, ImageGrab
import threading
import time
import datetime
import subprocess
import os
import json
from collections import deque

# 尝试导入screeninfo库，如果不可用则提供安装提示
try:
    import screeninfo
except ImportError:
    screeninfo = None

class AutoDoorOCR:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AutoDoor OCR 识别系统")
        self.root.geometry("800x700") 
        self.root.resizable(True, True) 
        self.root.minsize(750, 650)
        
        # 配置参数
        self.ocr_interval = 5
        self.pause_duration = 180
        self.click_delay = 0.5
        self.custom_key = "equal"
        
        # 关键词配置
        self.custom_keywords = ["men", "door"]
        self.ocr_language = "eng"
        
        # 坐标轴参数
        self.click_x = 0 
        self.click_y = 0
        self.click_mode = "center"
        
        # 状态变量
        self.selected_region = None
        self.is_running = False
        self.is_paused = False
        self.is_selecting = False
        self.last_trigger_time = 0
        
        # 配置文件路径
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "autodoor_config.json")
        
        # 日志文件路径
        self.log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "autodoor.log")
        
        # 线程控制
        self.ocr_thread = None
        self.timed_threads = []
        self.number_threads = []
        
        # 事件队列
        self.event_queue = deque()
        self.event_lock = threading.Lock()
        self.event_cond = threading.Condition(self.event_lock)
        self.is_event_running = False
        self.event_thread = None
        
        # 定时功能相关
        self.timed_enabled_var = None
        self.timed_groups = []
        
        # 数字识别相关
        self.number_enabled_var = None
        self.number_regions = []
        self.current_number_region = None
        
        # 初始化Tesseract相关变量
        self.tesseract_path = ""
        self.tesseract_available = False
        
        # 先创建界面元素，确保所有UI变量都被初始化
        self.create_widgets()
        
        # 加载配置（包括Tesseract路径）
        self.load_config()
        
        # 如果配置中没有Tesseract路径，使用项目自带的tesseract
        config_updated = False
        if not self.tesseract_path:
            self.tesseract_path = self.get_default_tesseract_path()
            config_updated = True
        
        # 执行Tesseract引擎的存在性检测和可用性验证
        self.tesseract_available = self.check_tesseract_availability()
        
        # 如果使用了默认Tesseract路径，将其保存到配置文件
        if config_updated:
            self.save_config()
        
        # 检查tesseract可用性
        if not self.tesseract_available:
            messagebox.showwarning("警告", "未检测到Tesseract OCR引擎，请先安装并配置环境变量！")
            self.status_var.set("Tesseract未安装")
        
        # 设置配置监听器
        self.setup_config_listeners()
        
        # 启动事件处理线程
        self.start_event_thread()
    

    
    def get_default_tesseract_path(self):
        """获取默认的Tesseract路径，使用项目自带的tesseract
        支持Windows和Mac平台，同时支持打包后的环境
        """
        import platform
        import sys
        
        # 获取程序运行目录
        if hasattr(sys, '_MEIPASS'):
            # 打包后的环境，使用_MEIPASS获取运行目录
            app_root = sys._MEIPASS
        else:
            # 开发环境，使用当前文件所在目录
            app_root = os.path.dirname(os.path.abspath(__file__))
        
        # 根据操作系统选择不同的tesseract路径
        if platform.system() == "Windows":
            # Windows平台
            tesseract_path = os.path.join(app_root, "tesseract", "tesseract.exe")
        elif platform.system() == "Darwin":
            # macOS平台
            tesseract_path = os.path.join(app_root, "tesseract", "tesseract")
        else:
            # 其他平台，返回空
            tesseract_path = ""
        
        self.log_message(f"默认Tesseract路径: {tesseract_path}")
        return tesseract_path
    
    def check_tesseract_availability(self):
        """检查Tesseract OCR是否可用
        包括：路径有效性验证、版本兼容性检查、基础功能测试
        """
        if not self.tesseract_path:
            self.log_message("Tesseract路径未配置")
            return False
        
        # 1. 路径有效性验证
        if not os.path.exists(self.tesseract_path):
            self.log_message(f"Tesseract路径不存在: {self.tesseract_path}")
            return False
        
        if not os.path.isfile(self.tesseract_path):
            self.log_message(f"Tesseract路径不是文件: {self.tesseract_path}")
            return False
        
        import platform
        # 根据操作系统检查可执行文件格式
        if platform.system() == "Windows":
            if not self.tesseract_path.endswith("tesseract.exe"):
                self.log_message(f"Tesseract路径不是可执行文件: {self.tesseract_path}")
                return False
        elif platform.system() == "Darwin":  # macOS
            if not os.path.basename(self.tesseract_path) == "tesseract":
                self.log_message(f"Tesseract路径不是可执行文件: {self.tesseract_path}")
                return False
        # 其他平台不做严格检查
        
        try:
            # 2. 版本兼容性检查
            version_result = subprocess.run(
                [self.tesseract_path, "--version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            
            # 解析版本信息
            version_output = version_result.stdout.strip()
            if "tesseract" in version_output.lower():
                # 提取版本号，格式类似 "tesseract 5.3.3"
                version_parts = version_output.split()
                if len(version_parts) >= 2:
                    version_str = version_parts[1]
                    self.log_message(f"检测到Tesseract版本: {version_str}")
                    
                    # 检查主要版本号，确保至少是4.x
                    try:
                        major_version = int(version_str.split('.')[0])
                        if major_version < 4:
                            self.log_message(f"Tesseract版本太旧 ({version_str})，建议使用4.x或更高版本")
                            return False
                    except (ValueError, IndexError):
                        self.log_message(f"无法解析Tesseract版本: {version_str}")
                        # 继续执行，不因为版本解析失败而直接返回False
            
            # 3. 基础功能测试
            # 配置pytesseract使用找到的路径
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
            
            # 创建一个简单的测试图像
            test_image = Image.new('RGB', (100, 30), color='white')
            test_image.save('test_tesseract.png')
            
            # 尝试执行OCR识别
            test_result = pytesseract.image_to_string('test_tesseract.png', lang='eng', timeout=5)
            
            # 清理测试文件
            if os.path.exists('test_tesseract.png'):
                os.remove('test_tesseract.png')
            
            # 配置界面中的路径变量
            if hasattr(self, 'tesseract_path_var'):
                self.tesseract_path_var.set(self.tesseract_path)
            
            self.log_message("Tesseract OCR引擎检测通过")
            return True
            
        except subprocess.TimeoutExpired:
            self.log_message(f"Tesseract命令执行超时: {self.tesseract_path}")
            return False
        except subprocess.CalledProcessError as e:
            self.log_message(f"Tesseract命令执行失败: {e}")
            return False
        except FileNotFoundError:
            self.log_message(f"Tesseract可执行文件未找到: {self.tesseract_path}")
            return False
        except pytesseract.TesseractError as e:
            self.log_message(f"Tesseract OCR测试失败: {e}")
            return False
        except Exception as e:
            self.log_message(f"Tesseract检测发生未知错误: {str(e)}")
            return False
        
    def create_widgets(self):
        # 设置全局样式
        style = ttk.Style()
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabel", background="#f0f0f0", font=("Arial", 10))
        style.configure("Header.TLabel", font=("Arial", 12, "bold"))
        style.configure("TButton", padding=5)
        
        # 主容器
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部状态栏
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 状态显示
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, style="Header.TLabel", foreground="green")
        status_label.pack(side=tk.LEFT)
        
        # 区域信息已移至文字识别标签页内，此处不再显示
        self.region_var = tk.StringVar(value="未选择区域")
        
        # 主内容区域 - 使用笔记本(tab)布局
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 文字识别标签页
        ocr_frame = ttk.Frame(notebook)
        notebook.add(ocr_frame, text="文字识别")
        self.create_ocr_tab(ocr_frame)
        
        # 定时功能标签页
        timed_frame = ttk.Frame(notebook)
        notebook.add(timed_frame, text="定时功能")
        self.create_timed_tab(timed_frame)
        
        # 数字识别标签页
        number_frame = ttk.Frame(notebook)
        notebook.add(number_frame, text="数字识别")
        self.create_number_tab(number_frame)
        
        # 基本设置标签页
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="基本设置")
        self.create_basic_tab(basic_frame)
        
        # 日志标签页
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="日志")
        self.create_log_tab(log_frame)
        
        # 控制按钮区域
        control_frame = ttk.Frame(main_frame, padding="10 5 10 0")
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 退出按钮在右侧
        exit_btn = ttk.Button(control_frame, text="退出程序", command=self.exit_program)
        exit_btn.pack(side=tk.RIGHT)
    
    def create_ocr_tab(self, parent):
        """创建文字识别标签页"""
        ocr_frame = ttk.Frame(parent, padding="10")
        ocr_frame.pack(fill=tk.BOTH, expand=True)
        
        # 区域选择
        region_frame = ttk.LabelFrame(ocr_frame, text="区域选择", padding="10")
        region_frame.pack(fill=tk.X, pady=(0, 10))
        
        region_btn = ttk.Button(region_frame, text="选择区域", command=self.start_region_selection)
        region_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        region_label = ttk.Label(region_frame, textvariable=self.region_var)
        region_label.pack(side=tk.LEFT)
        
        # 识别设置 - 第一行：识别间隔、暂停时长、按键设置
        setting_frame = ttk.LabelFrame(ocr_frame, text="识别设置", padding="10")
        setting_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 第一行：识别间隔、暂停时长、按键设置
        row1_frame = ttk.Frame(setting_frame)
        row1_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 识别间隔
        interval_frame = ttk.Frame(row1_frame)
        interval_frame.pack(side=tk.LEFT, padx=(0, 20))
        ocr_interval_label = ttk.Label(interval_frame, text="识别间隔(秒):")
        ocr_interval_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.ocr_interval_var = tk.IntVar(value=self.ocr_interval)
        ocr_interval_entry = ttk.Entry(interval_frame, textvariable=self.ocr_interval_var, width=15)
        ocr_interval_entry.pack(fill=tk.X)
        
        # 暂停时长
        pause_frame = ttk.Frame(row1_frame)
        pause_frame.pack(side=tk.LEFT, padx=(0, 20))
        pause_duration_label = ttk.Label(pause_frame, text="暂停时长(秒):")
        pause_duration_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.pause_duration_var = tk.IntVar(value=self.pause_duration)
        pause_duration_entry = ttk.Entry(pause_frame, textvariable=self.pause_duration_var, width=15)
        pause_duration_entry.pack(fill=tk.X)
        
        # 按键设置
        key_setting_frame = ttk.Frame(row1_frame)
        key_setting_frame.pack(side=tk.LEFT, padx=(0, 20))
        key_label = ttk.Label(key_setting_frame, text="触发按键:")
        key_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 按键配置区域
        key_config_frame = ttk.Frame(key_setting_frame)
        key_config_frame.pack(fill=tk.X)
        
        self.key_var = tk.StringVar(value=self.custom_key)
        
        # 显示当前按键的标签
        current_key_label = ttk.Label(key_config_frame, textvariable=self.key_var, relief="sunken", padding=5, width=10)
        current_key_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # 设置按键按钮
        self.set_key_btn = ttk.Button(key_config_frame, text="设置", 
                                    command=lambda: self.start_key_listening(self.key_var, self.set_key_btn))
        self.set_key_btn.pack(side=tk.LEFT)
        
        # 第二部分：关键词和语言设置
        keyword_language_frame = ttk.LabelFrame(setting_frame, text="关键词和语言", padding="10")
        keyword_language_frame.pack(fill=tk.X, pady=(0, 0))
        
        # 关键词设置行
        keyword_row = ttk.Frame(keyword_language_frame)
        keyword_row.pack(fill=tk.X, pady=(0, 10))
        
        keywords_label = ttk.Label(keyword_row, text="识别关键词:", width=12, anchor=tk.W)
        keywords_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # 关键词输入框
        self.keywords_var = tk.StringVar(value=",".join(self.custom_keywords))
        self.keywords_entry = ttk.Entry(keyword_row, textvariable=self.keywords_var, width=20)
        self.keywords_entry.pack(side=tk.LEFT)
        
        # 语言设置行
        language_row = ttk.Frame(keyword_language_frame)
        language_row.pack(fill=tk.X, pady=(0, 5))
        
        language_label = ttk.Label(language_row, text="OCR识别语言:", width=12, anchor=tk.W)
        language_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # 语言选择
        self.language_var = tk.StringVar(value=self.ocr_language)
        language_combobox = ttk.Combobox(language_row, textvariable=self.language_var, 
                                        values=["eng", "chi_sim", "chi_tra"], 
                                        width=15)
        language_combobox.pack(side=tk.LEFT)
        
        # 语言说明（放在输入框下方）
        language_desc = ttk.Label(keyword_language_frame, text="eng: 英文 | chi_sim: 简体中文 | chi_tra: 繁体中文", 
                                font=("Arial", 8), foreground="gray")
        language_desc.pack(anchor=tk.W, pady=(5, 10))
        
        # 按钮行（放在提示文字下方）
        btn_frame = ttk.Frame(keyword_language_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 5))
        
        set_keyword_btn = ttk.Button(btn_frame, text="保存关键词", command=self.set_custom_keywords)
        set_keyword_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        restore_keyword_btn = ttk.Button(btn_frame, text="恢复默认", command=self.restore_default_keywords)
        restore_keyword_btn.pack(side=tk.LEFT)
        
        # 操作按钮
        action_frame = ttk.Frame(ocr_frame)
        action_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_btn = ttk.Button(action_frame, text="开始监控", command=self.start_monitoring, state="disabled")
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(action_frame, text="停止监控", command=self.stop_monitoring, state="disabled")
        self.stop_btn.pack(side=tk.LEFT)
    
    def create_timed_tab(self, parent):
        """创建定时功能标签页"""
        timed_frame = ttk.Frame(parent, padding="10")
        timed_frame.pack(fill=tk.BOTH, expand=True)
        
        # 定时组配置
        self.timed_groups = []
        for i in range(3):
            group_frame = ttk.LabelFrame(timed_frame, text=f"定时组{i+1}", padding="10")
            group_frame.pack(fill=tk.X, pady=(0, 10))
            
            # 启用开关
            enabled_var = tk.BooleanVar(value=False)
            enabled_switch = ttk.Checkbutton(group_frame, text="启用", variable=enabled_var)
            enabled_switch.pack(side=tk.LEFT, padx=(0, 10))
            
            # 时间间隔
            interval_label = ttk.Label(group_frame, text="间隔(秒):", width=10)
            interval_label.pack(side=tk.LEFT)
            
            interval_var = tk.IntVar(value=10*(i+1))
            interval_entry = ttk.Entry(group_frame, textvariable=interval_var, width=10)
            interval_entry.pack(side=tk.LEFT, padx=(0, 10))
            
            # 按键选择
            key_label = ttk.Label(group_frame, text="按键:", width=5)
            key_label.pack(side=tk.LEFT)
            
            key_var = tk.StringVar(value=["space", "enter", "tab"][i])
            
            # 按键配置区域
            timed_key_config_frame = ttk.Frame(group_frame)
            timed_key_config_frame.pack(side=tk.LEFT)
            
            # 显示当前按键的标签
            timed_current_key_label = ttk.Label(timed_key_config_frame, textvariable=key_var, relief="sunken", padding=2, width=5)
            timed_current_key_label.pack(side=tk.LEFT, padx=(0, 5))
            
            # 设置按键按钮
            set_timed_key_btn = ttk.Button(timed_key_config_frame, text="设置", width=6)
            set_timed_key_btn.pack(side=tk.LEFT)
            # 单独绑定事件，避免UnboundLocalError
            set_timed_key_btn.config(command=lambda v=key_var, b=set_timed_key_btn: self.start_key_listening(v, b))
            
            self.timed_groups.append({
                "enabled": enabled_var,
                "interval": interval_var,
                "key": key_var
            })
        
        # 操作按钮
        action_frame = ttk.Frame(timed_frame)
        action_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_timed_btn = ttk.Button(action_frame, text="开始定时任务", command=self.start_timed_tasks, state="normal")
        self.start_timed_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_timed_btn = ttk.Button(action_frame, text="停止定时任务", command=self.stop_timed_tasks, state="disabled")
        self.stop_timed_btn.pack(side=tk.LEFT)
    
    def create_number_tab(self, parent):
        """创建数字识别标签页"""
        number_frame = ttk.Frame(parent, padding="10")
        number_frame.pack(fill=tk.BOTH, expand=True)
        
        # 区域配置
        self.number_regions = []
        for i in range(2):
            region_frame = ttk.LabelFrame(number_frame, text=f"区域{i+1}", padding="10")
            region_frame.pack(fill=tk.X, pady=(0, 10))
            
            # 启用开关
            enabled_var = tk.BooleanVar(value=False)
            enabled_switch = ttk.Checkbutton(region_frame, text="启用", variable=enabled_var)
            enabled_switch.pack(side=tk.LEFT, padx=(0, 10))
            
            # 区域选择
            select_btn = ttk.Button(region_frame, text="选择区域", command=lambda idx=i: self.start_number_region_selection(idx))
            select_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            region_var = tk.StringVar(value="未选择区域")
            region_label = ttk.Label(region_frame, textvariable=region_var)
            region_label.pack(side=tk.LEFT, padx=(0, 10))
            
            # 阈值设置
            threshold_label = ttk.Label(region_frame, text="阈值:", width=10)
            threshold_label.pack(side=tk.LEFT)
            
            threshold_var = tk.IntVar(value=500 if i == 0 else 1000)
            threshold_entry = ttk.Entry(region_frame, textvariable=threshold_var, width=10)
            threshold_entry.pack(side=tk.LEFT, padx=(0, 10))
            
            # 按键设置
            key_label = ttk.Label(region_frame, text="按键:", width=5)
            key_label.pack(side=tk.LEFT)
            
            key_var = tk.StringVar(value=["f1", "f2"][i])
            
            # 按键配置区域
            number_key_config_frame = ttk.Frame(region_frame)
            number_key_config_frame.pack(side=tk.LEFT)
            
            # 显示当前按键的标签
            number_current_key_label = ttk.Label(number_key_config_frame, textvariable=key_var, relief="sunken", padding=2, width=5)
            number_current_key_label.pack(side=tk.LEFT, padx=(0, 5))
            
            # 设置按键按钮
            set_number_key_btn = ttk.Button(number_key_config_frame, text="设置", width=6)
            set_number_key_btn.pack(side=tk.LEFT)
            # 单独绑定事件，避免UnboundLocalError
            set_number_key_btn.config(command=lambda v=key_var, b=set_number_key_btn: self.start_key_listening(v, b))
            
            self.number_regions.append({
                "enabled": enabled_var,
                "region_var": region_var,
                "region": None,
                "threshold": threshold_var,
                "key": key_var
            })
        
        # 操作按钮
        action_frame = ttk.Frame(number_frame)
        action_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_number_btn = ttk.Button(action_frame, text="开始数字识别", command=self.start_number_recognition, state="normal")
        self.start_number_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_number_btn = ttk.Button(action_frame, text="停止数字识别", command=self.stop_number_recognition, state="disabled")
        self.stop_number_btn.pack(side=tk.LEFT)
    
    def create_basic_tab(self, parent):
        """创建基本设置标签页"""
        # 基本设置区域
        basic_frame = ttk.Frame(parent, padding="10")
        basic_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tesseract配置
        tesseract_frame = ttk.LabelFrame(basic_frame, text="Tesseract配置", padding="10")
        tesseract_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Tesseract路径
        path_label = ttk.Label(tesseract_frame, text="Tesseract路径:")
        path_label.pack(anchor=tk.W, pady=(0, 5))
        
        path_frame = ttk.Frame(tesseract_frame)
        path_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.tesseract_path_var = tk.StringVar(value=self.tesseract_path)
        self.tesseract_path_entry = ttk.Entry(path_frame, textvariable=self.tesseract_path_var)
        self.tesseract_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.set_path_btn = ttk.Button(path_frame, text="设置", command=self.set_tesseract_path)
        self.set_path_btn.pack(side=tk.RIGHT)
        
        # 坐标模式设置
        coord_frame = ttk.LabelFrame(basic_frame, text="坐标模式", padding="10")
        coord_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 点击模式选择
        mode_frame = ttk.Frame(coord_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.click_mode_var = tk.StringVar(value=self.click_mode)
        
        center_rbtn = ttk.Radiobutton(mode_frame, text="区域中心", variable=self.click_mode_var, value="center", command=self.update_axis_inputs)
        center_rbtn.pack(side=tk.LEFT, padx=(0, 15))
        
        custom_rbtn = ttk.Radiobutton(mode_frame, text="自定义坐标", variable=self.click_mode_var, value="custom", command=self.update_axis_inputs)
        custom_rbtn.pack(side=tk.LEFT)
        
        # 自定义坐标输入
        self.x_coord_var = tk.IntVar(value=self.click_x)
        self.y_coord_var = tk.IntVar(value=self.click_y)
        
        x_frame = ttk.Frame(coord_frame)
        x_frame.pack(fill=tk.X, pady=(0, 10))
        
        x_label = ttk.Label(x_frame, text="X轴坐标:", width=10)
        x_label.pack(side=tk.LEFT)
        
        self.x_coord_entry = ttk.Entry(x_frame, textvariable=self.x_coord_var, width=10, state="disabled")
        self.x_coord_entry.pack(side=tk.LEFT)
        
        y_frame = ttk.Frame(coord_frame)
        y_frame.pack(fill=tk.X)
        
        y_label = ttk.Label(y_frame, text="Y轴坐标:", width=10)
        y_label.pack(side=tk.LEFT)
        
        self.y_coord_entry = ttk.Entry(y_frame, textvariable=self.y_coord_var, width=10, state="disabled")
        self.y_coord_entry.pack(side=tk.LEFT)
        
        # 配置管理
        config_frame = ttk.Frame(basic_frame)
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        save_btn = ttk.Button(config_frame, text="保存配置", command=self.save_config)
        save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        reset_btn = ttk.Button(config_frame, text="重置配置", command=self.load_config)
        reset_btn.pack(side=tk.LEFT)
    

    
    def create_log_tab(self, parent):
        """创建日志标签页"""
        log_frame = ttk.Frame(parent, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # 日志文本框
        self.log_text = tk.Text(log_frame, height=20, width=80, font=("Arial", 9), state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # 滚动条
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        # 清除日志按钮
        clear_btn = ttk.Button(parent, text="清除日志", command=self.clear_log)
        clear_btn.pack(side=tk.BOTTOM, pady=5, anchor=tk.E)
    

        
    def update_axis_inputs(self):
        """根据点击模式更新坐标轴输入状态"""
        mode = self.click_mode_var.get()
        if mode == "custom":
            self.x_coord_entry.config(state="normal")
            self.y_coord_entry.config(state="normal")
        else:
            self.x_coord_entry.config(state="disabled")
            self.y_coord_entry.config(state="disabled")
    
    def get_available_keys(self):
        """获取可用按键列表"""
        return [
            "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
            "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
            "space", "enter", "tab", "escape", "backspace", "delete", "insert",
            "equal", "plus", "minus", "asterisk", "slash", "backslash",
            "comma", "period", "semicolon", "apostrophe", "quote", "left", "right", "up", "down", "home", "end", "pageup", "pagedown",
            "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12"
        ]
    
    def preview_key(self):
        """预览按键效果"""
        key = self.key_var.get()
        messagebox.showinfo("按键预览", f"将模拟按下: {key}")
        self.log_message(f"预览按键: {key}")
    
    def restore_default_key(self):
        """恢复默认按键"""
        self.key_var.set("equal")
        self.log_message("已恢复默认按键设置")
        self.save_config()
    
    def start_key_listening(self, target_var, button):
        """开始监听用户按下的按键
        
        Args:
            target_var: 保存按键的StringVar变量
            button: 触发监听的按钮，用于更新按钮状态
        """
        # 保存当前焦点
        current_focus = self.root.focus_get()
        
        # 更新按钮状态
        original_text = button.cget("text")
        button.config(text="请按任意键...")
        button.config(state="disabled")
        
        # 创建按键监听函数
        def on_key_press(event):
            """处理按键按下事件"""
            # 获取按键名称
            key = event.keysym.lower()
            
            # 特殊按键映射
            key_mappings = {
                "Return": "enter",
                "Escape": "escape",
                "Tab": "tab",
                "BackSpace": "backspace",
                "Delete": "delete",
                "Insert": "insert",
                "space": "space",
                "minus": "minus",
                "plus": "plus",
                "asterisk": "asterisk",
                "slash": "slash",
                "backslash": "backslash",
                "comma": "comma",
                "period": "period",
                "semicolon": "semicolon",
                "apostrophe": "apostrophe",
                "quoteleft": "quote",
                "quoteright": "quote",
                "Left": "left",
                "Right": "right",
                "Up": "up",
                "Down": "down",
                "Home": "home",
                "End": "end",
                "Page_Up": "pageup",
                "Prior": "pageup",
                "Page_Down": "pagedown",
                "Next": "pagedown"
            }
            
            # 映射特殊按键
            if key in key_mappings:
                key = key_mappings[key]
            
            # 确保按键在可用列表中
            available_keys = self.get_available_keys()
            if key not in available_keys:
                self.log_message(f"不支持的按键: {key}")
                return
            
            # 保存按键
            target_var.set(key)
            
            # 恢复按钮状态
            button.config(text=original_text)
            button.config(state="normal")
            
            # 解除按键监听
            self.root.unbind("<KeyPress>")
            
            # 恢复焦点
            if current_focus:
                current_focus.focus_set()
            
            # 记录日志
            self.log_message(f"已设置按键: {key}")
            
            # 保存配置
            self.save_config()
        
        # 绑定按键事件
        self.root.bind("<KeyPress>", on_key_press)
        
        # 设置超时，防止永久监听
        def timeout():
            if button.cget("state") == "disabled":
                button.config(text=original_text)
                button.config(state="normal")
                self.root.unbind("<KeyPress>")
                if current_focus:
                    current_focus.focus_set()
                self.log_message("按键监听已超时")
        
        self.root.after(5000, timeout)  # 5秒超时
    
    def set_custom_keywords(self):
        """设置自定义关键词"""
        keywords_str = self.keywords_var.get().strip()
        if keywords_str:
            # 分割关键词并去除空格
            self.custom_keywords = [keyword.strip().lower() for keyword in keywords_str.split(",") if keyword.strip()]
            self.log_message(f"已设置自定义关键词: {', '.join(self.custom_keywords)}")
            messagebox.showinfo("成功", "关键词设置成功！")
            self.save_config()
        else:
            messagebox.showwarning("警告", "请至少输入一个关键词！")
    
    def restore_default_keywords(self):
        """恢复默认关键词"""
        self.custom_keywords = ["door", "men"]
        self.keywords_var.set(",".join(self.custom_keywords))
        self.log_message("已恢复默认关键词设置")
        self.save_config()
    
    def load_config(self):
        """加载配置
        增强错误处理，能够处理文件不存在、格式错误或路径配置缺失等异常情况
        确保加载所有前端设置，包括新增功能的相关配置
        支持新旧配置格式的兼容处理
        """
        # 初始化配置加载结果
        config_loaded = False
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.log_message(f"开始加载配置: {self.config_file}")
                
                # 获取配置版本，默认为1.0.0
                config_version = config.get('version', '1.0.0')
                self.log_message(f"配置版本: {config_version}")
                
                # 1. 加载Tesseract配置
                # 兼容旧格式和新格式
                tesseract_path = None
                if 'tesseract' in config and isinstance(config['tesseract'], dict):
                    # 新格式
                    tesseract_path = config['tesseract'].get('path')
                else:
                    # 旧格式
                    tesseract_path = config.get('tesseract_path')
                
                if tesseract_path and tesseract_path.strip():
                    temp_path = tesseract_path.strip()
                    # 检查路径是否存在
                    if os.path.exists(temp_path):
                        self.tesseract_path = temp_path
                        self.log_message(f"从配置文件加载Tesseract路径: {self.tesseract_path}")
                    else:
                        self.log_message(f"配置文件中的Tesseract路径不存在: {temp_path}")
                
                # 2. 加载基本OCR配置
                ocr_config = {}
                if 'ocr' in config and isinstance(config['ocr'], dict):
                    # 新格式
                    ocr_config = config['ocr']
                else:
                    # 旧格式
                    ocr_config = {
                        'interval': config.get('ocr_interval'),
                        'pause_duration': config.get('pause_duration'),
                        'selected_region': config.get('selected_region'),
                        'custom_key': config.get('custom_key'),
                        'custom_keywords': config.get('custom_keywords'),
                        'language': config.get('ocr_language')
                    }
                
                # 加载时间间隔
                if 'interval' in ocr_config and ocr_config['interval'] is not None:
                    self.ocr_interval = ocr_config['interval']
                    self.ocr_interval_var.set(self.ocr_interval)
                
                if 'pause_duration' in ocr_config and ocr_config['pause_duration'] is not None:
                    self.pause_duration = ocr_config['pause_duration']
                    self.pause_duration_var.set(self.pause_duration)
                
                # 加载选择区域
                if 'selected_region' in ocr_config and ocr_config['selected_region'] is not None:
                    try:
                        self.selected_region = tuple(ocr_config['selected_region'])
                        self.region_var.set(f"区域: {self.selected_region[0]},{self.selected_region[1]} - {self.selected_region[2]},{self.selected_region[3]}")
                        self.start_btn.config(state="normal")
                    except (TypeError, ValueError):
                        self.log_message(f"配置文件中的选择区域格式错误: {ocr_config['selected_region']}")
                
                # 加载自定义按键
                if 'custom_key' in ocr_config:
                    self.custom_key = ocr_config['custom_key']
                    self.key_var.set(self.custom_key)
                
                # 加载关键词
                if 'custom_keywords' in ocr_config and ocr_config['custom_keywords']:
                    self.custom_keywords = ocr_config['custom_keywords']
                    self.keywords_var.set(",".join(self.custom_keywords))
                
                # 加载语言设置
                if 'language' in ocr_config:
                    self.ocr_language = ocr_config['language']
                    self.language_var.set(self.ocr_language)
                
                # 3. 加载点击模式和坐标配置
                click_config = {}
                if 'click' in config and isinstance(config['click'], dict):
                    # 新格式
                    click_config = config['click']
                else:
                    # 旧格式
                    click_config = {
                        'mode': config.get('click_mode'),
                        'x': config.get('click_x'),
                        'y': config.get('click_y')
                    }
                
                if 'mode' in click_config:
                    self.click_mode_var.set(click_config['mode'])
                if 'x' in click_config and click_config['x'] is not None:
                    self.x_coord_var.set(click_config['x'])
                if 'y' in click_config and click_config['y'] is not None:
                    self.y_coord_var.set(click_config['y'])
                
                # 4. 加载定时功能配置
                timed_config = config.get('timed_key_press', {})
                if 'groups' in timed_config and isinstance(timed_config['groups'], list):
                    groups = timed_config['groups']
                    for i, group in enumerate(groups[:3]):
                        if i < len(self.timed_groups) and isinstance(group, dict):
                            if 'enabled' in group:
                                self.timed_groups[i]['enabled'].set(group['enabled'])
                            if 'interval' in group:
                                self.timed_groups[i]['interval'].set(group['interval'])
                            if 'key' in group:
                                self.timed_groups[i]['key'].set(group['key'])
                
                # 5. 加载数字识别配置
                number_config = config.get('number_recognition', {})
                if 'regions' in number_config and isinstance(number_config['regions'], list):
                    regions = number_config['regions']
                    for i, region_config in enumerate(regions[:2]):
                        if i < len(self.number_regions) and isinstance(region_config, dict):
                            if 'enabled' in region_config:
                                self.number_regions[i]['enabled'].set(region_config['enabled'])
                            if 'region' in region_config and region_config['region'] is not None:
                                try:
                                    region = tuple(region_config['region'])
                                    self.number_regions[i]['region'] = region
                                    self.number_regions[i]['region_var'].set(f"区域: {region[0]},{region[1]} - {region[2]},{region[3]}")
                                except (TypeError, ValueError):
                                    self.log_message(f"配置文件中的数字识别区域格式错误: {region_config['region']}")
                            if 'threshold' in region_config:
                                self.number_regions[i]['threshold'].set(region_config['threshold'])
                            if 'key' in region_config:
                                self.number_regions[i]['key'].set(region_config['key'])
                
                # 6. 更新界面控件状态
                self.update_axis_inputs()
                
                self.log_message("配置加载成功")
                config_loaded = True
                
            except json.JSONDecodeError as e:
                self.log_message(f"配置文件格式错误: {self.config_file}，错误详情: {str(e)}")
            except PermissionError:
                self.log_message(f"没有权限读取配置文件: {self.config_file}")
            except IOError as e:
                self.log_message(f"配置文件IO错误: {str(e)}")
            except Exception as e:
                self.log_message(f"配置加载错误: {str(e)}")
        else:
            self.log_message(f"配置文件不存在: {self.config_file}")
        
        # 无论配置是否加载成功，都更新界面中的Tesseract路径变量
        if hasattr(self, 'tesseract_path_var'):
            self.tesseract_path_var.set(self.tesseract_path)
            
        return config_loaded
    

    
    def setup_config_listeners(self):
        """为配置变量添加监听器，自动保存配置"""
        # 通用的延迟保存函数，避免频繁保存
        def delayed_save(*args):
            self.root.after(1000, self.save_config)
        
        # 即时保存函数
        def immediate_save(*args):
            self.save_config()
        
        # 1. 基本OCR配置监听器
        self.ocr_interval_var.trace_add("write", delayed_save)
        self.pause_duration_var.trace_add("write", delayed_save)
        self.key_var.trace_add("write", immediate_save)
        self.language_var.trace_add("write", immediate_save)
        
        # 2. 关键词配置监听器
        self.keywords_var.trace_add("write", delayed_save)
        
        # 3. 点击模式和坐标监听器
        self.click_mode_var.trace_add("write", immediate_save)
        self.x_coord_var.trace_add("write", delayed_save)
        self.y_coord_var.trace_add("write", delayed_save)
        
        # 4. 定时任务配置监听器
        for i, group in enumerate(self.timed_groups):
            group["enabled"].trace_add("write", immediate_save)
            group["interval"].trace_add("write", delayed_save)
            group["key"].trace_add("write", immediate_save)
        
        # 5. 数字识别配置监听器
        for i, region_config in enumerate(self.number_regions):
            region_config["enabled"].trace_add("write", immediate_save)
            region_config["threshold"].trace_add("write", delayed_save)
            region_config["key"].trace_add("write", immediate_save)
    
    def clear_log(self):
        """清除日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log_message("已清除日志")
    
    def set_tesseract_path(self):
        """设置Tesseract OCR路径"""
        new_path = self.tesseract_path_var.get().strip()
        
        if not new_path:
            messagebox.showwarning("警告", "请输入有效的Tesseract路径！")
            return
        
        if not os.path.exists(new_path):
            messagebox.showwarning("警告", "指定的路径不存在！")
            return
        
        import platform
        # 根据操作系统检查可执行文件格式
        if platform.system() == "Windows":
            if not new_path.endswith("tesseract.exe"):
                messagebox.showwarning("警告", "请指定tesseract.exe可执行文件！")
                return
        elif platform.system() == "Darwin":  # macOS
            if not os.path.basename(new_path) == "tesseract":
                messagebox.showwarning("警告", "请指定tesseract可执行文件！")
                return
        
        try:
            # 测试新路径是否可用
            result = subprocess.run(
                [new_path, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # 更新路径和配置
            self.tesseract_path = new_path
            pytesseract.pytesseract.tesseract_cmd = new_path
            self.tesseract_available = True
            
            self.log_message(f"已设置Tesseract路径: {new_path}")
            self.status_var.set("就绪")
            messagebox.showinfo("成功", "Tesseract路径设置成功！")
            
            # 保存配置
            self.save_config()
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            messagebox.showwarning("警告", "无法使用指定的Tesseract路径！")
            return
        
    def log_message(self, message):
        """记录日志信息"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # 写入日志文件
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"写入日志文件失败: {str(e)}")
        
        # 只有当log_text已经创建时才写入界面日志
        if hasattr(self, 'log_text'):
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        
        # 更新状态标签（仅当status_var已创建）
        if hasattr(self, 'status_var'):
            self.status_var.set(message.split(":")[0] if ":" in message else message)
    
    def start_region_selection(self):
        """开始区域选择"""
        self._start_selection("normal", None)
    
    def _start_selection(self, selection_type, region_index):
        """通用的区域选择方法
        
        Args:
            selection_type: 选择类型，"normal"或"number"
            region_index: 数字识别区域索引，仅当selection_type为"number"时有效
        """
        self.log_message(f"开始{'数字识别区域' if selection_type == 'number' else ''}区域选择...")
        self.is_selecting = True
        self.current_number_region = region_index
        
        # 检查screeninfo库是否可用
        if screeninfo is None:
            messagebox.showerror("错误", "screeninfo库未安装，无法支持多显示器选择。请运行 'pip install screeninfo' 安装该库。")
            return
        
        # 获取虚拟屏幕的尺寸（包含所有显示器）
        monitors = screeninfo.get_monitors()
        
        # 计算整个虚拟屏幕的边界
        self.min_x = min(monitor.x for monitor in monitors)
        self.min_y = min(monitor.y for monitor in monitors)
        max_x = max(monitor.x + monitor.width for monitor in monitors)
        max_y = max(monitor.y + monitor.height for monitor in monitors)
        
        # 创建透明的区域选择窗口，覆盖整个虚拟屏幕
        self.select_window = tk.Toplevel(self.root)
        self.select_window.geometry(f"{max_x - self.min_x}x{max_y - self.min_y}+{self.min_x}+{self.min_y}")
        self.select_window.overrideredirect(True)  # 移除窗口装饰
        self.select_window.attributes("-alpha", 0.3)
        self.select_window.attributes("-topmost", True)
        
        # 创建画布用于绘制选择框
        self.canvas = tk.Canvas(self.select_window, cursor="cross", 
                               width=max_x - self.min_x, height=max_y - self.min_y)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绑定鼠标事件
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        
        # 根据选择类型绑定不同的鼠标释放事件
        if selection_type == "number":
            self.canvas.bind("<ButtonRelease-1>", self.on_number_region_mouse_up)
        else:
            self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        self.select_window.protocol("WM_DELETE_WINDOW", self.cancel_selection)
    
    def on_mouse_down(self, event):
        """鼠标按下事件"""
        # 保存绝对坐标用于最终区域保存
        self.start_x_abs = event.x_root
        self.start_y_abs = event.y_root
        # 计算相对Canvas的坐标用于绘制
        self.start_x_rel = event.x_root - self.min_x
        self.start_y_rel = event.y_root - self.min_y
        self.rect = None
    
    def on_mouse_drag(self, event):
        """鼠标拖动事件"""
        # 获取当前绝对坐标
        current_x_abs = event.x_root
        current_y_abs = event.y_root
        # 计算相对Canvas的坐标用于绘制
        current_x_rel = current_x_abs - self.min_x
        current_y_rel = current_y_abs - self.min_y
        
        if self.rect:
            self.canvas.delete(self.rect)
        
        # 使用相对坐标绘制选择框，确保视觉上与鼠标位置一致
        self.rect = self.canvas.create_rectangle(
            self.start_x_rel, self.start_y_rel, current_x_rel, current_y_rel,
            outline="red", width=2, fill="red"
        )
    
    def on_mouse_up(self, event):
        """鼠标释放事件"""
        # 获取结束绝对坐标
        end_x_abs = event.x_root
        end_y_abs = event.y_root
        
        # 确保选择区域有效
        if abs(end_x_abs - self.start_x_abs) < 10 or abs(end_y_abs - self.start_y_abs) < 10:
            messagebox.showwarning("警告", "选择的区域太小，请重新选择")
            self.cancel_selection()
            return
        
        # 保存选择区域（使用绝对坐标）
        self.selected_region = (
            min(self.start_x_abs, end_x_abs),
            min(self.start_y_abs, end_y_abs),
            max(self.start_x_abs, end_x_abs),
            max(self.start_y_abs, end_y_abs)
        )
        
        # 更新界面
        self.region_var.set(f"区域: {self.selected_region[0]},{self.selected_region[1]} - {self.selected_region[2]},{self.selected_region[3]}")
        
        # 启用开始监控按钮
        self.start_btn.config(state="normal")
        
        self.log_message(f"已选择区域: {self.selected_region}")
        self.cancel_selection()
        
        # 保存配置
        self.save_config()
    
    def cancel_selection(self):
        """取消区域选择"""
        self.is_selecting = False
        if hasattr(self, 'select_window') and self.select_window.winfo_exists():
            self.select_window.destroy()
    
    def start_monitoring(self):
        """开始监控"""
        if not self.tesseract_available:
            messagebox.showwarning("警告", "Tesseract OCR引擎不可用，请先安装并配置环境变量！")
            return
            
        if not self.selected_region:
            messagebox.showwarning("警告", "请先选择监控区域")
            return
        
        self.is_running = True
        self.is_paused = False
        
        # 更新按钮状态
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        
        self.log_message("开始监控...")
        
        # 启动OCR线程
        self.ocr_thread = threading.Thread(target=self.ocr_loop, daemon=True)
        self.ocr_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        
        # 更新按钮状态
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        
        self.log_message("已停止监控")
    
    def ocr_loop(self):
        """OCR识别循环"""
        while self.is_running:
            try:
                current_time = time.time()
                
                # 检查是否需要暂停
                if self.is_paused:
                    time.sleep(1)
                    continue
                
                # 检查是否在暂停期
                pause_duration = self.pause_duration_var.get()
                if current_time - self.last_trigger_time < pause_duration:
                    remaining = int(pause_duration - (current_time - self.last_trigger_time))
                    self.status_var.set(f"暂停中... {remaining}秒")
                    time.sleep(1)
                    continue
                
                # 执行OCR识别
                self.perform_ocr()
                
                # 等待下一次识别
                ocr_interval = self.ocr_interval_var.get()
                for _ in range(ocr_interval):
                    if not self.is_running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.log_message(f"错误: {str(e)}")
                time.sleep(5)
    
    def perform_ocr(self):
        """执行OCR识别"""
        try:
            # 截取屏幕区域
            x1, y1, x2, y2 = self.selected_region
            
            # 确保坐标是(left, top, right, bottom)格式，且left < right, top < bottom
            left = min(x1, x2)
            top = min(y1, y2)
            right = max(x1, x2)
            bottom = max(y1, y2)
            
            # 使用PIL的ImageGrab.grab()方法，设置all_screens=True捕获所有屏幕
            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)
            
            # 转换为灰度图像以提高识别率
            screenshot = screenshot.convert('L')
            
            # 进行OCR识别
            current_lang = self.language_var.get()
            text = pytesseract.image_to_string(screenshot, lang=current_lang)
            
            self.log_message(f"识别结果: '{text.strip()}'")
            
            # 检查是否包含关键词
            lower_text = text.lower()
            if any(keyword in lower_text for keyword in self.custom_keywords):
                self.trigger_action()
                
        except Exception as e:
            self.log_message(f"OCR错误: {str(e)}")
    
    def save_config(self):
        """保存配置
        保存所有前端用户设置，包括新增功能的相关配置
        确保数据结构完整、一致，并处理边界情况
        """
        try:
            # 1. 保存定时功能配置
            timed_groups_config = []
            for group in self.timed_groups:
                timed_groups_config.append({
                    'enabled': group['enabled'].get(),
                    'interval': group['interval'].get(),
                    'key': group['key'].get()
                })
            
            # 2. 保存数字识别配置
            number_regions_config = []
            for region_config in self.number_regions:
                number_regions_config.append({
                    'enabled': region_config['enabled'].get(),
                    'region': list(region_config['region']) if region_config['region'] else None,
                    'threshold': region_config['threshold'].get(),
                    'key': region_config['key'].get()
                })
            
            # 3. 确保关键词列表是最新的
            keywords_str = self.keywords_var.get().strip()
            current_keywords = [keyword.strip().lower() for keyword in keywords_str.split(",") if keyword.strip()]
            if not current_keywords:
                current_keywords = self.custom_keywords  # 保留原有关键词作为备份
            
            # 更新内部关键词列表，确保一致性
            self.custom_keywords = current_keywords
            
            # 4. 完整的配置数据结构，确保所有配置项都被保存
            config = {
                'version': '1.0.1',  # 版本升级，支持更完整的配置保存
                'last_save_time': datetime.datetime.now().isoformat(),
                
                # 基本OCR配置
                'ocr': {
                    'interval': self.ocr_interval_var.get(),
                    'pause_duration': self.pause_duration_var.get(),
                    'selected_region': list(self.selected_region) if self.selected_region else None,
                    'custom_key': self.key_var.get(),
                    'custom_keywords': current_keywords,
                    'language': self.language_var.get()
                },
                
                # Tesseract配置
                'tesseract': {
                    'path': self.tesseract_path
                },
                
                # 坐标模式配置
                'click': {
                    'mode': self.click_mode_var.get(),
                    'x': self.x_coord_var.get(),
                    'y': self.y_coord_var.get()
                },
                
                # 定时功能配置
                'timed_key_press': {
                    'groups': timed_groups_config
                },
                
                # 数字识别配置
                'number_recognition': {
                    'regions': number_regions_config
                }
            }
            
            # 5. 确保配置文件目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # 6. 写入配置文件，使用更紧凑的格式
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False, default=str)
            
            self.log_message("配置已保存")
            
        except PermissionError:
            self.log_message(f"没有权限写入配置文件: {self.config_file}")
        except IOError as e:
            self.log_message(f"配置文件IO错误: {str(e)}")
        except json.JSONDecodeError as e:
            self.log_message(f"配置JSON编码错误: {str(e)}")
        except Exception as e:
            self.log_message(f"配置保存错误: {str(e)}")
    
    def trigger_action(self):
        """触发动作序列"""
        self.log_message("检测到关键词，执行动作...")
        
        # 计算点击位置
        click_x, click_y = self.calculate_click_position()
        
        try:
            # 1. 鼠标左键点击指定位置
            pyautogui.click(click_x, click_y)
            self.log_message(f"点击位置: ({click_x}, {click_y})")
            
            # 2. 等待固定时间（无需用户修改）
            time.sleep(self.click_delay)
            
            # 3. 通过事件队列按下自定义按键
            custom_key = self.key_var.get()
            self.add_event(('keypress', custom_key))
            
            # 记录触发时间
            self.last_trigger_time = time.time()
            
        except Exception as e:
            self.log_message(f"动作执行错误: {str(e)}")
    
    def calculate_click_position(self):
        """计算点击位置"""
        mode = self.click_mode_var.get()
        
        if mode == "custom":
            # 使用自定义坐标（相对于选择区域左上角）
            x_offset = self.x_coord_var.get()
            y_offset = self.y_coord_var.get()
            
            # 计算实际屏幕坐标
            click_x = self.selected_region[0] + x_offset
            click_y = self.selected_region[1] + y_offset
            
            # 确保坐标在选择区域内
            click_x = max(self.selected_region[0], min(click_x, self.selected_region[2]))
            click_y = max(self.selected_region[1], min(click_y, self.selected_region[3]))
        else:
            # 计算区域中心
            click_x = (self.selected_region[0] + self.selected_region[2]) // 2
            click_y = (self.selected_region[1] + self.selected_region[3]) // 2
        
        return click_x, click_y
    
    def start_event_thread(self):
        """启动事件处理线程"""
        self.is_event_running = True
        self.event_thread = threading.Thread(target=self.process_events, daemon=True)
        self.event_thread.start()
        self.log_message("事件处理线程已启动")
    
    def process_events(self):
        """处理事件队列中的事件"""
        while self.is_event_running:
            try:
                with self.event_cond:
                    while not self.event_queue:
                        self.event_cond.wait()
                    event = self.event_queue.popleft()
                
                # 执行事件
                self.execute_event(event)
            except Exception as e:
                self.log_message(f"事件处理错误: {str(e)}")
                time.sleep(1)
    
    def add_event(self, event):
        """添加事件到队列"""
        with self.event_cond:
            self.event_queue.append(event)
            self.event_cond.notify()
    
    def execute_event(self, event):
        """执行具体事件"""
        event_type, data = event
        
        if event_type == 'keypress':
            key = data
            try:
                pyautogui.press(key)
                self.log_message(f"按下了 {key} 键")
            except Exception as e:
                self.log_message(f"按键执行错误: {str(e)}")
        # 其他事件类型...
    
    def start_timed_tasks(self):
        """开始定时任务"""
        # 停止现有的定时任务
        self.stop_timed_tasks()
        
        self.log_message("开始定时任务")
        
        # 统计要启动的定时组数量
        start_count = 0
        for i, group in enumerate(self.timed_groups):
            if group["enabled"].get():
                interval = group["interval"].get()
                key = group["key"].get()
                # 创建线程并存储
                thread = threading.Thread(target=self.timed_task_loop, args=(i, interval, key), daemon=True)
                self.timed_threads.append(thread)
                thread.start()
                start_count += 1
        
        # 更新按钮状态
        self.start_timed_btn.config(state="disabled")
        self.stop_timed_btn.config(state="normal")
        
        if start_count == 0:
            self.log_message("没有启用任何定时组")
    
    def stop_timed_tasks(self):
        """停止定时任务"""
        # 停止所有定时任务
        self.log_message("停止所有定时任务")
        
        # 清空线程列表
        if self.timed_threads:
            self.log_message(f"停止{len(self.timed_threads)}个定时任务线程")
            self.timed_threads.clear()
        
        # 更新按钮状态
        self.start_timed_btn.config(state="normal")
        self.stop_timed_btn.config(state="disabled")
        
        self.log_message("已停止定时任务")
    
    def timed_task_loop(self, group_index, interval, key):
        """定时任务循环"""
        current_thread = threading.current_thread()
        
        # 检查线程是否在timed_threads列表中，以及定时组是否启用
        while current_thread in self.timed_threads and self.timed_groups[group_index]["enabled"].get():
            try:
                self.add_event(('keypress', key))
                self.log_message(f"定时任务{group_index+1}触发按键: {key}")
                
                # 等待指定的时间间隔
                for _ in range(interval):
                    time.sleep(1)
                    # 每秒钟检查一次线程是否仍在列表中
                    if current_thread not in self.timed_threads:
                        return
            except Exception as e:
                self.log_message(f"定时任务{group_index+1}错误: {str(e)}")
                break
    
    def start_number_region_selection(self, region_index):
        """开始数字识别区域选择"""
        self._start_selection("number", region_index)
    
    def on_number_region_mouse_up(self, event):
        """数字识别区域鼠标释放事件"""
        # 获取结束绝对坐标
        end_x_abs = event.x_root
        end_y_abs = event.y_root
        
        # 确保选择区域有效
        if abs(end_x_abs - self.start_x_abs) < 10 or abs(end_y_abs - self.start_y_abs) < 10:
            messagebox.showwarning("警告", "选择的区域太小，请重新选择")
            self.cancel_selection()
            return
        
        # 保存选择区域（使用绝对坐标）
        region = (
            min(self.start_x_abs, end_x_abs),
            min(self.start_y_abs, end_y_abs),
            max(self.start_x_abs, end_x_abs),
            max(self.start_y_abs, end_y_abs)
        )
        
        # 更新界面
        region_index = self.current_number_region
        self.number_regions[region_index]["region"] = region
        self.number_regions[region_index]["region_var"].set(f"区域: {region[0]},{region[1]} - {region[2]},{region[3]}")
        
        self.log_message(f"已选择数字识别区域{region_index+1}: {region}")
        self.cancel_selection()
        
        # 保存配置
        self.save_config()
    
    def start_number_recognition(self):
        """开始数字识别"""
        # 停止现有的数字识别任务
        self.stop_number_recognition()
        
        self.log_message("开始数字识别")
        
        # 统计要启动的数字识别区域数量
        start_count = 0
        for i, region_config in enumerate(self.number_regions):
            if region_config["enabled"].get():
                region = region_config["region"]
                if not region:
                    messagebox.showwarning("警告", f"请先为数字识别区域{i+1}选择区域")
                    return
                
                threshold = region_config["threshold"].get()
                key = region_config["key"].get()
                thread = threading.Thread(target=self.number_recognition_loop, args=(i, region, threshold, key), daemon=True)
                self.number_threads.append(thread)
                thread.start()
                start_count += 1
        
        # 更新按钮状态
        self.start_number_btn.config(state="disabled")
        self.stop_number_btn.config(state="normal")
        
        if start_count == 0:
            self.log_message("没有启用任何数字识别区域")
    
    def stop_number_recognition(self):
        """停止数字识别"""
        # 清空线程列表
        if self.number_threads:
            self.log_message(f"停止{len(self.number_threads)}个数字识别线程")
            self.number_threads.clear()
        
        # 更新按钮状态
        self.start_number_btn.config(state="normal")
        self.stop_number_btn.config(state="disabled")
        
        self.log_message("已停止数字识别")
    
    def number_recognition_loop(self, region_index, region, threshold, key):
        """数字识别循环"""
        current_thread = threading.current_thread()
        
        # 检查线程是否在number_threads列表中，以及数字识别区域是否启用
        while current_thread in self.number_threads and self.number_regions[region_index]["enabled"].get():
            try:
                # 截图并识别数字
                screenshot = self.take_screenshot(region)
                text = self.ocr_number(screenshot)
                self.log_message(f"数字识别{region_index+1}结果: '{text}'")
                
                number = self.parse_number(text)
                if number is not None:
                    self.log_message(f"数字识别{region_index+1}解析结果: {number}")
                    if number < threshold:
                        self.add_event(('keypress', key))
                        self.log_message(f"数字识别{region_index+1}触发按键: {key}")
                
                time.sleep(1)  # 1秒间隔
            except Exception as e:
                self.log_message(f"数字识别{region_index+1}错误: {str(e)}")
                time.sleep(5)
    
    def parse_number(self, text):
        """解析数字，支持X/Y格式
        打印详细日志以帮助排查问题
        """
        # 打印当前识别到的文字内容
        self.log_message(f"数字识别解析: 当前文字内容为 '{text}'")
        
        # 移除可能的空格和换行符
        text = text.strip()
        
        # 检查是否为X/Y格式
        if '/' in text:
            self.log_message("数字识别解析: 检测到X/Y格式文字 '{0}'".format(text))
            parts = text.split('/')
            self.log_message("数字识别解析: 分割结果为 {0}".format(parts))
            
            if len(parts) == 2:
                # 尝试解析X部分
                x_part = parts[0].strip()
                self.log_message("数字识别解析: 尝试解析X部分 '{0}'".format(x_part))
                try:
                    x_number = int(x_part)
                    self.log_message("数字识别解析: 成功解析X部分为 {0}".format(x_number))
                    return x_number
                except ValueError as e:
                    self.log_message("数字识别解析: 无法解析X部分 '{0}'，错误: {1}".format(x_part, str(e)))
                    # 尝试清理X部分，移除非数字字符
                    cleaned_x = ''.join(filter(str.isdigit, x_part))
                    if cleaned_x:
                        self.log_message("数字识别解析: 清理后X部分为 '{0}'".format(cleaned_x))
                        try:
                            return int(cleaned_x)
                        except ValueError:
                            self.log_message("数字识别解析: 清理后仍无法解析X部分 '{0}'".format(cleaned_x))
        else:
            self.log_message("数字识别解析: 未检测到X/Y格式，尝试直接解析数字 '{0}'".format(text))
            
        # 尝试直接解析为数字
        try:
            # 清理文字，移除非数字字符
            cleaned_text = ''.join(filter(str.isdigit, text))
            if cleaned_text:
                self.log_message(f"数字识别解析: 清理后文字为 '{cleaned_text}'")
                number = int(cleaned_text)
                self.log_message(f"数字识别解析: 成功解析为数字 {number}")
                return number
            else:
                self.log_message(f"数字识别解析: 清理后无数字字符")
                return None
        except ValueError as e:
            self.log_message(f"数字识别解析: 无法直接解析为数字，错误: {str(e)}")
            return None
    
    def take_screenshot(self, region):
        """截取指定区域的屏幕"""
        x1, y1, x2, y2 = region
        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1, x2)
        bottom = max(y1, y2)
        return ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)
    
    def ocr_number(self, image):
        """识别数字，支持X/Y格式
        简化图像预处理，保留字符白名单以避免'ee'错误识别
        """
        # 1. 转换为灰度图像
        image = image.convert('L')
        
        # 2. 不使用复杂的OpenCV预处理，只使用基本的阈值处理
        # 这样可以保留更多原始信息，提高识别率
        
        # 3. 优化OCR配置，平衡识别率和错误率
        # 使用--psm 7（单行文本）和--oem 3（默认OCR引擎模式）
        # 添加字符白名单，只识别数字和/符号，防止'ee'错误
        config = '--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789/'
        text = pytesseract.image_to_string(image, lang='eng', config=config)
        
        # 4. 额外的文本清理，移除可能的换行符和空格
        text = text.strip().replace('\n', '').replace('\r', '')
        
        return text
    

    
    def exit_program(self):
        """退出程序"""
        if self.is_running:
            self.stop_monitoring()
        self.stop_timed_tasks()
        self.stop_number_recognition()
        
        # 停止事件线程
        self.is_event_running = False
        if self.event_thread:
            self.add_event(('exit', None))
            self.event_thread.join(timeout=1)
        
        self.root.destroy()
    
    def run(self):
        """运行程序"""
        self.root.mainloop()

def main():
    """主函数，用于命令行调用"""
    app = AutoDoorOCR()
    app.run()

if __name__ == "__main__":
    main()
