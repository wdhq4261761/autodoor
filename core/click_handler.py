import time


class ClickHandler:
    """统一的鼠标点击处理器
    
    提供统一的鼠标点击接口，封装优先级处理、异常处理、日志记录等功能。
    """
    
    def __init__(self, app):
        self.app = app
    
    def execute_click(self, x, y, priority=0, module_name="", index=0, delay=None):
        """
        执行鼠标点击
        
        Args:
            x: 点击x坐标
            y: 点击y坐标
            priority: 优先级（默认0，数值越大优先级越高）
            module_name: 模块名称（用于日志）
            index: 组索引（用于日志，从0开始）
            delay: 点击后延迟时间（秒），None则使用app.click_delay
        
        Returns:
            bool: 是否执行成功
        """
        if not self._validate_running_state():
            return False
        
        if not self._validate_coordinates(x, y):
            return False
        
        try:
            self.app.input_controller.move_to(x, y, priority=priority)
            self.app.input_controller.mouse_down(x=x, y=y, button='left', priority=priority)
            time.sleep(0.1)
            self.app.input_controller.mouse_up(x=x, y=y, button='left', priority=priority)
            self._log_click_success(x, y, module_name, index)
            self._wait_delay(delay)
            return True
        except Exception as e:
            self._log_click_error(e, module_name, index)
            return False
    
    def calculate_region_center(self, region):
        """
        计算区域中心点
        
        Args:
            region: 区域坐标 (x1, y1, x2, y2)
        
        Returns:
            tuple: (center_x, center_y) 或 (None, None)
        """
        if not region:
            return None, None
        
        try:
            x1, y1, x2, y2 = region
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            return center_x, center_y
        except (ValueError, TypeError):
            return None, None
    
    def _validate_running_state(self):
        """验证运行状态"""
        if not self.app.is_running or getattr(self.app, 'system_stopped', False):
            return False
        return True
    
    def _validate_coordinates(self, x, y):
        """验证坐标有效性"""
        if x is None or y is None:
            return False
        return True
    
    def _log_click_success(self, x, y, module_name, index):
        """记录点击成功日志"""
        if module_name:
            platform = getattr(self.app, 'platform_adapter', None)
            platform_name = platform.platform if platform else ""
            self.app.logging_manager.log_message(
                f"[{platform_name}] {module_name}{index+1}执行鼠标点击: ({x}, {y})"
            )
    
    def _log_click_error(self, error, module_name, index):
        """记录点击错误日志"""
        if module_name:
            self.app.logging_manager.log_message(
                f"{module_name}{index+1}鼠标点击失败: {str(error)}"
            )
    
    def _wait_delay(self, delay):
        """等待延迟时间"""
        if delay is not None:
            time.sleep(delay)
        elif hasattr(self.app, 'click_delay'):
            time.sleep(self.app.click_delay)
        else:
            time.sleep(0.1)
