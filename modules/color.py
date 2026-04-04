import threading
import time
import numpy as np
from PIL import Image, ImageGrab
import imagehash
import tkinter as tk
from tkinter import messagebox

from utils.screenshot import ScreenshotManager
from utils.recognition import ColorRecognizer
from core.priority_lock import get_module_priority


class ColorRecognition:
    """
    颜色识别类
    优先级: 2 (Number=6 > Timed=5 > Image=4 > OCR=3 > Color=2 > Script=1)
    """
    
    PRIORITY = get_module_priority('color')
    
    def __init__(self, app):
        self.app = app
        self.is_running = False
        self.recognition_thread = None
        self.region = None
        self.target_color = None
        self.tolerance = 10
        self.interval = 5.0
        self.commands = ""
        
        self.last_image_hash = None
        self.screenshot_manager = ScreenshotManager()

    def set_region(self, region):
        """设置颜色识别区域"""
        self.region = region

    def start_recognition(self, target_color, tolerance, interval, commands):
        self.target_color = target_color
        self.tolerance = int(tolerance)
        self.interval = float(interval)
        self.commands = commands
        
        def recognize():
            self.is_running = True
            
            while self.is_running:
                time.sleep(self.interval)
                
                if hasattr(self.app, 'event_queue') and not self.app.event_queue.empty():
                    continue
                
                if self.recognize_color():
                    self.execute_commands()
                    time.sleep(self.interval)
            
            self.is_running = False
            self.app.status_var.set("颜色识别已停止")
            
            self.app.root.after(0, lambda:
                (self.app.status_var.set("颜色识别已停止"),)
            )
        
        self.recognition_thread = threading.Thread(target=recognize, daemon=True)
        self.recognition_thread.start()

    def recognize_color(self):
        """执行颜色识别 - 使用公共识别工具类"""
        if not self.region:
            self.app.logging_manager.log_message("颜色识别失败: 未设置识别区域")
            return False
        
        try:
            screenshot = self.screenshot_manager.get_region_screenshot(self.region, priority=self.PRIORITY)
            
            if not screenshot:
                self.app.logging_manager.log_message("颜色识别失败: 无法获取截图")
                return False
            
            if screenshot.size[0] == 0 or screenshot.size[1] == 0:
                self.app.logging_manager.log_message("颜色识别失败: 截图为空")
                return False
            
            current_hash = imagehash.average_hash(screenshot.resize((32, 32)))
            self.last_image_hash = current_hash
            
            matched, click_pos, match_pixels = ColorRecognizer.match_color(
                screenshot, self.target_color, self.tolerance,
                log_func=self.app.logging_manager.log_message
            )
            
            if matched:
                self.app.logging_manager.log_message(f"✅ 识别到目标颜色，匹配像素: {match_pixels}")
                return True
            else:
                return False
                
        except Exception as e:
            self.app.logging_manager.log_message(f"颜色识别错误: {str(e)}")
            import traceback
            self.app.logging_manager.log_message(f"错误详情: {traceback.format_exc()}")
            return False
    
    def execute_commands(self):
        """执行识别后命令（只执行一遍）"""
        if not self.commands:
            return
        
        from modules.script import ScriptExecutor
        temp_executor = ScriptExecutor(self.app)
        temp_executor.run_script_once(self.commands)

    def stop_recognition(self):
        """停止颜色识别"""
        self.is_running = False
        if hasattr(self, 'recognition_thread') and self.recognition_thread.is_alive():
            self.recognition_thread.join(timeout=1)


class ColorRecognitionManager:
    """颜色识别管理器类，处理颜色识别相关的UI操作"""
    
    def __init__(self, app):
        self.app = app
        self.color_recognition = None
        self.screenshot_manager = ScreenshotManager()
    
    def select_color_region(self):
        """选择颜色识别区域"""
        self.app.logging_manager.log_message("开始选择颜色识别区域...")
        from utils.region import _start_selection
        _start_selection(self.app, "color", 0)
    
    def select_color(self):
        """选择颜色"""
        def on_color_selected(color):
            r, g, b = color
            self.app.target_color = color
            self.app.color_var.set(f"RGB({r}, {g}, {b})")
            
            if hasattr(self.app, 'color_display'):
                self.app.color_display.configure(fg_color=f"#{r:02x}{g:02x}{b:02x}")
        
        from ui.utils import create_color_picker
        create_color_picker(self.app, on_color_selected, self.app.logging_manager.log_message)
    
    def start_color_recognition(self):
        """开始颜色识别"""
        if not self.color_recognition:
            self.color_recognition = ColorRecognition(self.app)
        
        try:
            if hasattr(self.app, 'target_color') and self.app.target_color:
                target_color = self.app.target_color
            else:
                messagebox.showwarning("警告", "请先选择目标颜色！")
                return
            
            tolerance = int(self.app.tolerance_var.get())
            interval = float(self.app.interval_var.get())
            commands = self.app.color_commands.get(1.0, tk.END)
        except ValueError:
            messagebox.showwarning("警告", "颜色设置参数格式错误，请检查！")
            return
        
        if not hasattr(self.app, 'color_recognition_region') or not self.app.color_recognition_region:
            messagebox.showwarning("警告", "请先选择颜色识别区域！")
            return
        
        self.color_recognition.set_region(self.app.color_recognition_region)
        self.color_recognition.start_recognition(target_color, tolerance, interval, commands)
        self.app.status_var.set("颜色识别中...")
    
    def stop_color_recognition(self):
        """停止颜色识别"""
        if self.color_recognition:
            if hasattr(self.color_recognition, 'is_running') and self.color_recognition.is_running:
                self.color_recognition.stop_recognition()
                self.app.status_var.set("颜色识别已停止")
            elif hasattr(self.color_recognition, 'recognition_thread') and self.color_recognition.recognition_thread.is_alive():
                self.color_recognition.is_running = False
                self.color_recognition.recognition_thread.join(timeout=2)
                self.app.status_var.set("颜色识别已停止")
