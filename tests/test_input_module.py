import pytest
import time
import threading
from unittest.mock import MagicMock, patch, PropertyMock
from modules.input import KeyEventExecutor


class TestKeyEventExecutor:
    """KeyEventExecutor测试类"""
    
    def test_init(self, mock_app, mock_tk_var):
        """测试初始化"""
        input_controller = MagicMock()
        delay_min_var = mock_tk_var(100)
        delay_max_var = mock_tk_var(200)
        
        executor = KeyEventExecutor(input_controller, delay_min_var, delay_max_var, priority=1)
        
        assert executor.input_controller == input_controller
        assert executor.priority == 1
    
    def test_execute_keypress(self, mock_app, mock_tk_var):
        """测试按键执行"""
        input_controller = MagicMock()
        delay_min_var = mock_tk_var(10)
        delay_max_var = mock_tk_var(10)
        
        executor = KeyEventExecutor(input_controller, delay_min_var, delay_max_var, priority=1)
        
        start_time = time.time()
        executor.execute_keypress("enter")
        elapsed = time.time() - start_time
        
        input_controller.key_down.assert_called_once_with("enter", priority=1)
        input_controller.key_up.assert_called_once_with("enter", priority=1)
        assert elapsed >= 0.01
    
    def test_execute_keypress_with_priority(self, mock_app, mock_tk_var):
        """测试带优先级的按键执行"""
        input_controller = MagicMock()
        delay_min_var = mock_tk_var(5)
        delay_max_var = mock_tk_var(5)
        
        executor = KeyEventExecutor(input_controller, delay_min_var, delay_max_var, priority=5)
        executor.execute_keypress("space")
        
        input_controller.key_down.assert_called_once_with("space", priority=5)
        input_controller.key_up.assert_called_once_with("space", priority=5)
    
    def test_delay_min_greater_than_max(self, mock_app, mock_tk_var):
        """测试delay_min大于delay_max的情况"""
        input_controller = MagicMock()
        delay_min_var = mock_tk_var(200)
        delay_max_var = mock_tk_var(100)
        
        executor = KeyEventExecutor(input_controller, delay_min_var, delay_max_var)
        executor.execute_keypress("a")
        
        input_controller.key_down.assert_called_once()
        input_controller.key_up.assert_called_once()
    
    def test_zero_delay(self, mock_app, mock_tk_var):
        """测试零延迟"""
        input_controller = MagicMock()
        delay_min_var = mock_tk_var(0)
        delay_max_var = mock_tk_var(0)
        
        executor = KeyEventExecutor(input_controller, delay_min_var, delay_max_var)
        executor.execute_keypress("a")
        
        input_controller.key_down.assert_called_once()
        input_controller.key_up.assert_called_once()
    
    def test_negative_delay(self, mock_app, mock_tk_var):
        """测试负延迟"""
        input_controller = MagicMock()
        delay_min_var = mock_tk_var(-10)
        delay_max_var = mock_tk_var(-5)
        
        executor = KeyEventExecutor(input_controller, delay_min_var, delay_max_var)
        executor.execute_keypress("a")
        
        input_controller.key_down.assert_called_once()
        input_controller.key_up.assert_called_once()
