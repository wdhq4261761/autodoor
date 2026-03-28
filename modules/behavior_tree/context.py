"""
执行上下文

管理行为树执行过程中的状态和资源
"""

import time
from typing import TYPE_CHECKING, Any, Optional

from .blackboard import Blackboard

if TYPE_CHECKING:
    from utils.screenshot import ScreenshotManager
    from input.controller import InputController
    from core.logging import LoggingManager


class ExecutionContext:
    """
    执行上下文
    
    包含：
    - 黑板（数据共享）
    - 截图管理器
    - 输入控制器
    - 日志管理器
    - 执行状态控制
    """
    
    def __init__(self, app):
        """
        初始化执行上下文
        
        Args:
            app: 主应用实例
        """
        self.app = app
        self.blackboard = Blackboard()
        
        self.screenshot_manager: "ScreenshotManager" = getattr(app, "screenshot_manager", None)
        self.input_controller: "InputController" = getattr(app, "input_controller", None)
        self.logging_manager: "LoggingManager" = getattr(app, "logging_manager", None)
        
        self._is_running = True
        self._is_paused = False
        self._start_time: Optional[float] = None
        self._tick_count = 0
    
    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._is_running
    
    @property
    def is_paused(self) -> bool:
        """是否已暂停"""
        return self._is_paused
    
    @property
    def elapsed_time(self) -> float:
        """已运行时间（秒）"""
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time
    
    @property
    def tick_count(self) -> int:
        """已执行 tick 次数"""
        return self._tick_count
    
    def start(self) -> None:
        """开始执行"""
        self._is_running = True
        self._is_paused = False
        self._start_time = time.time()
        self._tick_count = 0
        self.blackboard.set("execution_count", 0)
    
    def stop(self) -> None:
        """停止执行"""
        self._is_running = False
        self._is_paused = False
    
    def pause(self) -> None:
        """暂停执行"""
        self._is_paused = True
    
    def resume(self) -> None:
        """恢复执行"""
        self._is_paused = False
    
    def tick(self) -> None:
        """执行一次 tick"""
        self._tick_count += 1
        self.blackboard.increment("execution_count")
    
    def wait_if_paused(self, check_interval: float = 0.1) -> None:
        """
        如果暂停则等待
        
        Args:
            check_interval: 检查间隔（秒）
        """
        while self._is_paused and self._is_running:
            time.sleep(check_interval)
    
    def check_running(self) -> bool:
        """检查是否仍在运行"""
        self.wait_if_paused()
        return self._is_running
    
    def log(self, message: str, level: str = "info") -> None:
        """
        记录日志
        
        Args:
            message: 日志消息
            level: 日志级别
        """
        if self.logging_manager:
            self.logging_manager.log_message(f"[BT] {message}")
    
    def get_screenshot(self, region: Optional[tuple] = None) -> Any:
        """
        获取截图
        
        Args:
            region: 截图区域 (x1, y1, x2, y2)
            
        Returns:
            PIL.Image 截图图像
        """
        if self.screenshot_manager is None:
            return None
        
        if region:
            return self.screenshot_manager.get_region_screenshot(region)
        return self.screenshot_manager.get_full_screenshot()
    
    def execute_key_press(self, key: str, action: str = "press", duration: int = 0) -> bool:
        """
        执行按键操作
        
        Args:
            key: 按键名称
            action: 动作类型 (press/down/up)
            duration: 按住时长（毫秒）
            
        Returns:
            是否执行成功
        """
        if self.input_controller is None:
            return False
        
        try:
            if action == "press":
                self.input_controller.press(key)
            elif action == "down":
                self.input_controller.key_down(key)
            elif action == "up":
                self.input_controller.key_up(key)
            return True
        except Exception as e:
            self.log(f"按键执行失败: {e}", "error")
            return False
    
    def execute_mouse_click(self, button: str = "left", position: Optional[tuple] = None) -> bool:
        """
        执行鼠标点击
        
        Args:
            button: 鼠标按钮 (left/right/middle)
            position: 点击位置 (x, y)
            
        Returns:
            是否执行成功
        """
        if self.input_controller is None:
            return False
        
        try:
            if position:
                self.input_controller.move_to(position[0], position[1])
            self.input_controller.click(button=button)
            return True
        except Exception as e:
            self.log(f"鼠标点击失败: {e}", "error")
            return False
    
    def execute_delay(self, duration_ms: int) -> None:
        """
        执行延时
        
        Args:
            duration_ms: 延时时长（毫秒）
        """
        duration_sec = duration_ms / 1000.0
        start = time.time()
        
        while (time.time() - start) < duration_sec:
            if not self.check_running():
                break
            time.sleep(0.01)
    
    def reset(self) -> None:
        """重置上下文"""
        self._is_running = True
        self._is_paused = False
        self._start_time = None
        self._tick_count = 0
        self.blackboard.clear()
