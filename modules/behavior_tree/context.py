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
    - 节点状态回调
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
        
        self._on_node_status: Optional[callable] = None
    
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
    
    def set_node_status_callback(self, callback: callable) -> None:
        """设置节点状态回调"""
        self._on_node_status = callback
    
    def notify_node_status(self, node_id: str, status: str) -> None:
        """通知节点状态变化"""
        if self._on_node_status:
            try:
                self._on_node_status(node_id, status)
            except Exception:
                pass
    
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
        if self._is_paused:
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
            self.log("截图失败: screenshot_manager 未初始化", "error")
            return None
        
        if region:
            result = self.screenshot_manager.get_region_screenshot(region)
            if result is None:
                self.log(f"截图失败: 区域截图返回 None, region={region}", "error")
            return result
        
        result = self.screenshot_manager.get_full_screenshot()
        if result is None:
            self.log("截图失败: 全屏截图返回 None", "error")
        return result
    
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
                self.input_controller.press_key(key, delay=duration/1000.0 if duration > 0 else 0)
            elif action == "down":
                self.input_controller.key_down(key)
            elif action == "up":
                self.input_controller.key_up(key)
            return True
        except Exception as e:
            self.log(f"按键执行失败: {e}", "error")
            return False
    
    def execute_mouse_click(self, button: str = "left", action: str = "press", 
                            position: Optional[tuple] = None, duration: int = 0) -> bool:
        """
        执行鼠标点击
        
        Args:
            button: 鼠标按钮 (left/right/middle)
            action: 动作类型 (press/down/up)
            position: 点击位置 (x, y)
            duration: 按住时长（毫秒）
            
        Returns:
            是否执行成功
        """
        if self.input_controller is None:
            return False
        
        try:
            if position:
                self.input_controller.move_to(position[0], position[1])
            
            if action == "press":
                self.input_controller.mouse_press(button, duration/1000.0 if duration > 0 else 0)
            elif action == "down":
                self.input_controller.mouse_down(button)
            elif action == "up":
                self.input_controller.mouse_up(button)
            return True
        except Exception as e:
            self.log(f"鼠标点击失败: {e}", "error")
            return False
    
    def execute_mouse_scroll(self, clicks: int, direction: str = "垂直", speed: str = "正常") -> bool:
        """
        执行鼠标滚轮操作
        
        Args:
            clicks: 滚动次数，正数向上/右，负数向下/左
            direction: 滚动方向 (垂直/水平)
            speed: 滚动速度 (慢速/正常/快速)
            
        Returns:
            是否执行成功
        """
        if self.input_controller is None:
            return False
        
        try:
            speed_map = {
                "慢速": 0.1,
                "正常": 0.05,
                "快速": 0.01
            }
            
            interval = speed_map.get(speed, 0.05)
            abs_clicks = abs(clicks)
            
            for i in range(abs_clicks):
                if not self.check_running():
                    return False
                
                if direction == "水平":
                    if clicks > 0:
                        self.input_controller.scroll(1)
                    else:
                        self.input_controller.scroll(-1)
                else:
                    if clicks > 0:
                        self.input_controller.scroll(1)
                    else:
                        self.input_controller.scroll(-1)
                
                if i < abs_clicks - 1:
                    time.sleep(interval)
            
            return True
        except Exception as e:
            self.log(f"鼠标滚轮失败: {e}", "error")
            return False
    
    def get_mouse_position(self) -> Optional[tuple]:
        """
        获取当前鼠标位置
        
        Returns:
            鼠标位置 (x, y) 或 None
        """
        if self.input_controller is None:
            return None
        
        try:
            return self.input_controller.get_position()
        except Exception as e:
            self.log(f"获取鼠标位置失败: {e}", "error")
            return None
    
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
