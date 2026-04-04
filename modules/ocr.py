import threading
import time
import tkinter as tk
from tkinter import messagebox
from PIL import Image
import imagehash

from utils.image import _preprocess_image
from utils.screenshot import ScreenshotManager
from utils.recognition import OCRRecognizer
from core.priority_lock import get_module_priority
from core.click_handler import ClickHandler


class OCRModule:
    """
    OCR模块，负责文字识别核心逻辑
    优先级: 3 (Number=6 > Timed=5 > Image=4 > OCR=3 > Color=2 > Script=1)
    """
    
    PRIORITY = get_module_priority('ocr')
    
    def __init__(self, app):
        self.app = app
        self.last_recognition_times = {}
        self.last_trigger_times = {}
        self.click_handler = ClickHandler(app)
        self.screenshot_manager = ScreenshotManager()
        self._last_texts = {}  # 缓存上次识别文本，用于日志节流
    
    def start_monitoring(self):
        """开始监控"""
        if not self.app.tesseract_available:
            messagebox.showinfo("提示", "Tesseract OCR引擎未配置，请在设置中配置Tesseract路径后使用文字识别功能！")
            return

        has_enabled_group = False
        for group in self.app.ocr_groups:
            if group["enabled"].get() and group["region"]:
                has_enabled_group = True
                break

        if not has_enabled_group:
            messagebox.showwarning("警告", "请至少启用一个识别组并选择区域")
            return

        def start_func():
            self.app.is_running = True
            self.app.is_paused = False
            self.app.ocr_thread = threading.Thread(target=self.ocr_loop, daemon=True)
            self.app.ocr_thread.start()
            return 1

        self.app.start_module("ocr", start_func)

    def stop_monitoring(self):
        """停止监控"""
        self.app.is_running = False
        self._last_texts.clear()  # 清理缓存，确保下次启动时正常输出日志
    
    def ocr_loop(self):
        """
        OCR识别循环
        """
        self.last_recognition_times = {i: 0 for i in range(len(self.app.ocr_groups))}
        self.last_trigger_times = {i: 0 for i in range(len(self.app.ocr_groups))}
        
        last_hashes = {i: None for i in range(len(self.app.ocr_groups))}
        frame_counts = {i: 0 for i in range(len(self.app.ocr_groups))}

        while True:
            if not self.app.is_running:
                break
            try:
                min_interval = self._calculate_min_interval()
                self._wait_for_interval(min_interval)

                if self.app.is_paused:
                    continue

                current_time = time.time()

                for i, group in enumerate(self.app.ocr_groups):
                    if self._should_process_group(group, i, current_time):
                        self.perform_ocr_for_group_optimized(group, i, last_hashes, frame_counts)
                        self.last_recognition_times[i] = current_time
            except Exception as e:
                self.app.logging_manager.log_message(f"错误: {str(e)}")
                time.sleep(5)
    
    def _calculate_min_interval(self):
        enabled_groups = [group for group in self.app.ocr_groups if group["enabled"].get()]
        if enabled_groups:
            try:
                intervals = []
                for group in enabled_groups:
                    try:
                        interval = int(group["interval"].get())
                        intervals.append(interval)
                    except (ValueError, TypeError):
                        intervals.append(5)
                return min(intervals)
            except (ValueError, TypeError):
                return 5
        return 5        
    
    def _wait_for_interval(self, interval):
        for _ in range(interval):
            if not self.app.is_running:
                break
            time.sleep(1)
    
    def _should_process_group(self, group, i, current_time):
        if not group["enabled"].get() or not group["region"]:
            return False

        try:
            pause_duration = int(group["pause"].get())
        except (ValueError, TypeError):
            pause_duration = 180
        try:
            group_interval = int(group["interval"].get())
        except (ValueError, TypeError):
            group_interval = 5

        time_since_trigger = current_time - self.last_trigger_times[i]
        time_since_recognition = current_time - self.last_recognition_times[i]
        
        if time_since_trigger < pause_duration:
            return False

        if time_since_recognition < group_interval:
            return False

        return True
    
    def _validate_ocr_group_input(self, group, group_index):
        if not group:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 组配置为空")
            return False, None, None, None, None

        region = group.get("region")
        if not region:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 未设置识别区域")
            return False, None, None, None, None

        keywords_str = group.get("keywords", tk.StringVar(value="")).get().strip()
        current_lang = group.get("language", tk.StringVar(value="eng")).get()
        click_enabled = group.get("click", tk.BooleanVar(value=False)).get()
        return True, region, keywords_str, current_lang, click_enabled
    
    def _validate_region_coordinates(self, region, group_index):
        try:
            x1, y1, x2, y2 = region
            if len(region) != 4:
                raise ValueError("区域坐标格式错误")
        except (ValueError, TypeError) as e:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 区域坐标无效 - {str(e)}")
            return False, None, None, None, None

        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1, x2)
        bottom = max(y1, y2)

        if (right - left) < 10 or (bottom - top) < 10:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 识别区域太小")
            return False, None, None, None, None

        return True, left, top, right, bottom
    
    def _capture_screen_region(self, left, top, right, bottom, group_index):
        try:
            return self.screenshot_manager.get_region_screenshot((left, top, right, bottom), priority=self.PRIORITY)
        except Exception as e:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 屏幕截图失败 - {str(e)}")
            return None
    
    def perform_ocr_for_group_optimized(self, group, group_index, last_hashes, frame_counts):
        """
        为单个OCR组执行OCR识别（优化版本，使用增量截图和自适应帧率）
        """
        try:
            if not self.app.is_running:
                return

            valid, region, keywords_str, current_lang, click_enabled = self._validate_ocr_group_input(group, group_index)
            if not valid:
                return

            valid, left, top, right, bottom = self._validate_region_coordinates(region, group_index)
            if not valid:
                return

            screenshot = self._capture_screen_region(left, top, right, bottom, group_index)
            if not screenshot:
                return

            current_hash = imagehash.average_hash(screenshot.resize((64, 64)))
            
            if current_hash == last_hashes.get(group_index) and frame_counts.get(group_index, 0) % 5 != 0:
                frame_counts[group_index] += 1
                return
            
            last_hashes[group_index] = current_hash
            frame_counts[group_index] += 1

            start_time = time.time()

            processed_image = _preprocess_image(screenshot, group_index)
            if not processed_image:
                return

            if keywords_str:
                keywords = [keyword.strip().lower() for keyword in keywords_str.split(",") if keyword.strip()]
                
                text = OCRRecognizer.get_text(processed_image, current_lang)
                if not text:
                    return
                
                lower_text = text.lower()
                
                elapsed_time = time.time() - start_time
                sleep_time = max(0.01, 0.1 - elapsed_time)
                time.sleep(sleep_time)

                last_text = self._last_texts.get(group_index)
                if text.strip() != last_text:
                    self.app.logging_manager.log_message(f"识别组{group_index+1}识别结果: '{text.strip()}' (耗时: {elapsed_time:.2f}s, 延迟: {sleep_time:.2f}s)")
                    self._last_texts[group_index] = text.strip()

                if any(keyword in lower_text for keyword in keywords):
                    if click_enabled:
                        rel_pos = OCRRecognizer.find_keyword_position(processed_image, keywords, current_lang)
                        if rel_pos:
                            click_pos = (left + rel_pos[0], top + rel_pos[1])
                        else:
                            click_pos = ((left + right) // 2, (top + bottom) // 2)
                    else:
                        click_pos = ((left + right) // 2, (top + bottom) // 2)

                    self.trigger_action_for_group(group, group_index, click_enabled, click_pos)
            else:
                text = OCRRecognizer.get_text(processed_image, current_lang)
                if text:
                    elapsed_time = time.time() - start_time
                    sleep_time = max(0.01, 0.1 - elapsed_time)
                    time.sleep(sleep_time)
                    
                    last_text = self._last_texts.get(group_index)
                    if text.strip() != last_text:
                        self.app.logging_manager.log_message(f"识别组{group_index+1}识别结果: '{text.strip()}' (耗时: {elapsed_time:.2f}s)")
                        self._last_texts[group_index] = text.strip()

        except Exception as e:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 未知错误 - {str(e)}")
            import traceback
            self.app.logging_manager.log_message(f"错误详情: {traceback.format_exc()}")
    
    def _validate_trigger_input(self, group, group_index):
        if not group:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 组配置为空")
            return False, None, None, None

        key = group.get("key", tk.StringVar(value="")).get()
        alarm_enabled = group.get("alarm", tk.BooleanVar(value=False)).get()
        region = group.get("region")

        if not key:
            self.app.logging_manager.log_message(f"识别组{group_index+1}警告: 未设置触发按键")

        return True, key, alarm_enabled, region
    
    def _calculate_click_position(self, click_pos, region, group_index):
        if click_pos is not None:
            return click_pos

        if not region:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 未设置识别区域，无法计算点击位置")
            return None, None

        try:
            x1, y1, x2, y2 = region
            click_x = (x1 + x2) // 2
            click_y = (y1 + y2) // 2
            return click_x, click_y
        except (ValueError, TypeError) as e:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 区域坐标无效 - {str(e)}")
            return None, None
    
    def _execute_key_press(self, key, group_index):
        if not self.app.is_running or getattr(self.app, 'system_stopped', False):
            return

        if not key:
            return

        group = self.app.ocr_groups[group_index]
        
        from modules.input import KeyEventExecutor
        delay_min_var = group["delay_min"]
        delay_max_var = group["delay_max"]
        executor = KeyEventExecutor(self.app.input_controller, delay_min_var, delay_max_var, self.PRIORITY)
        executor.execute_keypress(key)
        
        self.app.logging_manager.log_message(f"识别组{group_index+1}按下了 {key} 键")
        self.last_trigger_times[group_index] = time.time()
    
    def _play_alarm_if_enabled(self, alarm_enabled, group_index):
        try:
            if alarm_enabled:
                import tkinter as tk
                temp_alarm_var = tk.BooleanVar(value=True)
                self.app.alarm_module.play_alarm_sound(temp_alarm_var)
        except Exception as e:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 播放报警声音失败 - {str(e)}")
    
    def trigger_action_for_group(self, group, group_index, click_enabled, click_pos=None):
        try:
            if not self.app.is_running or getattr(self.app, 'system_stopped', False):
                return

            valid, key, alarm_enabled, region = self._validate_trigger_input(group, group_index)
            if not valid:
                return

            self.app.logging_manager.log_message(f"识别组{group_index+1}触发动作，按键: {key}")

            if click_enabled:
                click_x, click_y = self._calculate_click_position(click_pos, region, group_index)
                self.click_handler.execute_click(
                    x=click_x,
                    y=click_y,
                    priority=self.PRIORITY,
                    module_name="识别组",
                    index=group_index
                )

            self._execute_key_press(key, group_index)
        except Exception as e:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 触发动作失败 - {str(e)}")
            import traceback
            self.app.logging_manager.log_message(f"错误详情: {traceback.format_exc()}")

        if 'alarm_enabled' in locals():
            self._play_alarm_if_enabled(alarm_enabled, group_index)
