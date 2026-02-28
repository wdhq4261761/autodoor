import threading
import time
import numpy as np
from PIL import Image, ImageGrab
import imagehash
import tkinter as tk
from tkinter import messagebox
from core.priority_lock import get_module_priority


class ColorRecognition:
    """
    颜色识别类
    优先级: 2 (Number=5 > Timed=4 > OCR=3 > Color=2 > Script=1)
    """
    
    PRIORITY = 2
    
    def __init__(self, app):
        self.app = app
        self.is_running = False
        self.recognition_thread = None
        self.region = None
        self.target_color = None
        self.tolerance = 10
        self.interval = 5.0
        self.commands = ""
        
        self.core_graphics_available = False
        
        self.last_image_hash = None

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
        """执行颜色识别（优化版本）"""
        if not self.region:
            self.app.logging_manager.log_message("颜色识别失败: 未设置识别区域")
            return False
        
        try:
            # 检查屏幕录制权限（macOS）
            if self.app.platform_adapter.platform == "Darwin":
                permission_manager = PermissionManager(self.app)
                if not permission_manager.check_screen_recording():
                    self.app.root.after(0, lambda: self.app._guide_screen_recording_setup())
                    self.app.logging_manager.log_message("颜色识别失败: 缺少屏幕录制权限")
                    return False
            
            screenshot = None
            try:
                from utils.screenshot import ScreenshotManager
                screenshot_manager = ScreenshotManager()
                screenshot = screenshot_manager.get_region_screenshot(self.region, priority=self.PRIORITY)
            except Exception as e:
                self.app.logging_manager.log_message(f"截图失败: {str(e)}")
            
            # 检查截图是否成功获取
            if not screenshot:
                self.app.logging_manager.log_message("颜色识别失败: 无法获取截图")
                return False
            
            # 检查截图是否为空
            if screenshot.size[0] == 0 or screenshot.size[1] == 0:
                self.app.logging_manager.log_message("颜色识别失败: 截图为空")
                return False
            
            # 使用图像哈希检测区域是否变化
            current_hash = imagehash.average_hash(screenshot.resize((32, 32)))
            
            # 注意：不再跳过颜色识别，即使区域未变化
            # 因为执行命令后屏幕可能没有变化，但我们需要继续检测颜色
            
            # 更新哈希缓存
            self.last_image_hash = current_hash
            
            # 转换为numpy数组
            img_array = np.array(screenshot)
            
            # 优化匹配逻辑，考虑RGB值范围限制
            valid_target_color = np.clip(np.array(self.target_color), 0, 255)
            lower_bound = np.maximum(0, valid_target_color - self.tolerance)
            upper_bound = np.minimum(255, valid_target_color + self.tolerance)
            
            # 区域采样：每隔几个像素检查一个，减少计算量
            sample_step = 2  # 每隔2个像素检查一个
            sampled_array = img_array[::sample_step, ::sample_step]
            
            # 向量化颜色匹配（NumPy 加速 100 倍+）
            is_match = np.all((sampled_array >= lower_bound) & (sampled_array <= upper_bound), axis=2)
            match_pixels = np.sum(is_match)

            if match_pixels > 0:  # 匹配到像素点即可认为识别到目标颜色
                # 识别到目标颜色
                self.app.logging_manager.log_message(f"✅ 识别到目标颜色")
                return True
            else:
                # 未识别到目标颜色
                return False
        except Exception as e:
            self.app.logging_manager.log_message(f"颜色识别错误: {str(e)}")
            # 添加详细的错误信息，帮助调试
            import traceback
            self.app.logging_manager.log_message(f"错误详情: {traceback.format_exc()}")
            # 即使出错也返回False，确保应用程序不会崩溃
            return False
    
    def execute_commands(self):
        """执行识别后命令（只执行一遍）"""
        if not self.commands:
            return
        
        # 创建临时脚本执行器
        from modules.script import ScriptExecutor
        temp_executor = ScriptExecutor(self.app)
        
        # 执行命令（只执行一遍）
        temp_executor.run_script_once(self.commands)

    def stop_recognition(self):
        """停止颜色识别"""
        self.is_running = False
        if hasattr(self, 'recognition_thread') and self.recognition_thread.is_alive():
            # 等待线程结束
            self.recognition_thread.join(timeout=1)

class ColorRecognitionManager:
    """颜色识别管理器类，处理颜色识别相关的UI操作"""
    def __init__(self, app):
        self.app = app
        self.color_recognition = None
    
    def select_color_region(self):
        """选择颜色识别区域"""
        self.app.logging_manager.log_message("开始选择颜色识别区域...")
        # 使用通用的区域选择方法
        from utils.region import _start_selection
        _start_selection(self.app, "color", 0)
    
    def select_color(self):
        """选择颜色"""
        self.app.logging_manager.log_message("开始选择目标颜色...")
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
        self.color_selection_window = tk.Toplevel(self.app.root)
        # 移除窗口装饰，确保窗口能够覆盖整个屏幕，包括顶部区域
        self.color_selection_window.overrideredirect(True)
        self.color_selection_window.geometry(f"{max_x - min_x}x{max_y - min_y}+{min_x}+{min_y}")
        self.color_selection_window.attributes("-alpha", 0.3)
        self.color_selection_window.attributes("-topmost", True)
        self.color_selection_window.configure(cursor="crosshair")
        
        # 创建画布
        self.color_canvas = tk.Canvas(self.color_selection_window, bg="white", highlightthickness=0)
        self.color_canvas.pack(fill=tk.BOTH, expand=True)
        
        self.color_canvas.bind("<Button-1>", self.on_color_select)
        
        self.color_selection_window.bind("<Escape>", lambda e: self.cancel_color_selection())
        
        self.color_selection_window.focus_set()
    
    def cancel_color_selection(self):
        """取消颜色选择"""
        self.app.logging_manager.log_message("已取消颜色选择")
        if hasattr(self, 'color_selection_window') and self.color_selection_window.winfo_exists():
            self.color_selection_window.destroy()
    
    def on_color_select(self, event):
        self.color_selection_window.withdraw()
        
        self.color_selection_window.update()
        
        abs_x, abs_y = event.x_root, event.y_root
        
        try:
            from utils.screenshot import ScreenshotManager
            screenshot_manager = ScreenshotManager()
            screen = screenshot_manager.get_full_screenshot()
        except Exception:
            screen = ImageGrab.grab(all_screens=True)
        
        try:
            import screeninfo
            monitors = screeninfo.get_monitors()
            min_x = min(monitor.x for monitor in monitors)
            min_y = min(monitor.y for monitor in monitors)
        except:
            min_x, min_y = 0, 0
        
        rel_x = abs_x - min_x
        rel_y = abs_y - min_y
        
        pixel = screen.getpixel((rel_x, rel_y))
        
        self.app.target_color = pixel
        r, g, b = pixel
        self.app.color_var.set(f"RGB({r}, {g}, {b})")
        self.app.logging_manager.log_message(f"选择颜色: RGB({r}, {g}, {b})")
        self.app.logging_manager.log_message(f"选择位置: ({abs_x}, {abs_y})")
        
        if hasattr(self.app, 'color_display'):
            self.app.color_display.configure(fg_color=f"#{r:02x}{g:02x}{b:02x}")
        
        self.color_selection_window.destroy()
    
    def start_color_recognition(self):
        """开始颜色识别"""
        if not self.color_recognition:
            self.color_recognition = ColorRecognition(self.app)
        
        # 获取设置参数
        try:
            # 从目标颜色变量获取颜色值
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
        
        # 检查区域是否已选择
        if not hasattr(self.app, 'color_recognition_region') or not self.app.color_recognition_region:
            messagebox.showwarning("警告", "请先选择颜色识别区域！")
            return
        
        # 设置颜色识别区域
        self.color_recognition.set_region(self.app.color_recognition_region)
        
        # 启动颜色识别
        self.color_recognition.start_recognition(target_color, tolerance, interval, commands)
        self.app.status_var.set("颜色识别中...")
    
    def stop_color_recognition(self):
        """停止颜色识别"""
        if self.color_recognition:
            # 检查线程是否正在运行
            if hasattr(self.color_recognition, 'is_running') and self.color_recognition.is_running:
                self.color_recognition.stop_recognition()
                self.app.status_var.set("颜色识别已停止")
            elif hasattr(self.color_recognition, 'recognition_thread') and self.color_recognition.recognition_thread.is_alive():
                # 如果is_running为False但是线程仍然在运行，强制停止
                self.color_recognition.is_running = False
                self.color_recognition.recognition_thread.join(timeout=2)
                self.app.status_var.set("颜色识别已停止")