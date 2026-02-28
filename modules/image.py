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


class ImageDetection:
    """
    图像检测类 - 使用模板匹配
    优先级: 4 (Number=6 > Timed=5 > Image=4 > OCR=3 > Color=2 > Script=1)
    """
    
    PRIORITY = 4
    
    def __init__(self, app):
        self.app = app
        self.is_running = False
        self.detection_thread = None
        self.region = None
        self.template_image = None
        self.template_path = None
        self.threshold = 0.8
        self.interval = 5.0
        self.pause = 180
        self.commands = ""
        self.last_trigger_time = 0
        self.last_match_pos = None
    
    def set_region(self, region):
        """设置检测区域"""
        self.region = region
    
    def set_reference_image(self, image_path):
        """设置参考图像（模板）"""
        if not os.path.exists(image_path):
            return False
        
        if not CV2_AVAILABLE:
            return False
        
        try:
            self.template_image = cv2.imread(image_path, cv2.IMREAD_COLOR)
            if self.template_image is None:
                return False
            
            self.template_path = image_path
            return True
        except Exception:
            return False
    
    def start_detection(self, threshold, interval, pause, commands):
        """开始检测"""
        self.threshold = float(threshold) / 100.0
        self.interval = float(interval)
        self.pause = int(pause)
        self.commands = commands
        
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
        """执行图像检测 - 模板匹配"""
        if not self.region or self.template_image is None:
            return None
        
        if not CV2_AVAILABLE:
            return None
        
        try:
            if self.app.platform_adapter.platform == "Darwin":
                from input.permissions import PermissionManager
                permission_manager = PermissionManager(self.app)
                if not permission_manager.check_screen_recording():
                    self.app.root.after(0, lambda: self.app._guide_screen_recording_setup())
                    return None
            
            screenshot = None
            try:
                from utils.screenshot import ScreenshotManager
                screenshot_manager = ScreenshotManager()
                screenshot = screenshot_manager.get_region_screenshot(self.region, priority=self.PRIORITY)
            except Exception:
                return None
            
            if not screenshot:
                return None
            
            if screenshot.size[0] == 0 or screenshot.size[1] == 0:
                return None
            
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            template_h, template_w = self.template_image.shape[:2]
            screenshot_h, screenshot_w = screenshot_cv.shape[:2]
            
            if template_w > screenshot_w or template_h > screenshot_h:
                return None
            
            result = cv2.matchTemplate(screenshot_cv, self.template_image, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= self.threshold:
                self.app.logging_manager.log_message(f"图像匹配成功：匹配度: {max_val:.2%}")
                
                center_x = max_loc[0] + template_w // 2
                center_y = max_loc[1] + template_h // 2
                
                abs_x = self.region[0] + center_x
                abs_y = self.region[1] + center_y
                
                self.last_match_pos = (abs_x, abs_y)
                
                return (abs_x, abs_y, max_val)
            else:
                self.app.logging_manager.log_message(f"图像匹配失败：匹配度: {max_val:.2%}")
                return None
                
        except Exception:
            return None
    
    def execute_commands(self, match_result):
        """执行识别后命令"""
        if not match_result:
            return
        
        abs_x, abs_y, match_score = match_result
        
        click_enabled = True
        if hasattr(self.app, 'image_groups'):
            for group in self.app.image_groups:
                if group.get("enabled") and group.get("enabled").get():
                    click_enabled = group.get("click", tk.BooleanVar(value=True)).get()
                    break
        
        if click_enabled:
            try:
                self.app.input_controller.click(abs_x, abs_y)
                time.sleep(self.app.click_delay if hasattr(self.app, 'click_delay') else 0.1)
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
            self.image_detections[group_index] = ImageDetection(self.app)
        
        detection = self.image_detections[group_index]
        detection.set_region(group["region"])
        
        detection.template_image = group["template_image"]
        detection.template_path = group.get("reference_image", "")
        
        threshold = group["threshold"].get()
        interval = group["interval"].get()
        pause = group["pause"].get()
        commands = group.get("commands", "")
        
        detection.start_detection(threshold, interval, pause, commands)
        
        if hasattr(self.app, 'status_labels') and "image" in self.app.status_labels:
            self.app.status_labels["image"].set(f"图像检测: 运行中 (组{group_index + 1})")
        self.app.status_var.set(f"图像检测组{group_index + 1}运行中...")
    
    def stop_detection(self, group_index):
        """停止单个检测组的检测"""
        if group_index in self.image_detections:
            self.image_detections[group_index].stop_detection()
            del self.image_detections[group_index]
        
        if hasattr(self.app, 'status_labels') and "image" in self.app.status_labels:
            self.app.status_labels["image"].set("图像检测: 未运行")
        self.app.status_var.set("图像检测已停止")
    
    def start_all_detection(self):
        """开始所有已启用的检测组"""
        has_enabled = False
        for i, group in enumerate(self.app.image_groups):
            if group["enabled"].get():
                has_enabled = True
                self.start_detection(i)
        
        if not has_enabled:
            messagebox.showwarning("警告", "请至少启用一个检测组")
            return
    
    def stop_all_detection(self):
        """停止所有检测组"""
        for group_index in list(self.image_detections.keys()):
            self.image_detections[group_index].stop_detection()
        self.image_detections.clear()
        
        if hasattr(self.app, 'status_labels') and "image" in self.app.status_labels:
            self.app.status_labels["image"].set("图像检测: 未运行")
        self.app.status_var.set("图像检测已停止")
    
    def trigger_action_for_group(self, group, group_index, click_enabled=False, click_pos=None):
        """为检测组触发动作"""
        try:
            if not self.app.is_running or getattr(self.app, 'system_stopped', False):
                return
            
            key = group.get("key", tk.StringVar(value="")).get()
            if not key:
                return
            
            try:
                delay_min = int(group.get("delay_min", tk.StringVar(value="300")).get())
            except (ValueError, TypeError):
                delay_min = 300
            try:
                delay_max = int(group.get("delay_max", tk.StringVar(value="500")).get())
            except (ValueError, TypeError):
                delay_max = 500
            
            alarm_enabled = group.get("alarm", tk.BooleanVar(value=False)).get()
            
            if click_enabled and click_pos:
                click_x, click_y = click_pos
                if click_x is not None and click_y is not None:
                    self.app.input_controller.click(click_x, click_y)
                    time.sleep(self.app.click_delay if hasattr(self.app, 'click_delay') else 0.1)
            
            import random
            hold_delay = random.randint(delay_min, delay_max) / 1000
            
            self.app.input_controller.key_down(key, priority=ImageDetection.PRIORITY)
            time.sleep(hold_delay)
            self.app.input_controller.key_up(key, priority=ImageDetection.PRIORITY)
            
            if alarm_enabled:
                try:
                    temp_alarm_var = tk.BooleanVar(value=True)
                    self.app.alarm_module.play_alarm_sound(temp_alarm_var)
                except Exception:
                    pass
        
        except Exception:
            pass
