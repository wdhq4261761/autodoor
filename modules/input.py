import time
import random


class KeyEventExecutor:
    """
    统一按键执行器类
    
    执行流程：按下 -> 等待(delay) -> 抬起
    delay_min/max 表示按键按住的时长范围（毫秒）
    """
    
    def __init__(self, input_controller, delay_min_var, delay_max_var, priority=0):
        self.input_controller = input_controller
        self.delay_min_var = delay_min_var
        self.delay_max_var = delay_max_var
        self.priority = priority
    
    def execute_keypress(self, key):
        delay_min = max(1, int(self.delay_min_var.get()))
        delay_max = max(delay_min, int(self.delay_max_var.get()))
        
        hold_delay = random.randint(delay_min, delay_max) / 1000
        
        self.input_controller.key_down(key, priority=self.priority)
        time.sleep(hold_delay)
        self.input_controller.key_up(key, priority=self.priority)