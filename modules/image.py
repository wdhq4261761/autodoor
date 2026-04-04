import threading
import time
import os
from PIL import Image
import tkinter as tk
from tkinter import messagebox
import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from utils.screenshot import ScreenshotManager
from utils.recognition import ImageRecognizer
from core.click_handler import ClickHandler
from core.priority_lock import get_module_priority


class ImageDetection:
    """
    图像检测类 - 使用模板匹配
    优先级: 4 (Number=6 > Timed=5 > Image=4 > OCR=3 > Color=2 > Script=1)
    """
    
    PRIORITY = get_module_priority('image')
    
    def __init__(self, app, group_index=0):
        self.app = app
        self.group_index = group_index
        self.is_running = False
        self.detection_thread = None
        self.region = None
        self.template_image = None
        self.template_path = None
        self.threshold = 0.8
        self.interval = 5.0
        self.pause = 180
        self.commands = ""
        self.click_handler = ClickHandler(app)
        self.last_trigger_time = 0
        self.last_match_pos = None
        self.screenshot_manager = ScreenshotManager()
    
    def set_region(self, region):
        """设置检测区域"""
        self.region = region
    
    def start_detection(self, threshold, interval, pause, commands):
        """开始检测"""
        self.threshold = float(threshold) / 100.0
        self.interval = float(interval)
        self.pause = int(pause)
        self.commands = commands
        self.last_trigger_time = 0
        
        if not CV2_AVAILABLE:
            return
        
        if self.template_image is None:
            return
        
        if not self.region:
            return
        
        def detect():
            self.is_running = True
            
            while self.is_running:
                time.sleep(self.interval)
                
                if hasattr(self.app, 'event_queue') and not self.app.event_queue.empty():
                    continue
                
                current_time = time.time()
                
                if current_time - self.last_trigger_time < self.pause:
                    continue
                
                match_result = self.detect_image()
                if match_result:
                    self.execute_commands(match_result)
                    self.last_trigger_time = current_time
                    time.sleep(5)
            
            self.is_running = False
            self.app.status_var.set("图像检测已停止")
            
            self.app.root.after(0, lambda:
                (self.app.status_var.set("图像检测已停止"),)
            )
        
        self.detection_thread = threading.Thread(target=detect, daemon=True)
        self.detection_thread.start()
    
    def detect_image(self):
        """执行图像检测 - 使用公共识别工具类"""
        if not self.region or self.template_image is None:
            return None
        
        if not CV2_AVAILABLE:
            return None
        
        try:
            screenshot = self.screenshot_manager.get_region_screenshot(self.region, priority=self.PRIORITY)
            
            if not screenshot:
                return None
            
            if screenshot.size[0] == 0 or screenshot.size[1] == 0:
                return None
            
            matched, click_pos, score = ImageRecognizer.match_template(
                screenshot, self.template_image, self.threshold,
                log_func=self.app.logging_manager.log_message,
                group_index=self.group_index
            )
            
            if matched and click_pos:
                abs_x = self.region[0] + click_pos[0]
                abs_y = self.region[1] + click_pos[1]
                
                self.last_match_pos = (abs_x, abs_y)
                
                return (abs_x, abs_y, score)
            
            return None
                
        except Exception:
            return None
    
    def execute_commands(self, match_result):
        """执行识别后命令"""
        if not match_result:
            return
        
        if not self.app.is_running or getattr(self.app, 'system_stopped', False):
            return
        
        abs_x, abs_y, match_score = match_result
        
        group = None
        if hasattr(self.app, 'image_groups') and self.group_index < len(self.app.image_groups):
            group = self.app.image_groups[self.group_index]
        
        if not group:
            return
        
        key = group.get("key", tk.StringVar(value="")).get()
        
        alarm_enabled = group.get("alarm", tk.BooleanVar(value=False)).get()
        click_enabled = group.get("click", tk.BooleanVar(value=True)).get()
        
        if click_enabled:
            self.click_handler.execute_click(
                x=abs_x,
                y=abs_y,
                priority=self.PRIORITY,
                module_name="检测组",
                index=self.group_index
            )
        
        if key:
            from modules.input import KeyEventExecutor
            delay_min_var = group["delay_min"]
            delay_max_var = group["delay_max"]
            executor = KeyEventExecutor(self.app.input_controller, delay_min_var, delay_max_var, self.PRIORITY)
            executor.execute_keypress(key)
            
            self.app.logging_manager.log_message(f"检测组{self.group_index+1}按下了 {key} 键")
        
        if alarm_enabled:
            try:
                temp_alarm_var = tk.BooleanVar(value=True)
                self.app.alarm_module.play_alarm_sound(temp_alarm_var)
            except Exception:
                pass
        
        if self.commands:
            from modules.script import ScriptExecutor
            temp_executor = ScriptExecutor(self.app)
            temp_executor.run_script_once(self.commands)
    
    def stop_detection(self):
        """停止检测"""
        self.is_running = False
        if hasattr(self, 'detection_thread') and self.detection_thread is not None and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=1)


class ImageDetectionManager:
    """图像检测管理器类，处理图像检测相关的UI操作和多检测组管理"""
    
    def __init__(self, app):
        self.app = app
        self.image_detections = {}
    
    def select_region(self, group_index):
        """选择检测区域"""
        from utils.region import _start_selection
        _start_selection(self.app, "image", group_index)
    
    def select_reference_image(self, group_index):
        """选择参考图像"""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            title="选择参考图像（模板）",
            filetypes=[
                ("图像文件", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            if group_index < len(self.app.image_groups):
                group = self.app.image_groups[group_index]
                
                try:
                    if not CV2_AVAILABLE:
                        messagebox.showerror("错误", "OpenCV未安装，无法使用图像检测功能")
                        return
                    
                    template = cv2.imread(file_path, cv2.IMREAD_COLOR)
                    if template is None:
                        messagebox.showerror("错误", f"无法读取图像文件: {file_path}")
                        return
                    
                    group["template_image"] = template
                    group["reference_image"] = file_path
                    group["image_path_var"].set(os.path.basename(file_path))
                    
                    if "image_preview" in group and group["image_preview"]:
                        self._update_image_preview(group, file_path)
                    
                except Exception as e:
                    messagebox.showerror("错误", f"加载图像失败: {str(e)}")
    
    def _update_image_preview(self, group, image_path):
        """更新图像预览"""
        try:
            if "image_preview" in group and group["image_preview"]:
                image = Image.open(image_path)
                orig_w, orig_h = image.size
                
                max_w, max_h = 60, 40
                ratio = min(max_w / orig_w, max_h / orig_h)
                new_w = int(orig_w * ratio)
                new_h = int(orig_h * ratio)
                
                import customtkinter as ctk
                ctk_image = ctk.CTkImage(light_image=image, size=(new_w, new_h))
                group["image_preview"].configure(image=ctk_image)
                group["image_preview"].image = ctk_image
        except Exception:
            pass
    
    def start_detection(self, group_index):
        """开始单个检测组的检测"""
        if group_index >= len(self.app.image_groups):
            return
        
        group = self.app.image_groups[group_index]
        
        if not group["enabled"].get():
            return
        
        if group.get("template_image") is None:
            messagebox.showwarning("警告", f"检测组{group_index + 1}未设置参考图像！")
            return
        
        if not group.get("region"):
            messagebox.showwarning("警告", f"检测组{group_index + 1}未设置检测区域！")
            return
        
        if group_index not in self.image_detections:
            self.image_detections[group_index] = ImageDetection(self.app, group_index)
        
        detection = self.image_detections[group_index]
        detection.set_region(group["region"])
        
        detection.template_image = group["template_image"]
        detection.template_path = group.get("reference_image", "")
        
        threshold = group["threshold"].get()
        interval = group["interval"].get()
        pause = group["pause"].get()
        commands = group.get("commands", "")
        
        detection.start_detection(threshold, interval, pause, commands)
        
        self.app.status_var.set(f"图像检测组{group_index + 1}运行中...")
    
    def stop_detection(self, group_index):
        """停止单个检测组的检测"""
        if group_index in self.image_detections:
            self.image_detections[group_index].stop_detection()
            del self.image_detections[group_index]
        
        self.app.status_var.set("图像检测已停止")
    
    def start_all_detection(self):
        """开始所有已启用的检测组"""
        def start_func():
            start_count = 0
            for i, group in enumerate(self.app.image_groups):
                if group["enabled"].get():
                    if group.get("template_image") is None:
                        continue
                    if not group.get("region"):
                        continue
                    self.start_detection(i)
                    start_count += 1
            return start_count
        
        has_enabled = False
        for group in self.app.image_groups:
            if group["enabled"].get():
                has_enabled = True
                break
        
        if not has_enabled:
            messagebox.showwarning("警告", "请至少启用一个检测组")
            return
        
        self.app.start_module("image", start_func)
    
    def stop_all_detection(self):
        """停止所有检测组"""
        for group_index in list(self.image_detections.keys()):
            self.image_detections[group_index].stop_detection()
        self.image_detections.clear()
        
        self.app.status_var.set("图像检测已停止")
