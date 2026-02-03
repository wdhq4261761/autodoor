import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import pyautogui
import pytesseract
from PIL import Image, ImageGrab
import threading
import time
import random
import datetime
import subprocess
import os
import sys
import json
import platform
from collections import deque
import requests
import re
import numpy as np

# 导入pynput用于全局键盘监听
try:
    from pynput import keyboard
    PYINPUT_AVAILABLE = True
except ImportError:
    PYINPUT_AVAILABLE = False

# 导入pygame用于音频播放
try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

# 全局版本号配置
VERSION = "2.0.3"

class VersionChecker:
    def __init__(self, app):
        self.app = app
        self.current_version = VERSION
        self.last_check_time = None
        self.check_interval = 24 * 60 * 60  # 24小时
        self.update_available = False
        self.latest_version_info = None
        self.ignored_version = None
        # 从配置中加载已忽略的版本
        self._load_ignored_version()

    def _load_ignored_version(self):
        """从配置中加载已忽略的版本"""
        try:
            # 直接从配置文件中读取
            config_file_path = getattr(self.app, 'config_file_path', None)
            if config_file_path and os.path.exists(config_file_path):
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if 'update' in config:
                        self.ignored_version = config.get('update', {}).get('ignored_version')
        except Exception as e:
            self.app.log_message(f"加载已忽略版本失败: {str(e)}")

    def check_for_updates(self, manual=False):
        """检查版本更新"""
        try:
            # 检查是否在间隔时间内
            if not manual and self.last_check_time:
                time_since_last_check = time.time() - self.last_check_time
                if time_since_last_check < self.check_interval:
                    return

            self.last_check_time = time.time()

            # 使用GitHub API获取最新版本
            url = "https://api.github.com/repos/wdhq4261761/autodoor/releases/latest"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            latest_version = data.get('tag_name', '')  # tag_name直接是版本号，如"1.5.0"

            # 提取下载链接
            windows_download_url = None
            macos_download_url = None

            for asset in data.get('assets', []):
                asset_name = asset.get('name', '')
                if 'windows' in asset_name.lower():
                    windows_download_url = asset.get('browser_download_url')
                elif 'macos' in asset_name.lower():
                    macos_download_url = asset.get('browser_download_url')

            # 比较版本
            comparison = self.compare_versions(self.current_version, latest_version)

            if comparison == 1:
                # 发现新版本
                # 检查版本是否已被忽略
                # 注意：手动检查更新时不受历史忽略状态的影响，始终显示最新版本信息
                if not manual and self.ignored_version:
                    ignored_comparison = self.compare_versions(self.ignored_version, latest_version)
                    if ignored_comparison <= 0:
                        # 版本已被忽略或相同，不显示更新通知
                        # 说明：compare_versions(a, b) 返回 1 表示 a < b，返回 0 表示 a == b，返回 -1 表示 a > b
                        # 所以当 ignored_comparison <= 0 时，表示已忽略版本 >= 最新版本
                        return
                
                self.update_available = True
                self.latest_version_info = {
                    'version': latest_version,
                    'release_date': data.get('published_at', ''),
                    'changelog': data.get('body', ''),
                    'download_url': 'https://my.feishu.cn/wiki/GqoWwddPMizkLYkogn8cdoynn3c?from=from_copylink',
                    'github_url': data.get('html_url', ''),
                    'windows_download_url': windows_download_url,
                    'macos_download_url': macos_download_url
                }

                # 显示更新通知
                self.show_update_notification()
            else:
                # 当前已是最新版本或开发版本
                if manual:
                    # 手动检查时显示反馈
                    self.show_no_update_notification()

        except Exception as e:
            self.app.log_message(f"版本检查失败: {str(e)}")

    def compare_versions(self, current, latest):
        """比较两个版本号
        返回值：
        - 1: 当前版本旧，需要更新
        - 0: 当前版本是最新
        - -1: 当前版本新（开发版本）
        """
        try:
            current_parts = list(map(int, current.split('.')))
            latest_parts = list(map(int, latest.split('.')))
            
            for i in range(max(len(current_parts), len(latest_parts))):
                current_val = current_parts[i] if i < len(current_parts) else 0
                latest_val = latest_parts[i] if i < len(latest_parts) else 0

                if current_val < latest_val:
                    return 1
                elif current_val > latest_val:
                    return -1

            return 0
        except:
            return 0

    def show_update_notification(self):
        """显示更新通知"""
        def show_notification():
            if not self.latest_version_info:
                return

            latest_version = self.latest_version_info.get('version', '')
            release_date = self.latest_version_info.get('release_date', '')
            changelog = self.latest_version_info.get('changelog', '')
            download_url = self.latest_version_info.get('download_url', '')

            # 格式化发布日期
            if release_date:
                try:
                    from datetime import datetime
                    release_date_obj = datetime.fromisoformat(release_date.replace('Z', '+00:00'))
                    release_date_str = release_date_obj.strftime('%Y-%m-%d')
                except:
                    release_date_str = release_date
            else:
                release_date_str = '未知'

            # 简化更新内容
            changelog_summary = changelog[:500] + '...' if len(changelog) > 500 else changelog

            # 创建通知窗口
            notification_window = tk.Toplevel(self.app.root)
            notification_window.title("发现新版本")
            window_width = 450
            window_height = 400
            notification_window.geometry(f"{window_width}x{window_height}")
            notification_window.minsize(window_width, window_height)
            notification_window.transient(self.app.root)
            notification_window.grab_set()

            # 计算并设置窗口位置到主窗口中心
            self.app.root.update_idletasks()
            root_x = self.app.root.winfo_x()
            root_y = self.app.root.winfo_y()
            root_width = self.app.root.winfo_width()
            root_height = self.app.root.winfo_height()

            # 计算弹窗位置
            pos_x = root_x + (root_width // 2) - (window_width // 2)
            pos_y = root_y + (root_height // 2) - (window_height // 2)

            # 设置弹窗位置
            notification_window.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")

            # 添加内容
            frame = ttk.Frame(notification_window, padding="20")
            frame.pack(fill=tk.BOTH, expand=True)

            ttk.Label(frame, text=f"发现新版本: v{latest_version}", font=('Arial', 12, 'bold')).pack(pady=(0, 10))
            ttk.Label(frame, text=f"发布日期: {release_date_str}").pack(pady=(0, 10))
            ttk.Label(frame, text="更新内容:", font=('Arial', 10, 'bold')).pack(anchor='w')

            # 添加滚动条的文本框
            text_frame = ttk.Frame(frame)
            text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

            changelog_text = tk.Text(text_frame, height=8, wrap=tk.WORD, state=tk.DISABLED)
            scrollbar = ttk.Scrollbar(text_frame, command=changelog_text.yview)
            changelog_text.config(yscrollcommand=scrollbar.set)
            
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            changelog_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            changelog_text.config(state=tk.NORMAL)
            changelog_text.insert(tk.END, changelog_summary)
            changelog_text.config(state=tk.DISABLED)

            # 添加按钮
            button_frame = ttk.Frame(frame)
            button_frame.pack(fill=tk.X, pady=(10, 0))

            ttk.Button(button_frame, text="查看更新", command=lambda: self.open_update_link(download_url)).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(button_frame, text="稍后提醒", command=notification_window.destroy).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(button_frame, text="忽略此版本", command=lambda: self.ignore_version(latest_version, notification_window)).pack(side=tk.LEFT)

        # 在主线程中显示通知
        self.app.root.after(0, show_notification)

    def open_update_link(self, url):
        """打开更新链接"""
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception as e:
            self.app.log_message(f"打开更新链接失败: {str(e)}")

    def ignore_version(self, version, notification_window):
        """忽略指定版本"""
        try:
            # 直接更新配置文件
            config_file_path = getattr(self.app, 'config_file_path', None)
            if config_file_path:
                # 确保配置文件目录存在
                os.makedirs(os.path.dirname(config_file_path), exist_ok=True)
                
                # 无论配置文件操作是否成功，都先设置 ignored_version 属性
                self.ignored_version = version
                
                # 读取现有配置
                if os.path.exists(config_file_path):
                    try:
                        with open(config_file_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                    except json.JSONDecodeError:
                        # 配置文件格式错误，使用空配置
                        config = {}
                else:
                    config = {}
                
                # 更新被忽略的版本
                if 'update' not in config:
                    config['update'] = {}
                config['update']['ignored_version'] = version
                
                # 保存配置
                with open(config_file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False, default=str)
                
                self.app.log_message(f"已忽略版本: {version}")
        except Exception as e:
            self.app.log_message(f"忽略版本失败: {str(e)}")
        finally:
            # 无论是否发生异常，都关闭通知窗口
            notification_window.destroy()

    def show_no_update_notification(self):
        """显示无更新通知"""
        def show_notification():
            # 创建通知窗口
            notification_window = tk.Toplevel(self.app.root)
            notification_window.title("检查更新")
            notification_window.geometry("300x150")
            notification_window.transient(self.app.root)
            notification_window.grab_set()
            
            # 计算主窗口中心位置，使弹窗居中显示
            self.app.root.update_idletasks()
            root_x = self.app.root.winfo_x()
            root_y = self.app.root.winfo_y()
            root_width = self.app.root.winfo_width()
            root_height = self.app.root.winfo_height()
            
            # 计算弹窗位置
            dialog_width = 300
            dialog_height = 150
            pos_x = root_x + (root_width // 2) - (dialog_width // 2)
            pos_y = root_y + (root_height // 2) - (dialog_height // 2)
            
            # 设置弹窗位置
            notification_window.geometry(f"{dialog_width}x{dialog_height}+{pos_x}+{pos_y}")
            
            # 添加内容
            frame = ttk.Frame(notification_window, padding="20")
            frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(frame, text="检查更新", font=('Arial', 12, 'bold')).pack(pady=(0, 10))
            ttk.Label(frame, text="当前已是最新版本！", wraplength=260).pack(pady=(0, 15))
            
            # 添加按钮
            button_frame = ttk.Frame(frame)
            button_frame.pack(fill=tk.X, pady=(10, 0))
            
            ttk.Button(button_frame, text="确定", command=notification_window.destroy).pack()

        # 在主线程中显示通知
        self.app.root.after(0, show_notification)

    def start_auto_check(self):
        """启动自动检查线程"""
        def check_loop():
            while True:
                self.check_for_updates()
                time.sleep(self.check_interval)
        
        thread = threading.Thread(target=check_loop, daemon=True)
        thread.start()

# 尝试导入screeninfo库，如果不可用则提供安装提示
try:
    import screeninfo
except ImportError:
    screeninfo = None

class AutoDoorOCR:
    """
    AutoDoor OCR 识别系统主类
    该类实现了一个基于OCR的自动识别和操作系统，主要功能包括：
    1. 文字识别：监控指定区域，识别关键词并触发动作
    2. 定时功能：按照设定的时间间隔执行按键操作
    3. 数字识别：监控指定区域的数字变化并触发动作
    4. 报警功能：在触发动作时播放报警声音

    使用Tesseract OCR引擎进行文字识别，PyAutoGUI进行鼠标和键盘操作。
    """

    def __init__(self):
        """
        初始化AutoDoor OCR系统
        主要初始化工作：
        1. 创建主窗口
        2. 初始化版本检查器
        3. 设置配置参数和状态变量
        4. 确定配置文件和日志文件路径
        5. 初始化线程控制和事件队列
        6. 创建界面元素
        7. 加载配置
        8. 检测Tesseract OCR引擎可用性
        9. 设置配置监听器和快捷键
        10. 启动事件处理线程
        """
        # 禁用PyAutoGUI的故障安全机制，防止鼠标移动到屏幕角落时触发异常
        pyautogui.FAILSAFE = False

        # 创建主窗口
        self.root = tk.Tk()
        self.root.title(f"AutoDoor OCR 识别系统 v{VERSION}")
        self.root.geometry("900x850")  # 增加默认高度
        self.root.resizable(True, True) 
        self.root.minsize(900, 850)  # 增加最小高度

        # ========== 配置参数 ==========
        # OCR相关配置
        self.ocr_interval = 5  # OCR识别间隔（秒）
        self.pause_duration = 180  # 触发动作后的暂停时间（秒）
        self.click_delay = 0.5  # 点击后的延迟时间（秒）
        self.default_custom_key = "equal"  # 默认自定义按键

        # 关键词配置
        self.default_keywords = ["men", "door"]  # 默认识别关键词
        self.default_ocr_language = "eng"  # 默认OCR识别语言

        # ========== 状态变量 ==========
        self.selected_region = None  # 选择的识别区域
        self.is_running = False  # 是否正在运行
        self.is_paused = False  # 是否暂停
        self.is_selecting = False  # 是否正在选择区域
        self.last_trigger_time = 0  # 上次触发动作的时间
        self.system_stopped = False  # 系统完全停止标志，用于阻止外部命令唤醒

        # OCR组触发时间跟踪
        self.last_recognition_times = {}  # 识别间隔时间记录
        self.last_trigger_times = {}  # 暂停期时间记录

        # ========== 文件路径配置 ==========
        app_name = "AutoDoorOCR"

        # 根据不同操作系统选择配置文件目录
        if platform.system() == "Windows":
            # Windows: 使用APPDATA环境变量
            config_dir = os.path.join(os.environ.get("APPDATA"), app_name)
        elif platform.system() == "Darwin":
            # macOS: 使用Library/Preferences目录
            config_dir = os.path.join(os.path.expanduser("~"), "Library", "Preferences", app_name)
        else:
            # 其他系统: 回退到程序运行目录
            config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")

        # 确保配置目录存在
        os.makedirs(config_dir, exist_ok=True)

        # 配置文件路径
        self.config_file_path = os.path.join(config_dir, "autodoor_config.json")

        # 初始化版本检查器
        self.version_checker = VersionChecker(self)

        # 启动自动检查
        self.version_checker.start_auto_check()

        # 应用启动时检查一次
        self.version_checker.check_for_updates()

        # 日志文件路径
        self.log_file_path = os.path.join(config_dir, "autodoor.log")

        # ========== 线程控制 ==========
        self.ocr_thread = None  # OCR识别线程
        self.timed_threads = []  # 定时功能线程列表
        self.number_threads = []  # 数字识别线程列表

        # 事件队列
        self.event_queue = deque()  # 事件队列
        self.event_lock = threading.Lock()  # 事件队列锁
        self.event_condition = threading.Condition(self.event_lock)  # 事件队列条件变量
        self.is_event_running = False  # 事件处理线程是否运行
        self.event_thread = None  # 事件处理线程

        # ========== 功能模块配置 ==========
        # 定时功能相关
        self.timed_enabled_var = None  # 定时功能启用状态变量
        self.timed_groups = []  # 定时功能组列表

        # 数字识别相关
        self.number_enabled_var = None  # 数字识别启用状态变量
        self.number_regions = []  # 数字识别区域列表
        self.current_number_region_index = None  # 当前正在配置的数字识别区域索引
        
        # Tesseract相关
        self.tesseract_path = ""  # Tesseract OCR引擎路径
        self.tesseract_available = False  # Tesseract OCR引擎是否可用

        # 报警功能相关
        self.alarm_enabled = {}  # 各模块报警启用状态
        self.alarm_sound_path = tk.StringVar(value="")  # 全局报警声音路径
        self.alarm_volume = tk.IntVar(value=70)  # 全局报警音量，默认70%
        self.alarm_volume_str = tk.StringVar(value="70")  # 用于显示的音量字符串

        # 初始化报警配置
        for module in ["ocr", "timed", "number"]:
            self.alarm_enabled[module] = tk.BooleanVar(value=False)

        # 按键延迟配置
        self.ocr_delay_min = tk.IntVar(value=300)  # 按键按下最小延迟（毫秒）
        self.ocr_delay_max = tk.IntVar(value=500)  # 按键按下最大延迟（毫秒）

        # OCR组管理相关
        self.ocr_groups = []  # OCR识别组列表
        self.current_ocr_region_index = None  # 当前正在配置的OCR识别区域索引

        # 先创建界面元素，确保所有UI变量都被初始化
        self.create_widgets()

        # 加载配置（包括Tesseract路径和报警设置）
        self.load_config()

        # 如果配置中没有Tesseract路径，使用空字符串（不强制使用项目自带的tesseract）
        config_updated = False
        if not self.tesseract_path:
            self.tesseract_path = ""  # 初始为空，让用户后续自行配置
            config_updated = True

        # 如果配置中没有报警声音路径，使用项目自带的alarm.mp3
        if not self.alarm_sound_path.get():
            self.alarm_sound_path.set(self.get_default_alarm_sound_path())
            config_updated = True

        # 执行Tesseract引擎的存在性检测和可用性验证
        self.tesseract_available = self.check_tesseract_availability()

        # 如果使用了默认配置，将其保存到配置文件
        if config_updated:
            self.save_config()

        # 设置配置监听器
        self.setup_config_listeners()

        # 检查tesseract可用性，在主循环开始后显示提示
        if not self.tesseract_available:
            self.status_var.set("Tesseract未配置")
            # 使用after将提示延迟到主循环开始后显示
            self.root.after(100, lambda: messagebox.showinfo("提示", "未检测到Tesseract OCR引擎，请在设置中配置Tesseract路径后使用文字识别功能！"))

        # 设置快捷键绑定
        self.setup_shortcuts()

        # 启动事件处理线程
        self.start_event_thread()

    def get_default_tesseract_path(self):
        """
        获取默认的Tesseract路径，使用项目自带的tesseract

        支持Windows和Mac平台，同时支持打包后的环境

        Returns:
            str: Tesseract可执行文件的路径，如果未找到则返回空字符串
        """
        # 获取程序运行目录
        if hasattr(sys, '_MEIPASS'):
            # 打包后的环境，使用_MEIPASS获取运行目录
            app_root = sys._MEIPASS
        else:
            # 开发环境，使用当前文件所在目录
            app_root = os.path.dirname(os.path.abspath(__file__))

        # 根据操作系统选择不同的tesseract路径
        tesseract_path = ""
        if platform.system() == "Windows":
            # Windows平台
            tesseract_path = os.path.join(app_root, "tesseract", "tesseract.exe")
        elif platform.system() == "Darwin":
            # macOS平台
            # 检查可能的路径 - 针对.app包结构优化
            possible_paths = [
                os.path.join(app_root, "tesseract", "tesseract"),  # 主要路径
                os.path.join(app_root, "tesseract"),  # 备选路径
                os.path.join(os.path.dirname(app_root), "tesseract", "tesseract"),  # 应用包外部路径
                # 针对.app包结构的额外路径
                os.path.join(os.path.dirname(os.path.dirname(app_root)), "Resources", "tesseract", "tesseract"),
                os.path.join(os.path.dirname(os.path.dirname(app_root)), "Resources", "tesseract"),
                # macOS系统路径
                "/usr/local/bin/tesseract",  # Homebrew (Intel)
                "/opt/homebrew/bin/tesseract",  # Homebrew (Apple Silicon)
                # 其他可能的系统路径
                "/usr/bin/tesseract"
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    tesseract_path = path
                    break
        else:
            # 其他平台，返回空
            tesseract_path = ""

        self.log_message(f"默认Tesseract路径: {tesseract_path}")
        return tesseract_path

    def get_default_alarm_sound_path(self):
        """
        获取默认的报警声音路径，使用项目自带的alarm.mp3

        支持Windows和Mac平台，同时支持打包后的环境

        Returns:
            str: 报警声音文件的路径
        """
        # 获取程序运行目录
        if hasattr(sys, '_MEIPASS'):
            # 打包后的环境，使用_MEIPASS获取运行目录
            app_root = sys._MEIPASS
        else:
            # 开发环境，使用当前文件所在目录
            app_root = os.path.dirname(os.path.abspath(__file__))

        # 构建跨平台的报警声音路径
        alarm_path = os.path.join(app_root, "voice", "alarm.mp3")

        # 确保路径格式正确
        alarm_path = os.path.normpath(alarm_path)

        return alarm_path

    def _validate_tesseract_path(self):
        """
        验证Tesseract路径有效性

        Returns:
            bool: 如果路径有效则返回True，否则返回False
        """
        if not self.tesseract_path:
            self.log_message("Tesseract路径未配置")
            return False

        if not os.path.exists(self.tesseract_path):
            self.log_message(f"Tesseract路径不存在: {self.tesseract_path}")
            return False

        if not os.path.isfile(self.tesseract_path):
            self.log_message(f"Tesseract路径不是文件: {self.tesseract_path}")
            return False

        return True
    
    def _check_tesseract_permissions(self):
        """
        检查并修复Tesseract执行权限
        Returns:
            bool: 如果权限正确则返回True，否则返回False
        """
        if platform.system() == "Windows":
            if not self.tesseract_path.endswith("tesseract.exe"):
                self.log_message(f"Tesseract路径不是可执行文件: {self.tesseract_path}")
                return False
        elif platform.system() == "Darwin":  # macOS
            if not os.path.basename(self.tesseract_path) == "tesseract":
                self.log_message(f"Tesseract路径不是可执行文件: {self.tesseract_path}")
                return False

            if not os.access(self.tesseract_path, os.X_OK):
                self.log_message(f"Tesseract文件缺少执行权限，尝试修复: {self.tesseract_path}")
                try:
                    subprocess.run(["chmod", "+x", self.tesseract_path], 
                                  capture_output=True, check=True, timeout=5)
                    self.log_message("成功添加执行权限")
                except Exception as e:
                    self.log_message(f"添加执行权限失败: {str(e)}")
                    return False
        # 其他平台不做严格检查
        return True

    def _check_tesseract_version(self):
        """
        检查Tesseract版本兼容性
        Returns:
            bool: 如果版本兼容则返回True，否则返回False
        """
        try:
            version_result = subprocess.run(
                [self.tesseract_path, "--version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )

            version_output = version_result.stdout.strip()
            if "tesseract" in version_output.lower():
                version_parts = version_output.split()
                if len(version_parts) >= 2:
                    version_str = version_parts[1]
                    self.log_message(f"检测到Tesseract版本: {version_str}")

                    try:
                        cleaned_version = version_str.lstrip('v')
                        major_version = int(cleaned_version.split('.')[0])
                        if major_version < 4:
                            self.log_message(f"Tesseract版本太旧 ({version_str})，建议使用4.x或更高版本")
                            return False
                    except (ValueError, IndexError):
                        self.log_message(f"无法解析Tesseract版本: {version_str}")
                        # 继续执行，不因为版本解析失败而直接返回False
            return True
        except Exception as e:
            self.log_message(f"版本检查失败: {str(e)}")
            return False

    def _get_test_file_path(self):
        """
        获取测试文件路径
        Returns:
            str: 测试文件路径
        """
        if platform.system() == "Darwin":
            return os.path.join(os.path.expanduser("~"), "test_tesseract.png")
        return 'test_tesseract.png'

    def _cleanup_test_files(self, test_file_path):
        """
        清理测试文件
        Args:
            test_file_path: 测试文件路径
        """
        if os.path.exists(test_file_path):
            try:
                os.remove(test_file_path)
            except Exception as e:
                self.log_message(f"清理测试文件失败: {str(e)}")

    def _test_tesseract_functionality(self):
        """
        测试Tesseract基本功能
        Returns:
            bool: 如果功能测试通过则返回True，否则返回False
        """
        try:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path

            test_file_path = self._get_test_file_path()
            test_image = Image.new('RGB', (100, 30), color='white')
            test_image.save(test_file_path)

            test_result = pytesseract.image_to_string(test_file_path, lang='eng', timeout=5)

            self._cleanup_test_files(test_file_path)
            return True
        except Exception as e:
            test_file_path = self._get_test_file_path()
            self._cleanup_test_files(test_file_path)
            self.log_message(f"功能测试失败: {str(e)}")
            return False

    def check_tesseract_availability(self):
        """
        检查Tesseract OCR是否可用

        包括：
        1. 路径有效性验证
        2. 版本兼容性检查
        3. 基础功能测试

        Returns:
            bool: 如果Tesseract OCR可用则返回True，否则返回False
        """
        # 如果tesseract路径为空，直接返回False
        if not self.tesseract_path:
            self.log_message("Tesseract路径未配置")
            return False

        try:
            if not self._validate_tesseract_path():
                return False

            if not self._check_tesseract_permissions():
                return False

            if not self._check_tesseract_version():
                return False

            if not self._test_tesseract_functionality():
                return False

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
        except PermissionError as e:
            self.log_message(f"Tesseract权限错误: {str(e)}")
            return False
        except Exception as e:
            self.log_message(f"Tesseract检测发生未知错误: {str(e)}")
            return False

    def create_widgets(self):
        """
        创建应用程序的所有界面元素

        主要工作：
        1. 设置全局样式和主题
        2. 创建主容器和状态栏
        3. 创建标签页布局（首页、文字识别、定时功能、数字识别、基本设置）
        4. 添加控制按钮和页脚信息
        """
        # 设置全局样式
        style = ttk.Style()
        # 统一背景色
        bg_color = "#f0f0f0"
        green_bg_color = "#e8f4e8"

        # 基本样式配置，所有组件背景色与整体背景色一致
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, font=("Arial", 10))
        style.configure("Header.TLabel", font=("Arial", 12, "bold"), background=bg_color)
        style.configure("TButton", padding=5, background=bg_color)
        style.configure("TEntry", background=bg_color, fieldbackground=bg_color)
        style.configure("TCheckbutton", background=bg_color)
        style.configure("TCombobox", background=bg_color, fieldbackground=bg_color)
        style.configure("TLabelFrame", background=bg_color, bordercolor=bg_color)
        style.configure("TLabelFrame.Label", background=bg_color)

        # 修复文本元素底部灰色问题，确保所有标签相关组件都使用正确背景色
        style.configure(".", background=bg_color)  # 设置所有组件的默认背景色
        style.configure("TLabel", relief="flat")  # 移除标签的默认边框
        style.map("TLabel", background=[("active", bg_color)])  # 确保选中时背景色正确
        style.map("TLabelFrame.Label", background=[("active", bg_color)])  # 标签框架标题选中时背景色
        style.map("TFrame", background=[("active", bg_color)])  # 框架选中时背景色

        # 添加绿色边框样式，用于标记启用的识别组
        style.configure("Green.TFrame", background=green_bg_color)
        style.configure("Green.TLabelframe", background=green_bg_color, borderwidth=2, relief=tk.SOLID)
        style.configure("Green.TLabelframe.Label", foreground="green", font=("Arial", 10, "bold"), background=green_bg_color)
        style.configure("Green.TLabel", background=green_bg_color)
        style.configure("Green.TEntry", background=green_bg_color, fieldbackground=bg_color)
        style.configure("Green.TButton", background=green_bg_color)
        style.configure("Green.TCheckbutton", background=green_bg_color)
        style.configure("Green.TCombobox", background=green_bg_color, fieldbackground=bg_color)

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

        # 首页标签页 - 新增
        home_frame = ttk.Frame(notebook)
        notebook.add(home_frame, text="首页")
        self.create_home_tab(home_frame)

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

        # 脚本运行标签页
        script_frame = ttk.Frame(notebook)
        notebook.add(script_frame, text="脚本运行")
        self.create_script_tab(script_frame)

        # 基本设置标签页
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="基本设置")
        self.create_basic_tab(basic_frame)


        # 控制按钮区域 - 简化布局，让退出按钮靠近右下角
        control_frame = ttk.Frame(main_frame, padding="10 5 10 0")
        control_frame.pack(fill=tk.X, pady=(10, 0))

        # 左侧声明区域
        footer_frame = ttk.Frame(control_frame)
        footer_frame.pack(side=tk.LEFT, anchor=tk.W)

        # 禁止商用声明
        footer_label = ttk.Label(footer_frame, text="本程序仅供个人学习研究使用，禁止商用 | 制作人：", 
                                  font=("等线", 10), foreground="#888888", cursor="arrow")
        footer_label.pack(side=tk.LEFT)

        # 制作人Bilibili超链接
        author_label = ttk.Label(footer_frame, text="Flown王砖家", 
                                  font=("等线", 10), foreground="blue", cursor="hand2")
        author_label.pack(side=tk.LEFT)
        author_label.bind("<Button-1>", lambda e: self.open_bilibili())

        # 右侧按钮区域 - 简化布局
        buttons_frame = ttk.Frame(control_frame)
        buttons_frame.pack(side=tk.RIGHT, anchor=tk.E)

        # 定义工具介绍按钮的点击事件
        def open_tool_intro():
            import webbrowser
            webbrowser.open("https://my.feishu.cn/wiki/GqoWwddPMizkLYkogn8cdoynn3c?from=from_copylink")

        # 退出程序按钮（右侧）
        exit_btn = ttk.Button(buttons_frame, text="退出程序", command=self.exit_program)
        exit_btn.pack(side=tk.RIGHT)

        # 检查更新按钮
        check_update_btn = ttk.Button(buttons_frame, text="检查更新", command=self.check_for_updates)
        check_update_btn.pack(side=tk.RIGHT, padx=(0, 20))

        # 工具介绍按钮（左侧），与退出按钮保持20px间距
        tool_intro_btn = ttk.Button(buttons_frame, text="工具介绍", command=open_tool_intro)
        tool_intro_btn.pack(side=tk.RIGHT, padx=(0, 20))

    def open_bilibili(self):
        """打开Bilibili主页"""
        import webbrowser
        webbrowser.open("https://space.bilibili.com/263150759")

    def check_for_updates(self):
        """手动检查更新"""
        self.version_checker.check_for_updates(manual=True)

    def create_ocr_tab(self, parent):
        """创建文字识别标签页"""
        ocr_frame = ttk.Frame(parent, padding="10")
        ocr_frame.pack(fill=tk.BOTH, expand=True)

        # 顶部按钮栏
        top_frame = ttk.Frame(ocr_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        # 新增组按钮
        self.add_ocr_group_btn = ttk.Button(top_frame, text="新增识别组", command=self.add_ocr_group)
        self.add_ocr_group_btn.pack(side=tk.LEFT)

        # 识别组容器，带滚动条
        groups_container = ttk.Frame(ocr_frame)
        groups_container.pack(fill=tk.BOTH, expand=True)

        # 垂直滚动条
        groups_scrollbar = ttk.Scrollbar(groups_container, orient=tk.VERTICAL)
        groups_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 画布，用于实现滚动
        groups_canvas = tk.Canvas(groups_container, yscrollcommand=groups_scrollbar.set, highlightthickness=0)
        groups_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        groups_scrollbar.config(command=groups_canvas.yview)

        # 内部容器，用于放置所有识别组
        self.ocr_groups_frame = ttk.Frame(groups_canvas)
        groups_canvas.create_window((0, 0), window=self.ocr_groups_frame, anchor="nw", tags="inner_frame")

        # 配置画布尺寸和滚动区域
        def configure_scroll_region(event):
            self._configure_scroll_region(event, groups_canvas, "inner_frame")

        groups_canvas.bind("<Configure>", configure_scroll_region)
        self.ocr_groups_frame.bind("<Configure>", configure_scroll_region)

        # 为画布绑定鼠标滚轮事件
        groups_canvas.bind("<MouseWheel>", lambda event: self._on_mousewheel(event, groups_canvas))

        # 为内部框架绑定鼠标滚轮事件
        self.ocr_groups_frame.bind("<MouseWheel>", lambda event: self._on_mousewheel(event, groups_canvas))

        # 为整个标签页绑定鼠标滚轮事件
        ocr_frame.bind("<MouseWheel>", lambda event: self._on_mousewheel(event, groups_canvas))

        # 保存文字识别的画布和框架引用
        self.ocr_canvas = groups_canvas
        self.ocr_frame = ocr_frame
        self.ocr_groups_container = groups_container

        # 区域配置
        self.ocr_groups = []
        for i in range(2):
            self.create_ocr_group(i)

        # 绑定所有文字识别区域的鼠标滚轮事件
        self._bind_mousewheel_to_widgets(groups_canvas, [group["frame"] for group in self.ocr_groups])

    def create_ocr_group(self, index):
        """创建单个文字识别组"""
        # 创建识别组框架
        group_frame = self._create_group_frame(self.ocr_groups_frame, index, "识别组")

        # 启用状态变量
        enabled_var = tk.BooleanVar(value=False)

        # 设置组点击事件和样式更新
        self._setup_group_click_handler(group_frame, enabled_var)

        # 初始应用样式
        self.update_group_style(group_frame, enabled_var.get())

        # 第一行：区域选择、区域坐标、删除按钮
        row1_frame = ttk.Frame(group_frame)
        row1_frame.pack(fill=tk.X, pady=(0, 10))

        # 区域选择和区域坐标
        select_btn = ttk.Button(row1_frame, text="选择区域", command=lambda idx=index: self.start_ocr_region_selection(idx))
        select_btn.pack(side=tk.LEFT, padx=(0, 10))

        region_var = tk.StringVar(value="未选择区域")
        region_label = ttk.Label(row1_frame, textvariable=region_var, width=25)
        region_label.pack(side=tk.LEFT, padx=(0, 10))

        # 删除按钮
        delete_btn = ttk.Button(row1_frame, text="删除", width=6, command=lambda idx=index: self.delete_ocr_group(idx))
        delete_btn.pack(side=tk.RIGHT, padx=(10, 0))

        # 第二行：间隔(秒)、暂停时长（秒）、触发按键、按键时长、启用报警
        row2_frame = ttk.Frame(group_frame)
        row2_frame.pack(fill=tk.X, pady=(0, 10))

        # 间隔(秒)输入框 - 水平排列
        ttk.Label(row2_frame, text="间隔(秒):", width=10).pack(side=tk.LEFT, padx=(0, 5))
        interval_var = tk.IntVar(value=5)
        ttk.Entry(row2_frame, textvariable=interval_var, width=6).pack(side=tk.LEFT, padx=(0, 10))

        # 暂停时长（秒）输入框 - 水平排列
        ttk.Label(row2_frame, text="暂停时长(秒):", width=12).pack(side=tk.LEFT, padx=(0, 5))
        pause_var = tk.IntVar(value=180)
        ttk.Entry(row2_frame, textvariable=pause_var, width=6).pack(side=tk.LEFT, padx=(0, 10))

        # 触发按键选择器 - 水平排列
        ttk.Label(row2_frame, text="按键:", width=10).pack(side=tk.LEFT, padx=(0, 5))
        key_var = tk.StringVar(value="equal")
        key_label = ttk.Label(row2_frame, textvariable=key_var, relief="sunken", padding=2, width=8)
        key_label.pack(side=tk.LEFT, padx=(0, 5))
        set_key_btn = ttk.Button(row2_frame, text="修改", width=6)
        set_key_btn.pack(side=tk.LEFT, padx=(0, 10))
        set_key_btn.config(command=lambda v=key_var, b=set_key_btn: self.start_key_listening(v, b))

        # 按键时长设置框 - 水平排列
        ttk.Label(row2_frame, text="按键时长:", width=10).pack(side=tk.LEFT, padx=(0, 5))
        delay_min_var = tk.IntVar(value=300)
        delay_max_var = tk.IntVar(value=500)

        def validate_positive_int(P):
            if P == "":
                return True
            try:
                val = int(P)
                return val > 0
            except ValueError:
                return False

        delay_min_entry = ttk.Entry(row2_frame, textvariable=delay_min_var, width=5, validate="key")
        delay_min_entry.pack(side=tk.LEFT)
        delay_min_entry.configure(validatecommand=(delay_min_entry.register(validate_positive_int), '%P'))
        ttk.Label(row2_frame, text=" - ", width=2).pack(side=tk.LEFT)
        delay_max_entry = ttk.Entry(row2_frame, textvariable=delay_max_var, width=5, validate="key")
        delay_max_entry.pack(side=tk.LEFT)
        delay_max_entry.configure(validatecommand=(delay_max_entry.register(validate_positive_int), '%P'))
        ttk.Label(row2_frame, text="ms", width=3).pack(side=tk.LEFT, padx=(0, 10))

        # 启用报警复选框 - 水平排列
        alarm_var = tk.BooleanVar(value=False)
        alarm_switch = ttk.Checkbutton(row2_frame, text="启用报警", variable=alarm_var)
        alarm_switch.pack(side=tk.LEFT, padx=(0, 10))

        # 识别关键词、识别语言、是否点击识别文字
        row3_frame = ttk.Frame(group_frame)
        row3_frame.pack(fill=tk.X)

        # 识别关键词输入框 - 水平排列
        ttk.Label(row3_frame, text="识别关键词:", width=12, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 5))
        keywords_var = tk.StringVar(value="men,door")
        ttk.Entry(row3_frame, textvariable=keywords_var, width=20).pack(side=tk.LEFT, padx=(0, 10))

        # 识别语言选择下拉菜单 - 水平排列
        ttk.Label(row3_frame, text="识别语言:", width=10, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 5))
        language_var = tk.StringVar(value="eng")
        ttk.Combobox(row3_frame, textvariable=language_var, values=["eng", "chi_sim", "chi_tra"], width=12).pack(side=tk.LEFT, padx=(0, 10))

        # 是否点击识别文字复选框 - 水平排列
        click_var = tk.BooleanVar(value=True)
        click_switch = ttk.Checkbutton(row3_frame, text="点击识别文字", variable=click_var)
        click_switch.pack(side=tk.LEFT, padx=(0, 10))

        # 保存组配置
        group_config = {
            "frame": group_frame,
            "enabled": enabled_var,
            "region_var": region_var,
            "region": None,
            "interval": interval_var,
            "pause": pause_var,
            "key": key_var,
            "delay_min": delay_min_var,
            "delay_max": delay_max_var,
            "alarm": alarm_var,
            "keywords": keywords_var,
            "language": language_var,
            "click": click_var
        }
        self.ocr_groups.append(group_config)

        # 为新创建的识别组添加配置监听器
        if hasattr(self, '_setup_ocr_group_listeners'):
            self._setup_ocr_group_listeners(group_config)

        # 为新创建的识别组绑定鼠标滚轮事件
        canvas = self.ocr_groups_frame.master
        if isinstance(canvas, tk.Canvas):
            self._bind_mousewheel_to_widgets(canvas, [group_frame])

    def add_ocr_group(self):
        """新增文字识别组"""
        if len(self.ocr_groups) >= 15:
            messagebox.showwarning("警告", "最多只能创建15个识别组！")
            return

        self.create_ocr_group(len(self.ocr_groups))
        self.log_message(f"新增文字识别组{len(self.ocr_groups)}")

    def delete_ocr_group(self, index, confirm=True):
        """删除文字识别组"""
        if len(self.ocr_groups) <= 1:
            messagebox.showwarning("警告", "至少需要保留一个识别组！")
            return

        if confirm:
            if not messagebox.askyesno("确认", f"确定要删除识别组{index+1}吗？"):
                return

        if 0 <= index < len(self.ocr_groups):
            self.ocr_groups[index]["frame"].destroy()
            del self.ocr_groups[index]
            self.renumber_ocr_groups()
            self.log_message(f"已删除文字识别组{index+1}")

    def renumber_ocr_groups(self):
        """重新编号所有文字识别组"""
        for i, group in enumerate(self.ocr_groups):
            # 保持组名称前的空格，确保布局一致
            group["frame"].configure(text=f"  识别组{i+1}")

    def start_ocr_region_selection(self, index):
        """开始选择OCR识别区域"""
        self._start_selection("ocr", index)

    def _on_mousewheel(self, event, canvas):
        """公共的鼠标滚轮事件处理函数"""
        # 使用yview_moveto方法实现平滑滚动
        current_pos = canvas.yview()
        scroll_amount = event.delta / 120 / 10  # 调整滚动速度
        new_pos = current_pos[0] - scroll_amount
        new_pos = max(0, min(1, new_pos))
        canvas.yview_moveto(new_pos)
        # 阻止事件继续传播
        return "break"

    def _configure_scroll_region(self, event, canvas, frame_tag):
        """公共的滚动区域配置函数"""
        canvas.configure(scrollregion=canvas.bbox("all"))
        # 确保内部框架宽度与画布一致
        canvas.itemconfig(frame_tag, width=canvas.winfo_width())

    def _bind_mousewheel_to_widgets(self, canvas, widgets):
        """为指定的控件及其子控件绑定鼠标滚轮事件"""
        def on_mousewheel(event):
            return self._on_mousewheel(event, canvas)

        for widget in widgets:
            widget.bind("<MouseWheel>", on_mousewheel)
            # 为控件内所有子组件绑定鼠标滚轮事件
            for child in widget.winfo_children():
                child.bind("<MouseWheel>", on_mousewheel)
                # 递归绑定到所有子组件的子组件
                for grandchild in child.winfo_children():
                    grandchild.bind("<MouseWheel>", on_mousewheel)

    def create_timed_tab(self, parent):
        """创建定时功能标签页"""
        timed_frame = ttk.Frame(parent, padding="10")
        timed_frame.pack(fill=tk.BOTH, expand=True)

        # 顶部按钮栏
        top_frame = ttk.Frame(timed_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        # 新增组按钮
        self.add_timed_group_btn = ttk.Button(top_frame, text="新增定时组", command=self.add_timed_group)
        self.add_timed_group_btn.pack(side=tk.LEFT)

        # 定时组容器，带滚动条
        groups_container = ttk.Frame(timed_frame)
        groups_container.pack(fill=tk.BOTH, expand=True)

        # 垂直滚动条
        groups_scrollbar = ttk.Scrollbar(groups_container, orient=tk.VERTICAL)
        groups_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 画布，用于实现滚动
        groups_canvas = tk.Canvas(groups_container, yscrollcommand=groups_scrollbar.set, highlightthickness=0)
        groups_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        groups_scrollbar.config(command=groups_canvas.yview)

        # 内部容器，用于放置所有定时组
        self.timed_groups_frame = ttk.Frame(groups_canvas)
        groups_canvas.create_window((0, 0), window=self.timed_groups_frame, anchor="nw", tags="inner_frame")

        # 配置画布尺寸和滚动区域
        def configure_scroll_region(event):
            self._configure_scroll_region(event, groups_canvas, "inner_frame")

        groups_canvas.bind("<Configure>", configure_scroll_region)
        self.timed_groups_frame.bind("<Configure>", configure_scroll_region)

        # 为画布绑定鼠标滚轮事件
        groups_canvas.bind("<MouseWheel>", lambda event: self._on_mousewheel(event, groups_canvas))

        # 为内部框架绑定鼠标滚轮事件
        self.timed_groups_frame.bind("<MouseWheel>", lambda event: self._on_mousewheel(event, groups_canvas))

        # 为整个标签页绑定鼠标滚轮事件
        timed_frame.bind("<MouseWheel>", lambda event: self._on_mousewheel(event, groups_canvas))

        # 保存定时功能的画布和框架引用
        self.timed_canvas = groups_canvas
        self.timed_frame = timed_frame
        self.timed_groups_container = groups_container

        # 定时组配置
        self.timed_groups = []
        for i in range(3):
            self.create_timed_group(i)

        # 绑定所有定时组的鼠标滚轮事件
        self._bind_mousewheel_to_widgets(groups_canvas, [group["frame"] for group in self.timed_groups])

    def create_timed_group(self, index):
        """创建单个定时组，所有UI元素布局在一行中"""
        # 创建定时组框架
        group_frame = self._create_group_frame(self.timed_groups_frame, index, "定时组")

        # 启用状态变量
        enabled_var = tk.BooleanVar(value=False)

        # 设置组点击事件和样式更新
        self._setup_group_click_handler(group_frame, enabled_var)

        # 初始应用样式
        self.update_group_style(group_frame, enabled_var.get())

        # 基本配置
        row1_frame = ttk.Frame(group_frame)
        row1_frame.pack(fill=tk.X, pady=(0, 10))

        # 时间间隔
        interval_label = ttk.Label(row1_frame, text="间隔(秒):", width=10)
        interval_label.pack(side=tk.LEFT)

        interval_var = tk.IntVar(value=10*(index+1))
        interval_entry = ttk.Entry(row1_frame, textvariable=interval_var, width=6)  # 调整宽度为6，能显示4位整数
        interval_entry.pack(side=tk.LEFT, padx=(0, 10))

        # 按键选择
        key_label = ttk.Label(row1_frame, text="按键:", width=5)
        key_label.pack(side=tk.LEFT)

        key_var = tk.StringVar(value=["space", "enter", "tab", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12"][index % 15])

        # 显示当前按键的标签
        timed_current_key_label = ttk.Label(row1_frame, textvariable=key_var, relief="sunken", padding=2, width=5)
        timed_current_key_label.pack(side=tk.LEFT, padx=(0, 5))

        # 设置按键按钮
        set_timed_key_btn = ttk.Button(row1_frame, text="修改按键", width=8)
        set_timed_key_btn.pack(side=tk.LEFT, padx=(0, 10))
        # 单独绑定事件，避免UnboundLocalError
        set_timed_key_btn.config(command=lambda v=key_var, b=set_timed_key_btn: self.start_key_listening(v, b))

        # 按键延迟配置
        delay_min_var = tk.IntVar(value=300)
        delay_max_var = tk.IntVar(value=500)
        ttk.Label(row1_frame, text="按键时长：").pack(side=tk.LEFT)

        # 延迟最小值输入框
        def validate_positive_int(P):
            if P == "":
                return True
            try:
                val = int(P)
                return val > 0
            except ValueError:
                return False

        delay_min_entry = ttk.Entry(row1_frame, textvariable=delay_min_var, width=5, validate="key")
        delay_min_entry.pack(side=tk.LEFT)
        delay_min_entry.configure(validatecommand=(delay_min_entry.register(validate_positive_int), '%P'))

        # 失去焦点时的验证，确保值为正整数
        def validate_min_on_focusout(event):
            value = delay_min_var.get()
            if value <= 0:
                delay_min_var.set(300)
        delay_min_entry.bind("<FocusOut>", validate_min_on_focusout)

        ttk.Label(row1_frame, text=" - ", width=2).pack(side=tk.LEFT)

        delay_max_entry = ttk.Entry(row1_frame, textvariable=delay_max_var, width=5, validate="key")
        delay_max_entry.pack(side=tk.LEFT)
        delay_max_entry.configure(validatecommand=(delay_max_entry.register(validate_positive_int), '%P'))

        # 失去焦点时的验证，确保值为正整数且不小于最小值
        def validate_max_on_focusout(event):
            min_val = delay_min_var.get()
            max_val = delay_max_var.get()
            if max_val <= 0:
                delay_max_var.set(500)
            elif max_val < min_val:
                delay_max_var.set(min_val)
        delay_max_entry.bind("<FocusOut>", validate_max_on_focusout)

        ttk.Label(row1_frame, text="ms", width=3).pack(side=tk.LEFT, padx=(0, 10))

        # 报警开关 - 为每个定时组创建独立变量
        alarm_var = tk.BooleanVar(value=False)
        alarm_switch = ttk.Checkbutton(row1_frame, text="启用报警", variable=alarm_var)
        alarm_switch.pack(side=tk.LEFT, padx=(0, 10))

        # 删除按钮
        delete_btn = ttk.Button(row1_frame, text="删除", width=6, command=lambda idx=index: self.delete_timed_group(idx))
        delete_btn.pack(side=tk.RIGHT, padx=(10, 0))

        # 鼠标点击配置
        row2_frame = ttk.Frame(group_frame)
        row2_frame.pack(fill=tk.X, pady=(0, 10))

        # 启用鼠标点击复选框
        click_enabled_var = tk.BooleanVar(value=False)
        click_enabled_switch = ttk.Checkbutton(row2_frame, text="启用鼠标点击", variable=click_enabled_var)
        click_enabled_switch.pack(side=tk.LEFT, padx=(0, 10))

        # 左侧：选择位置按钮
        select_pos_btn = ttk.Button(row2_frame, text="选择位置", width=8, command=lambda idx=index: self.start_timed_position_selection(idx))
        select_pos_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 右侧：位置显示 - 移除边框和凹陷效果，与文字识别和数字识别的显示风格保持一致
        position_var = tk.StringVar(value="未选择位置")
        position_label = ttk.Label(row2_frame, textvariable=position_var, width=15, anchor=tk.W)
        position_label.pack(side=tk.LEFT, padx=(5, 0))

        # 保存组配置
        group_config = {
            "frame": group_frame,
            "enabled": enabled_var,
            "interval": interval_var,
            "key": key_var,
            "delay_min": delay_min_var,
            "delay_max": delay_max_var,
            "alarm": alarm_var,
            "click_enabled": click_enabled_var,
            "position": position_var,
            "position_x": tk.IntVar(value=0),
            "position_y": tk.IntVar(value=0)
        }
        self.timed_groups.append(group_config)

        # 为新创建的定时组添加配置监听器
        if hasattr(self, '_setup_group_listeners'):
            self._setup_group_listeners(group_config)

        # 为新创建的定时组绑定鼠标滚轮事件
        # 获取当前标签页的画布
        canvas = self.timed_groups_frame.master
        if isinstance(canvas, tk.Canvas):
            self._bind_mousewheel_to_widgets(canvas, [group_frame])

    def delete_timed_group(self, index, confirm=True):
        """删除定时组
        Args:
            index: 要删除的定时组索引
            confirm: 是否显示确认对话框，默认为True
        """
        if len(self.timed_groups) <= 1:
            messagebox.showwarning("警告", "至少需要保留一个定时组！")
            return

        # 只有在confirm为True时才显示确认对话框
        if confirm:
            if not messagebox.askyesno("确认", f"确定要删除定时组{index+1}吗？"):
                return

        # 检查索引是否有效，避免删除后索引过期导致的IndexError
        if 0 <= index < len(self.timed_groups):
            # 移除组框架
            self.timed_groups[index]["frame"].destroy()
            # 从列表中删除
            del self.timed_groups[index]
            # 重新编号所有定时组
            self.renumber_timed_groups()
            self.log_message(f"已删除定时组{index+1}")

    def renumber_timed_groups(self):
        """重新编号所有定时组"""
        for i, group in enumerate(self.timed_groups):
            # 保持组名称前的空格，确保布局一致
            group["frame"].configure(text=f"  定时组{i+1}")

    def add_timed_group(self):
        """新增定时组"""
        if len(self.timed_groups) >= 15:
            messagebox.showwarning("警告", "最多只能创建15个定时组！")
            return

        self.create_timed_group(len(self.timed_groups))
        self.log_message(f"新增定时组{len(self.timed_groups)}")

    def create_number_tab(self, parent):
        """创建数字识别标签页"""
        number_frame = ttk.Frame(parent, padding="10")
        number_frame.pack(fill=tk.BOTH, expand=True)

        # 顶部按钮栏
        top_frame = ttk.Frame(number_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        # 新增区域按钮
        self.add_number_region_btn = ttk.Button(top_frame, text="新增识别组", command=self.add_number_region)
        self.add_number_region_btn.pack(side=tk.LEFT)

        # 区域容器，带滚动条
        regions_container = ttk.Frame(number_frame)
        regions_container.pack(fill=tk.BOTH, expand=True)

        # 垂直滚动条
        regions_scrollbar = ttk.Scrollbar(regions_container, orient=tk.VERTICAL)
        regions_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 画布，用于实现滚动
        regions_canvas = tk.Canvas(regions_container, yscrollcommand=regions_scrollbar.set, highlightthickness=0)
        regions_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        regions_scrollbar.config(command=regions_canvas.yview)

        # 内部容器，用于放置所有识别区域
        self.number_regions_frame = ttk.Frame(regions_canvas)
        regions_canvas.create_window((0, 0), window=self.number_regions_frame, anchor="nw", tags="inner_frame")

        # 配置画布尺寸和滚动区域
        def configure_scroll_region(event):
            self._configure_scroll_region(event, regions_canvas, "inner_frame")

        regions_canvas.bind("<Configure>", configure_scroll_region)
        self.number_regions_frame.bind("<Configure>", configure_scroll_region)

        # 为画布绑定鼠标滚轮事件
        regions_canvas.bind("<MouseWheel>", lambda event: self._on_mousewheel(event, regions_canvas))

        # 为内部框架绑定鼠标滚轮事件
        self.number_regions_frame.bind("<MouseWheel>", lambda event: self._on_mousewheel(event, regions_canvas))

        # 为整个标签页绑定鼠标滚轮事件
        number_frame.bind("<MouseWheel>", lambda event: self._on_mousewheel(event, regions_canvas))

        # 保存数字识别的画布和框架引用
        self.number_canvas = regions_canvas
        self.number_frame = number_frame
        self.number_regions_container = regions_container

        # 区域配置
        self.number_regions = []
        for i in range(2):
            self.create_number_region(i)

        # 绑定所有数字识别区域的鼠标滚轮事件
        self._bind_mousewheel_to_widgets(regions_canvas, [region["frame"] for region in self.number_regions])

        # 操作按钮已移除，统一由首页全局控制

    def create_number_region(self, index):
        """创建单个数字识别区域"""
        # 创建识别组框架
        region_frame = self._create_group_frame(self.number_regions_frame, index, "识别组")

        # 启用状态变量
        enabled_var = tk.BooleanVar(value=False)

        # 设置组点击事件和样式更新
        self._setup_group_click_handler(region_frame, enabled_var)

        # 初始应用样式
        self.update_group_style(region_frame, enabled_var.get())

        # 第一行：区域选择、区域坐标、删除按钮
        row1_frame = ttk.Frame(region_frame)
        row1_frame.pack(fill=tk.X, pady=(0, 10))

        # 中间：区域选择和区域坐标
        select_btn = ttk.Button(row1_frame, text="选择区域", command=lambda idx=index: self.start_number_region_selection(idx))
        select_btn.pack(side=tk.LEFT, padx=(0, 10))

        region_var = tk.StringVar(value="未选择区域")
        region_label = ttk.Label(row1_frame, textvariable=region_var, width=25)  # 设置固定宽度
        region_label.pack(side=tk.LEFT, padx=(0, 10))

        # 右侧：删除按钮
        delete_btn = ttk.Button(row1_frame, text="删除", width=6, command=lambda idx=index: self.delete_number_region(idx))
        delete_btn.pack(side=tk.RIGHT, padx=(10, 0))

        # 第二行：阈值设置、按键设置、延迟配置、报警开关
        row2_frame = ttk.Frame(region_frame)
        row2_frame.pack(fill=tk.X)

        # 阈值设置
        threshold_label = ttk.Label(row2_frame, text="阈值:", width=5)  # 减小宽度
        threshold_label.pack(side=tk.LEFT)

        threshold_var = tk.IntVar(value=500 if index == 0 else 1000)
        threshold_entry = ttk.Entry(row2_frame, textvariable=threshold_var, width=10)
        threshold_entry.pack(side=tk.LEFT, padx=(0, 10))

        # 按键设置
        key_label = ttk.Label(row2_frame, text="按键:", width=5)
        key_label.pack(side=tk.LEFT)
        key_var = tk.StringVar(value=["f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12", "space", "enter", "tab"][index % 15])

        # 按键配置区域
        number_key_config_frame = ttk.Frame(row2_frame)
        number_key_config_frame.pack(side=tk.LEFT)

        # 显示当前按键的标签
        number_current_key_label = ttk.Label(number_key_config_frame, textvariable=key_var, relief="sunken", padding=2, width=5)
        number_current_key_label.pack(side=tk.LEFT, padx=(0, 5))

        # 设置按键按钮
        set_number_key_btn = ttk.Button(number_key_config_frame, text="修改按键", width=8)
        set_number_key_btn.pack(side=tk.LEFT)
        # 单独绑定事件，避免UnboundLocalError
        set_number_key_btn.config(command=lambda v=key_var, b=set_number_key_btn: self.start_key_listening(v, b))

        # 按键延迟配置
        delay_min_var = tk.IntVar(value=100)
        delay_max_var = tk.IntVar(value=200)
        delay_frame = ttk.Frame(number_key_config_frame)
        delay_frame.pack(side=tk.LEFT, padx=(10, 0))

        # 添加"延迟："文本，确保使用全局字体样式
        ttk.Label(delay_frame, text="按键时长：").pack(side=tk.LEFT)

        # 延迟最小值输入框
        def validate_positive_int(P):
            if P == "":
                return True
            try:
                val = int(P)
                return val > 0
            except ValueError:
                return False

        delay_min_entry = ttk.Entry(delay_frame, textvariable=delay_min_var, width=5, validate="key")
        delay_min_entry.pack(side=tk.LEFT)
        delay_min_entry.configure(validatecommand=(delay_min_entry.register(validate_positive_int), '%P'))

        # 失去焦点时的验证，确保值为正整数
        def validate_min_on_focusout(event):
            value = delay_min_var.get()
            if value <= 0:
                delay_min_var.set(100)
        delay_min_entry.bind("<FocusOut>", validate_min_on_focusout)
        ttk.Label(delay_frame, text=" - ", width=2).pack(side=tk.LEFT)
        delay_max_entry = ttk.Entry(delay_frame, textvariable=delay_max_var, width=5, validate="key")
        delay_max_entry.pack(side=tk.LEFT)
        delay_max_entry.configure(validatecommand=(delay_max_entry.register(validate_positive_int), '%P'))

        # 失去焦点时的验证，确保值为正整数且不小于最小值
        def validate_max_on_focusout(event):
            min_val = delay_min_var.get()
            max_val = delay_max_var.get()
            if max_val <= 0:
                delay_max_var.set(200)
            elif max_val < min_val:
                delay_max_var.set(min_val)
        delay_max_entry.bind("<FocusOut>", validate_max_on_focusout)
        ttk.Label(delay_frame, text="ms", width=3).pack(side=tk.LEFT)
        # 报警开关 - 为每个数字识别区域创建独立变量
        alarm_var = tk.BooleanVar(value=False)
        alarm_switch = ttk.Checkbutton(number_key_config_frame, text="启用报警", variable=alarm_var)
        alarm_switch.pack(side=tk.LEFT, padx=(10, 0))

        # 保存区域配置
        region_config = {
            "frame": region_frame,
            "enabled": enabled_var,
            "region_var": region_var,
            "region": None,
            "threshold": threshold_var,
            "key": key_var,
            "delay_min": delay_min_var,
            "delay_max": delay_max_var,
            "alarm": alarm_var
        }
        self.number_regions.append(region_config)

        # 为新创建的数字识别区域添加配置监听器
        if hasattr(self, '_setup_region_listeners'):
            self._setup_region_listeners(region_config)

        # 为新创建的数字识别区域绑定鼠标滚轮事件
        # 获取当前标签页的画布
        canvas = self.number_regions_frame.master
        if isinstance(canvas, tk.Canvas):
            self._bind_mousewheel_to_widgets(canvas, [region_frame])

    def delete_number_region(self, index, confirm=True):
        """删除数字识别区域
        Args:
            index: 要删除的区域索引
            confirm: 是否显示确认对话框，默认为True
        """
        if len(self.number_regions) <= 1:
            messagebox.showwarning("警告", "至少需要保留一个识别区域！")
            return

        # 只有在confirm为True时才显示确认对话框
        if confirm:
            if not messagebox.askyesno("确认", f"确定要删除区域{index+1}吗？"):
                return

        # 检查索引是否有效，避免删除后索引过期导致的IndexError
        if 0 <= index < len(self.number_regions):
            # 移除区域框架
            self.number_regions[index]["frame"].destroy()
            # 从列表中删除
            del self.number_regions[index]
            # 重新编号所有区域
            self.renumber_number_regions()
            self.log_message(f"已删除识别组{index+1}")

    def renumber_number_regions(self):
        """重新编号所有数字识别区域"""
        for i, region in enumerate(self.number_regions):
            # 更新区域标题为"识别组"，保持名称前的空格
            region["frame"].configure(text=f"  识别组{i+1}")

    def add_number_region(self):
        """新增数字识别区域"""
        if len(self.number_regions) >= 15:
            messagebox.showwarning("警告", "最多只能创建15个识别区域！")
            return

        self.create_number_region(len(self.number_regions))
        self.log_message(f"新增识别区域{len(self.number_regions)}")

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

        # 报警声音设置
        alarm_sound_frame = ttk.LabelFrame(basic_frame, text="报警声音设置", padding="10")
        alarm_sound_frame.pack(fill=tk.X, pady=(10, 10))

        # 报警声音文件选择
        sound_file_frame = ttk.Frame(alarm_sound_frame)
        sound_file_frame.pack(fill=tk.X, pady=(0, 10))

        alarm_sound_label = ttk.Label(sound_file_frame, text="报警声音:", width=12, anchor=tk.W)
        alarm_sound_label.pack(side=tk.LEFT, padx=(0, 10))

        alarm_sound_entry = ttk.Entry(sound_file_frame, textvariable=self.alarm_sound_path, state="readonly", width=30)
        alarm_sound_entry.pack(side=tk.LEFT, padx=(0, 10))

        alarm_sound_btn = ttk.Button(sound_file_frame, text="选择", width=8,
                                   command=self.select_alarm_sound)
        alarm_sound_btn.pack(side=tk.LEFT)

        # 报警音量调节
        volume_frame = ttk.Frame(alarm_sound_frame)
        volume_frame.pack(fill=tk.X)
        volume_label = ttk.Label(volume_frame, text="音量调节:", width=12, anchor=tk.W)
        volume_label.pack(side=tk.LEFT, padx=(0, 10))

        # 音量变化跟踪函数，确保显示为整数
        def update_volume_display(*args):
            self.alarm_volume_str.set(str(self.alarm_volume.get()))

        # 绑定音量变化事件
        self.alarm_volume.trace_add("write", update_volume_display)

        volume_scale = ttk.Scale(volume_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.alarm_volume, length=200)
        volume_scale.pack(side=tk.LEFT, padx=(0, 10))

        volume_value_label = ttk.Label(volume_frame, textvariable=self.alarm_volume_str, width=3)
        volume_value_label.pack(side=tk.LEFT)

        volume_percent_label = ttk.Label(volume_frame, text="%")
        volume_percent_label.pack(side=tk.LEFT)

        # 快捷键设置 - 从首页迁移
        shortcut_frame = ttk.LabelFrame(basic_frame, text="快捷键设置", padding="10")
        shortcut_frame.pack(fill=tk.X, pady=(10, 10))

        # 单行布局
        shortcut_row = ttk.Frame(shortcut_frame)
        shortcut_row.pack(fill=tk.X, pady=5)

        # 开始快捷键
        ttk.Label(shortcut_row, text="开始运行:", width=10, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 10))
        self.start_shortcut_var = tk.StringVar(value="F10")
        start_shortcut_label = ttk.Label(shortcut_row, textvariable=self.start_shortcut_var, relief="sunken", padding=5, width=6)
        start_shortcut_label.pack(side=tk.LEFT, padx=(0, 5))
        self.set_start_shortcut_btn = ttk.Button(shortcut_row, text="修改", width=8)
        self.set_start_shortcut_btn.pack(side=tk.LEFT, padx=(0, 20))
        self.set_start_shortcut_btn.config(command=lambda: self.start_key_listening(self.start_shortcut_var, self.set_start_shortcut_btn))

        # 结束快捷键
        ttk.Label(shortcut_row, text="结束运行:", width=10, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 10))
        self.stop_shortcut_var = tk.StringVar(value="F12")
        stop_shortcut_label = ttk.Label(shortcut_row, textvariable=self.stop_shortcut_var, relief="sunken", padding=5, width=6)
        stop_shortcut_label.pack(side=tk.LEFT, padx=(0, 5))
        self.set_stop_shortcut_btn = ttk.Button(shortcut_row, text="修改", width=8)
        self.set_stop_shortcut_btn.pack(side=tk.LEFT, padx=(0, 20))
        self.set_stop_shortcut_btn.config(command=lambda: self.start_key_listening(self.stop_shortcut_var, self.set_stop_shortcut_btn))

        # 录制快捷键
        ttk.Label(shortcut_row, text="录制按钮:", width=10, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 10))
        self.record_hotkey_var = tk.StringVar(value="F11")
        record_shortcut_label = ttk.Label(shortcut_row, textvariable=self.record_hotkey_var, relief="sunken", padding=5, width=6)
        record_shortcut_label.pack(side=tk.LEFT, padx=(0, 5))
        self.set_record_shortcut_btn = ttk.Button(shortcut_row, text="修改", width=8)
        self.set_record_shortcut_btn.pack(side=tk.LEFT)
        self.set_record_shortcut_btn.config(command=lambda: self.start_key_listening(self.record_hotkey_var, self.set_record_shortcut_btn))

        # 配置管理
        config_frame = ttk.Frame(basic_frame)
        config_frame.pack(fill=tk.X, pady=(0, 10))

        save_btn = ttk.Button(config_frame, text="保存配置", command=self.save_config)
        save_btn.pack(side=tk.LEFT, padx=(0, 10))

        reset_btn = ttk.Button(config_frame, text="重置配置", command=self.load_config)
        reset_btn.pack(side=tk.LEFT)


    
    def create_home_tab(self, parent):
        """创建首页标签页"""
        home_frame = ttk.Frame(parent, padding="20")
        home_frame.pack(fill=tk.BOTH, expand=True)

        # 功能状态显示
        status_frame = ttk.LabelFrame(home_frame, text="功能状态", padding="15")
        status_frame.pack(fill=tk.X, pady=(0, 20))

        # 状态标签和勾选框
        self.status_labels = {
            "ocr": tk.StringVar(value="文字识别: 未运行"),
            "timed": tk.StringVar(value="定时功能: 未运行"),
            "number": tk.StringVar(value="数字识别: 未运行"),
            "script": tk.StringVar(value="脚本运行: 未运行")
        }

        # 勾选框变量
        self.module_check_vars = {
            "ocr": tk.BooleanVar(value=True),
            "timed": tk.BooleanVar(value=True),
            "number": tk.BooleanVar(value=True),
            "script": tk.BooleanVar(value=True)
        }

        # 保存Checkbutton组件引用
        self.module_check_buttons = {}

        # 模块名称映射
        module_names = {
            "ocr": "文字识别",
            "timed": "定时功能",
            "number": "数字识别",
            "script": "脚本运行"
        }

        # 创建带勾选框的状态行
        for module, var in self.status_labels.items():
            row_frame = ttk.Frame(status_frame)
            row_frame.pack(fill=tk.X, pady=2)  # 减少行间隔

            # 勾选框
            check_btn = ttk.Checkbutton(row_frame, variable=self.module_check_vars[module])
            check_btn.pack(side=tk.LEFT, padx=(0, 10))
            self.module_check_buttons[module] = check_btn

            # 状态标签 - 左对齐并填充可用空间，确保文本完整显示
            ttk.Label(row_frame, textvariable=var, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 全局控制按钮 - 重新定位至功能状态区域下方
        control_frame = ttk.Frame(status_frame)
        control_frame.pack(fill=tk.X, pady=(15, 0))

        # 开始/结束按钮
        self.global_start_btn = ttk.Button(control_frame, text="开始运行", command=self.start_all, style="TButton")
        self.global_start_btn.pack(side=tk.LEFT, padx=(0, 15), fill=tk.X, expand=True)

        self.global_stop_btn = ttk.Button(control_frame, text="停止运行", command=self.stop_all, style="TButton", state="disabled")
        self.global_stop_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)



        # 日志展示模块 - 添加到首页功能状态模块下方
        log_frame = ttk.LabelFrame(home_frame, text="运行日志", padding="15")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # 日志显示区域
        log_display_frame = ttk.Frame(log_frame)
        log_display_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 日志文本框
        self.home_log_text = tk.Text(log_display_frame, height=15, width=80, font=("Arial", 9), state=tk.DISABLED)
        self.home_log_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # 日志滚动条
        home_log_scrollbar = ttk.Scrollbar(log_display_frame, orient=tk.VERTICAL, command=self.home_log_text.yview)
        home_log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.home_log_text.configure(yscrollcommand=home_log_scrollbar.set)

        # 清除日志按钮 - 放置在日志展示窗口下方，固定宽度
        home_clear_btn = ttk.Button(log_frame, text="清除日志", command=self.clear_log, width=12)
        home_clear_btn.pack(side=tk.RIGHT, pady=5)

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
        """
        开始监听用户按下的按键
        Args:
            target_var: 保存按键的StringVar变量
            button: 触发监听的按钮，用于更新按钮状态
        """
        # 保存当前焦点
        current_focus = self.root.focus_get()

        # 保存原始状态文本，用于恢复
        original_status = self.status_var.get()

        # 更新按钮状态
        button.config(state="disabled")

        # 在原有状态栏显示提示信息
        self.status_var.set("请按任意按键进行设置，按ESC键清空当前记录")

        # 绑定按键事件，并保存绑定ID
        key_listener_id = self.root.bind("<KeyPress>", 
                                         lambda event: self._handle_key_press(event, target_var, button, original_status, current_focus), 
                                         add="+")

        # 设置超时，防止永久监听
        self.root.after(5000, 
                        lambda: self._handle_key_listening_timeout(button, original_status, current_focus, key_listener_id))

    def _handle_key_press(self, event, target_var, button, original_status, current_focus):
        """
        处理按键按下事件
        Args:
            event: 按键事件对象
            target_var: 保存按键的StringVar变量
            button: 触发监听的按钮
            original_status: 原始状态文本
            current_focus: 原始焦点控件
        """
        # 恢复原始状态文本
        self.status_var.set(original_status)

        # 获取按键名称
        keysym = event.keysym

        # 特殊处理ESC键：清空当前记录的按键
        if keysym == "Escape":
            return self._handle_escape_key(target_var, button, current_focus)

        # 直接使用keysym，不转换为小写，保持功能键的大小写一致性
        key = keysym

        # 确保按键在可用列表中
        if not self._is_key_available(key):
            self.log_message(f"不支持的按键: {key}")
            self._restore_button_state(button, current_focus)
            return "break"  # 阻止事件继续传播

        # 快捷键唯一性校验
        if not self._is_key_unique(key, target_var):
            self._restore_button_state(button, current_focus)
            return "break"  # 阻止事件继续传播

        # 保存按键（保持原始大小写，如F10而不是f10）
        target_var.set(key)

        # 恢复按钮状态
        self._restore_button_state(button, current_focus)

        # 记录日志
        self.log_message(f"已设置按键: {key}")

        # 保存配置
        self.save_config()

        return "break"  # 阻止事件继续传播
    
    def _handle_escape_key(self, target_var, button, current_focus):
        """
        处理ESC键按下事件
        Args:
            target_var: 保存按键的StringVar变量
            button: 触发监听的按钮
            current_focus: 原始焦点控件
        """
        # 清空当前按键配置
        target_var.set("")

        # 恢复按钮状态
        self._restore_button_state(button, current_focus)

        # 记录日志
        self.log_message("已清空当前按键设置")

        # 保存配置
        self.save_config()

        return "break"  # 阻止事件继续传播
    
    def _is_key_available(self, key):
        """
        检查按键是否在可用列表中
        Args:
            key: 按键名称

        Returns:
            bool: 如果按键可用则返回True，否则返回False
        """
        available_keys = self.get_available_keys()
        return key.lower() in available_keys

    def _is_key_unique(self, key, target_var):
        """
        检查快捷键是否唯一
        Args:
            key: 按键名称
            target_var: 保存按键的StringVar变量
        
        Returns:
            bool: 如果按键唯一则返回True，否则返回False
        """
        # 判断当前正在设置的是哪个快捷键
        is_setting_start = target_var is self.start_shortcut_var
        is_setting_stop = target_var is self.stop_shortcut_var

        if is_setting_start:
            # 检查是否与结束快捷键冲突
            if key == self.stop_shortcut_var.get():
                messagebox.showwarning("警告", "该按键已被设置为结束快捷键，请选择其他按键！")
                return False
        elif is_setting_stop:
            # 检查是否与开始快捷键冲突
            if key == self.start_shortcut_var.get():
                messagebox.showwarning("警告", "该按键已被设置为开始快捷键，请选择其他按键！")
                return False

        return True

    def _restore_button_state(self, button, current_focus):
        """
        恢复按钮状态和焦点
        Args:
            button: 触发监听的按钮
            current_focus: 原始焦点控件
        """
        # 恢复按钮状态
        button.config(state="normal")

        # 恢复焦点
        if current_focus:
            current_focus.focus_set()

    def _handle_key_listening_timeout(self, button, original_status, current_focus, key_listener_id):
        """
        处理按键监听超时
        Args:
            button: 触发监听的按钮
            original_status: 原始状态文本
            current_focus: 原始焦点控件
            key_listener_id: 按键监听绑定ID
        """
        if button.cget("state") == "disabled":
            # 恢复原始状态文本
            self.status_var.set(original_status)
            # 恢复按钮状态
            button.config(state="normal")
            self.root.unbind("<KeyPress>", funcid=key_listener_id)
            if current_focus:
                current_focus.focus_set()
            self.log_message("按键监听已超时")

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

    def _get_config_value(self, config, key_path, default=None):
        """获取配置值，支持嵌套路径
        Args:
            config: 配置字典
            key_path: 键路径，如 'tesseract.path' 或 ['tesseract', 'path']
            default: 默认值
        
        Returns:
            配置值
        """
        if isinstance(key_path, str):
            key_path = key_path.split('.')

        value = config
        for key in key_path:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def _load_tesseract_config(self, config):
        """加载Tesseract配置"""
        tesseract_path = self._get_config_value(config, 'tesseract.path')
        if not tesseract_path:
            # 兼容旧格式
            tesseract_path = config.get('tesseract_path')

        if tesseract_path and tesseract_path.strip():
            temp_path = tesseract_path.strip()
            # 检查路径是否存在
            if os.path.exists(temp_path):
                self.tesseract_path = temp_path
                self.log_message(f"从配置文件加载Tesseract路径: {self.tesseract_path}")
            else:
                self.log_message(f"配置文件中的Tesseract路径不存在: {temp_path}")

    def _clear_ocr_groups(self):
        """清空所有OCR组"""
        for group in self.ocr_groups:
            group['frame'].destroy()
        self.ocr_groups.clear()

    def _load_group_config(self, group, group_config):
        """加载单个OCR组的配置
        Args:
            group: OCR组配置字典
            group_config: 从配置文件读取的组配置
        """
        # 配置项映射
        config_mappings = {
            'enabled': lambda val: self._load_enabled_config(group, val),
            'region': lambda val: self._load_region_config(group, val),
            'interval': lambda val: group['interval'].set(val),
            'pause': lambda val: group['pause'].set(val),
            'key': lambda val: group['key'].set(val),
            'delay_min': lambda val: group['delay_min'].set(val),
            'delay_max': lambda val: group['delay_max'].set(val),
            'alarm': lambda val: group['alarm'].set(val),
            'keywords': lambda val: group['keywords'].set(val),
            'language': lambda val: group['language'].set(val),
            'click': lambda val: group['click'].set(val)
        }

        # 应用配置
        for key, setter in config_mappings.items():
            if key in group_config:
                setter(group_config[key])

    def _load_enabled_config(self, group, enabled):
        """加载启用状态配置
        Args:
            group: OCR组配置字典
            enabled: 是否启用
        """
        group['enabled'].set(enabled)
        group_frame = group['frame']
        self.update_group_style(group_frame, enabled)

    def _load_region_config(self, group, region):
        """加载区域配置
        Args:
            group: OCR组配置字典
            region: 区域坐标
        """
        if region is not None:
            try:
                region_tuple = tuple(region)
                group['region'] = region_tuple
                group['region_var'].set(f"区域: {region_tuple[0]},{region_tuple[1]} - {region_tuple[2]},{region_tuple[3]}")
            except (TypeError, ValueError):
                self.log_message(f"配置文件中的OCR区域格式错误: {region}")

    def _load_legacy_ocr_config(self, ocr_config):
        """加载旧格式的OCR配置
        Args:
            ocr_config: OCR配置字典
        """
        if 'interval' in ocr_config and ocr_config['interval'] is not None:
            self.ocr_interval = ocr_config['interval']
        if 'pause_duration' in ocr_config and ocr_config['pause_duration'] is not None:
            self.pause_duration = ocr_config['pause_duration']
        if 'selected_region' in ocr_config and ocr_config['selected_region'] is not None:
            try:
                self.selected_region = tuple(ocr_config['selected_region'])
            except (TypeError, ValueError):
                self.log_message(f"配置文件中的选择区域格式错误: {ocr_config['selected_region']}")
        if 'custom_key' in ocr_config:
            self.custom_key = ocr_config['custom_key']
        if 'custom_keywords' in ocr_config and ocr_config['custom_keywords']:
            self.custom_keywords = ocr_config['custom_keywords']
        if 'language' in ocr_config:
            self.ocr_language = ocr_config['language']

    def _load_ocr_config(self, config):
        """加载OCR配置"""
        ocr_config = self._get_config_value(config, 'ocr', {})
        groups = self._get_config_value(ocr_config, 'groups', [])

        if isinstance(groups, list):
            # 直接清空所有OCR组
            for group in self.ocr_groups:
                group['frame'].destroy()
            self.ocr_groups.clear()

            # 然后根据配置重新创建所有OCR组
            for i, group_config in enumerate(groups):
                if isinstance(group_config, dict):
                    # 直接调用create_ocr_group创建OCR组
                    self.create_ocr_group(i)
                    # 设置组配置
                    if i < len(self.ocr_groups):
                        if 'enabled' in group_config:
                            enabled = group_config['enabled']
                            self.ocr_groups[i]['enabled'].set(enabled)
                            # 使用类方法更新样式
                            group_frame = self.ocr_groups[i]['frame']
                            self.update_group_style(group_frame, enabled)
                        if 'region' in group_config and group_config['region'] is not None:
                            try:
                                region = tuple(group_config['region'])
                                self.ocr_groups[i]['region'] = region
                                self.ocr_groups[i]['region_var'].set(f"区域: {region[0]},{region[1]} - {region[2]},{region[3]}")
                            except (TypeError, ValueError):
                                self.log_message(f"配置文件中的OCR区域格式错误: {group_config['region']}")
                        if 'interval' in group_config:
                            self.ocr_groups[i]['interval'].set(group_config['interval'])
                        if 'pause' in group_config:
                            self.ocr_groups[i]['pause'].set(group_config['pause'])
                        if 'key' in group_config:
                            self.ocr_groups[i]['key'].set(group_config['key'])
                        if 'delay_min' in group_config:
                            self.ocr_groups[i]['delay_min'].set(group_config['delay_min'])
                        if 'delay_max' in group_config:
                            self.ocr_groups[i]['delay_max'].set(group_config['delay_max'])
                        if 'alarm' in group_config:
                            self.ocr_groups[i]['alarm'].set(group_config['alarm'])
                        if 'keywords' in group_config:
                            self.ocr_groups[i]['keywords'].set(group_config['keywords'])
                        if 'language' in group_config:
                            self.ocr_groups[i]['language'].set(group_config['language'])
                        if 'click' in group_config:
                            self.ocr_groups[i]['click'].set(group_config['click'])

            # 如果没有配置，至少创建一个OCR组
            if len(self.ocr_groups) == 0:
                self.create_ocr_group(0)
        else:
            # 兼容旧格式
            if 'interval' in ocr_config and ocr_config['interval'] is not None:
                self.ocr_interval = ocr_config['interval']
            if 'pause_duration' in ocr_config and ocr_config['pause_duration'] is not None:
                self.pause_duration = ocr_config['pause_duration']
            if 'selected_region' in ocr_config and ocr_config['selected_region'] is not None:
                try:
                    self.selected_region = tuple(ocr_config['selected_region'])
                except (TypeError, ValueError):
                    self.log_message(f"配置文件中的选择区域格式错误: {ocr_config['selected_region']}")
            if 'custom_key' in ocr_config:
                self.custom_key = ocr_config['custom_key']
            if 'custom_keywords' in ocr_config and ocr_config['custom_keywords']:
                self.custom_keywords = ocr_config['custom_keywords']
            if 'language' in ocr_config:
                self.ocr_language = ocr_config['language']

    def _load_click_config(self, config):
        """加载点击模式和坐标配置（保持兼容性）"""
        # 保持配置文件兼容性，但不再加载坐标模式配置
        # 旧配置文件中的click部分将被忽略
        pass

    def _clear_timed_groups(self):
        """清空所有定时组"""
        for group in self.timed_groups:
            group['frame'].destroy()
        self.timed_groups.clear()

    def _load_timed_group_config(self, group, group_config):
        """加载单个定时组的配置
        Args:
            group: 定时组配置字典
            group_config: 从配置文件读取的组配置
        """
        # 配置项映射
        config_mappings = {
            'enabled': lambda val: self._load_timed_enabled_config(group, val),
            'interval': lambda val: group['interval'].set(val),
            'key': lambda val: group['key'].set(val),
            'delay_min': lambda val: group['delay_min'].set(val),
            'delay_max': lambda val: group['delay_max'].set(val),
            'click_enabled': lambda val: group['click_enabled'].set(val),
            'position_x': lambda val: group['position_x'].set(val),
            'position_y': lambda val: group['position_y'].set(val),
            'position': lambda val: group['position'].set(val)
        }

        # 应用配置
        for key, setter in config_mappings.items():
            if key in group_config:
                setter(group_config[key])

    def _load_timed_enabled_config(self, group, enabled):
        """加载定时组启用状态配置
        Args:
            group: 定时组配置字典
            enabled: 是否启用
        """
        group['enabled'].set(enabled)
        group_frame = group['frame']
        self.update_group_style(group_frame, enabled)

    def _load_timed_config(self, config):
        """加载定时功能配置"""
        timed_config = config.get('timed_key_press', {})
        groups = self._get_config_value(timed_config, 'groups', [])

        if isinstance(groups, list):
            self._clear_timed_groups()

            # 根据配置重新创建所有定时组
            for i, group_config in enumerate(groups):
                if isinstance(group_config, dict):
                    self.create_timed_group(i)
                    # 设置组配置
                    if i < len(self.timed_groups):
                        self._load_timed_group_config(self.timed_groups[i], group_config)

            # 如果没有配置，至少创建一个定时组
            if len(self.timed_groups) == 0:
                self.create_timed_group(0)

    def _clear_number_regions(self):
        """清空所有数字识别区域"""
        for region in self.number_regions:
            region['frame'].destroy()
        self.number_regions.clear()

    def _load_number_enabled_config(self, number_region, enabled):
        """加载数字识别区域启用状态配置
        Args:
            number_region: 数字识别区域配置
            enabled: 是否启用
        """
        number_region['enabled'].set(enabled)
        region_frame = number_region['frame']
        self.update_group_style(region_frame, enabled)

    def _load_number_region_coordinates(self, number_region, region_config):
        """加载数字识别区域坐标配置
        Args:
            number_region: 数字识别区域配置
            region_config: 从配置文件读取的区域配置
        """
        if 'region' in region_config and region_config['region'] is not None:
            try:
                region = tuple(region_config['region'])
                number_region['region'] = region
                number_region['region_var'].set(f"区域: {region[0]},{region[1]} - {region[2]},{region[3]}")
            except (TypeError, ValueError):
                self.log_message(f"配置文件中的数字识别区域格式错误: {region_config['region']}")

    def _load_number_region_config(self, number_region, region_config):
        """加载单个数字识别区域的配置
        Args:
            number_region: 数字识别区域配置
            region_config: 从配置文件读取的区域配置
        """
        # 配置项映射
        config_mappings = {
            'enabled': lambda val: self._load_number_enabled_config(number_region, val),
            'threshold': lambda val: number_region['threshold'].set(val),
            'key': lambda val: number_region['key'].set(val),
            'delay_min': lambda val: number_region['delay_min'].set(val),
            'delay_max': lambda val: number_region['delay_max'].set(val)
        }

        # 应用配置
        for key, setter in config_mappings.items():
            if key in region_config:
                setter(region_config[key])

        # 单独处理区域坐标配置
        self._load_number_region_coordinates(number_region, region_config)

    def _load_number_config(self, config):
        """加载数字识别配置"""
        number_config = config.get('number_recognition', {})
        regions = self._get_config_value(number_config, 'regions', [])

        if isinstance(regions, list):
            self._clear_number_regions()

            # 根据配置重新创建所有数字识别区域
            for i, region_config in enumerate(regions):
                if isinstance(region_config, dict):
                    self.create_number_region(i)
                    # 设置区域配置
                    if i < len(self.number_regions):
                        self._load_number_region_config(self.number_regions[i], region_config)

            # 如果没有配置，至少创建一个数字识别区域
            if len(self.number_regions) == 0:
                self.create_number_region(0)

    def _load_alarm_config(self, config):
        """
        加载报警配置
        Args:
            config: 配置字典
        """
        alarm_config = self._get_config_value(config, 'alarm', {})

        # 加载全局报警声音
        if 'sound' in alarm_config:
            self.alarm_sound_path.set(alarm_config['sound'])

        # 加载报警音量
        if 'volume' in alarm_config:
            self.alarm_volume.set(alarm_config['volume'])
            self.alarm_volume_str.set(str(alarm_config['volume']))

        # 加载各模块报警开关状态
        for module in ["ocr", "timed", "number"]:
            module_config = alarm_config.get(module, {})
            if 'enabled' in module_config:
                self.alarm_enabled[module].set(module_config['enabled'])

    def _load_shortcuts_config(self, config):
        """加载快捷键配置"""
        shortcuts_config = self._get_config_value(config, 'shortcuts', {})
        if hasattr(self, 'start_shortcut_var') and 'start' in shortcuts_config:
            self.start_shortcut_var.set(shortcuts_config['start'])
        if hasattr(self, 'stop_shortcut_var') and 'stop' in shortcuts_config:
            self.stop_shortcut_var.set(shortcuts_config['stop'])

    def _load_home_checkboxes_config(self, config):
        """加载首页勾选框配置"""
        if 'home_checkboxes' in config and hasattr(self, 'module_check_vars'):
            home_checkboxes = config['home_checkboxes']
            for module in ['ocr', 'timed', 'number']:
                if module in home_checkboxes:
                    self.module_check_vars[module].set(home_checkboxes[module])

    def _load_script_config(self, config):
        """加载脚本和颜色识别配置"""
        script_config = self._get_config_value(config, 'script', {})

        # 加载脚本内容
        if 'script_content' in script_config and hasattr(self, 'script_text'):
            script_content = script_config['script_content']
            self.script_text.delete(1.0, tk.END)
            self.script_text.insert(1.0, script_content)

        # 加载颜色识别命令内容
        if 'color_commands' in script_config and hasattr(self, 'color_commands_text'):
            color_commands_content = script_config['color_commands']
            self.color_commands_text.delete(1.0, tk.END)
            self.color_commands_text.insert(1.0, color_commands_content)

        # 加载颜色识别区域
        if 'color_recognition_region' in script_config and script_config['color_recognition_region']:
            color_recognition_region = script_config['color_recognition_region']
            if hasattr(self, 'region_var'):
                try:
                    x1, y1, x2, y2 = color_recognition_region
                    self.region_var.set(f"({x1}, {y1}) - ({x2}, {y2})")
                    # 同时更新实际使用的属性
                    self.color_recognition_region = color_recognition_region
                except (TypeError, ValueError):
                    self.log_message(f"配置文件中的颜色识别区域格式错误: {color_recognition_region}")

        # 加载目标颜色
        if 'target_color' in script_config and script_config['target_color']:
            target_color = script_config['target_color']
            if hasattr(self, 'color_var'):
                try:
                    r, g, b = target_color
                    self.color_var.set(f"RGB({r}, {g}, {b})")
                    if hasattr(self, 'color_display'):
                        self.color_display.config(background=f"#{r:02x}{g:02x}{b:02x}")
                    # 同时更新实际使用的属性
                    self.target_color = target_color
                except (TypeError, ValueError):
                    self.log_message(f"配置文件中的目标颜色格式错误: {target_color}")

        # 加载颜色容差
        if 'color_tolerance' in script_config and hasattr(self, 'tolerance_var'):
            color_tolerance = script_config['color_tolerance']
            self.tolerance_var.set(color_tolerance)

        # 加载检查间隔
        if 'color_interval' in script_config and hasattr(self, 'interval_var'):
            color_interval = script_config['color_interval']
            self.interval_var.set(color_interval)

        # 加载颜色识别启用状态
        if 'color_recognition_enabled' in script_config and hasattr(self, 'color_recognition_enabled'):
            color_recognition_enabled = script_config['color_recognition_enabled']
            self.color_recognition_enabled.set(color_recognition_enabled)

    def load_config(self):
        """
        加载配置
        增强错误处理，能够处理文件不存在、格式错误或路径配置缺失等异常情况
        确保加载所有前端设置，包括新增功能的相关配置
        支持新旧配置格式的兼容处理
        
        Returns:
            bool: 如果配置加载成功则返回True，否则返回False
        """
        # 初始化配置加载结果
        config_loaded = False
        config_version = '1.0.0'
        config = None

        # 根据配置文件是否存在选择不同的读取方式
        if os.path.exists(self.config_file_path):
            config = self._read_config_file()
        else:
            self.log_message(f"配置文件不存在: {self.config_file_path}")

        # 如果成功读取配置文件，则加载配置
        if config:
            config_loaded, config_version = self._process_config(config)

        # 更新配置文件版本号（如果与当前版本不一致）
        if config_loaded and config:
            self._update_config_version(config, config_version)

        # 无论配置是否加载成功，都更新界面中的Tesseract路径变量
        self._update_tesseract_path_var()

        return config_loaded

    def _read_config_file(self):
        """
        读取配置文件
        Returns:
            dict or None: 如果成功读取则返回配置字典，否则返回None
        """
        try:
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.log_message(f"开始加载配置: {self.config_file_path}")
            return config
        except json.JSONDecodeError as e:
            self.log_message(f"配置文件格式错误: {self.config_file_path}，错误详情: {str(e)}")
        except PermissionError:
            self.log_message(f"没有权限读取配置文件: {self.config_file_path}")
        except IOError as e:
            self.log_message(f"配置文件IO错误: {str(e)}")
        except Exception as e:
            self.log_message(f"配置加载错误: {str(e)}")
        return None

    def _process_config(self, config):
        """
        处理配置数据
        Args:
            config: 配置字典
        
        Returns:
            tuple: (config_loaded, config_version)，其中config_loaded是布尔值，config_version是配置版本字符串
        """
        try:
            # 获取配置版本，默认为1.0.0
            config_version = self._get_config_value(config, 'version', '1.0.0')
            self.log_message(f"配置版本: {config_version}")

            # 加载各部分配置
            self._load_tesseract_config(config)
            self._load_ocr_config(config)
            self._load_click_config(config)
            self._load_timed_config(config)
            self._load_number_config(config)
            self._load_alarm_config(config)
            self._load_shortcuts_config(config)
            self._load_home_checkboxes_config(config)
            self._load_script_config(config)

            # 更新界面控件状态
            # 移除不存在的方法调用

            self.log_message("配置加载成功")
            return True, config_version
        except Exception as e:
            self.log_message(f"处理配置时发生错误: {str(e)}")
            return False, '1.0.0'

    def _update_config_version(self, config, config_version):
        """
        更新配置文件版本号
        Args:
            config: 配置字典
            config_version: 当前配置版本
        """
        if config_version != VERSION:
            self.log_message(f"配置版本更新: {config_version} → {VERSION}")
            # 更新配置版本并保存
            config['version'] = VERSION
            config['last_save_time'] = datetime.datetime.now().isoformat()
            try:
                with open(self.config_file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
            except Exception as e:
                self.log_message(f"更新配置版本失败: {str(e)}")

    def _update_tesseract_path_var(self):
        """
        更新界面中的Tesseract路径变量
        """
        if hasattr(self, 'tesseract_path_var'):
            self.tesseract_path_var.set(self.tesseract_path)

    def setup_config_listeners(self):
        """为配置变量添加监听器，自动保存配置"""
        # 通用的延迟保存函数，避免频繁保存
        def delayed_save(*args):
            self.root.after(1000, self.save_config)

        # 即时保存函数
        def immediate_save(*args):
            self.save_config()

        # 定时任务配置监听器
        def setup_group_listeners(group):
            group["enabled"].trace_add("write", immediate_save)
            group["interval"].trace_add("write", delayed_save)
            group["key"].trace_add("write", immediate_save)

        # 为所有现有定时组添加监听器
        for group in self.timed_groups:
            setup_group_listeners(group)

        # 保存监听器函数，以便后续新增定时组时使用
        self._setup_group_listeners = setup_group_listeners

        # 数字识别配置监听器
        def setup_region_listeners(region_config):
            region_config["enabled"].trace_add("write", immediate_save)
            region_config["threshold"].trace_add("write", delayed_save)
            region_config["key"].trace_add("write", immediate_save)

        # 为所有现有区域添加监听器
        for region_config in self.number_regions:
            setup_region_listeners(region_config)

        # 保存监听器函数，以便后续新增区域时使用
        self._setup_region_listeners = setup_region_listeners

        #  OCR组配置监听器
        def setup_ocr_group_listeners(group):
            group["enabled"].trace_add("write", immediate_save)
            group["interval"].trace_add("write", delayed_save)
            group["pause"].trace_add("write", delayed_save)
            group["key"].trace_add("write", immediate_save)
            group["delay_min"].trace_add("write", delayed_save)
            group["delay_max"].trace_add("write", delayed_save)
            group["alarm"].trace_add("write", immediate_save)
            group["keywords"].trace_add("write", delayed_save)
            group["language"].trace_add("write", immediate_save)
            group["click"].trace_add("write", immediate_save)

        # 为所有现有OCR组添加监听器
        for group in self.ocr_groups:
            setup_ocr_group_listeners(group)

        # 保存监听器函数，以便后续新增OCR组时使用
        self._setup_ocr_group_listeners = setup_ocr_group_listeners

        # 首页模块勾选状态监听器
        if hasattr(self, 'module_check_vars'):
            for module, var in self.module_check_vars.items():
                var.trace_add("write", immediate_save)

        # 快捷键配置监听器
        self.start_shortcut_var.trace_add("write", lambda *args: (immediate_save(), self.setup_shortcuts()))
        self.stop_shortcut_var.trace_add("write", lambda *args: (immediate_save(), self.setup_shortcuts()))

        # 脚本和颜色识别配置监听器
        # 为脚本文本框添加内容变化监听器
        if hasattr(self, 'script_text'):
            def on_script_change(event):
                if self.script_text.edit_modified():
                    delayed_save()
                    self.script_text.edit_modified(False)
            self.script_text.bind("<<Modified>>", on_script_change)
            self.script_text.edit_modified(False)

        # 为颜色识别命令文本框添加内容变化监听器
        if hasattr(self, 'color_commands_text'):
            def on_color_commands_change(event):
                if self.color_commands_text.edit_modified():
                    delayed_save()
                    self.color_commands_text.edit_modified(False)
            self.color_commands_text.bind("<<Modified>>", on_color_commands_change)
            self.color_commands_text.edit_modified(False)

        # 为颜色识别启用状态添加监听器
        if hasattr(self, 'color_recognition_enabled'):
            self.color_recognition_enabled.trace_add("write", immediate_save)

        # 为颜色容差添加监听器
        if hasattr(self, 'tolerance_var'):
            self.tolerance_var.trace_add("write", delayed_save)

        # 为检查间隔添加监听器
        if hasattr(self, 'interval_var'):
            self.interval_var.trace_add("write", delayed_save)

    def _stop_old_listener(self):
        """停止旧的全局键盘监听器（如果存在）"""
        if hasattr(self, 'global_listener') and self.global_listener:
            self.global_listener.stop()

    def _get_key_name(self, key):
        """获取按键名称
        Args:
            key: 按键对象
        
        Returns:
            str: 按键名称
        """
        if hasattr(key, 'name'):
            # 普通按键
            return key.name.upper()
        elif hasattr(key, 'char') and key.char:
            # 字符按键
            return key.char.upper()
        elif hasattr(key, 'vk'):
            # 特殊按键（F键等）
            if 112 <= key.vk <= 123:  # VK_F1=112, VK_F12=123
                return f"F{key.vk - 111}"  # F1=112-111=1, 依此类推
            else:
                return str(key)
        else:
            return str(key)

    def _handle_global_key_press(self, key):
        """处理全局按键事件
        Args:
            key: 按键对象
        """
        try:
            key_name = self._get_key_name(key)

            # 检查是否是开始快捷键
            if key_name == self.start_shortcut_var.get().upper() and not self.is_running:
                self.root.after(0, self.start_all)
            # 检查是否是结束快捷键
            if key_name == self.stop_shortcut_var.get().upper() and self.is_running:
                self.root.after(0, self.stop_all)
            # 检查是否是录制快捷键
            if key_name == self.record_hotkey_var.get().upper():
                self.root.after(0, lambda: (
                    self.start_recording() if not hasattr(self, 'script_executor') or not getattr(self.script_executor, 'is_recording', False) else self.stop_recording()
                ))
        except Exception as e:
            self.log_message(f"全局快捷键处理错误: {str(e)}")

    def _setup_global_shortcuts(self):
        """设置全局快捷键"""
        if PYINPUT_AVAILABLE:
            # 创建并启动全局键盘监听器
            self.global_listener = keyboard.Listener(on_press=self._handle_global_key_press)
            self.global_listener.start()
            self.log_message("全局快捷键监听已启动")
            return True
        return False



    def setup_shortcuts(self):
        """设置快捷键绑定"""
        # 停止旧的全局键盘监听器（如果存在）
        self._stop_old_listener()

        # 只使用全局快捷键
        if self._setup_global_shortcuts():
            self.log_message("全局快捷键设置成功")
        else:
            self.log_message("全局快捷键设置失败，快捷键功能将不可用")

    def clear_log(self):
        """清除日志"""
        # 清除首页的日志文本框
        if hasattr(self, 'home_log_text'):
            self.home_log_text.config(state=tk.NORMAL)
            self.home_log_text.delete("1.0", tk.END)
            self.home_log_text.config(state=tk.DISABLED)

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
        """
        记录日志信息
        Args:
            message: 要记录的日志消息
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        # 写入日志文件
        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"写入日志文件失败: {str(e)}")

        # 写入首页的日志文本框
        if hasattr(self, 'home_log_text'):
            self.home_log_text.config(state=tk.NORMAL)
            self.home_log_text.insert(tk.END, log_entry)
            self.home_log_text.see(tk.END)
            self.home_log_text.config(state=tk.DISABLED)

        # 更新状态标签（仅当status_var已创建）
        if hasattr(self, 'status_var'):
            self.status_var.set(message.split(":")[0] if ":" in message else message)

    def start_region_selection(self):
        """开始区域选择（兼容旧方法）"""
        if self.ocr_groups:
            self.start_ocr_region_selection(0)
        else:
            self._start_selection("ocr", 0)

    def _start_selection(self, selection_type, region_index):
        """
        通用的区域选择方法
        Args:
            selection_type: 选择类型，"normal"、"number"或"ocr"
            region_index: 识别区域索引，仅当selection_type为"number"或"ocr"时有效
        """
        self.log_message(f"开始{'数字识别区域' if selection_type == 'number' else '文字识别区域' if selection_type == 'ocr' else ''}区域选择...")
        self.is_selecting = True
        self.selection_type = selection_type

        if selection_type == "number":
            self.current_number_region_index = region_index
        elif selection_type == "ocr":
            self.current_ocr_region_index = region_index

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

    def _save_selection(self, start_x, start_y, end_x, end_y):
        """保存选择区域的公共方法"""
        # 确保选择区域有效
        if abs(end_x - start_x) < 10 or abs(end_y - start_y) < 10:
            messagebox.showwarning("警告", "选择的区域太小，请重新选择")
            self.cancel_selection()
            return None

        # 保存选择区域（使用绝对坐标）
        region = (
            min(start_x, end_x),
            min(start_y, end_y),
            max(start_x, end_x),
            max(start_y, end_y)
        )

        return region

    def on_mouse_up(self, event):
        """
        鼠标释放事件
        """
        # 获取结束绝对坐标
        end_x_abs = event.x_root
        end_y_abs = event.y_root

        # 保存选择区域
        region = self._save_selection(self.start_x_abs, self.start_y_abs, end_x_abs, end_y_abs)
        if region is None:
            return

        # 根据选择类型保存区域
        if hasattr(self, 'selection_type'):
            if self.selection_type == 'ocr':
                # OCR组区域选择
                if self.current_ocr_region_index is not None and 0 <= self.current_ocr_region_index < len(self.ocr_groups):
                    self.ocr_groups[self.current_ocr_region_index]['region'] = region
                    self.ocr_groups[self.current_ocr_region_index]['region_var'].set(f"区域: {region[0]},{region[1]} - {region[2]},{region[3]}")
                    self.log_message(f"已为识别组{self.current_ocr_region_index+1}选择区域: {region}")
            elif self.selection_type == 'color':
                # 颜色识别区域选择
                if not hasattr(self, 'color_recognition'):
                    self.color_recognition = ColorRecognition(self)
                self.color_recognition.set_region(region)
                self.color_recognition_region = region
                if hasattr(self, 'region_var'):
                    self.region_var.set(f"({region[0]}, {region[1]}) - ({region[2]}, {region[3]})")
                self.log_message(f"已选择颜色识别区域: {region}")
            else:
                # 兼容旧方法
                self.selected_region = region
                if hasattr(self, 'region_var'):
                    self.region_var.set(f"区域: {region[0]},{region[1]} - {region[2]},{region[3]}")
                self.log_message(f"已选择区域: {region}")
        else:
            # 兼容旧方法
            self.selected_region = region
            if hasattr(self, 'region_var'):
                self.region_var.set(f"区域: {region[0]},{region[1]} - {region[2]},{region[3]}")
            self.log_message(f"已选择区域: {region}")

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
            messagebox.showinfo("提示", "Tesseract OCR引擎未配置，请在设置中配置Tesseract路径后使用文字识别功能！")
            return

        # 检查是否有启用的OCR组且已选择区域
        has_enabled_group = False
        for group in self.ocr_groups:
            if group["enabled"].get() and group["region"]:
                has_enabled_group = True
                break

        if not has_enabled_group:
            messagebox.showwarning("警告", "请至少启用一个识别组并选择区域")
            return

        self.is_running = True
        self.is_paused = False

        # 更新状态标签
        self.status_labels["ocr"].set("文字识别: 运行中")
        self.log_message("开始监控...")

        # 启动OCR线程
        self.ocr_thread = threading.Thread(target=self.ocr_loop, daemon=True)
        self.ocr_thread.start()

    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False

        # 更新状态标签
        self.status_labels["ocr"].set("文字识别: 未运行")

    def _calculate_min_interval(self):
        """计算所有启用组的最小间隔时间
        Returns:
            int: 最小间隔时间
        """
        enabled_groups = [group for group in self.ocr_groups if group["enabled"].get()]
        if enabled_groups:
            return min(group["interval"].get() for group in enabled_groups)
        return 5

    def _wait_for_interval(self, interval):
        """等待设定的间隔时间
        Args:
            interval: 间隔时间（秒）
        """
        for _ in range(interval):
            if not self.is_running:
                break
            time.sleep(1)

    def _should_process_group(self, group, i, current_time):
        """检查是否应该处理指定的OCR组
        Args:
            group: OCR组配置
            i: 组索引
            current_time: 当前时间

        Returns:
            bool: 是否应该处理
        """
        # 检查组是否启用且已选择区域
        if not group["enabled"].get() or not group["region"]:
            return False

        # 获取组配置
        pause_duration = group["pause"].get()
        group_interval = group["interval"].get()

        # 检查是否在暂停期（触发动作后）
        if current_time - self.last_trigger_times[i] < pause_duration:
            return False

        # 检查是否达到识别间隔
        if current_time - self.last_recognition_times[i] < group_interval:
            return False

        return True

    def ocr_loop(self):
        """OCR识别循环"""
        # 初始化每个组的上次识别时间和上次触发时间
        self.last_recognition_times = {i: 0 for i in range(len(self.ocr_groups))}  # 用于识别间隔
        self.last_trigger_times = {i: 0 for i in range(len(self.ocr_groups))}  # 用于暂停期

        while self.is_running:
            try:
                # 等待下一次识别，使用最小间隔
                min_interval = self._calculate_min_interval()
                self._wait_for_interval(min_interval)

                # 检查是否需要暂停
                if self.is_paused:
                    continue

                current_time = time.time()

                # 遍历所有OCR组，并行处理
                for i, group in enumerate(self.ocr_groups):
                    if self._should_process_group(group, i, current_time):
                        # 执行OCR识别
                        self.perform_ocr_for_group(group, i)
                        # 更新上次识别时间
                        self.last_recognition_times[i] = current_time
            except Exception as e:
                self.log_message(f"错误: {str(e)}")
                time.sleep(5)

    def perform_ocr(self):
        """执行OCR识别（兼容旧方法）"""
        # 如果有OCR组，使用第一个组的配置
        if self.ocr_groups:
            self.perform_ocr_for_group(self.ocr_groups[0], 0)
        else:
            try:
                # 截取屏幕区域
                if hasattr(self, 'selected_region') and self.selected_region:
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
                    current_lang = self.language_var.get() if hasattr(self, 'language_var') else 'eng'
                    text = pytesseract.image_to_string(screenshot, lang=current_lang)
                    self.log_message(f"识别结果: '{text.strip()}'")

                    # 检查是否包含关键词
                    lower_text = text.lower()
                    keywords = self.custom_keywords if hasattr(self, 'custom_keywords') else ['men', 'door']
                    if any(keyword in lower_text for keyword in keywords):
                        self.trigger_action()
            except Exception as e:
                self.log_message(f"OCR错误: {str(e)}")

    def _validate_ocr_group_input(self, group, group_index):
        """
        验证OCR组输入参数
        Args:
            group: OCR组配置字典
            group_index: OCR组索引
        
        Returns:
            tuple: (valid, region, keywords_str, current_lang, click_enabled)
        """
        if not group:
            self.log_message(f"识别组{group_index+1}错误: 组配置为空")
            return False, None, None, None, None

        region = group.get("region")
        if not region:
            self.log_message(f"识别组{group_index+1}错误: 未设置识别区域")
            return False, None, None, None, None

        keywords_str = group.get("keywords", tk.StringVar(value="")).get().strip()
        current_lang = group.get("language", tk.StringVar(value="eng")).get()
        click_enabled = group.get("click", tk.BooleanVar(value=False)).get()
        return True, region, keywords_str, current_lang, click_enabled

    def _validate_region_coordinates(self, region, group_index):
        """
        验证并规范化区域坐标
        Args:
            region: 区域坐标
            group_index: OCR组索引
        
        Returns:
            tuple: (valid, left, top, right, bottom)
        """
        try:
            x1, y1, x2, y2 = region
            if len(region) != 4:
                raise ValueError("区域坐标格式错误")
        except (ValueError, TypeError) as e:
            self.log_message(f"识别组{group_index+1}错误: 区域坐标无效 - {str(e)}")
            return False, None, None, None, None

        # 确保坐标是(left, top, right, bottom)格式
        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1, x2)
        bottom = max(y1, y2)

        # 验证区域大小
        if (right - left) < 10 or (bottom - top) < 10:
            self.log_message(f"识别组{group_index+1}错误: 识别区域太小")
            return False, None, None, None, None

        return True, left, top, right, bottom

    def _capture_screen_region(self, left, top, right, bottom, group_index):
        """
        截取屏幕区域
        Args:
            left: 左上角x坐标
            top: 左上角y坐标
            right: 右下角x坐标
            bottom: 右下角y坐标
            group_index: OCR组索引

        Returns:
            Image: 截图图像
        """
        try:
            return ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)
        except Exception as e:
            self.log_message(f"识别组{group_index+1}错误: 屏幕截图失败 - {str(e)}")
            return None

    def _preprocess_image(self, image, group_index):
        """
        图像预处理
        Args:
            image: 原始图像
            group_index: OCR组索引

        Returns:
            Image: 处理后的图像
        """
        try:
            # 转换为灰度图像以提高识别率
            image = image.convert('L')

            # 添加图像预处理，提高识别精度
            from PIL import ImageEnhance, ImageFilter

            # 提高对比度
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)

            # 锐化图像
            image = image.filter(ImageFilter.SHARPEN)

            # 添加阈值处理，增强文字与背景的对比度
            image = image.point(lambda p: p > 128 and 255)

            return image
        except Exception as e:
            self.log_message(f"识别组{group_index+1}错误: 图像处理失败 - {str(e)}")
            return None

    def _perform_ocr(self, image, lang, group_index):
        """
        执行OCR识别
        Args:
            image: 处理后的图像
            lang: 识别语言
            group_index: OCR组索引

        Returns:
            str: 识别结果
        """
        try:
            # 使用优化的Tesseract配置进行OCR识别
            custom_config = r'--psm 6 --oem 3'
            text = pytesseract.image_to_string(image, lang=lang, config=custom_config)
            return text
        except pytesseract.TesseractError as e:
            self.log_message(f"识别组{group_index+1}错误: OCR识别失败 - {str(e)}")
            return None
        except Exception as e:
            self.log_message(f"识别组{group_index+1}错误: OCR引擎错误 - {str(e)}")
            return None

    def _find_keyword_position(self, image, keywords, lang, left, top, right, bottom, group_index):
        """
        查找关键词位置
        Args:
            image: 处理后的图像
            keywords: 关键词列表
            lang: 识别语言
            left: 左上角x坐标
            top: 左上角y坐标
            right: 右下角x坐标
            bottom: 右下角y坐标
            group_index: OCR组索引

        Returns:
            tuple: 点击位置坐标
        """
        try:
            # 使用image_to_data获取文字位置信息，使用相同的优化配置
            custom_config = r'--psm 6 --oem 3'
            data = pytesseract.image_to_data(image, lang=lang, config=custom_config, output_type=pytesseract.Output.DICT)

            # 遍历所有识别到的文字，找到关键词的位置
            for i in range(len(data['text'])):
                word = data['text'][i].lower().strip()
                if word in keywords or any(keyword in word for keyword in keywords):
                    # 获取文字的边界框
                    left_word = data['left'][i]
                    top_word = data['top'][i]
                    width = data['width'][i]
                    height = data['height'][i]

                    # 计算文字中心位置（相对于截图）
                    center_x = left_word + width // 2
                    center_y = top_word + height // 2

                    # 转换为屏幕坐标
                    return (left + center_x, top + center_y)

            # 如果没有找到关键词位置，使用区域中心
            return ((left + right) // 2, (top + bottom) // 2)
        except Exception as e:
            self.log_message(f"识别组{group_index+1}错误: 获取文字位置失败 - {str(e)}")
            # 失败时使用区域中心
            return ((left + right) // 2, (top + bottom) // 2)

    def perform_ocr_for_group(self, group, group_index):
        """
        为单个OCR组执行OCR识别
        Args:
            group: OCR组配置字典
            group_index: OCR组索引
        """
        try:
            # 验证输入参数
            valid, region, keywords_str, current_lang, click_enabled = self._validate_ocr_group_input(group, group_index)
            if not valid:
                return

            # 验证区域坐标
            valid, left, top, right, bottom = self._validate_region_coordinates(region, group_index)
            if not valid:
                return

            # 截取屏幕区域
            screenshot = self._capture_screen_region(left, top, right, bottom, group_index)
            if not screenshot:
                return

            # 图像预处理
            processed_image = self._preprocess_image(screenshot, group_index)
            if not processed_image:
                return

            # OCR识别
            text = self._perform_ocr(processed_image, current_lang, group_index)
            if not text:
                return

            self.log_message(f"识别组{group_index+1}识别结果: '{text.strip()}'")

            # 检查是否包含关键词
            lower_text = text.lower()
            if keywords_str:
                keywords = [keyword.strip().lower() for keyword in keywords_str.split(",") if keyword.strip()]
                if any(keyword in lower_text for keyword in keywords):
                    # 确定点击位置
                    if click_enabled:
                        click_pos = self._find_keyword_position(processed_image, keywords, current_lang, left, top, right, bottom, group_index)
                    else:
                        # 未启用点击，使用区域中心
                        click_pos = ((left + right) // 2, (top + bottom) // 2)

                    # 触发动作，传递文字位置
                    self.trigger_action_for_group(group, group_index, click_enabled, click_pos)

        except Exception as e:
            self.log_message(f"识别组{group_index+1}错误: 未知错误 - {str(e)}")
            import traceback
            self.log_message(f"错误详情: {traceback.format_exc()}")

    def _validate_trigger_input(self, group, group_index):
        """
        验证触发动作的输入参数
        Args:
            group: OCR组配置字典
            group_index: OCR组索引
        
        Returns:
            tuple: (valid, key, delay_min, delay_max, alarm_enabled, region)
        """
        if not group:
            self.log_message(f"识别组{group_index+1}错误: 组配置为空")
            return False, None, None, None, None, None

        # 获取组配置
        key = group.get("key", tk.StringVar(value="")).get()
        delay_min = group.get("delay_min", tk.IntVar(value=300)).get()
        delay_max = group.get("delay_max", tk.IntVar(value=500)).get()
        alarm_enabled = group.get("alarm", tk.BooleanVar(value=False)).get()
        region = group.get("region")

        # 验证必要参数
        if not key:
            self.log_message(f"识别组{group_index+1}错误: 未设置触发按键")
            return False, None, None, None, None, None

        # 验证延迟参数
        if delay_min < 0 or delay_max < delay_min:
            self.log_message(f"识别组{group_index+1}错误: 延迟参数无效")
            delay_min = 300
            delay_max = 500

        return True, key, delay_min, delay_max, alarm_enabled, region

    def _calculate_click_position(self, click_pos, region, group_index):
        """
        计算点击位置
        Args:
            click_pos: 点击位置坐标
            region: 区域坐标
            group_index: OCR组索引

        Returns:
            tuple: (click_x, click_y)
        """
        if click_pos is not None:
            return click_pos

        if not region:
            self.log_message(f"识别组{group_index+1}错误: 未设置识别区域，无法计算点击位置")
            return None, None

        try:
            # 计算点击位置（区域中心）
            x1, y1, x2, y2 = region
            click_x = (x1 + x2) // 2
            click_y = (y1 + y2) // 2
            return click_x, click_y
        except (ValueError, TypeError) as e:
            self.log_message(f"识别组{group_index+1}错误: 区域坐标无效 - {str(e)}")
            return None, None

    def _execute_mouse_click(self, click_x, click_y, group_index):
        """
        执行鼠标点击
        Args:
            click_x: 点击x坐标
            click_y: 点击y坐标
            group_index: OCR组索引
        """
        if click_x is not None and click_y is not None:
            try:
                # 执行鼠标点击
                pyautogui.click(click_x, click_y)
                self.log_message(f"识别组{group_index+1}点击位置: ({click_x}, {click_y})")

                # 等待固定时间
                time.sleep(self.click_delay)
            except Exception as e:
                self.log_message(f"识别组{group_index+1}错误: 鼠标点击失败 - {str(e)}")

    def _execute_key_press(self, key, delay, group_index):
        """
        执行按键操作
        Args:
            key: 按键
            delay: 延迟时间
            group_index: OCR组索引
        """
        try:
            pyautogui.press(key, interval=delay)
            self.log_message(f"识别组{group_index+1}已模拟按键: {key}，延迟: {delay*1000}ms")

            # 更新该组的上次触发时间，进入暂停期
            self.last_trigger_times[group_index] = time.time()
        except Exception as e:
            self.log_message(f"识别组{group_index+1}错误: 按键操作失败 - {str(e)}")

    def _play_alarm_if_enabled(self, alarm_enabled, group_index):
        """
        播放报警声音（如果启用）
        Args:
            alarm_enabled: 是否启用报警
            group_index: OCR组索引
        """
        if alarm_enabled and PYGAME_AVAILABLE:
            try:
                self.play_alarm_sound()
            except Exception as e:
                self.log_message(f"识别组{group_index+1}错误: 播放报警声音失败 - {str(e)}")

    def trigger_action_for_group(self, group, group_index, click_enabled, click_pos=None):
        """
        为单个OCR组触发动作
        Args:
            group: OCR组配置字典
            group_index: OCR组索引
            click_enabled: 是否启用点击
            click_pos: 点击位置坐标
        """
        try:
            # 验证输入参数
            valid, key, delay_min, delay_max, alarm_enabled, region = self._validate_trigger_input(group, group_index)
            if not valid:
                return

            self.log_message(f"识别组{group_index+1}触发动作，按键: {key}")

            # 生成随机延迟
            delay = random.randint(delay_min, delay_max) / 1000.0

            # 如果启用点击，执行鼠标点击
            if click_enabled:
                click_x, click_y = self._calculate_click_position(click_pos, region, group_index)
                self._execute_mouse_click(click_x, click_y, group_index)

            # 执行按键操作
            self._execute_key_press(key, delay, group_index)
        except Exception as e:
            self.log_message(f"识别组{group_index+1}错误: 触发动作失败 - {str(e)}")
            import traceback
            self.log_message(f"错误详情: {traceback.format_exc()}")

        # 播放报警声音（如果启用）
        self._play_alarm_if_enabled(alarm_enabled, group_index)

    def _get_keywords_config(self):
        """获取关键词配置"""
        keywords_str = self.keywords_var.get().strip()
        current_keywords = [keyword.strip().lower() for keyword in keywords_str.split(",") if keyword.strip()]
        if not current_keywords:
            current_keywords = self.custom_keywords  # 保留原有关键词作为备份

        # 更新内部关键词列表，确保一致性
        self.custom_keywords = current_keywords
        return current_keywords

    def _get_timed_config(self):
        """获取定时功能配置"""
        timed_groups_config = []
        for group in self.timed_groups:
            timed_groups_config.append({
                'enabled': group['enabled'].get(),
                'interval': group['interval'].get(),
                'key': group['key'].get(),
                'delay_min': group['delay_min'].get(),
                'delay_max': group['delay_max'].get(),
                'click_enabled': group['click_enabled'].get(),
                'position_x': group['position_x'].get(),
                'position_y': group['position_y'].get(),
                'position': group['position'].get()
            })
        return timed_groups_config

    def _get_number_config(self):
        """获取数字识别配置"""
        number_regions_config = []
        for region_config in self.number_regions:
            number_regions_config.append({
                'enabled': region_config['enabled'].get(),
                'region': list(region_config['region']) if region_config['region'] else None,
                'threshold': region_config['threshold'].get(),
                'key': region_config['key'].get(),
                'delay_min': region_config['delay_min'].get(),
                'delay_max': region_config['delay_max'].get()
            })
        return number_regions_config

    def _get_ocr_config(self):
        """获取OCR配置"""
        ocr_groups_config = []
        for group in self.ocr_groups:
            ocr_groups_config.append({
                'enabled': group['enabled'].get(),
                'region': list(group['region']) if group['region'] else None,
                'interval': group['interval'].get(),
                'pause': group['pause'].get(),
                'key': group['key'].get(),
                'delay_min': group['delay_min'].get(),
                'delay_max': group['delay_max'].get(),
                'alarm': group['alarm'].get(),
                'keywords': group['keywords'].get(),
                'language': group['language'].get(),
                'click': group['click'].get()
            })
        return {
            'groups': ocr_groups_config
        }

    def _get_tesseract_config(self):
        """获取Tesseract配置"""
        return {
            'path': self.tesseract_path
        }

    def _get_shortcuts_config(self):
        """获取快捷键配置"""
        return {
            'start': self.start_shortcut_var.get(),
            'stop': self.stop_shortcut_var.get()
        }

    def _get_alarm_config(self):
        """
        获取报警功能配置
        Returns:
            dict: 报警功能配置字典
        """
        return {
            'sound': self.alarm_sound_path.get(),
            'volume': self.alarm_volume.get(),
            'ocr': {
                'enabled': self.alarm_enabled['ocr'].get()
            },
            'timed': {
                'enabled': self.alarm_enabled['timed'].get()
            },
            'number': {
                'enabled': self.alarm_enabled['number'].get()
            }
        }

    def _get_home_checkboxes_config(self):
        """获取首页勾选框配置"""
        return {
            'ocr': self.module_check_vars['ocr'].get(),
            'timed': self.module_check_vars['timed'].get(),
            'number': self.module_check_vars['number'].get()
        }

    def _get_script_config(self):
        """获取脚本和颜色识别配置"""
        script_content = ""
        color_commands_content = ""
        color_recognition_region = None
        target_color = None
        color_tolerance = 10
        color_interval = 1.0
        color_recognition_enabled = False

        # 获取脚本内容
        if hasattr(self, 'script_text'):
            script_content = self.script_text.get(1.0, tk.END)

        # 获取颜色识别命令内容
        if hasattr(self, 'color_commands_text'):
            color_commands_content = self.color_commands_text.get(1.0, tk.END)

        # 获取颜色识别区域
        if hasattr(self, 'region_var'):
            # 从region_var中解析区域信息
            region_text = self.region_var.get()
            import re
            match = re.search(r'\((\d+),\s*(\d+)\)\s*-\s*\((\d+),\s*(\d+)\)', region_text)
            if match:
                try:
                    color_recognition_region = [
                        int(match.group(1)),
                        int(match.group(2)),
                        int(match.group(3)),
                        int(match.group(4))
                    ]
                except (ValueError, IndexError):
                    pass

        # 获取目标颜色
        if hasattr(self, 'color_var'):
            # 从color_var中解析颜色信息
            color_text = self.color_var.get()
            match = re.search(r'RGB\((\d+),\s*(\d+),\s*(\d+)\)', color_text)
            if match:
                try:
                    target_color = [
                        int(match.group(1)),
                        int(match.group(2)),
                        int(match.group(3))
                    ]
                except (ValueError, IndexError):
                    pass

        # 获取颜色容差
        if hasattr(self, 'tolerance_var'):
            color_tolerance = self.tolerance_var.get()

        # 获取检查间隔
        if hasattr(self, 'interval_var'):
            color_interval = self.interval_var.get()

        # 获取颜色识别启用状态
        if hasattr(self, 'color_recognition_enabled'):
            color_recognition_enabled = self.color_recognition_enabled.get()

        return {
            'script_content': script_content,
            'color_commands': color_commands_content,
            'color_recognition_region': color_recognition_region,
            'target_color': target_color,
            'color_tolerance': color_tolerance,
            'color_interval': color_interval,
            'color_recognition_enabled': color_recognition_enabled
        }

    def save_config(self):
        """
        保存配置
        保存所有前端用户设置，包括新增功能的相关配置
        确保数据结构完整、一致，并处理边界情况
        """
        try:
            # 获取各部分配置
            timed_groups_config = self._get_timed_config()
            number_regions_config = self._get_number_config()

            # 完整的配置数据结构，确保所有配置项都被保存
            config = {
                'version': VERSION,  # 使用全局版本号，自动同步
                'last_save_time': datetime.datetime.now().isoformat(),
                # 基本OCR配置
            'ocr': self._get_ocr_config(),
            # Tesseract配置
            'tesseract': self._get_tesseract_config(),
            # 定时功能配置
                'timed_key_press': {
                    'groups': timed_groups_config
                },
                # 数字识别配置
                'number_recognition': {
                    'regions': number_regions_config
                },
                # 快捷键配置 - 新增
                'shortcuts': self._get_shortcuts_config(),
                # 报警功能配置
                'alarm': self._get_alarm_config(),
                # 首页功能状态勾选框配置
                'home_checkboxes': self._get_home_checkboxes_config(),
                # 脚本和颜色识别配置
                'script': self._get_script_config()
            }

            # 确保配置文件目录存在
            os.makedirs(os.path.dirname(self.config_file_path), exist_ok=True)

            # 写入配置文件，使用更紧凑的格式
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False, default=str)

            self.log_message("配置已保存")

        except PermissionError:
            self.log_message(f"没有权限写入配置文件: {self.config_file_path}")
        except IOError as e:
            self.log_message(f"配置文件IO错误: {str(e)}")
        except json.JSONDecodeError as e:
            self.log_message(f"配置JSON编码错误: {str(e)}")
        except Exception as e:
            self.log_message(f"配置保存错误: {str(e)}")

    def trigger_action(self):
        """触发动作序列"""
        self.log_message("检测到关键词，执行动作...")

        # 播放OCR模块报警声音
        self.play_alarm_sound(self.alarm_enabled["ocr"])

        # 获取自定义按键
        custom_key = self.key_var.get()

        # 只有当按键不为空时才执行按键操作
        if custom_key:
            try:
                # 计算点击位置（使用区域中心）
                if hasattr(self, 'selected_region') and self.selected_region:
                    x1, y1, x2, y2 = self.selected_region
                    click_x = (x1 + x2) // 2
                    click_y = (y1 + y2) // 2

                    # 1. 鼠标左键点击指定位置
                    pyautogui.click(click_x, click_y)
                    self.log_message(f"点击位置: ({click_x}, {click_y})")

                    # 2. 等待固定时间（无需用户修改）
                    time.sleep(self.click_delay)

                # 3. 通过事件队列按下自定义按键
                self.add_event(('keypress', custom_key), ('ocr', 0))

                # 记录触发时间
                self.last_trigger_time = time.time()

            except Exception as e:
                self.log_message(f"动作执行错误: {str(e)}")
        else:
            self.log_message("按键配置为空，仅执行报警操作")

    def start_event_thread(self):
        """启动事件处理线程"""
        self.is_event_running = True
        self.event_thread = threading.Thread(target=self.process_events, daemon=True)
        self.event_thread.start()
        self.log_message("事件处理线程已启动")

    def process_events(self):
        """
        处理事件队列中的事件
        """
        while self.is_event_running:
            try:
                with self.event_condition:
                    while not self.event_queue:
                        self.event_condition.wait()
                    event_data = self.event_queue.popleft()

                # 执行事件
                self.execute_event(event_data)
            except Exception as e:
                self.log_message(f"事件处理错误: {str(e)}")
                time.sleep(1)

    def add_event(self, event, module_info=None):
        """
        添加事件到队列
        Args:
            event: 事件元组
            module_info: 模块信息，可选
        """
        with self.event_condition:
            self.event_queue.append((event, module_info))
            self.event_condition.notify()

    def execute_event(self, event_data):
        """执行具体事件"""
        event, module_info = event_data
        event_type, data = event

        if event_type == 'keypress':
            key = data
            try:
                # 立即按下按键
                pyautogui.keyDown(key)

                # 根据模块信息获取延迟范围
                if module_info:
                    module_type, module_index = module_info
                    if module_type == 'ocr':
                        delay_min = self.ocr_delay_min.get()
                        delay_max = self.ocr_delay_max.get()
                    elif module_type == 'timed':
                        delay_min = self.timed_groups[module_index]['delay_min'].get()
                        delay_max = self.timed_groups[module_index]['delay_max'].get()
                    elif module_type == 'number':
                        delay_min = self.number_regions[module_index]['delay_min'].get()
                        delay_max = self.number_regions[module_index]['delay_max'].get()
                    else:
                        delay_min = 300
                        delay_max = 500
                else:
                    # 默认延迟
                    delay_min = 300
                    delay_max = 500

                # 确保延迟范围有效
                delay_min = max(1, delay_min)  # 至少1ms
                delay_max = max(delay_min, delay_max)  # 确保max不小于min

                # 生成随机延迟
                delay = random.randint(delay_min, delay_max) / 1000  # 转换为秒

                # 延迟等待（不会影响UI主线程，因为事件处理在单独线程中）
                time.sleep(delay)

                # 延迟后弹起按键
                pyautogui.keyUp(key)

                self.log_message(f"按下了 {key} 键，延迟 {delay*1000:.0f} 毫秒")
            except Exception as e:
                self.log_message(f"按键执行错误: {str(e)}")
        elif event_type == 'exit':
            # 退出事件，什么都不做
            pass
        # 其他事件类型...

    def _manage_threads(self, module_type, start_func, stop_func, thread_list, status_var_key, log_prefix):
        """线程管理的公共方法"""
        # 停止现有线程
        stop_func()

        self.log_message(f"开始{log_prefix}")

        # 统计要启动的线程数量
        start_count = start_func()

        # 更新状态标签
        module_display_name = {
            "定时功能": "定时功能",
            "数字识别": "数字识别",
            "文字识别": "文字识别",
            "脚本运行": "脚本运行"
        }.get(log_prefix, log_prefix)
        
        if start_count > 0:
            self.status_labels[status_var_key].set(f"{module_display_name}: 运行中")
        else:
            self.status_labels[status_var_key].set(f"{module_display_name}: 未运行")

        if start_count == 0:
            self.log_message(f"没有启用任何{module_display_name}")

    def _stop_threads(self, thread_list, module_name, status_var_key):
        """停止线程的公共方法"""
        # 停止所有线程

        # 清空线程列表
        if thread_list:
            thread_list.clear()

        # 更新状态标签
        module_display_name = {
            "定时功能": "定时功能",
            "数字识别": "数字识别",
            "文字识别": "文字识别",
            "脚本运行": "脚本运行"
        }.get(module_name, module_name)
        
        self.status_labels[status_var_key].set(f"{module_display_name}: 未运行")

    def start_timed_tasks(self):
        """开始定时任务"""
        def start_func():
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
            return start_count

        self._manage_threads("timed", start_func, self.stop_timed_tasks, self.timed_threads, "timed", "定时功能")

    def stop_timed_tasks(self):
        """停止定时任务"""
        self._stop_threads(self.timed_threads, "定时功能", "timed")

    def timed_task_loop(self, group_index, interval, key):
        """定时任务循环"""
        current_thread = threading.current_thread()

        # 检查线程是否在timed_threads列表中，以及定时组是否启用
        while current_thread in self.timed_threads and self.timed_groups[group_index]["enabled"].get():
            try:
                # 等待指定的时间间隔
                for _ in range(interval):
                    time.sleep(1)
                    # 每秒钟检查一次线程是否仍在列表中
                    if current_thread not in self.timed_threads:
                        return

                # 获取定时组配置
                group = self.timed_groups[group_index]

                # 播放定时模块报警声音
                self.play_alarm_sound(group["alarm"])

                # 检查是否启用了鼠标点击
                if group["click_enabled"].get():
                    # 获取保存的位置坐标
                    pos_x = group["position_x"].get()
                    pos_y = group["position_y"].get()

                    if pos_x != 0 or pos_y != 0:  # 确保位置已选择
                        # 执行鼠标点击操作
                        pyautogui.click(pos_x, pos_y)
                        self.log_message(f"定时任务{group_index+1}执行鼠标点击: ({pos_x}, {pos_y})")

                        # 等待0.5秒后触发按键
                        time.sleep(0.5)

                # 只有当按键不为空时才执行按键操作
                if key:
                    self.add_event(('keypress', key), ('timed', group_index))
                    self.log_message(f"定时任务{group_index+1}触发按键: {key}")
                else:
                    self.log_message(f"定时任务{group_index+1}按键配置为空")
            except Exception as e:
                self.log_message(f"定时任务{group_index+1}错误: {str(e)}")
                break

    def start_number_region_selection(self, region_index):
        """开始数字识别区域选择"""
        self._start_selection("number", region_index)

    def start_timed_position_selection(self, group_index):
        """开始定时任务屏幕位置选择"""
        self.log_message(f"开始定时组{group_index+1}屏幕位置选择...")
        self.is_selecting = True
        self.current_timed_group = group_index

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

        # 创建透明的位置选择窗口，覆盖整个虚拟屏幕
        self.select_window = tk.Toplevel(self.root)
        self.select_window.geometry(f"{max_x - self.min_x}x{max_y - self.min_y}+{self.min_x}+{self.min_y}")
        self.select_window.overrideredirect(True)  # 移除窗口装饰
        self.select_window.attributes("-alpha", 0.3)
        self.select_window.attributes("-topmost", True)

        # 创建画布用于显示提示
        self.canvas = tk.Canvas(self.select_window, cursor="cross", 
                               width=max_x - self.min_x, height=max_y - self.min_y)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 显示提示文字
        self.canvas.create_text((max_x - self.min_x) // 2, (max_y - self.min_y) // 2, 
                              text="请点击要记录的屏幕位置", font=("Arial", 16), fill="red")

        # 绑定鼠标事件
        self.canvas.bind("<Button-1>", self.on_timed_position_click)
        self.select_window.protocol("WM_DELETE_WINDOW", self.cancel_selection)

    def on_timed_position_click(self, event):
        """定时任务位置选择鼠标点击事件"""
        # 获取绝对坐标
        pos_x = event.x_root
        pos_y = event.y_root

        self.log_message(f"定时组{self.current_timed_group+1}已选择位置: {pos_x},{pos_y}")

        # 更新配置
        if 0 <= self.current_timed_group < len(self.timed_groups):
            group = self.timed_groups[self.current_timed_group]
            group["position_x"].set(pos_x)
            group["position_y"].set(pos_y)
            group["position"].set(f"位置：{pos_x},{pos_y}")

            # 保存配置
            self.save_config()

        self.cancel_selection()

    def on_number_region_mouse_up(self, event):
        """数字识别区域鼠标释放事件"""
        # 获取结束绝对坐标
        end_x_abs = event.x_root
        end_y_abs = event.y_root

        # 保存选择区域
        region = self._save_selection(self.start_x_abs, self.start_y_abs, end_x_abs, end_y_abs)
        if region is None:
            return

        # 更新界面
        region_index = self.current_number_region_index
        self.number_regions[region_index]["region"] = region
        self.number_regions[region_index]["region_var"].set(f"区域: {region[0]},{region[1]} - {region[2]},{region[3]}")
        self.log_message(f"已选择数字识别区域{region_index+1}: {region}")
        self.cancel_selection()

        # 保存配置
        self.save_config()

    def start_number_recognition(self):
        """开始数字识别"""
        def start_func():
            start_count = 0
            for i, region_config in enumerate(self.number_regions):
                if region_config["enabled"].get():
                    region = region_config["region"]
                    if not region:
                        continue
                    threshold = region_config["threshold"].get()
                    key = region_config["key"].get()
                    # 创建线程并存储
                    thread = threading.Thread(target=self.number_recognition_loop, args=(i, region, threshold, key), daemon=True)
                    self.number_threads.append(thread)
                    thread.start()
                    start_count += 1
            return start_count

        self._manage_threads("number", start_func, self.stop_number_recognition, self.number_threads, "number", "数字识别")

    def stop_number_recognition(self):
        """停止数字识别"""
        self._stop_threads(self.number_threads, "数字识别", "number")

    def _toggle_ui_state(self, root_widget, state):
        """递归地禁用或启用根控件及其所有子控件
        Args:
            root_widget: 根控件
            state: 控件状态，"disabled" 或 "normal"
        """
        # 跳过停止运行按钮，始终保持可用
        if root_widget == self.global_stop_btn:
            return

        try:
            # 尝试设置控件状态
            root_widget.configure(state=state)
        except (tk.TclError, AttributeError):
            # 某些控件（如Frame）没有state属性，跳过
            pass

        # 递归处理所有子控件
        for child in root_widget.winfo_children():
            self._toggle_ui_state(child, state)

    def start_all(self):
        """开始运行"""
        self.log_message("开始运行")

        # 重置系统完全停止标志
        self.system_stopped = False

        # 禁用首页的功能状态勾选框
        for button in self.module_check_buttons.values():
            button.configure(state="disabled")

        # 禁用开始运行按钮
        self.global_start_btn.configure(state="disabled")

        # 禁用所有其他UI控件
        for child in self.root.winfo_children():
            self._toggle_ui_state(child, "disabled")

        # 确保停止运行按钮可用
        self.global_stop_btn.configure(state="normal")

        # 开始勾选的功能
        if self.module_check_vars["ocr"].get():
            self.start_monitoring()

        if self.module_check_vars["timed"].get():
            self.start_timed_tasks()

        if self.module_check_vars["number"].get():
            self.start_number_recognition()

        if self.module_check_vars["script"].get():
            # 启动脚本
            self.start_script()

        # 播放开始运行的音频
        self.play_start_sound()
        
        # 设置运行状态
        self.is_running = True

    def stop_all(self):
        """停止运行"""
        self.log_message("停止运行")

        # 设置系统完全停止标志，阻止任何外部命令唤醒
        self.system_stopped = True

        # 停止运行
        self.stop_monitoring()
        self.stop_timed_tasks()
        self.stop_number_recognition()
        
        # 停止脚本（不在这里停止颜色识别，留到下面统一处理）
        self.stop_script(stop_color_recognition=False)
        
        # 停止颜色识别 - 无论color_recognition_enabled状态如何，都停止颜色识别线程
        if hasattr(self, 'color_recognition'):
            # 检查线程是否正在运行
            if hasattr(self.color_recognition, 'is_running') and self.color_recognition.is_running:
                self.color_recognition.stop_recognition()
            elif hasattr(self.color_recognition, 'recognition_thread') and self.color_recognition.recognition_thread.is_alive():
                # 如果is_running为False但是线程仍然在运行，强制停止
                self.color_recognition.is_running = False
                self.color_recognition.recognition_thread.join(timeout=2)

        # 播放停止运行的反向音频
        self.play_stop_sound()

        # 启用首页的功能状态勾选框
        for button in self.module_check_buttons.values():
            button.configure(state="normal")

        # 启用开始运行按钮
        self.global_start_btn.configure(state="normal")

        # 启用所有其他UI控件
        for child in self.root.winfo_children():
            self._toggle_ui_state(child, "normal")

        # 确保开始运行按钮可用
        self.global_start_btn.configure(state="normal")
        
        # 禁用停止运行按钮，因为系统已经停止
        self.global_stop_btn.configure(state="disabled")
        
        # 设置停止状态
        self.is_running = False

    def number_recognition_loop(self, region_index, region, threshold, key):
        """数字识别循环"""
        current_thread = threading.current_thread()

        # 检查线程是否在number_threads列表中，以及数字识别区域是否启用
        while current_thread in self.number_threads and self.number_regions[region_index]["enabled"].get():
            try:
                time.sleep(1)  # 1秒间隔

                # 截图并识别数字
                screenshot = self.take_screenshot(region)
                text = self.ocr_number(screenshot)

                number = self.parse_number(text)
                if number is not None:
                    self.log_message(f"数字识别{region_index+1}解析结果: {number}")
                    if number < threshold:
                        # 播放数字识别模块报警声音
                        self.play_alarm_sound(self.number_regions[region_index]["alarm"])

                        # 只有当数字小于阈值且按键不为空时才执行按键操作
                        if key:
                            self.add_event(('keypress', key), ('number', region_index))
                            self.log_message(f"数字识别{region_index+1}触发按键: {key}")
                        else:
                            self.log_message(f"数字识别{region_index+1}按键配置为空，仅执行报警操作")
                else:
                    # 识别失败时，输出原始识别结果
                    self.log_message(f"数字识别{region_index+1}结果: '{text}'")
            except Exception as e:
                self.log_message(f"数字识别{region_index+1}错误: {str(e)}")
                time.sleep(5)

    def parse_number(self, text):
        """解析数字，支持X/Y格式
        只在识别失败时输出详细日志
        """
        # 移除可能的空格和换行符
        text = text.strip()

        # 检查是否为X/Y格式
        if '/' in text:
            parts = text.split('/')
            if len(parts) == 2:
                # 尝试解析X部分
                x_part = parts[0].strip()
                try:
                    x_number = int(x_part)
                    return x_number
                except ValueError as e:
                    self.log_message("数字识别解析: 无法解析X部分 '{0}'，错误: {1}".format(x_part, str(e)))
                    # 尝试清理X部分，移除非数字字符
                    cleaned_x = ''.join(filter(str.isdigit, x_part))
                    if cleaned_x:
                        try:
                            return int(cleaned_x)
                        except ValueError:
                            self.log_message("数字识别解析: 清理后仍无法解析X部分 '{0}'".format(cleaned_x))
        else:
            # 尝试直接解析为数字
            try:
                # 清理文字，移除非数字字符
                cleaned_text = ''.join(filter(str.isdigit, text))
                if cleaned_text:
                    number = int(cleaned_text)
                    return number
                else:
                    self.log_message("数字识别解析: 清理后无数字字符")
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
        image = image.convert('L')
        config = '--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789/'
        text = pytesseract.image_to_string(image, lang='eng', config=config)

        # 4. 额外的文本清理，移除可能的换行符和空格
        text = text.strip().replace('\n', '').replace('\r', '')

        return text

    def play_alarm_sound(self, alarm_var):
        """播放报警声音
        Args:
            alarm_var: 报警开关的BooleanVar变量
        """
        if not PYGAME_AVAILABLE:
            self.log_message("pygame库未安装，无法播放报警声音")
            return

        if not alarm_var.get():
            return

        sound_file = self.alarm_sound_path.get()
        if not sound_file or not os.path.exists(sound_file):
            self.log_message("未设置有效的全局报警声音文件")
            return

        try:
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.set_volume(self.alarm_volume.get() / 100)  # 设置音量
            pygame.mixer.music.play()
            self.log_message("报警声音已播放")
        except Exception as e:
            self.log_message(f"播放报警声音失败: {str(e)}")

    def play_start_sound(self):
        """播放开始运行的音频"""
        if not PYGAME_AVAILABLE:
            self.log_message("pygame库未安装，无法播放开始运行音效")
            return

        # 直接使用固定的音频文件路径，不受报警声音设置的影响
        sound_file = self.get_default_alarm_sound_path()
        if not sound_file or not os.path.exists(sound_file):
            self.log_message("未找到默认音频文件，无法播放开始运行音效")
            return

        try:
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.set_volume(0.7)  # 使用固定音量 70%
            pygame.mixer.music.play()
        except pygame.error as e:
            self.log_message(f"音频文件格式错误或损坏: {str(e)}")
        except Exception as e:
            self.log_message(f"播放开始运行音效失败: {str(e)}")

    def play_stop_sound(self):
        """播放停止运行的反向音频"""
        if not PYGAME_AVAILABLE:
            return

        try:
            # 获取程序运行目录
            if hasattr(sys, '_MEIPASS'):
                # 打包后的环境，使用_MEIPASS获取运行目录
                app_root = sys._MEIPASS
            else:
                # 开发环境，使用当前文件所在目录
                app_root = os.path.dirname(os.path.abspath(__file__))

            # 构建跨平台的反向音频路径
            reversed_file = os.path.join(app_root, "voice", "temp_reversed.mp3")
            reversed_file = os.path.normpath(reversed_file)

            if os.path.exists(reversed_file):
                try:
                    pygame.mixer.music.load(reversed_file)
                    pygame.mixer.music.set_volume(0.7)  # 使用固定音量 70%
                    pygame.mixer.music.play()
                except pygame.error:
                    # 播放原始音频作为备选
                    sound_file = self.get_default_alarm_sound_path()
                    if sound_file and os.path.exists(sound_file):
                        try:
                            pygame.mixer.music.load(sound_file)
                            pygame.mixer.music.set_volume(0.7)  # 使用固定音量 70%
                            pygame.mixer.music.play()
                        except Exception:
                            pass
            else:
                # 如果反向音频文件不存在，播放原始音频
                sound_file = self.get_default_alarm_sound_path()
                if sound_file and os.path.exists(sound_file):
                    try:
                        pygame.mixer.music.load(sound_file)
                        pygame.mixer.music.set_volume(0.7)  # 使用固定音量 70%
                        pygame.mixer.music.play()
                    except Exception:
                        pass
        except Exception:
            pass

    def _create_reversed_audio(self, input_file):
        """创建反向音频文件
        Args:
            input_file: 输入音频文件路径
            
        Returns:
            反向音频文件路径，失败返回None
        """
        try:
            # 创建临时文件路径
            # 在macOS上，确保临时文件保存在可写位置
            if platform.system() == "Darwin":
                temp_dir = os.path.expanduser("~")  # 使用用户主目录
            else:
                temp_dir = os.path.dirname(input_file)

            temp_file = os.path.join(temp_dir, "temp_reversed.mp3")

            # 检查临时文件是否已存在，如果存在则直接返回
            if os.path.exists(temp_file):
                return temp_file

            # 由于pygame的限制，我们使用一种替代方法：
            # 1. 尝试使用外部库如pydub（如果可用）
            try:
                from pydub import AudioSegment

                # 加载音频文件
                audio = AudioSegment.from_mp3(input_file)

                # 反转音频
                reversed_audio = audio.reverse()

                # 导出为临时文件
                reversed_audio.export(temp_file, format="mp3")

                return temp_file
            except ImportError:
                # 如果pydub不可用，使用pygame的有限功能
                # 注意：这种方法可能无法实现真正的音频反转
                # 但为了兼容性，我们仍然返回原始文件
                return input_file
            except Exception as e:
                self.log_message(f"pydub处理音频失败: {str(e)}")
                return input_file
        except Exception as e:
            self.log_message(f"创建反向音频失败: {str(e)}")
            return None

    def select_alarm_sound(self):
        """选择全局报警声音文件
        """
        filetypes = [
            ("音频文件", "*.mp3 *.wav *.ogg *.flac"),
            ("所有文件", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="选择全局报警声音",
            filetypes=filetypes
        )

        if filename:
            self.alarm_sound_path.set(filename)
            self.log_message(f"已选择全局报警声音: {os.path.basename(filename)}")
            self.save_config()

    def toggle_alarm(self, module):
        """切换报警开关状态
        Args:
            module: 模块名称，如"ocr"、"timed"或"number"
        """
        self.log_message(f"{module}模块报警状态已{'启用' if self.alarm_enabled[module].get() else '禁用'}")
        self.save_config()

    def update_child_styles(self, widget, is_enabled):
        """递归更新所有子组件样式
        Args:
            widget: 要更新样式的组件
            is_enabled: 组件是否启用
        """
        # 组件样式映射
        style_mappings = {
            ttk.Frame: lambda: "Green.TFrame" if is_enabled else "TFrame",
            ttk.Button: lambda: "Green.TButton" if is_enabled else "TButton",
            ttk.Checkbutton: lambda: "Green.TCheckbutton" if is_enabled else "TCheckbutton",
            ttk.Combobox: lambda: "Green.TCombobox" if is_enabled else "TCombobox",
            ttk.Entry: lambda: "TEntry",  # 始终使用默认样式，不随组启用状态变化
            ttk.LabelFrame: lambda: "Green.TLabelframe" if is_enabled else "TLabelframe"
        }

        # 特殊处理Label组件
        if isinstance(widget, ttk.Label):
            # 检查是否为显示按键的标签（有sunken relief）
            if widget.cget("relief") != "sunken":
                widget.configure(style="Green.TLabel" if is_enabled else "TLabel")
        # 处理其他组件类型
        else:
            for widget_type, style_func in style_mappings.items():
                if isinstance(widget, widget_type):
                    widget.configure(style=style_func())
                    break

        # 递归处理所有子组件
        for child in widget.winfo_children():
            self.update_child_styles(child, is_enabled)

    def update_group_style(self, group_frame, enabled):
        """更新组样式
        Args:
            group_frame: 要更新样式的组框架
            enabled: 组是否启用
        """
        # 更新当前框架样式
        if enabled:
            group_frame.configure(style="Green.TLabelframe")
        else:
            group_frame.configure(style="TLabelframe")

        # 递归更新所有子组件样式
        self.update_child_styles(group_frame, enabled)

    def _create_group_frame(self, parent_frame, index, group_type):
        """
        创建组框架
        Args:
            parent_frame: 父框架
            index: 组索引
            group_type: 组类型名称

        Returns:
            ttk.LabelFrame: 创建的组框架
        """
        # 创建识别组框架
        group_frame = ttk.LabelFrame(parent_frame, text=f"{group_type}{index+1}", padding="10")
        group_frame.pack(fill=tk.X, pady=(0, 10))
        # 设置初始边框样式
        group_frame.configure(relief=tk.GROOVE, borderwidth=2)

        return group_frame

    def _setup_group_click_handler(self, group_frame, enabled_var):
        """
        设置组点击事件处理器
        Args:
            group_frame: 组框架
            enabled_var: 启用状态变量
        """
        # 点击事件处理函数
        def on_group_click(event):
            # 检查点击事件是否来自输入控件
            if isinstance(event.widget, (ttk.Entry, ttk.Button, ttk.Combobox, ttk.Checkbutton)):
                return  # 输入控件事件不处理

            # 切换启用状态
            enabled_var.set(not enabled_var.get())

            # 根据启用状态调整样式
            update_group_style(enabled_var.get())

        # 使用类方法更新组样式
        def update_group_style(enabled):
            self.update_group_style(group_frame, enabled)

        # 为enabled变量添加trace监听，当状态变化时自动更新样式
        enabled_var.trace_add("write", lambda *args: update_group_style(enabled_var.get()))

        # 绑定点击事件到框架及其子组件
        group_frame.bind("<Button-1>", on_group_click)

        # 为子组件绑定事件
        def bind_child_events(widget):
            for child in widget.winfo_children():
                if isinstance(child, (ttk.Entry, ttk.Button, ttk.Combobox, ttk.Checkbutton)):
                    # 输入控件保持原有功能
                    pass
                else:
                    # 其他组件继续绑定点击事件
                    child.bind("<Button-1>", on_group_click)
                    bind_child_events(child)

        bind_child_events(group_frame)

    def exit_program(self):
        """退出程序"""
        # 停止所有运行中的任务
        if self.is_running:
            self.stop_monitoring()
        self.stop_timed_tasks()
        self.stop_number_recognition()

        # 停止脚本执行
        if hasattr(self, 'script_executor') and self.script_executor.is_running:
            self.script_executor.stop_script()

        # 停止颜色识别
        if hasattr(self, 'color_recognition') and self.color_recognition.is_running:
            self.color_recognition.stop_recognition()

        # 停止全局键盘监听器
        if hasattr(self, 'global_listener') and self.global_listener:
            self.global_listener.stop()

        # 停止事件线程
        self.is_event_running = False
        
        # 退出程序
        self.log_message("程序正在退出...")
        self.root.quit()
        self.root.destroy()

    def run(self):
        """运行程序"""
        self.root.mainloop()

    def create_script_tab(self, parent):
        """创建脚本运行标签页"""
        script_frame = ttk.Frame(parent, padding="10")
        script_frame.pack(fill=tk.BOTH, expand=True)

        # 左右容器
        left_right_frame = ttk.Frame(script_frame)
        left_right_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧：命令输入区域，占据剩余空间
        left_frame = ttk.LabelFrame(left_right_frame, text="命令输入", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # 按键命令组
        key_cmd_frame = ttk.LabelFrame(left_frame, text="按键命令", padding="8")
        key_cmd_frame.pack(fill=tk.X, pady=(0, 8))

        # 参数行 - 所有参数和插入按钮在同一行
        params_row = ttk.Frame(key_cmd_frame)
        params_row.pack(fill=tk.X)

        # 按键名称
        ttk.Label(params_row, text="按键:", width=5).pack(side=tk.LEFT)
        self.key_var = tk.StringVar(value="1")
        current_key_label = ttk.Label(params_row, textvariable=self.key_var, relief="sunken", padding=4, width=5)
        current_key_label.pack(side=tk.LEFT, padx=(0, 2))

        # 设置按键按钮 - 缩短为"修改"并减小宽度
        self.set_key_btn = ttk.Button(params_row, text="修改", width=4, 
                                    command=lambda: self.start_key_listening(self.key_var, self.set_key_btn))
        self.set_key_btn.pack(side=tk.LEFT, padx=(0, 2))

        # 按键指令类型（按下/抬起）- 增加宽度和间距，确保完整显示
        ttk.Label(params_row, text="类型:", width=5).pack(side=tk.LEFT, padx=(0, 5))
        self.key_type = tk.StringVar(value="KeyDown")
        key_type_combo = ttk.Combobox(params_row, textvariable=self.key_type, values=["KeyDown", "KeyUp"], width=8)
        key_type_combo.pack(side=tk.LEFT, padx=(0, 5))

        # 执行次数变量（保留供逻辑使用）
        self.key_count = tk.IntVar(value=1)

        # 插入按键命令按钮 - 放在同一行，固定宽度
        self.insert_key_btn = ttk.Button(params_row, text="插入命令", command=self.insert_key_command, width=10)
        self.insert_key_btn.pack(side=tk.LEFT, padx=(10, 0))

        # 延迟命令组
        delay_cmd_frame = ttk.LabelFrame(left_frame, text="延迟命令", padding="8")
        delay_cmd_frame.pack(fill=tk.X, pady=(0, 8))

        # 延迟时间和插入按钮在同一行
        delay_row = ttk.Frame(delay_cmd_frame)
        delay_row.pack(fill=tk.X)

        ttk.Label(delay_row, text="延迟(ms):", width=8).pack(side=tk.LEFT, padx=(0, 5))
        self.delay_entry = ttk.Entry(delay_row, width=8)
        self.delay_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.delay_entry.insert(0, "250")

        # 插入延迟命令按钮 - 放在同一行，固定宽度
        self.insert_delay_btn = ttk.Button(delay_row, text="插入命令", command=self.insert_delay_command, width=10)
        self.insert_delay_btn.pack(side=tk.LEFT, padx=(10, 0))

        # 鼠标命令组
        mouse_cmd_frame = ttk.LabelFrame(left_frame, text="鼠标命令", padding="8")
        mouse_cmd_frame.pack(fill=tk.X, pady=(0, 8))

        # 鼠标点击命令和插入按钮在同一行
        mouse_click_frame = ttk.Frame(mouse_cmd_frame)
        mouse_click_frame.pack(fill=tk.X, pady=(0, 4))

        # 鼠标按键选择
        ttk.Label(mouse_click_frame, text="按键:", width=5).pack(side=tk.LEFT)
        self.mouse_button_var = tk.StringVar(value="Left")
        mouse_button_combo = ttk.Combobox(mouse_click_frame, textvariable=self.mouse_button_var, values=["Left", "Right", "Middle"], width=8)
        mouse_button_combo.pack(side=tk.LEFT, padx=(0, 5))

        # 鼠标操作类型
        ttk.Label(mouse_click_frame, text="操作:", width=5).pack(side=tk.LEFT)
        self.mouse_action_var = tk.StringVar(value="Down")
        mouse_action_combo = ttk.Combobox(mouse_click_frame, textvariable=self.mouse_action_var, values=["Down", "Up"], width=8)
        mouse_action_combo.pack(side=tk.LEFT, padx=(0, 5))

        # 执行次数变量（保留供逻辑使用）
        self.mouse_count_var = tk.IntVar(value=1)

        # 插入鼠标点击命令按钮 - 放在同一行，固定宽度
        self.insert_mouse_click_btn = ttk.Button(mouse_click_frame, text="插入命令", command=self.insert_mouse_click_command, width=10)
        self.insert_mouse_click_btn.pack(side=tk.LEFT, padx=(10, 0))

        # 选择坐标点按钮
        select_coordinate_frame = ttk.Frame(mouse_cmd_frame)
        select_coordinate_frame.pack(fill=tk.X, pady=(4, 0))

        # 左键选择坐标
        self.select_coordinate_btn = ttk.Button(select_coordinate_frame, text="选择坐标点", command=self.select_coordinate)
        self.select_coordinate_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 组合按键命令组
        combo_key_frame = ttk.LabelFrame(left_frame, text="组合按键命令", padding="8")
        combo_key_frame.pack(fill=tk.X, pady=(0, 8))

        # 脚本控制按钮组
        control_cmd_frame = ttk.LabelFrame(left_frame, text="脚本控制", padding="8")
        control_cmd_frame.pack(fill=tk.X, pady=(0, 8))

        # 控制按钮行 - 只保留录制按钮
        control_buttons_row = ttk.Frame(control_cmd_frame)
        control_buttons_row.pack(fill=tk.X, pady=(0, 8))

        # 录制按钮
        self.record_btn = ttk.Button(control_buttons_row, text="开始录制", command=self.start_recording)
        self.record_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        # 停止录制按钮
        self.stop_record_btn = ttk.Button(control_buttons_row, text="停止录制", command=self.stop_recording)
        # 初始状态下停止录制按钮为禁用状态
        self.stop_record_btn.config(state="disabled")
        self.stop_record_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 脚本操作按钮行
        script_buttons_row = ttk.Frame(control_cmd_frame)
        script_buttons_row.pack(fill=tk.X)

        # 清空脚本按钮
        clear_script_btn = ttk.Button(script_buttons_row, text="清空脚本", command=self.clear_script)
        clear_script_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        # 导入脚本按钮
        import_script_btn = ttk.Button(script_buttons_row, text="导入脚本", command=self.load_script)
        import_script_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        # 导出脚本按钮
        export_script_btn = ttk.Button(script_buttons_row, text="导出脚本", command=self.save_script)
        export_script_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 组合命令第一行 - 按键和修改按钮
        combo_row1 = ttk.Frame(combo_key_frame)
        combo_row1.pack(fill=tk.X, pady=(0, 4))

        # 按键
        ttk.Label(combo_row1, text="按键:", width=4).pack(side=tk.LEFT)
        self.combo_key_var = tk.StringVar(value="1")
        combo_key_label = ttk.Label(combo_row1, textvariable=self.combo_key_var, relief="sunken", padding=4, width=5)
        combo_key_label.pack(side=tk.LEFT, padx=(0, 2))

        # 设置组合命令按键按钮 - 缩短为"修改"并减小宽度
        self.set_combo_key_btn = ttk.Button(combo_row1, text="修改", width=4, 
                                           command=lambda: self.start_key_listening(self.combo_key_var, self.set_combo_key_btn))
        self.set_combo_key_btn.pack(side=tk.LEFT)

        # 组合命令第二行 - 按键延迟、抬起延迟和插入按钮，增加宽度和间距
        combo_row2 = ttk.Frame(combo_key_frame)
        combo_row2.pack(fill=tk.X, pady=(0, 4))

        # 按键延迟 - 增加宽度和间距，确保完整显示
        ttk.Label(combo_row2, text="按键延迟:", width=8).pack(side=tk.LEFT, padx=(0, 5))
        self.combo_key_delay = tk.StringVar(value="2500")
        combo_delay_entry = ttk.Entry(combo_row2, textvariable=self.combo_key_delay, width=8)
        combo_delay_entry.pack(side=tk.LEFT, padx=(0, 10))

        # 抬起后延迟 - 增加宽度和间距，确保完整显示
        ttk.Label(combo_row2, text="抬起延迟:", width=8).pack(side=tk.LEFT, padx=(0, 5))
        self.combo_after_delay = tk.StringVar(value="300")
        combo_after_delay_entry = ttk.Entry(combo_row2, textvariable=self.combo_after_delay, width=8)
        combo_after_delay_entry.pack(side=tk.LEFT, padx=(0, 10))

        # 插入组合命令按钮 - 放在同一行，固定宽度
        self.insert_combo_btn = ttk.Button(combo_row2, text="插入命令", command=self.insert_combo_command, width=10)
        self.insert_combo_btn.pack(side=tk.LEFT, padx=(10, 0))

        # 右侧：使用Notebook实现多tab页，固定宽度450px
        right_frame = ttk.Frame(left_right_frame, width=450)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right_frame.pack_propagate(False)  # 禁止子组件影响固定宽度

        # 创建Notebook
        self.script_notebook = ttk.Notebook(right_frame)
        self.script_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 第一个tab页：脚本编辑
        script_tab = ttk.Frame(self.script_notebook)
        self.script_notebook.add(script_tab, text="脚本编辑")

        # 脚本文本框
        script_text_frame = ttk.Frame(script_tab)
        script_text_frame.pack(fill=tk.BOTH, expand=True)

        # 脚本内容文本框
        self.script_text = tk.Text(script_text_frame, wrap=tk.NONE, font=("Consolas", 10))
        self.script_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 垂直滚动条
        v_scrollbar = ttk.Scrollbar(script_text_frame, orient=tk.VERTICAL, command=self.script_text.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.script_text.config(yscrollcommand=v_scrollbar.set)

        # 水平滚动条
        h_scrollbar = ttk.Scrollbar(script_tab, orient=tk.HORIZONTAL, command=self.script_text.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.script_text.config(xscrollcommand=h_scrollbar.set)

        # 第二个tab页：颜色识别
        color_tab = ttk.Frame(self.script_notebook)
        self.script_notebook.add(color_tab, text="颜色识别")
        self.create_color_recognition_tab(color_tab)

    def create_color_recognition_tab(self, parent):
        """创建颜色识别标签页"""
        # 主容器
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 颜色识别勾选框
        color_recognition_frame = ttk.Frame(main_frame, padding="8")
        color_recognition_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.color_recognition_enabled = tk.BooleanVar(value=False)
        color_recognition_checkbox = ttk.Checkbutton(color_recognition_frame, text="颜色识别", variable=self.color_recognition_enabled)
        color_recognition_checkbox.pack(side=tk.LEFT)
        color_recognition_checkbox.bind("<Enter>", lambda e: self.show_tooltip(e, "勾选后，启动脚本运行时会自动激活颜色识别功能"))
        color_recognition_checkbox.bind("<Leave>", lambda e: self.hide_tooltip())
        
        # 区域选择
        region_frame = ttk.LabelFrame(main_frame, text="区域选择", padding="8")
        region_frame.pack(fill=tk.X, pady=(0, 8))
        
        region_btn = ttk.Button(region_frame, text="选择区域", command=self.select_color_region)
        region_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        self.region_var = tk.StringVar(value="未选择区域")
        region_label = ttk.Label(region_frame, textvariable=self.region_var, width=30)
        region_label.pack(side=tk.LEFT)
        
        # 颜色选择
        color_frame = ttk.LabelFrame(main_frame, text="颜色选择", padding="8")
        color_frame.pack(fill=tk.X, pady=(0, 8))
        
        color_btn = ttk.Button(color_frame, text="选择颜色", command=self.select_color)
        color_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        self.color_var = tk.StringVar(value="未选择颜色")
        color_label = ttk.Label(color_frame, textvariable=self.color_var, width=20)
        color_label.pack(side=tk.LEFT, padx=(0, 8))
        
        # 颜色展示槽
        self.color_display = tk.Frame(color_frame, width=30, height=20, relief="sunken", borderwidth=1)
        self.color_display.pack(side=tk.LEFT, padx=(0, 15))
        self.color_display.config(background="gray")  # 默认灰色
        
        # 颜色容差
        ttk.Label(color_frame, text="容差:").pack(side=tk.LEFT)
        self.tolerance_var = tk.IntVar(value=10)
        tolerance_entry = ttk.Entry(color_frame, textvariable=self.tolerance_var, width=5)
        tolerance_entry.pack(side=tk.LEFT, padx=(0, 8))
        
        # 检查间隔
        interval_frame = ttk.LabelFrame(main_frame, text="检查设置", padding="8")
        interval_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(interval_frame, text="检查间隔(秒):").pack(side=tk.LEFT, padx=(0, 8))
        self.interval_var = tk.DoubleVar(value=5.0)
        interval_entry = ttk.Entry(interval_frame, textvariable=self.interval_var, width=6)
        interval_entry.pack(side=tk.LEFT, padx=(0, 8))
        
        # 命令输入区域
        commands_frame = ttk.LabelFrame(main_frame, text="颜色识别执行命令", padding="8")
        commands_frame.pack(fill=tk.BOTH, expand=True)
        
        self.color_commands_text = tk.Text(commands_frame, wrap=tk.NONE, font=("Consolas", 10), height=10)
        self.color_commands_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 垂直滚动条
        v_scrollbar = ttk.Scrollbar(commands_frame, orient=tk.VERTICAL, command=self.color_commands_text.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.color_commands_text.config(yscrollcommand=v_scrollbar.set)
        
        # 水平滚动条
        h_scrollbar = ttk.Scrollbar(commands_frame, orient=tk.HORIZONTAL, command=self.color_commands_text.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.color_commands_text.config(xscrollcommand=h_scrollbar.set)
        
        # 命令说明
        info_frame = ttk.Frame(main_frame, padding="8")
        info_frame.pack(fill=tk.X)
        
        info_label = ttk.Label(info_frame, text="额外命令: StartScript/StopScript；用于开始/停止脚本运行", 
                              font=("Arial", 9), foreground="gray")
        info_label.pack(anchor=tk.W)

    def start_key_listening(self, target_var, button, is_shortcut=False):
        """开始监听用户按下的按键"""
        # 保存当前焦点
        current_focus = self.root.focus_get()
        
        # 保存原始状态文本，用于恢复
        original_status = self.status_var.get()
        
        # 更新按钮状态
        original_text = button.cget("text")
        button.config(state="disabled")
        
        # 在原有状态栏显示提示信息
        self.status_var.set("请按任意按键进行设置，按ESC键清空当前记录")
        
        # 创建按键监听函数
        def on_key_press(event):
            """处理按键按下事件
            屏蔽中文输入法，只处理物理按键事件
            """
            # 恢复原始状态文本
            self.status_var.set(original_status)
            
            # 获取按键名称 - 使用keysym获取物理按键，而非字符
            keysym = event.keysym
            
            # 过滤掉中文输入法相关事件
            # 只处理物理按键，不处理输入法生成的字符
            # 允许的按键类型：
            # 1. 单个字符（如字母、数字、符号）
            # 2. 功能按键（如Insert、Delete、Home、End、PageUp、PageDown等）
            if not keysym:
                # 无效按键，跳过
                return "break"
            
            # 允许的功能按键列表
            allowed_function_keys = [
                "Insert", "Delete", "Home", "End", "Prior", "Next", "PageUp", "PageDown",
                "Up", "Down", "Left", "Right",
                "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12",
                "Escape", "Tab", "Return", "Enter", "Space", "BackSpace",
                "Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L", "Alt_R"
            ]
            
            # 检查按键是否允许：
            # - 单个字符，或
            # - 在允许的功能按键列表中，或
            # - 以"Key"开头的按键
            if not (
                len(keysym) == 1 or 
                keysym in allowed_function_keys or 
                keysym.startswith("Key")
            ):
                # 这可能是一个输入法生成的字符，跳过
                return "break"
            
            # 按键名称映射表 - 将系统按键名称转换为用户友好的名称
            keysym_map = {
                "Prior": "PageUp",    # PageUp键在Tkinter中可能被识别为Prior
                "Next": "PageDown",   # PageDown键在Tkinter中可能被识别为Next
                "Return": "Enter"     # Return键转换为更常用的Enter
            }
            
            # 转换按键名称为用户友好的名称
            keysym = keysym_map.get(keysym, keysym)
            
            # 特殊处理ESC键：清空当前记录的按键
            if keysym == "Escape":
                # 清空当前按键配置
                target_var.set("")
                
                # 恢复按钮状态
                button.config(state="normal")
                
                # 解除按键监听
                self.root.unbind("<KeyPress>", funcid=key_listener_id)
                
                # 恢复焦点
                if current_focus:
                    current_focus.focus_set()
                
                return "break"  # 阻止事件继续传播
            
            # 设置按键值
            target_var.set(keysym)
            
            # 如果是快捷键设置，更新快捷键对象
            if is_shortcut:
                self.update_hotkey()
            
            # 恢复按钮状态
            button.config(state="normal")
            
            # 解除按键监听
            self.root.unbind("<KeyPress>", funcid=key_listener_id)
            
            # 恢复焦点
            if current_focus:
                current_focus.focus_set()
            
            return "break"  # 阻止事件继续传播
        
        # 绑定按键事件
        key_listener_id = self.root.bind("<KeyPress>", on_key_press)
        
        # 设置窗口焦点，确保能捕获按键事件
        self.root.focus_set()

    def insert_key_command(self):
        """插入按键命令到当前选中的文本框"""
        key = self.key_var.get().strip()
        key_type = self.key_type.get()
        count = self.key_count.get()
        
        if not key:
            messagebox.showwarning("警告", "请输入按键名称！")
            return
        
        if count < 1:
            messagebox.showwarning("警告", "请输入有效的执行次数！")
            return
        
        # 格式化命令
        command = f"{key_type} \"{key}\", {count}\n"
        
        # 获取当前选中的标签页
        if hasattr(self, 'script_notebook'):
            current_tab = self.script_notebook.select()
            tab_text = self.script_notebook.tab(current_tab, "text")
            
            # 插入到对应的文本框
            if tab_text == "颜色识别" and hasattr(self, 'color_commands_text'):
                self.color_commands_text.insert(tk.INSERT, command)
                self.color_commands_text.see(tk.END)
            elif hasattr(self, 'script_text'):
                self.script_text.insert(tk.INSERT, command)
                self.script_text.see(tk.END)

    def insert_delay_command(self):
        """插入延迟命令到当前选中的文本框"""
        delay = self.delay_entry.get().strip()
        
        if not delay.isdigit() or int(delay) < 0:
            messagebox.showwarning("警告", "请输入有效的延迟时间！")
            return
        
        # 格式化命令
        command = f"Delay {delay}\n"
        
        # 获取当前选中的标签页
        if hasattr(self, 'script_notebook'):
            current_tab = self.script_notebook.select()
            tab_text = self.script_notebook.tab(current_tab, "text")
            
            # 插入到对应的文本框
            if tab_text == "颜色识别" and hasattr(self, 'color_commands_text'):
                self.color_commands_text.insert(tk.INSERT, command)
                self.color_commands_text.see(tk.END)
            elif hasattr(self, 'script_text'):
                self.script_text.insert(tk.INSERT, command)
                self.script_text.see(tk.END)

    def insert_mouse_click_command(self):
        """插入鼠标点击命令"""
        button = self.mouse_button_var.get()
        action = self.mouse_action_var.get()
        count = self.mouse_count_var.get()
        
        if count < 1:
            messagebox.showwarning("警告", "请输入有效的执行次数！")
            return
        
        # 格式化鼠标点击命令
        mouse_command = f"{button}{action} {count}\n"
        
        # 获取当前选中的标签页
        if hasattr(self, 'script_notebook'):
            current_tab = self.script_notebook.select()
            tab_text = self.script_notebook.tab(current_tab, "text")
            
            # 插入到对应的文本框
            if tab_text == "颜色识别" and hasattr(self, 'color_commands_text'):
                self.color_commands_text.insert(tk.INSERT, mouse_command)
                self.color_commands_text.see(tk.END)
            elif hasattr(self, 'script_text'):
                self.script_text.insert(tk.INSERT, mouse_command)
                self.script_text.see(tk.END)

    def select_coordinate(self):
        """选择坐标点"""
        self.log_message("开始选择坐标点...")
        # 创建坐标点选择窗口
        self.create_coordinate_selection_window()

    def create_coordinate_selection_window(self):
        """创建坐标点选择窗口"""
        # 检查screeninfo库是否可用
        try:
            import screeninfo
            monitors = screeninfo.get_monitors()
            
            # 计算整个虚拟屏幕的边界
            min_x = min(monitor.x for monitor in monitors)
            min_y = min(monitor.y for monitor in monitors)
            max_x = max(monitor.x + monitor.width for monitor in monitors)
            max_y = max(monitor.y + monitor.height for monitor in monitors)
        except ImportError:
            messagebox.showerror("错误", "screeninfo库未安装，无法支持多显示器选择。请运行 'pip install screeninfo' 安装该库。")
            return
        except Exception as e:
            # 如果获取显示器信息失败，使用默认值
            min_x, min_y, max_x, max_y = 0, 0, 1920, 1080
        
        # 创建覆盖整个虚拟屏幕的选择窗口
        self.coordinate_window = tk.Toplevel(self.root)
        # 移除窗口装饰，确保窗口能够覆盖整个屏幕，包括顶部区域
        self.coordinate_window.overrideredirect(True)
        self.coordinate_window.geometry(f"{max_x - min_x}x{max_y - min_y}+{min_x}+{min_y}")
        self.coordinate_window.attributes("-alpha", 0.3)
        self.coordinate_window.attributes("-topmost", True)
        self.coordinate_window.config(cursor="crosshair")
        
        # 创建画布
        self.coordinate_canvas = tk.Canvas(self.coordinate_window, bg="white", highlightthickness=0)
        self.coordinate_canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绑定鼠标事件
        self.coordinate_canvas.bind("<Button-1>", self.on_coordinate_select)
        
        # 绑定ESC键退出选择
        self.coordinate_window.bind("<Escape>", lambda e: self.coordinate_window.destroy())

    def on_coordinate_select(self, event):
        """坐标点选择事件处理"""
        # 获取鼠标在屏幕上的绝对坐标
        abs_x = event.x_root
        abs_y = event.y_root
        
        # 关闭选择窗口
        self.coordinate_window.destroy()
        
        # 格式化坐标命令
        coordinate_command = f"MoveTo {abs_x}, {abs_y}\n"
        
        # 获取当前选中的标签页
        if hasattr(self, 'script_notebook'):
            current_tab = self.script_notebook.select()
            tab_text = self.script_notebook.tab(current_tab, "text")
            
            # 插入到对应的文本框
            if tab_text == "颜色识别" and hasattr(self, 'color_commands_text'):
                self.color_commands_text.insert(tk.INSERT, coordinate_command)
                self.color_commands_text.see(tk.END)
            elif hasattr(self, 'script_text'):
                self.script_text.insert(tk.INSERT, coordinate_command)
                self.script_text.see(tk.END)
        
        # 记录日志
        self.log_message(f"已选择坐标点: ({abs_x}, {abs_y})")

    def insert_combo_command(self):
        """插入组合按键命令到当前选中的文本框"""
        key = self.combo_key_var.get().strip()
        key_delay = self.combo_key_delay.get().strip()
        after_delay = self.combo_after_delay.get().strip()
        
        if not key:
            messagebox.showwarning("警告", "请输入按键名称！")
            return
        
        if not key_delay.isdigit() or int(key_delay) < 0:
            messagebox.showwarning("警告", "请输入有效的按键延迟时间！")
            return
        
        if not after_delay.isdigit() or int(after_delay) < 0:
            messagebox.showwarning("警告", "请输入有效的抬起后延迟时间！")
            return
        
        # 格式化组合命令序列
        combo_command = f"Delay {key_delay}\nKeyDown \"{key}\", 1\nDelay {after_delay}\nKeyUp \"{key}\", 1\n"
        
        # 获取当前选中的标签页
        if hasattr(self, 'script_notebook'):
            current_tab = self.script_notebook.select()
            tab_text = self.script_notebook.tab(current_tab, "text")
            
            # 插入到对应的文本框
            if tab_text == "颜色识别" and hasattr(self, 'color_commands_text'):
                self.color_commands_text.insert(tk.INSERT, combo_command)
                self.color_commands_text.see(tk.END)
            elif hasattr(self, 'script_text'):
                self.script_text.insert(tk.INSERT, combo_command)
                self.script_text.see(tk.END)



    def start_script(self, start_color_recognition=True):
        """从首页启动脚本
        
        Args:
            start_color_recognition: 是否同时启动颜色识别线程，默认值为True
        """
        # 检查系统是否已完全停止，如果是则拒绝启动脚本
        if self.system_stopped:
            self.log_message("系统已完全停止，拒绝执行StartScript命令")
            return
        
        if not hasattr(self, 'script_executor'):
            self.script_executor = ScriptExecutor(self)
        
        # 获取脚本内容
        if hasattr(self, 'script_text'):
            script_content = self.script_text.get(1.0, tk.END)
            if not script_content.strip():
                messagebox.showwarning("警告", "脚本内容为空，请先编写脚本！")
                return
            
            self.script_executor.run_script(script_content)
            if hasattr(self, 'status_labels') and "script" in self.status_labels:
                self.status_labels["script"].set("脚本运行: 运行中")
            self.status_var.set("脚本执行中...")
            self.log_message("脚本已启动")
        
        # 根据参数决定是否启动颜色识别
        if start_color_recognition and hasattr(self, 'color_recognition_enabled') and self.color_recognition_enabled.get():
            self.start_color_recognition()
            self.log_message("颜色识别已自动启动")

    def stop_script(self, stop_color_recognition=True):
        """停止脚本执行
        
        Args:
            stop_color_recognition: 是否同时停止颜色识别线程，默认值为True
        """
        if hasattr(self, 'script_executor') and hasattr(self.script_executor, 'is_running') and self.script_executor.is_running:
            self.script_executor.stop_script()
            if hasattr(self, 'status_labels') and "script" in self.status_labels:
                self.status_labels["script"].set("脚本运行: 未运行")
            self.status_var.set("脚本已停止")
        
        # 根据参数决定是否停止颜色识别
        if stop_color_recognition:
            # 无论color_recognition_enabled状态如何，都停止颜色识别线程
            self.stop_color_recognition()

    def start_recording(self):
        """开始录制脚本"""
        if not hasattr(self, 'script_executor'):
            self.script_executor = ScriptExecutor(self)
        
        self.script_executor.start_recording()
        if hasattr(self, 'record_btn'):
            self.record_btn.config(text="录制中...", state="disabled")
        if hasattr(self, 'stop_record_btn'):
            self.stop_record_btn.config(state="normal")
        if hasattr(self, 'status_labels') and "script" in self.status_labels:
            self.status_labels["script"].set("脚本运行: 录制中")
        self.status_var.set("录制中...")
        self.log_message("开始录制脚本")
        # 播放开始运行音效
        self.play_start_sound()

    def stop_recording(self):
        """停止录制脚本"""
        if hasattr(self, 'script_executor'):
            self.script_executor.stop_recording()
            if hasattr(self, 'record_btn'):
                self.record_btn.config(text="开始录制", state="normal")
            if hasattr(self, 'stop_record_btn'):
                self.stop_record_btn.config(state="disabled")
            if hasattr(self, 'status_labels') and "script" in self.status_labels:
                self.status_labels["script"].set("脚本运行: 未运行")
            self.status_var.set("录制已停止")
            self.log_message("停止录制脚本")
            # 播放停止运行音效
            self.play_stop_sound()

    def select_color_region(self):
        """选择颜色识别区域"""
        self.log_message("开始选择颜色识别区域...")
        # 使用通用的区域选择方法
        self._start_selection("color", 0)

    def select_color(self):
        """选择颜色"""
        self.log_message("开始选择目标颜色...")
        # 创建颜色选择窗口
        self.create_color_selection_window()

    def create_color_selection_window(self):
        """创建颜色选择窗口"""
        try:
            import screeninfo
            monitors = screeninfo.get_monitors()
            
            # 计算整个虚拟屏幕的边界
            min_x = min(monitor.x for monitor in monitors)
            min_y = min(monitor.y for monitor in monitors)
            max_x = max(monitor.x + monitor.width for monitor in monitors)
            max_y = max(monitor.y + monitor.height for monitor in monitors)
        except ImportError:
            messagebox.showerror("错误", "screeninfo库未安装，无法支持多显示器选择。请运行 'pip install screeninfo' 安装该库。")
            return
        except Exception as e:
            # 如果获取显示器信息失败，使用默认值
            min_x, min_y, max_x, max_y = 0, 0, 1920, 1080
        
        # 创建覆盖整个虚拟屏幕的选择窗口
        self.color_selection_window = tk.Toplevel(self.root)
        # 移除窗口装饰，确保窗口能够覆盖整个屏幕，包括顶部区域
        self.color_selection_window.overrideredirect(True)
        self.color_selection_window.geometry(f"{max_x - min_x}x{max_y - min_y}+{min_x}+{min_y}")
        self.color_selection_window.attributes("-alpha", 0.3)
        self.color_selection_window.attributes("-topmost", True)
        self.color_selection_window.config(cursor="crosshair")
        
        # 创建画布
        self.color_canvas = tk.Canvas(self.color_selection_window, bg="white", highlightthickness=0)
        self.color_canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绑定鼠标事件
        self.color_canvas.bind("<Button-1>", self.on_color_select)
        
        # 绑定ESC键退出选择
        self.color_selection_window.bind("<Escape>", lambda e: self.color_selection_window.destroy())

    def on_color_select(self, event):
        """处理颜色选择事件"""
        # 先隐藏选择窗口，避免捕获到蒙版
        self.color_selection_window.withdraw()
        
        # 等待窗口隐藏
        self.color_selection_window.update()
        
        # 获取鼠标在屏幕上的实际位置，使用event.x_root和event.y_root获取绝对坐标
        abs_x, abs_y = event.x_root, event.y_root
        
        # 截取屏幕像素，使用all_screens=True确保捕获所有屏幕
        screen = ImageGrab.grab(all_screens=True)
        
        try:
            import screeninfo
            monitors = screeninfo.get_monitors()
            min_x = min(monitor.x for monitor in monitors)
            min_y = min(monitor.y for monitor in monitors)
        except:
            min_x, min_y = 0, 0
        
        # 将绝对坐标转换为截图内的相对坐标
        rel_x = abs_x - min_x
        rel_y = abs_y - min_y
        
        # 获取像素颜色
        pixel = screen.getpixel((rel_x, rel_y))
        
        # 保存目标颜色
        self.target_color = pixel
        r, g, b = pixel
        self.color_var.set(f"RGB({r}, {g}, {b})")
        self.log_message(f"选择颜色: RGB({r}, {g}, {b})")
        self.log_message(f"选择位置: ({abs_x}, {abs_y})")
        
        # 更新颜色显示槽
        self.color_display.config(background=f"#{r:02x}{g:02x}{b:02x}")
        
        # 关闭选择窗口
        self.color_selection_window.destroy()



    def start_color_recognition(self):
        """开始颜色识别"""
        if not hasattr(self, 'color_recognition'):
            self.color_recognition = ColorRecognition(self)
        
        # 获取设置参数
        try:
            # 从目标颜色变量获取颜色值
            if hasattr(self, 'target_color') and self.target_color:
                target_color = self.target_color
            else:
                messagebox.showwarning("警告", "请先选择目标颜色！")
                return
            
            tolerance = int(self.tolerance_var.get())
            interval = float(self.interval_var.get())
            commands = self.color_commands_text.get(1.0, tk.END)
        except ValueError:
            messagebox.showwarning("警告", "颜色设置参数格式错误，请检查！")
            return
        
        # 检查区域是否已选择
        if not hasattr(self, 'color_recognition_region') or not self.color_recognition_region:
            messagebox.showwarning("警告", "请先选择颜色识别区域！")
            return
        
        # 设置颜色识别区域
        self.color_recognition.set_region(self.color_recognition_region)
        
        # 启动颜色识别
        self.color_recognition.start_recognition(target_color, tolerance, interval, commands)
        self.status_var.set("颜色识别中...")

    def stop_color_recognition(self):
        """停止颜色识别"""
        if hasattr(self, 'color_recognition'):
            # 检查线程是否正在运行
            if hasattr(self.color_recognition, 'is_running') and self.color_recognition.is_running:
                self.color_recognition.stop_recognition()
                self.status_var.set("颜色识别已停止")
            elif hasattr(self.color_recognition, 'recognition_thread') and self.color_recognition.recognition_thread.is_alive():
                # 如果is_running为False但是线程仍然在运行，强制停止
                self.color_recognition.is_running = False
                self.color_recognition.recognition_thread.join(timeout=2)
                self.status_var.set("颜色识别已停止")

    def update_hotkey(self):
        """更新快捷键配置"""
        # 这里可以添加快捷键更新逻辑
        pass

    def clear_script(self):
        """清空脚本文本框"""
        if messagebox.askyesno("确认", "确定要清空当前脚本吗？"):
            self.script_text.delete(1.0, tk.END)

    def save_script(self):
        """保存脚本到文件"""
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            title="保存脚本"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.script_text.get(1.0, tk.END))
                messagebox.showinfo("成功", f"脚本已保存到: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存脚本失败: {str(e)}")

    def load_script(self):
        """从文件加载脚本"""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            title="加载脚本"
        )
        if file_path:
            try:
                # 尝试不同编码读取文件
                encodings = ['utf-8', 'gbk', 'gb2312', 'ansi']
                content = None
                
                for encoding in encodings:
                    try:
                        with open(file_path, "r", encoding=encoding) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                
                if content is None:
                    messagebox.showerror("错误", "无法读取文件，编码不支持！")
                    return
                
                self.script_text.delete(1.0, tk.END)
                self.script_text.insert(1.0, content)
                messagebox.showinfo("成功", f"脚本已从: {file_path} 加载")
            except Exception as e:
                messagebox.showerror("错误", f"加载脚本失败: {str(e)}")

    def show_tooltip(self, event, text):
        """显示工具提示"""
        self.tooltip = tk.Toplevel(self.root)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root-10}")
        label = ttk.Label(self.tooltip, text=text, background="lightyellow", relief="solid", borderwidth=1, padding=(5, 2))
        label.pack()

    def hide_tooltip(self):
        """隐藏工具提示"""
        if hasattr(self, 'tooltip'):
            self.tooltip.destroy()

class ScriptExecutor:
    """脚本执行器类"""
    def __init__(self, app):
        self.app = app
        self.is_running = False
        self.is_paused = False
        self.execution_thread = None
        self.recording_thread = None
        self.recording_events = []
        self.recording_start_time = None
        self.last_event_time = None
        self.recording_grace_period = False

    def run_script(self, script_content):
        """执行脚本（无限循环）"""
        def execute():
            self.is_running = True
            self.is_paused = False
            # 记录当前按下的按键，用于确保最终能抬起所有按键
            pressed_keys = set()
            
            try:
                # 解析脚本内容
                lines = script_content.splitlines()
                commands = []
                for line in lines:
                    command = self.parse_line(line)
                    if command:
                        commands.append(command)
                
                if not commands:
                    self.app.log_message("脚本中没有有效命令！")
                    self.is_running = False
                    return
                
                # 无限循环执行脚本，直到用户停止
                while self.is_running:
                    # 遍历所有命令，执行一次
                    for i, command in enumerate(commands):
                        if not self.is_running:
                            break
                        
                        while self.is_paused:
                            time.sleep(0.1)
                            if not self.is_running:
                                break
                        
                        if not self.is_running:
                            break
                        
                        # 处理按键命令，跟踪按下的按键
                        if command["type"] in ["keydown", "keyup"]:
                            key = command["key"]
                            for _ in range(command["count"]):
                                if not self.is_running:
                                    break
                                while self.is_paused:
                                    time.sleep(0.1)
                                    if not self.is_running:
                                        break
                                if not self.is_running:
                                    break
                                
                                if command["type"] == "keydown":
                                    if key not in pressed_keys:
                                        pyautogui.keyDown(key)
                                        pressed_keys.add(key)
                                        self.app.log_message(f"执行: 按下 {key}")
                                elif command["type"] == "keyup":
                                    if key in pressed_keys:
                                        pyautogui.keyUp(key)
                                        pressed_keys.remove(key)
                                        self.app.log_message(f"执行: 抬起 {key}")
                        else:
                            # 优化延迟逻辑：如果当前命令是延迟，且下一条命令是按键操作，则减少100ms延迟
                            if command["type"] == "delay":
                                # 检查下一条命令是否为按键操作
                                if i + 1 < len(commands):
                                    next_cmd = commands[i + 1]
                                    if next_cmd["type"] in ["keydown", "keyup"]:
                                        # 下一条是按键操作，减少100ms延迟
                                        original_time = command["time"]
                                        # 创建临时命令副本，避免修改原始命令
                                        temp_command = command.copy()
                                        # 确保延迟时间不小于0
                                        temp_command["time"] = max(0, original_time - 100)
                                        self.execute_command(temp_command)
                                    else:
                                        # 下一条不是按键操作，使用原始延迟
                                        self.execute_command(command)
                                else:
                                    # 已经是最后一条命令，使用原始延迟
                                    self.execute_command(command)
                            else:
                                # 非延迟命令，直接执行
                                self.execute_command(command)
            except Exception as e:
                error_msg = f"脚本执行出错: {str(e)}"
                self.app.log_message(error_msg)
                self.app.status_var.set(f"执行错误: {str(e)}")
            finally:
                # 确保所有按下的按键都被抬起
                for key in pressed_keys:
                    try:
                        pyautogui.keyUp(key)
                        self.app.log_message(f"确保抬起: {key}")
                    except Exception as e:
                        self.app.log_message(f"抬起按键 {key} 时出错: {str(e)}")
                
                self.is_running = False
        
        # 启动执行线程
        self.execution_thread = threading.Thread(target=execute, daemon=True)
        self.execution_thread.start()

    def run_script_once(self, script_content):
        """执行脚本（只执行一遍）"""
        def execute():
            self.is_running = True
            self.is_paused = False
            # 记录当前按下的按键，用于确保最终能抬起所有按键
            pressed_keys = set()
            
            try:
                # 解析脚本内容
                lines = script_content.splitlines()
                commands = []
                for line in lines:
                    command = self.parse_line(line)
                    if command:
                        commands.append(command)
                
                if not commands:
                    self.app.log_message("脚本中没有有效命令！")
                    self.is_running = False
                    return
                
                # 只执行一遍脚本
                for i, command in enumerate(commands):
                    if not self.is_running:
                        break
                    
                    while self.is_paused:
                        time.sleep(0.1)
                        if not self.is_running:
                            break
                    
                    if not self.is_running:
                        break
                    
                    # 处理按键命令，跟踪按下的按键
                    if command["type"] in ["keydown", "keyup"]:
                        key = command["key"]
                        for _ in range(command["count"]):
                            if not self.is_running:
                                break
                            while self.is_paused:
                                time.sleep(0.1)
                                if not self.is_running:
                                    break
                            if not self.is_running:
                                break
                            
                            if command["type"] == "keydown":
                                if key not in pressed_keys:
                                    pyautogui.keyDown(key)
                                    pressed_keys.add(key)
                                    self.app.log_message(f"执行: 按下 {key}")
                            elif command["type"] == "keyup":
                                if key in pressed_keys:
                                    pyautogui.keyUp(key)
                                    pressed_keys.remove(key)
                                    self.app.log_message(f"执行: 抬起 {key}")
                    else:
                        # 优化延迟逻辑：如果当前命令是延迟，且下一条命令是按键操作，则减少100ms延迟
                        if command["type"] == "delay":
                            # 检查下一条命令是否为按键操作
                            if i + 1 < len(commands):
                                next_cmd = commands[i + 1]
                                if next_cmd["type"] in ["keydown", "keyup"]:
                                    # 下一条是按键操作，减少100ms延迟
                                    original_time = command["time"]
                                    # 创建临时命令副本，避免修改原始命令
                                    temp_command = command.copy()
                                    # 确保延迟时间不小于0
                                    temp_command["time"] = max(0, original_time - 100)
                                    self.execute_command(temp_command)
                                else:
                                    # 下一条不是按键操作，使用原始延迟
                                    self.execute_command(command)
                            else:
                                # 已经是最后一条命令，使用原始延迟
                                self.execute_command(command)
                        else:
                            # 非延迟命令，直接执行
                            self.execute_command(command)
            except Exception as e:
                error_msg = f"脚本执行出错: {str(e)}"
                self.app.log_message(error_msg)
                self.app.status_var.set(f"执行错误: {str(e)}")
            finally:
                # 确保所有按下的按键都被抬起
                for key in pressed_keys:
                    try:
                        pyautogui.keyUp(key)
                        self.app.log_message(f"确保抬起: {key}")
                    except Exception as e:
                        self.app.log_message(f"抬起按键 {key} 时出错: {str(e)}")
                
                self.is_running = False
                self.app.log_message("脚本执行完成")
        
        # 启动执行线程
        self.execution_thread = threading.Thread(target=execute, daemon=True)
        self.execution_thread.start()

    def parse_line(self, line):
        """解析单条伪代码命令"""
        line = line.strip()
        if not line:
            return None  # 跳过空行
        
        # 匹配 KeyDown 或 KeyUp 命令，支持单引号和双引号，大小写不敏感
        key_pattern = re.compile(r'^(KeyDown|KeyUp)\s+["\'](.*?)["\']\s*\,\s*(\d+)$', re.IGNORECASE)
        match = key_pattern.match(line)
        if match:
            command_type = match.group(1).lower()  # 转换为小写：keydown 或 keyup
            key = match.group(2).lower()  # 转换按键名为小写，适配 pyautogui
            count = int(match.group(3))  # 执行次数
            return {
                "type": command_type,
                "key": key,
                "count": count
            }
        
        # 匹配鼠标点击命令，格式：LeftDown 1、RightUp 1等，大小写不敏感
        mouse_pattern = re.compile(r'^(Left|Right|Middle)(Down|Up)\s+(\d+)$', re.IGNORECASE)
        match = mouse_pattern.match(line)
        if match:
            button = match.group(1).lower()  # 转换为小写：left、right、middle
            action = match.group(2).lower()  # 转换为小写：down、up
            count = int(match.group(3))  # 执行次数
            return {
                "type": f"mouse_{action}",
                "button": button,
                "count": count
            }
        
        # 匹配鼠标移动命令，格式：MoveTo 300,200，大小写不敏感
        move_pattern = re.compile(r"^MoveTo\s+(\d+)\s*\,\s*(\d+)$", re.IGNORECASE)
        match = move_pattern.match(line)
        if match:
            x = int(match.group(1))  # x坐标
            y = int(match.group(2))  # y坐标
            return {
                "type": "moveto",
                "x": x,
                "y": y
            }
        
        # 匹配 Delay 命令，大小写不敏感
        delay_pattern = re.compile(r"^Delay\s+(\d+)$", re.IGNORECASE)
        match = delay_pattern.match(line)
        if match:
            delay_time = int(match.group(1))  # 延迟时间（毫秒）
            return {
                "type": "delay",
                "time": delay_time
            }
        
        # 匹配特殊指令：StopScript 和 StartScript
        if line.strip().lower() == "stopscript":
            return {
                "type": "stopscript"
            }
        elif line.strip().lower() == "startscript":
            return {
                "type": "startscript"
            }
        
        # 如果都不匹配，返回 None 表示无效命令
        return None

    def execute_command(self, command):
        """执行单个命令"""
        try:
            if command["type"] in ["keydown", "keyup"]:
                key = command["key"]
                for _ in range(command["count"]):
                    if not self.is_running:
                        break
                    while self.is_paused:
                        time.sleep(0.1)
                        if not self.is_running:
                            break
                    if not self.is_running:
                        break
                    
                    if command["type"] == "keydown":
                        pyautogui.keyDown(key)
                        self.app.log_message(f"执行: 按下 {key}")
                    else:
                        pyautogui.keyUp(key)
                        self.app.log_message(f"执行: 抬起 {key}")
            elif command["type"] in ["mouse_down", "mouse_up"]:
                button = command["button"]
                for _ in range(command["count"]):
                    if not self.is_running:
                        break
                    while self.is_paused:
                        time.sleep(0.1)
                        if not self.is_running:
                            break
                    if not self.is_running:
                        break
                    
                    if command["type"] == "mouse_down":
                        pyautogui.mouseDown(button=button)
                        self.app.log_message(f"执行: 按下鼠标{button}键")
                    else:
                        pyautogui.mouseUp(button=button)
                        self.app.log_message(f"执行: 抬起鼠标{button}键")
            elif command["type"] == "moveto":
                x = command["x"]
                y = command["y"]
                if self.is_running and not self.is_paused:
                    pyautogui.moveTo(x, y)
                    self.app.log_message(f"执行: 移动鼠标到 ({x}, {y})")
            elif command["type"] == "delay":
                delay_time = command["time"] / 1000  # 转换为秒
                self.app.log_message(f"执行: 延迟 {delay_time}秒")
                
                # 分段延迟，以便能够响应暂停/停止命令
                start_time = time.time()
                elapsed_time = 0
                while elapsed_time < delay_time:
                    if not self.is_running:
                        break
                    while self.is_paused:
                        time.sleep(0.1)
                        if not self.is_running:
                            break
                    if not self.is_running:
                        break
                    
                    sleep_time = min(0.1, delay_time - elapsed_time)
                    time.sleep(sleep_time)
                    elapsed_time = time.time() - start_time
            elif command["type"] == "stopscript":
                # 停止脚本执行，确保在主线程中执行
                if not self.is_running:
                    return
                while self.is_paused:
                    time.sleep(0.1)
                    if not self.is_running:
                        return
                if not self.is_running:
                    return
                self.app.log_message("执行: 停止脚本")
                # 调用应用程序的停止脚本方法，使用after确保在主线程中执行，传递stop_color_recognition=False参数
                self.app.root.after(0, lambda: self.app.stop_script(stop_color_recognition=False))
                # 不立即设置is_running为False，让线程继续执行到下一个命令
            elif command["type"] == "startscript":
                # 启动脚本执行，确保在主线程中执行
                if not self.is_running:
                    return
                while self.is_paused:
                    time.sleep(0.1)
                    if not self.is_running:
                        return
                if not self.is_running:
                    return
                self.app.log_message("执行: 启动脚本")
                # 调用应用程序的启动脚本方法，使用after确保在主线程中执行，传递start_color_recognition=False参数
                self.app.root.after(0, lambda: self.app.start_script(start_color_recognition=False))
        except Exception as e:
            # 添加错误处理，确保即使执行命令失败也不会导致应用程序崩溃
            error_msg = f"执行命令出错: {str(e)}"
            self.app.log_message(error_msg)
            # 记录详细的错误信息
            import traceback
            self.app.log_message(f"错误详情: {traceback.format_exc()}")
            # 继续执行其他命令，而不是终止整个脚本
            return

    def pause_script(self):
        """暂停脚本执行"""
        self.is_paused = True

    def resume_script(self):
        """恢复脚本执行"""
        self.is_paused = False

    def stop_script(self):
        """停止脚本执行"""
        self.is_running = False
        self.is_paused = False

    def start_recording(self):
        """开始录制按键"""
        # 设置录制缓冲期，避免记录开始录制时的操作
        self.recording_grace_period = True
        
        def record():
            import time
            self.is_recording = True
            self.recording_events = []
            self.recording_start_time = time.time()
            self.last_event_time = self.recording_start_time
            
            # 记录当前按下的按键，用于避免重复记录
            pressed_keys = set()
            # 记录鼠标移动的最后位置
            last_mouse_position = None
            
            # 导入pynput模块
            try:
                from pynput import keyboard, mouse

            except Exception as e:
                self.app.log_message(f"❌ 导入pynput模块失败: {str(e)}")
                self.is_recording = False
                return
            
            # 键盘事件处理
            def on_key_press(key):
                if not self.is_recording:
                    return False
                if getattr(self, 'recording_grace_period', False):
                    return
                
                try:
                    key_name = key.char
                except AttributeError:
                    key_name = key.name
                
                # 检查是否是录制快捷键（F11），如果是则不记录
                if key_name == 'f11':
                    return
                
                # 只记录首次按下的事件，避免重复记录
                if key_name not in pressed_keys:
                    current_time = time.time()
                    delay = int((current_time - self.last_event_time) * 1000)
                    self.last_event_time = current_time
                    
                    self.recording_events.append({
                        "type": "keydown",
                        "key": key_name,
                        "delay": delay
                    })
                    pressed_keys.add(key_name)
                    # 添加日志记录

            
            def on_key_release(key):
                if not self.is_recording:
                    return False
                if getattr(self, 'recording_grace_period', False):
                    return
                
                try:
                    key_name = key.char
                except AttributeError:
                    key_name = key.name
                
                # 检查是否是录制快捷键（F11），如果是则不记录
                if key_name == 'f11':
                    return
                
                # 只记录首次释放的事件
                if key_name in pressed_keys:
                    current_time = time.time()
                    delay = int((current_time - self.last_event_time) * 1000)
                    self.last_event_time = current_time
                    
                    self.recording_events.append({
                        "type": "keyup",
                        "key": key_name,
                        "delay": delay
                    })
                    pressed_keys.remove(key_name)
                    # 添加日志记录

            
            # 鼠标移动事件处理
            def on_mouse_move(x, y):
                if not self.is_recording:
                    return False
                if getattr(self, 'recording_grace_period', False):
                    return
                
                # 只记录鼠标位置，不立即添加到事件列表
                nonlocal last_mouse_position
                last_mouse_position = (x, y)
                # 添加日志记录
                # self.app.log_message(f"🔵 记录鼠标移动: ({x}, {y})")
            
            # 鼠标点击事件处理
            def on_mouse_click(x, y, button, pressed):
                if not self.is_recording:
                    return False
                if getattr(self, 'recording_grace_period', False):
                    return
                
                current_time = time.time()
                delay = int((current_time - self.last_event_time) * 1000)
                self.last_event_time = current_time
                
                button_name = button.name
                
                # 使用最后记录的鼠标位置或当前位置
                if last_mouse_position:
                    mouse_x, mouse_y = last_mouse_position
                else:
                    mouse_x, mouse_y = x, y
                
                # 添加鼠标移动事件
                self.recording_events.append({
                    "type": "moveto",
                    "x": int(mouse_x),
                    "y": int(mouse_y),
                    "delay": delay
                })
                
                # 添加鼠标点击事件
                self.recording_events.append({
                    "type": f"mouse_{'down' if pressed else 'up'}",
                    "button": button_name,
                    "x": int(mouse_x),
                    "y": int(mouse_y),
                    "delay": 0  # 鼠标移动后立即点击，不需要延迟
                })
                # 添加日志记录

            
            # 使用with语句创建监听器，确保在打包环境中也能正常工作
            import time
            
            # 0.5秒后关闭缓冲期，允许记录操作
            time.sleep(0.5)
            self.recording_grace_period = False
            
            # 添加日志记录

            
            try:
                # 使用with语句创建监听器
                with keyboard.Listener(on_press=on_key_press, on_release=on_key_release) as keyboard_listener, \
                     mouse.Listener(on_move=on_mouse_move, on_click=on_mouse_click) as mouse_listener:
                    

                    
                    # 等待录制停止
                    while self.is_recording:
                        time.sleep(0.1)
                        
            except Exception as e:
                self.app.log_message(f"❌ 启动事件监听器失败: {str(e)}")
                self.is_recording = False
            
            # 生成录制脚本
            self.generate_recorded_script()
        
        # 启动录制线程
        self.recording_thread = threading.Thread(target=record, daemon=True)
        self.recording_thread.start()

    def stop_recording(self):
        """停止录制按键"""
        # 设置录制缓冲期，避免记录停止录制时的操作
        self.recording_grace_period = True
        self.is_recording = False
        # 等待0.5秒后再生成脚本，确保缓冲期生效
        import time
        time.sleep(0.1)

    def generate_recorded_script(self):
        """生成录制脚本"""
        script_content = ""
        
        for event in self.recording_events:
            if event["delay"] > 0:
                script_content += f"Delay {event['delay']}\n"
            
            if event["type"] in ["keydown", "keyup"]:
                script_content += f"{event['type'].capitalize()} \"{event['key']}\", 1\n"
            elif event["type"] == "moveto":
                # 生成鼠标移动命令
                script_content += f"MoveTo {event['x']}, {event['y']}\n"
            elif event["type"] in ["mouse_down", "mouse_up"]:
                button = event["button"].capitalize()
                action = event["type"].split('_')[1].capitalize()
                script_content += f"{button}{action} 1\n"
        
        # 将生成的脚本插入到文本框
        self.app.root.after(0, lambda:
            (self.app.script_text.insert(tk.END, script_content),
             self.app.script_text.see(tk.END),
             self.app.log_message(f"录制完成，生成了 {len(self.recording_events)} 个事件"))
        )

class ColorRecognition:
    """颜色识别类"""
    def __init__(self, app):
        self.app = app
        self.is_running = False
        self.recognition_thread = None
        self.region = None
        self.target_color = None
        self.tolerance = 10
        self.interval = 5.0
        self.commands = ""

    def set_region(self, region):
        """设置颜色识别区域"""
        self.region = region

    def start_recognition(self, target_color, tolerance, interval, commands):
        """开始颜色识别"""
        self.target_color = target_color
        self.tolerance = tolerance
        self.interval = interval
        self.commands = commands
        
        def recognize():
            self.is_running = True
            
            while self.is_running:
                # 检查是否需要暂停（处理事件插队）
                if hasattr(self.app, 'event_queue') and self.app.event_queue:
                    # 检查是否有高优先级事件
                    high_priority_event = False
                    for event in self.app.event_queue:
                        event_type = event.get('type')
                        if event_type in ['number_recognition', 'timed_task', 'ocr_recognition']:
                            high_priority_event = True
                            break
                    
                    if high_priority_event:
                        time.sleep(0.1)
                        continue
                
                # 执行颜色识别
                if self.recognize_color():
                    # 识别到目标颜色，执行命令
                    self.execute_commands()
                    # 执行后暂停一段时间
                    time.sleep(5)  # 避免频繁执行
                
                # 检查间隔
                time.sleep(self.interval)
            
            self.is_running = False
            self.app.status_var.set("颜色识别已停止")
            
            # 更新UI状态
            self.app.root.after(0, lambda:
                (self.app.status_var.set("颜色识别已停止"),)
            )
        
        # 启动识别线程
        self.recognition_thread = threading.Thread(target=recognize, daemon=True)
        self.recognition_thread.start()

    def recognize_color(self):
        """执行颜色识别"""
        if not self.region:
            self.app.log_message("颜色识别失败: 未设置识别区域")
            return False
        
        try:
            # 截取区域图像，使用与文字识别和数字识别相同的方法
            screenshot = ImageGrab.grab(bbox=self.region, all_screens=True)
            
            # 检查截图是否为空
            if screenshot.size[0] == 0 or screenshot.size[1] == 0:
                self.app.log_message("颜色识别失败: 截图为空")
                return False
            
            # 转换为numpy数组
            img_array = np.array(screenshot)
            
            # 使用像素级检查方法
            # 转换目标颜色为numpy数组
            target_color = np.array(self.target_color)
            
            # 优化匹配逻辑，考虑RGB值范围限制
            valid_target_color = np.clip(np.array(self.target_color), 0, 255)
            lower_bound = np.maximum(0, valid_target_color - self.tolerance)
            upper_bound = np.minimum(255, valid_target_color + self.tolerance)
            
            # 检查每个像素是否在范围内
            is_match = np.all((img_array >= lower_bound) & (img_array <= upper_bound), axis=2)
            match_pixels = np.sum(is_match)
            
            if match_pixels > 0:
                # 识别到目标颜色
                self.app.log_message(f"✅ 识别到目标颜色，匹配像素数: {match_pixels}")
                return True
            else:
                # 未识别到目标颜色
                return False
        except Exception as e:
            self.app.log_message(f"颜色识别错误: {str(e)}")
            # 添加详细的错误信息，帮助调试
            import traceback
            self.app.log_message(f"错误详情: {traceback.format_exc()}")
            # 即使出错也返回False，确保应用程序不会崩溃
            return False
    


    def execute_commands(self):
        """执行识别后命令（只执行一遍）"""
        if not self.commands:
            return
        
        # 创建临时脚本执行器
        temp_executor = ScriptExecutor(self.app)
        
        # 执行命令（只执行一遍）
        temp_executor.run_script_once(self.commands)

    def stop_recognition(self):
        """停止颜色识别"""
        self.is_running = False
        if hasattr(self, 'recognition_thread') and self.recognition_thread.is_alive():
            # 等待线程结束
            self.recognition_thread.join(timeout=1)

def main():
    """主函数，用于命令行调用"""
    app = AutoDoorOCR()
    app.run()

if __name__ == "__main__":
    main()