import customtkinter as ctk
from tkinter import messagebox
import pyautogui
import threading
import os

from ui.theme import Theme, init_theme
from ui.widgets import AnimatedButton
from ui.home import create_home_tab
from ui.ocr_tab import create_ocr_tab
from ui.timed_tab import create_timed_tab
from ui.number_tab import create_number_tab
from ui.script_tab import create_script_tab
from ui.basic_tab import create_basic_tab
from ui.image_tab import create_image_tab
from core.config import ConfigManager
from core.platform import PlatformAdapter
from core.threading import ThreadManager
from core.events import EventManager
from core.logging import LoggingManager
from core.utils import exit_program
from core.controller import ModuleController
from core.proxy import OCRProxy, TimedProxy, NumberProxy, ScriptProxy, ColorProxy, ImageDetectionProxy, UIProxy
from input.permissions import PermissionManager
from input.controller import InputController
from input.keyboard import setup_shortcuts
from utils.version import VersionChecker, open_bilibili, open_tool_intro
from utils.tesseract import TesseractManager
from modules.ocr import OCRModule
from modules.timed import TimedModule
from modules.number import NumberModule
from modules.alarm import AlarmModule
from modules.script import ScriptModule
from modules.color import ColorRecognitionManager
from modules.image import ImageDetectionManager

VERSION = "2.2.0"


class AutoDoorOCR:
    def __init__(self):
        self._init_basic_settings()
        self._init_platform()
        self._init_managers()
        self._init_proxy_classes()
        self._init_ui()
        self._init_modules()
        self._load_config()
        self._start_services()

    def _init_basic_settings(self):
        pyautogui.FAILSAFE = False
        self.version = VERSION
        
        from core.atomic import AtomicBool
        self._is_running_atomic = AtomicBool(False)
        self._is_paused_atomic = AtomicBool(False)

        self.is_selecting = False
        self.last_trigger_time = 0
        self.system_stopped = False

        self.last_recognition_times = {}
        self.last_trigger_times = {}
        self._number_cache = {}

        self.click_delay = 0.5
        self.default_custom_key = "equal"
        self.default_keywords = ["men", "door"]
        self.default_ocr_language = "eng"

        self.ocr_thread = None
        self.timed_threads = []
        self.number_threads = []
        self.timed_stop_events = {}
        self.number_stop_events = {}

        self.PRIORITIES = {
            "number": 6,
            "timed": 5,
            "image": 4,
            "ocr": 3,
            "color": 2,
            "script": 1
        }

        self.timed_enabled_var = None
        self.timed_groups = []
        self.number_enabled_var = None
        self.number_regions = []
        self.current_number_region_index = None
        self.tesseract_path = ""
        self.tesseract_available = False

        self.alarm_enabled = {}
        self.ocr_delay_min = None
        self.ocr_delay_max = None
        self.ocr_groups = []
        self.current_ocr_region_index = None
        self.image_groups = []
        self.current_image_region_index = None
        
        self._current_page = 'home'
        self.nav_items = {}
        self.pages = {}
        self.module_switches = {}
        self.module_indicators = {}
    
    @property
    def is_running(self) -> bool:
        return self._is_running_atomic.get()
    
    @is_running.setter
    def is_running(self, value: bool) -> None:
        self._is_running_atomic.set(value)
    
    @property
    def is_paused(self) -> bool:
        return self._is_paused_atomic.get()
    
    @is_paused.setter
    def is_paused(self, value: bool) -> None:
        self._is_paused_atomic.set(value)

    def _init_platform(self):
        self.platform_adapter = PlatformAdapter(self)
        config_dir = self.platform_adapter.get_config_dir()
        os.makedirs(config_dir, exist_ok=True)
        self.config_file_path = os.path.join(config_dir, "autodoor_config.json")
        self.log_file_path = self.platform_adapter.get_log_file_path()

    def _init_managers(self):
        self.logging_manager = LoggingManager(self)
        self.logging_manager.log_message(f"[{self.platform_adapter.platform}] 日志文件路径: {self.log_file_path}")
        self.version_checker = VersionChecker(self)
        self.input_controller = InputController(self)
        self.thread_manager = ThreadManager(self)
        self.event_manager = EventManager(self)
        self.config_manager = ConfigManager(self)
        self.permission_manager = PermissionManager(self)

    def _init_proxy_classes(self):
        self.ocr = OCRProxy(self)
        self.timed = TimedProxy(self)
        self.number = NumberProxy(self)
        self.script = ScriptProxy(self)
        self.color = ColorProxy(self)
        self.image = ImageDetectionProxy(self)
        self.ui = UIProxy(self)

    def _init_ui(self):
        init_theme()
        
        self.root = ctk.CTk()
        self.root.title(f"AutoDoor OCR v{VERSION}")
        self.root.geometry("1050x700")
        self.root.minsize(950, 600)
        self.root.protocol("WM_DELETE_WINDOW", lambda: exit_program(self))
        
        self._init_tk_variables()
        self._create_layout()

    def _init_tk_variables(self):
        import tkinter as tk
        self.alarm_sound_path = tk.StringVar(value="")
        self.alarm_volume = tk.IntVar(value=70)
        self.alarm_volume_str = tk.StringVar(value="70")
        for module in ["ocr", "timed", "number"]:
            self.alarm_enabled[module] = tk.BooleanVar(value=False)
        self.ocr_delay_min = tk.IntVar(value=300)
        self.ocr_delay_max = tk.IntVar(value=500)
        self.status_var = tk.StringVar(value="就绪")
        self.region_var = tk.StringVar(value="未选择区域")
        self.color_var = tk.StringVar(value="未选择颜色")
        self.tolerance_var = tk.StringVar(value="10")
        self.interval_var = tk.StringVar(value="5")

    def _create_layout(self):
        self._create_header()
        self._create_main_container()
        self._create_sidebar()
        self._create_content_area()
        self._create_footer()

    def _create_header(self):
        self.header = ctk.CTkFrame(self.root, height=44, corner_radius=0)
        self.header.pack(fill='x')
        self.header.pack_propagate(False)
        
        header_content = ctk.CTkFrame(self.header, fg_color='transparent')
        header_content.pack(fill='x', padx=12, pady=6)
        
        left_section = ctk.CTkFrame(header_content, fg_color='transparent')
        left_section.pack(side='left')
        
        ctk.CTkLabel(left_section, text='◉', font=Theme.get_font('xl'), 
                    text_color=Theme.COLORS['primary']).pack(side='left', padx=(0, 6))
        ctk.CTkLabel(left_section, text='AutoDoor OCR', font=Theme.get_font('lg')).pack(side='left')
        ctk.CTkLabel(left_section, text=f'v{VERSION}', font=Theme.get_font('xs'), 
                    text_color=Theme.COLORS['primary'],
                    fg_color=Theme.COLORS['info_light'], corner_radius=4, 
                    padx=6, pady=1).pack(side='left', padx=8)
        
        center_section = ctk.CTkFrame(header_content, fg_color='transparent')
        center_section.pack(side='left', expand=True)
        
        self.status_frame = ctk.CTkFrame(center_section, fg_color='transparent')
        self.status_frame.pack()
        self.status_dot = ctk.CTkLabel(self.status_frame, text='●', font=('Arial', 10), 
                                       text_color=Theme.COLORS['success'])
        self.status_dot.pack(side='left', padx=(0, 4))
        self.status_label = ctk.CTkLabel(self.status_frame, textvariable=self.status_var, 
                                         font=Theme.get_font('sm'), 
                                         text_color=Theme.COLORS['success'])
        self.status_label.pack(side='left')
        
        right_section = ctk.CTkFrame(header_content, fg_color='transparent')
        right_section.pack(side='right')
        
        AnimatedButton(right_section, text='检查更新', width=70, height=26, 
                      font=Theme.get_font('xs'),
                      fg_color=Theme.COLORS['primary'], 
                      hover_color=Theme.COLORS['primary_hover'],
                      corner_radius=6, border_width=0,
                      command=self.check_for_updates).pack(side='left', padx=4)
        
        AnimatedButton(right_section, text='工具介绍', width=70, height=26,
                      font=Theme.get_font('xs'),
                      fg_color=Theme.COLORS['primary'], 
                      hover_color=Theme.COLORS['primary_hover'],
                      corner_radius=6, border_width=0,
                      command=open_tool_intro).pack(side='left', padx=4)
        
        # TODO: 夜间模式功能待后续迭代完善，目前暂时不在前端展示
        # 需要完善的工作：
        # 1. 所有组件的深色主题样式适配
        # 2. 颜色选择器的深色模式支持
        # 3. 输入框和下拉框的深色模式样式
        # 4. 状态指示器的深色模式颜色
        # theme_frame = ctk.CTkFrame(right_section, fg_color='transparent')
        # theme_frame.pack(side='left', padx=8)
        # ctk.CTkLabel(theme_frame, text='夜间模式', font=Theme.get_font('xs'),
        #             text_color=Theme.COLORS['text_secondary']).pack(side='left', padx=(0, 2))
        # self.theme_switch = ctk.CTkSwitch(theme_frame, text='', width=36, 
        #                                   command=self._toggle_theme, state='disabled')
        # self.theme_switch.pack(side='left')

    def _create_main_container(self):
        self.main_container = ctk.CTkFrame(self.root, fg_color='transparent')
        self.main_container.pack(fill='both', expand=True)

    def _create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self.main_container, width=180, corner_radius=0)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)
        
        nav_config = [
            ('home', '🏠', '首页'),
            ('ocr', '📝', '文字识别'),
            ('timed', '⏱', '定时功能'),
            ('number', '🔢', '数字识别'),
            ('image', '🖼', '图像检测'),
            ('script', '📜', '脚本运行'),
            ('settings', '⚙', '基本设置')
        ]
        
        for i, (page_id, icon, text) in enumerate(nav_config):
            item = self._create_nav_item(self.sidebar, text, icon, 
                                         lambda p=page_id: self._navigate_to(p), i == 0)
            item.pack(fill='x')
            self.nav_items[page_id] = item

    def _create_nav_item(self, master, text, icon, command, is_active):
        frame = ctk.CTkFrame(master, fg_color='transparent', corner_radius=0)
        indicator = ctk.CTkFrame(frame, width=3, height=22, fg_color='transparent', corner_radius=0)
        indicator.pack(side='left', padx=(6, 0), pady=6)
        
        content = ctk.CTkFrame(frame, fg_color='transparent')
        content.pack(side='left', fill='x', expand=True, padx=6, pady=6)
        
        icon_label = ctk.CTkLabel(content, text=icon, font=('Segoe UI Emoji', 14), 
                                  width=24, anchor='center')
        icon_label.pack(side='left')
        
        text_label = ctk.CTkLabel(content, text=text, font=Theme.get_font('sm'), 
                                  text_color=Theme.COLORS['text_secondary'], anchor='w')
        text_label.pack(side='left', padx=(4, 0))
        
        def on_enter(e):
            if not frame._is_active:
                frame.configure(fg_color=Theme.COLORS['info_light'])
        def on_leave(e):
            if not frame._is_active:
                frame.configure(fg_color='transparent')
        def on_click(e):
            command()
        
        frame._is_active = is_active
        frame.bind('<Enter>', on_enter)
        frame.bind('<Leave>', on_leave)
        frame.bind('<Button-1>', on_click)
        content.bind('<Enter>', on_enter)
        content.bind('<Leave>', on_leave)
        content.bind('<Button-1>', on_click)
        indicator.bind('<Enter>', on_enter)
        indicator.bind('<Leave>', on_leave)
        indicator.bind('<Button-1>', on_click)
        icon_label.bind('<Enter>', on_enter)
        icon_label.bind('<Leave>', on_leave)
        icon_label.bind('<Button-1>', on_click)
        text_label.bind('<Enter>', on_enter)
        text_label.bind('<Leave>', on_leave)
        text_label.bind('<Button-1>', on_click)
        
        if is_active:
            frame.configure(fg_color=Theme.COLORS['info_light'])
            indicator.configure(fg_color=Theme.COLORS['primary'])
            text_label.configure(text_color=Theme.COLORS['primary'])
        
        frame._indicator = indicator
        frame._text_label = text_label
        return frame

    def _create_content_area(self):
        self.content_area = ctk.CTkFrame(self.main_container, fg_color='transparent')
        self.content_area.pack(side='left', fill='both', expand=True, padx=12, pady=12)
        
        create_home_tab(self)
        create_ocr_tab(self)
        create_timed_tab(self)
        create_number_tab(self)
        create_image_tab(self)
        create_script_tab(self)
        create_basic_tab(self)
        
        self._show_page('home')

    def _create_footer(self):
        self.footer = ctk.CTkFrame(self.root, height=28, corner_radius=0)
        self.footer.pack(fill='x')
        self.footer.pack_propagate(False)
        
        footer_content = ctk.CTkFrame(self.footer, fg_color='transparent')
        footer_content.pack(fill='x', padx=12, pady=4)
        
        ctk.CTkLabel(footer_content, 
                    text=f'AutoDoor OCR v{VERSION} | 本程序仅供个人学习研究使用，禁止商用 | 制作人: ',
                    font=Theme.get_font('xs'), 
                    text_color=Theme.COLORS['text_muted']).pack(side='left')
        
        author_label = ctk.CTkLabel(footer_content, text='Flown王砖家', 
                                    font=Theme.get_font('xs'),
                                    text_color=Theme.COLORS['primary'],
                                    cursor='hand2')
        author_label.pack(side='left')
        author_label.bind('<Button-1>', lambda e: open_bilibili())

    def _show_page(self, page_id):
        for pid, page in self.pages.items():
            if pid == page_id:
                page.pack(fill='both', expand=True)
            else:
                page.pack_forget()
        
        for pid, item in self.nav_items.items():
            if pid == page_id:
                item._is_active = True
                item.configure(fg_color=Theme.COLORS['info_light'])
                item._indicator.configure(fg_color=Theme.COLORS['primary'])
                item._text_label.configure(text_color=Theme.COLORS['primary'])
            else:
                item._is_active = False
                item.configure(fg_color='transparent')
                item._indicator.configure(fg_color='transparent')
                item._text_label.configure(text_color=Theme.COLORS['text_secondary'])
        
        self._current_page = page_id

    def _navigate_to(self, page_id):
        self._show_page(page_id)

    # TODO: 夜间模式切换功能，待后续迭代完善后启用
    def _toggle_theme(self):
        """切换日间/夜间模式"""
        current = ctk.get_appearance_mode()
        new_mode = 'Dark' if current == 'Light' else 'Light'
        ctk.set_appearance_mode(new_mode)

    def _init_modules(self):
        self.ocr_module = OCRModule(self)
        self.timed_module = TimedModule(self)
        self.number_module = NumberModule(self)
        self.alarm_module = AlarmModule(self)
        self.script_module = ScriptModule(self)
        self.tesseract_manager = TesseractManager(self)
        self.color_recognition_manager = ColorRecognitionManager(self)
        self.image_detection_manager = ImageDetectionManager(self)
        self.MODULES = {
            "ocr": {"threads": "ocr_threads", "stop_func": "ocr.stop_monitoring", "label": "文字识别"},
            "timed": {"threads": "timed_threads", "stop_func": "timed.stop_tasks", "label": "定时功能"},
            "number": {"threads": "number_threads", "stop_func": "number.stop_recognition", "label": "数字识别"},
            "image": {"threads": "image_threads", "stop_func": "image.stop_detection", "label": "图像检测"},
            "color": {"threads": "color_threads", "stop_func": "color.stop_recognition", "label": "颜色识别"}
        }
        self.module_controller = ModuleController(self)

    def _load_config(self):
        self.config_manager.load_config()
        config_updated = False
        if not self.tesseract_path:
            self.tesseract_path = ""
            config_updated = True

        if not self.alarm_sound_path.get():
            self.alarm_sound_path.set(self.alarm_module.get_default_alarm_sound_path())
            config_updated = True

        self.tesseract_available = self.tesseract_manager.check_tesseract_availability()

        if config_updated:
            self.config_manager.defer_save_config()

    def _start_services(self):
        if self.platform_adapter.platform == "Darwin":
            self.root.after(100, self.permission_manager.check_macos_permissions)

        self.config_manager.setup_config_listeners()

        if not self.tesseract_available:
            self.status_var.set("Tesseract未配置")
            self.root.after(100, lambda: messagebox.showinfo("提示", 
                "未检测到Tesseract OCR引擎，请在设置中配置Tesseract路径后使用文字识别功能！"))

        self.setup_shortcuts()
        self.event_manager.start_event_thread()

        self.version_checker.start_auto_check()

    def check_for_updates(self):
        self.version_checker.check_for_updates(manual=True)

    def cancel_selection(self):
        from utils.region import cancel_selection
        cancel_selection(self)

    def log_message(self, message):
        self.logging_manager.log_message(message)

    def get_available_keys(self):
        from input.keyboard import get_available_keys
        return get_available_keys()

    def _clear_ocr_groups(self):
        self.config_manager.clear_ocr_groups()

    def _load_group_config(self, group, group_config):
        self.config_manager.load_group_config(group, group_config)

    def _load_enabled_config(self, group, enabled):
        self.config_manager.load_enabled_config(group, enabled)

    def setup_shortcuts(self):
        setup_shortcuts(self)

    def clear_log(self):
        self.logging_manager.clear_log()

    def set_tesseract_path(self):
        self.tesseract_manager.set_tesseract_path()

    def save_config(self):
        try:
            config = self.config_manager.get_full_config()
            self.config_manager.save_config(config)
        except Exception as e:
            self.logging_manager.log_message(f"配置保存错误: {str(e)}")

    def start_module(self, module_name, start_func):
        self.module_controller.start_module(module_name, start_func)

    def start_all(self):
        self.module_controller.start_all()

    def stop_all(self):
        self.module_controller.stop_all()

    def run(self):
        self.root.mainloop()


def main():
    import traceback
    try:
        app = AutoDoorOCR()
        app.run()
    except Exception as e:
        error_msg = f"程序启动失败: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        try:
            log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "autodoor.log")
            with open(log_file, 'a', encoding='utf-8') as f:
                import datetime
                f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {error_msg}\n")
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()
