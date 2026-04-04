import threading
import time
from PIL import Image
from input.permissions import PermissionManager
from utils.screenshot import ScreenshotManager
from utils.recognition import NumberRecognizer
from core.priority_lock import get_module_priority


class NumberModule:
    """数字识别模块 - 优先级最高(6)"""
    
    PRIORITY = get_module_priority('number')
    
    def __init__(self, app):
        self.app = app
        self.screenshot_manager = ScreenshotManager()
        self._last_results = {}  # 缓存上次识别结果，用于日志节流
    
    def start_number_recognition(self):
        def start_func():
            start_count = 0
            for i, region_config in enumerate(self.app.number_regions):
                if region_config["enabled"].get():
                    region = region_config["region"]
                    if not region:
                        continue
                    try:
                        threshold = int(region_config["threshold"].get())
                    except (ValueError, TypeError):
                        threshold = 500
                    key = region_config["key"].get()
                    stop_event = threading.Event()
                    self.app.number_stop_events[i] = stop_event
                    thread = threading.Thread(target=self.number_recognition_loop, args=(i, region, threshold, key, stop_event), daemon=True)
                    self.app.number_threads.append(thread)
                    thread.start()
                    start_count += 1
            return start_count

        self.app.start_module("number", start_func)

    def stop_number_recognition(self):
        for stop_event in self.app.number_stop_events.values():
            stop_event.set()
        self.app.number_stop_events.clear()
        if self.app.number_threads:
            self.app.number_threads.clear()
        self._last_results.clear()  # 清理缓存，确保下次启动时正常输出日志

    def number_recognition_loop(self, region_index, region, threshold, key, stop_event):
        while not stop_event.is_set() and self.app.number_regions[region_index]["enabled"].get():
            if not self.app.is_running:
                break
            try:
                time.sleep(1)

                if stop_event.is_set():
                    return

                screenshot = self.take_screenshot(region)
                if screenshot is None:
                    continue
                
                text = self.ocr_number(screenshot)

                number = NumberRecognizer.parse_number(text, self.app._number_cache)
                if number is not None:
                    last_result = self._last_results.get(region_index)
                    if number != last_result:
                        self.app.logging_manager.log_message(f"数字识别{region_index+1}解析结果: {number}")
                        self._last_results[region_index] = number
                    
                    if number < threshold:
                        self.app.alarm_module.play_alarm_sound(self.app.number_regions[region_index]["alarm"])

                        if key:
                            self.app.logging_manager.log_message(f"数字识别{region_index+1}触发按键: {key}")
                            
                            from modules.input import KeyEventExecutor
                            delay_min_var = self.app.number_regions[region_index]["delay_min"]
                            delay_max_var = self.app.number_regions[region_index]["delay_max"]
                            executor = KeyEventExecutor(self.app.input_controller, delay_min_var, delay_max_var, self.PRIORITY)
                            executor.execute_keypress(key)
                            
                            delay_min = int(delay_min_var.get())
                            delay_max = int(delay_max_var.get())
                            self.app.logging_manager.log_message(f"数字识别{region_index+1}按下了 {key} 键，按住时长范围: {delay_min}-{delay_max} 毫秒")
                        else:
                            self.app.logging_manager.log_message(f"数字识别{region_index+1}按键配置为空，仅执行报警操作")
                else:
                    last_result = self._last_results.get(region_index)
                    if text != last_result:
                        self.app.logging_manager.log_message(f"数字识别{region_index+1}结果: '{text}'")
                        self._last_results[region_index] = text
            except Exception as e:
                self.app.logging_manager.log_message(f"数字识别{region_index+1}错误: {str(e)}")
                time.sleep(5)

    def take_screenshot(self, region):
        try:
            return self.screenshot_manager.get_region_screenshot(region, priority=self.PRIORITY)
        except Exception as e:
            self.app.logging_manager.log_message(f"数字识别错误: 屏幕截图失败 - {str(e)}")
            return None

    def ocr_number(self, image):
        processed_image = self._preprocess_number_image(image)
        if processed_image is None:
            processed_image = image.convert('L')
        
        high_conf_text, confidence, all_text = NumberRecognizer.recognize_with_confidence(processed_image)
        return high_conf_text if high_conf_text else all_text
    
    def _preprocess_number_image(self, image):
        """
        数字识别专用图像预处理 - 增强识别精度
        """
        try:
            from PIL import ImageEnhance, ImageFilter
            
            image = image.convert('L')
            
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            image = image.filter(ImageFilter.SHARPEN)
            
            image = image.point(lambda p: p > 128 and 255)
            
            return image
        except Exception:
            return None
