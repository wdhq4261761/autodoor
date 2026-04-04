import threading
import time
import tkinter as tk
from tkinter import messagebox
from typing import Optional, Dict, Any

from utils.window_capture import (
    capture_window_region, find_window_by_title, 
    get_window_rect, get_window_title
)
from utils.quick_switch import QuickSwitchBackend
from utils.coordinate import RelativeCoordinate, WindowCoordinate
from utils.recognition import OCRRecognizer, ImageRecognizer, ColorRecognizer
from utils.image import _preprocess_image
from core.priority_lock import get_module_priority

class BackgroundMonitor:
    """
    单个后台监控组
    
    优先级: 1 (最低)
    """
    
    PRIORITY = get_module_priority('background')
    
    def __init__(self, app, group_index: int = 0):
        self.app = app
        self.group_index = group_index
        self.is_running = False
        self.monitor_thread = None
        self.stop_event = threading.Event()
        
        self.hwnd = None
        self.region = None
        self.region_ratio = None
        self.recognition_type = "ocr"
        self.interval = 5.0
        self.pause = 180
        
        self.ocr_config = {}
        self.image_config = {}
        self.color_config = {}
        
        self.trigger_key = None
        self.delay_min = 100
        self.delay_max = 200
        self.trigger_click = False
        self.alarm_enabled = False
        
        self.last_trigger_time = 0
        self._last_text = None  # 缓存上次识别文本，用于日志节流
    
    def set_window(self, hwnd: int) -> None:
        """设置目标窗口"""
        self.hwnd = hwnd
    
    def set_region(self, region: tuple, save_ratio: bool = True) -> None:
        """
        设置监控区域（窗口相对坐标）
        
        Args:
            region: (x1, y1, x2, y2) 窗口相对坐标
            save_ratio: 是否保存比例坐标
        """
        self.region = region
        
        if save_ratio and self.hwnd and region:
            window_size = WindowCoordinate.get_window_size(self.hwnd)
            if window_size:
                self.region_ratio = RelativeCoordinate.pixel_to_ratio(region, window_size)
    
    def configure_ocr(self, keywords: str, language: str) -> None:
        """配置OCR识别"""
        self.ocr_config = {
            "keywords": keywords,
            "language": language
        }
    
    def configure_image(self, template_image, threshold: float) -> None:
        """配置图像识别"""
        self.image_config = {
            "template": template_image,
            "threshold": threshold
        }
    
    def configure_color(self, target_color: tuple, tolerance: int) -> None:
        """配置颜色识别"""
        self.color_config = {
            "target_color": target_color,
            "tolerance": tolerance
        }
    
    def start_monitoring(self) -> bool:
        """开始监控"""
        if self.is_running:
            return True
        
        if not self.hwnd:
            return False
        
        if not self.region and not self.region_ratio:
            return False
        
        self.stop_event.clear()
        self.is_running = True
        self.last_trigger_time = 0
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        return True
    
    def stop_monitoring(self) -> None:
        """停止监控"""
        self.is_running = False
        self.stop_event.set()
        self._last_text = None  # 清理缓存，确保下次启动时正常输出日志
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
    
    def _get_current_region(self) -> Optional[tuple]:
        """获取当前有效的区域坐标（支持分辨率自适应）"""
        if self.region_ratio and self.hwnd:
            window_size = WindowCoordinate.get_window_size(self.hwnd)
            if window_size:
                return RelativeCoordinate.ratio_to_pixel(self.region_ratio, window_size)
        
        return self.region
    
    def _monitor_loop(self) -> None:
        """监控主循环"""
        for _ in range(int(self.interval)):
            if not self.is_running or self.stop_event.is_set():
                return
            time.sleep(1)
        
        while self.is_running and not self.stop_event.is_set():
            try:
                current_time = time.time()
                
                if current_time - self.last_trigger_time < self.pause:
                    time.sleep(0.5)
                    continue
                
                region = self._get_current_region()
                if not region:
                    time.sleep(self.interval)
                    continue
                
                image = self._capture_region(region)
                if image is None:
                    for _ in range(int(self.interval)):
                        if not self.is_running or self.stop_event.is_set():
                            return
                        time.sleep(1)
                    continue
                
                matched, click_position = self._recognize(image)
                
                if matched:
                    if click_position and region:
                        click_position = (
                            click_position[0] + region[0],
                            click_position[1] + region[1]
                        )
                    self._trigger_action(click_position)
                    self.last_trigger_time = current_time
                
                for _ in range(int(self.interval)):
                    if not self.is_running or self.stop_event.is_set():
                        return
                    time.sleep(1)
                
            except Exception as e:
                self.app.logging_manager.log_message(
                    f"后台监控组{self.group_index + 1}错误: {str(e)}"
                )
                time.sleep(5)
    
    def _capture_region(self, region: tuple):
        """截取监控区域"""
        if not self.hwnd:
            return None
        
        try:
            return capture_window_region(self.hwnd, region)
        except Exception:
            return None
    
    def _recognize(self, image) -> tuple:
        """执行识别，返回 (matched, click_position)"""
        if self.recognition_type == "ocr":
            return self._recognize_ocr(image)
        elif self.recognition_type == "image":
            return self._recognize_image(image)
        elif self.recognition_type == "color":
            return self._recognize_color(image)
        return (False, None)
    
    def _recognize_ocr(self, image) -> tuple:
        """OCR识别 - 使用与常规OCR模块相同的实现"""
        keywords = self.ocr_config.get("keywords", "")
        language = self.ocr_config.get("language", "eng")
        
        if not keywords:
            return (False, None)
        
        processed = _preprocess_image(image, self.group_index)
        if not processed:
            return (False, None)
        
        keyword_list = [keyword.strip().lower() for keyword in keywords.split(",") if keyword.strip()]
        if not keyword_list:
            return (False, None)
        
        text = OCRRecognizer.get_text(processed, language)
        
        if text and text.strip() != self._last_text:
            self.app.logging_manager.log_message(
                f"后台监控组{self.group_index + 1}识别结果: '{text.strip()}'"
            )
            self._last_text = text.strip()
        
        if not text:
            return (False, None)
        
        lower_text = text.lower()
        if not any(keyword in lower_text for keyword in keyword_list):
            return (False, None)
        
        self.app.logging_manager.log_message(
            f"后台监控组{self.group_index + 1}识别到关键词: {text.strip()}"
        )
        
        click_pos = OCRRecognizer.find_keyword_position(processed, keyword_list, language)
        
        if click_pos is None:
            region = self._get_current_region()
            if region:
                center_x = (region[0] + region[2]) // 2
                center_y = (region[1] + region[3]) // 2
                click_pos = (center_x, center_y)
        
        return (True, click_pos)
    
    def _recognize_image(self, image) -> tuple:
        """图像识别 - 使用公共识别工具类"""
        template = self.image_config.get("template")
        threshold = self.image_config.get("threshold", 0.8)
        
        if template is None:
            return (False, None)
        
        matched, click_pos, _ = ImageRecognizer.match_template(
            image, template, threshold,
            log_func=self.app.logging_manager.log_message,
            group_index=self.group_index
        )
        
        return (matched, click_pos)
    
    def _recognize_color(self, image) -> tuple:
        """颜色识别 - 使用公共识别工具类"""
        target_color = self.color_config.get("target_color")
        tolerance = self.color_config.get("tolerance", 10)
        
        if not target_color:
            return (False, None)
        
        matched, click_pos, _ = ColorRecognizer.match_color(
            image, target_color, tolerance,
            log_func=self.app.logging_manager.log_message,
            group_index=self.group_index
        )
        
        return (matched, click_pos)
    
    def _trigger_action(self, click_position=None) -> None:
        """触发动作"""
        if not self.app.is_running:
            return
        
        # 播放报警声音
        if self.alarm_enabled:
            try:
                temp_alarm_var = tk.BooleanVar(value=True)
                self.app.alarm_module.play_alarm_sound(temp_alarm_var)
            except Exception:
                pass
        
        # 如果只设置了报警，无需切换窗口
        if not self.trigger_click and not self.trigger_key:
            return
        
        quick_switch = QuickSwitchBackend(self.app)
        quick_switch.set_hwnd(self.hwnd)
        
        # 保存原窗口并切换到目标窗口
        quick_switch._save_foreground_window()
        switch_success = quick_switch._switch_to_target()
        
        if switch_success:
            # 执行点击操作
            if self.trigger_click:
                if click_position:
                    # 转换为绝对坐标
                    rect = get_window_rect(self.hwnd)
                    if rect:
                        abs_x = rect[0] + click_position[0]
                        abs_y = rect[1] + click_position[1]
                        # 直接使用输入控制器执行点击
                        self.app.input_controller.click(abs_x, abs_y, priority=1)
                else:
                    region = self._get_current_region()
                    if region:
                        click_x = (region[0] + region[2]) // 2
                        click_y = (region[1] + region[3]) // 2
                        # 转换为绝对坐标
                        rect = get_window_rect(self.hwnd)
                        if rect:
                            abs_x = rect[0] + click_x
                            abs_y = rect[1] + click_y
                            # 直接使用输入控制器执行点击
                            self.app.input_controller.click(abs_x, abs_y, priority=1)
            
            # 等待0.1秒
            time.sleep(0.1)
            
            # 执行按键操作
            if self.trigger_key:
                # 直接使用输入控制器执行按键
                import random
                hold_delay = random.randint(self.delay_min, self.delay_max) / 1000.0
                self.app.input_controller.key_down(self.trigger_key, priority=1)
                time.sleep(hold_delay)
                self.app.input_controller.key_up(self.trigger_key, priority=1)
            
            # 切换回原窗口
            quick_switch._restore_foreground_window()
        else:
            self.app.logging_manager.log_message(
                f"后台监控组{self.group_index + 1}窗口切换失败，跳过操作"
            )

class BackgroundManager:
    """后台监控管理器"""
    def __init__(self, app):
        self.app = app
        self.monitors: Dict[int, BackgroundMonitor] = {}
        self.quick_switch = QuickSwitchBackend()
        self.target_hwnd: Optional[int] = None
        self.target_title: Optional[str] = None
    
    def find_target_window(self, keyword: str) -> tuple:
        """
        查找目标窗口
        
        Returns:
            tuple: (success, message)
        """
        if not keyword:
            return (False, "请输入窗口标题关键字")
        
        hwnd = find_window_by_title(keyword)
        if hwnd:
            self.target_hwnd = hwnd
            self.target_title = get_window_title(hwnd)
            return (True, self.target_title)
        
        return (False, "未找到匹配的窗口")
    
    def set_target_window(self, hwnd: int) -> None:
        """设置目标窗口"""
        self.target_hwnd = hwnd
        self.target_title = get_window_title(hwnd) if hwnd else None
    
    def create_group(self, index: int, monitor_type: str = "ocr") -> BackgroundMonitor:
        """创建监控组"""
        monitor = BackgroundMonitor(self.app, index)
        monitor.recognition_type = monitor_type
        
        if self.target_hwnd:
            monitor.set_window(self.target_hwnd)
        
        self.monitors[index] = monitor
        return monitor
    
    def start_group(self, group_index: int) -> bool:
        """启动单个监控组"""
        if group_index not in self.monitors:
            return False
        
        monitor = self.monitors[group_index]
        
        if not self.target_hwnd:
            return False
        
        monitor.set_window(self.target_hwnd)
        return monitor.start_monitoring()
    
    def stop_group(self, group_index: int) -> None:
        """停止单个监控组"""
        if group_index in self.monitors:
            self.monitors[group_index].stop_monitoring()
    
    def start_all_groups(self) -> int:
        """
        启动所有启用的监控组
        
        Returns:
            int: 启动的监控组数量
        """
        if not self.target_hwnd:
            messagebox.showwarning("警告", "请先绑定目标窗口")
            return 0
        
        start_count = 0
        
        for group_index, group in enumerate(self.app.background_groups):
            if not group.get("enabled", tk.BooleanVar(value=False)).get():
                continue
            
            if group_index not in self.monitors:
                monitor_type = group.get("type", "ocr")
                self.create_group(group_index, monitor_type)
            
            monitor = self.monitors[group_index]
            monitor.set_window(self.target_hwnd)
            
            region = group.get("region")
            region_ratio = group.get("region_ratio")
            if region:
                monitor.region = region
            if region_ratio:
                monitor.region_ratio = region_ratio
            
            if not monitor.region and not monitor.region_ratio:
                continue
            
            try:
                monitor.interval = float(group.get("interval", tk.StringVar(value="5")).get())
                monitor.pause = int(group.get("pause", tk.StringVar(value="180")).get())
            except (ValueError, TypeError):
                monitor.interval = 5.0
                monitor.pause = 180
            
            monitor_type = group.get("type", "ocr")
            monitor.recognition_type = monitor_type
            
            if monitor_type == "ocr":
                keywords = group.get("keywords", tk.StringVar(value="")).get()
                language = group.get("language", tk.StringVar(value="eng")).get()
                monitor.configure_ocr(keywords, language)
            
            elif monitor_type == "image":
                template = group.get("template_image")
                try:
                    threshold = float(group.get("threshold", tk.StringVar(value="80")).get()) / 100.0
                except (ValueError, TypeError):
                    threshold = 0.8
                monitor.configure_image(template, threshold)
            
            elif monitor_type == "color":
                target_color = group.get("target_color")
                try:
                    tolerance = int(group.get("tolerance", tk.StringVar(value="10")).get())
                except (ValueError, TypeError):
                    tolerance = 10
                monitor.configure_color(target_color, tolerance)
            
            monitor.trigger_key = group.get("key", tk.StringVar(value="")).get()
            try:
                monitor.delay_min = int(group.get("delay_min", tk.StringVar(value="100")).get())
                monitor.delay_max = int(group.get("delay_max", tk.StringVar(value="200")).get())
            except (ValueError, TypeError):
                monitor.delay_min = 100
                monitor.delay_max = 200
            
            monitor.trigger_click = group.get("click_enabled", tk.BooleanVar(value=False)).get()
            
            monitor.alarm_enabled = group.get("alarm", tk.BooleanVar(value=False)).get()
            
            if monitor.start_monitoring():
                start_count += 1
        
        return start_count
    
    def stop_all_groups(self) -> None:
        """停止所有监控组"""
        for monitor in self.monitors.values():
            monitor.stop_monitoring()

    def get_window_info(self) -> Optional[Dict[str, Any]]:
        """获取目标窗口信息"""
        if not self.target_hwnd:
            return None
        
        rect = get_window_rect(self.target_hwnd)
        size = WindowCoordinate.get_window_size(self.target_hwnd)
        title = get_window_title(self.target_hwnd)
        
        return {
            "hwnd": self.target_hwnd,
            "title": title,
            "rect": rect,
            "size": size
        }
