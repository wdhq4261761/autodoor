import pyautogui
import threading
import time
from core.priority_lock import PriorityLock, get_module_priority


KEY_NAME_MAPPING = {
    'alt_l': 'altleft',
    'alt_r': 'altright',
    'control_l': 'ctrlleft',
    'control_r': 'ctrlright',
    'shift_l': 'shiftleft',
    'shift_r': 'shiftright',
    'win_l': 'winleft',
    'win_r': 'winright',
    'super_l': 'winleft',
    'super_r': 'winright',
    'meta_l': 'winleft',
    'meta_r': 'winright',
    'escape': 'escape',
    'return': 'enter',
    'backspace': 'backspace',
    'tab': 'tab',
    'space': 'space',
    'prior': 'pageup',
    'next': 'pagedown',
    'caps_lock': 'capslock',
    'num_lock': 'numlock',
    'scroll_lock': 'scrolllock',
    'up': 'up',
    'down': 'down',
    'left': 'left',
    'right': 'right',
}


class InputController:
    """
    输入控制器类，提供通用的按键和鼠标操作方法
    
    使用优先级锁确保高优先级模块优先执行输入操作。
    优先级顺序：Number(5) > Timed(4) > OCR(3) > Color(2) > Script(1)
    """
    
    def __init__(self, app=None):
        self.app = app
        self.core_graphics_available = False
        self.key_lock = PriorityLock()
        self.mouse_lock = PriorityLock()
        if self.app:
            if hasattr(self.app, 'logging_manager'):
                self.app.logging_manager.log_message("InputController初始化完成，使用PyAutoGUI执行所有输入操作")
            else:
                print("InputController初始化完成，使用PyAutoGUI执行所有输入操作")
    
    @staticmethod
    def handle_permission_errors(func):
        """统一处理权限相关错误"""
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                error_msg = str(e).lower()
                if self.app and ("accessibility" in error_msg or "permission" in error_msg):
                    if hasattr(self.app, 'logging_manager'):
                        self.app.logging_manager.log_message("❌ 辅助功能权限缺失，请授权后重试")
                    else:
                        print("❌ 辅助功能权限缺失，请授权后重试")
                    if hasattr(self.app, 'root') and hasattr(self.app, '_guide_accessibility_setup'):
                        self.app.root.after(0, self.app._guide_accessibility_setup)
                elif self.app:
                    if hasattr(self.app, 'logging_manager'):
                        self.app.logging_manager.log_message(f"❌ 操作错误: {e}")
                    else:
                        print(f"❌ 操作错误: {e}")
                raise
        return wrapper
    
    @handle_permission_errors
    def press_key(self, key, delay=0, priority=0):
        with self.key_lock.acquire(priority):
            try:
                if delay > 0:
                    time.sleep(delay)
                
                pyautogui.press(key.lower(), interval=delay)
                if self.app:
                    self.app.logging_manager.log_message(f"[{self.app.platform_adapter.platform}] 执行按键: {key}")
            except pyautogui.FailSafeException:
                if self.app:
                    self.app.logging_manager.log_message("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
            except pyautogui.ImageNotFoundException:
                if self.app:
                    self.app.logging_manager.log_message(f"⚠️ 未找到目标图像: {key}")
                if hasattr(self, 'fallback_keys') and key in self.fallback_keys:
                    if self.app:
                        self.app.logging_manager.log_message(f"  → 尝试备用按键: {self.fallback_keys[key]}")
                    try:
                        pyautogui.press(self.fallback_keys[key].lower(), interval=delay)
                        if self.app:
                            self.app.logging_manager.log_message(f"执行: 按下备用按键 {self.fallback_keys[key]}")
                    except Exception as e:
                        if self.app:
                            self.app.logging_manager.log_message(f"备用按键执行错误: {str(e)}")
    
    @handle_permission_errors
    def key_down(self, key, priority=0):
        with self.key_lock.acquire(priority):
            try:
                mapped_key = KEY_NAME_MAPPING.get(key.lower(), key.lower())
                pyautogui.keyDown(mapped_key)
                if self.app:
                    self.app.logging_manager.log_message(f"执行: 按下 {key} (映射: {mapped_key})")
            except pyautogui.FailSafeException:
                if self.app:
                    self.app.logging_manager.log_message("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
            except pyautogui.ImageNotFoundException:
                if self.app:
                    self.app.logging_manager.log_message(f"⚠️ 未找到目标图像: {key}")
                if hasattr(self, 'fallback_keys') and key in self.fallback_keys:
                    if self.app:
                        self.app.logging_manager.log_message(f"  → 尝试备用按键: {self.fallback_keys[key]}")
                    try:
                        pyautogui.keyDown(self.fallback_keys[key].lower())
                        if self.app:
                            self.app.logging_manager.log_message(f"执行: 按下备用按键 {self.fallback_keys[key]}")
                    except Exception as e:
                        if self.app:
                            self.app.logging_manager.log_message(f"备用按键执行错误: {str(e)}")
    
    @handle_permission_errors
    def key_up(self, key, priority=0):
        with self.key_lock.acquire(priority):
            try:
                mapped_key = KEY_NAME_MAPPING.get(key.lower(), key.lower())
                pyautogui.keyUp(mapped_key)
                if self.app:
                    self.app.logging_manager.log_message(f"执行: 抬起 {key} (映射: {mapped_key})")
            except pyautogui.FailSafeException:
                if self.app:
                    self.app.logging_manager.log_message("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
    
    @handle_permission_errors
    def click(self, x, y, priority=0):
        with self.mouse_lock.acquire(priority):
            try:
                pyautogui.click(x, y)
                if self.app:
                    self.app.logging_manager.log_message(f"[{self.app.platform_adapter.platform}] 执行鼠标点击: ({x}, {y})")
            except pyautogui.FailSafeException:
                if self.app:
                    self.app.logging_manager.log_message("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
    
    @handle_permission_errors
    def mouse_down(self, x=None, y=None, button='left', priority=0):
        with self.mouse_lock.acquire(priority):
            try:
                if x is not None and y is not None:
                    pyautogui.moveTo(x, y)
                pyautogui.mouseDown(button=button)
                if self.app:
                    self.app.logging_manager.log_message(f"执行: 按下鼠标{button}键")
            except pyautogui.FailSafeException:
                if self.app:
                    self.app.logging_manager.log_message("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
    
    @handle_permission_errors
    def mouse_up(self, x=None, y=None, button='left', priority=0):
        with self.mouse_lock.acquire(priority):
            try:
                if x is not None and y is not None:
                    pyautogui.moveTo(x, y)
                pyautogui.mouseUp(button=button)
                if self.app:
                    self.app.logging_manager.log_message(f"执行: 抬起鼠标{button}键")
            except pyautogui.FailSafeException:
                if self.app:
                    self.app.logging_manager.log_message("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
    
    @handle_permission_errors
    def move_to(self, x, y, priority=0):
        with self.mouse_lock.acquire(priority):
            try:
                pyautogui.moveTo(x, y)
                if self.app:
                    self.app.logging_manager.log_message(f"执行: 移动鼠标到 ({x}, {y})")
            except pyautogui.FailSafeException:
                if self.app:
                    self.app.logging_manager.log_message("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
