import pytest
import time
import threading
from unittest.mock import MagicMock, patch
from modules.timed import TimedModule


class TestTimedModuleFull:
    """TimedModule完整测试类"""
    
    @pytest.fixture
    def timed_module(self, mock_app, create_mock_timed_group):
        mock_app.timed_groups = [
            create_mock_timed_group(enabled=True, interval="1", key="space"),
        ]
        mock_app.timed_stop_events = {}
        mock_app.timed_threads = []
        mock_app.platform_adapter = MagicMock()
        mock_app.platform_adapter.platform = "Windows"
        mock_app.is_running = True
        return TimedModule(mock_app)
    
    def test_timed_task_loop_normal_execution(self, timed_module):
        """测试正常执行的定时任务循环"""
        stop_event = threading.Event()
        stop_event.set()
        
        timed_module.timed_task_loop(0, 1, "space", stop_event)
    
    def test_timed_task_loop_with_both_actions(self, timed_module):
        """测试同时执行按键和点击"""
        timed_module.app.timed_groups[0]["click_enabled"].set(True)
        timed_module.app.timed_groups[0]["position_x"].set(100)
        timed_module.app.timed_groups[0]["position_y"].set(200)
        
        stop_event = threading.Event()
        stop_event.set()
        
        timed_module.timed_task_loop(0, 1, "space", stop_event)
    
    def test_timed_task_loop_alarm_triggered(self, timed_module):
        """测试报警触发"""
        timed_module.app.timed_groups[0]["alarm"].set(True)
        
        stop_event = threading.Event()
        stop_event.set()
        
        timed_module.timed_task_loop(0, 1, "space", stop_event)
    
    def test_timed_task_loop_empty_key(self, timed_module):
        """测试空按键"""
        stop_event = threading.Event()
        stop_event.set()
        
        timed_module.timed_task_loop(0, 1, "", stop_event)
        
        timed_module.app.input_controller.key_down.assert_not_called()
    
    def test_timed_task_loop_disabled_during_execution(self, timed_module):
        """测试执行期间禁用"""
        stop_event = threading.Event()
        
        def disable_after_delay():
            time.sleep(0.3)
            timed_module.app.timed_groups[0]["enabled"].set(False)
            time.sleep(0.3)
            stop_event.set()
        
        disable_thread = threading.Thread(target=disable_after_delay)
        disable_thread.start()
        
        timed_module.timed_task_loop(0, 1, "space", stop_event)
        
        disable_thread.join()


class TestTimedModuleStartStop:
    """定时模块启动停止测试"""
    
    @pytest.fixture
    def timed_module(self, mock_app, create_mock_timed_group):
        mock_app.timed_groups = [
            create_mock_timed_group(enabled=True, interval="1", key="space"),
            create_mock_timed_group(enabled=False, interval="2", key="enter"),
        ]
        mock_app.timed_stop_events = {}
        mock_app.timed_threads = []
        mock_app.platform_adapter = MagicMock()
        mock_app.platform_adapter.platform = "Windows"
        return TimedModule(mock_app)
    
    def test_start_timed_tasks_creates_threads(self, timed_module):
        """测试启动定时任务创建线程"""
        timed_module.app.start_module = MagicMock(return_value=1)
        
        timed_module.start_timed_tasks()
        
        timed_module.app.start_module.assert_called()
    
    def test_stop_timed_tasks_clears_all(self, timed_module):
        """测试停止定时任务清除所有"""
        timed_module.app.timed_stop_events = {0: threading.Event(), 1: threading.Event()}
        timed_module.app.timed_threads = [MagicMock(), MagicMock()]
        
        timed_module.stop_timed_tasks()
        
        assert len(timed_module.app.timed_stop_events) == 0
        assert len(timed_module.app.timed_threads) == 0
    
    def test_multiple_start_stop_cycles(self, timed_module):
        """测试多次启动停止循环"""
        for _ in range(3):
            timed_module.app.timed_stop_events = {0: threading.Event()}
            timed_module.app.timed_threads = [MagicMock()]
            
            timed_module.stop_timed_tasks()
            
            assert len(timed_module.app.timed_stop_events) == 0
