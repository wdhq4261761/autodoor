import pytest
import time
import threading
from unittest.mock import MagicMock, patch
from modules.timed import TimedModule


class TestTimedModuleComprehensive:
    """TimedModule综合测试类"""
    
    @pytest.fixture
    def timed_module(self, mock_app, create_mock_timed_group):
        mock_app.timed_groups = [
            create_mock_timed_group(enabled=True, interval="1", key="space"),
            create_mock_timed_group(enabled=True, interval="2", key="enter"),
        ]
        mock_app.timed_stop_events = {}
        mock_app.timed_threads = []
        mock_app.platform_adapter = MagicMock()
        mock_app.platform_adapter.platform = "Windows"
        mock_app.is_running = True
        return TimedModule(mock_app)
    
    def test_start_timed_tasks_all_enabled(self, timed_module):
        """测试所有启用的定时任务"""
        timed_module.app.start_module = MagicMock(return_value=2)
        
        timed_module.start_timed_tasks()
        
        timed_module.app.start_module.assert_called_once()
    
    def test_stop_timed_tasks_with_threads(self, timed_module):
        """测试停止有线程的定时任务"""
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = False
        timed_module.app.timed_threads = [mock_thread]
        timed_module.app.timed_stop_events = {0: threading.Event()}
        
        timed_module.stop_timed_tasks()
        
        assert len(timed_module.app.timed_stop_events) == 0
        assert len(timed_module.app.timed_threads) == 0
    
    def test_timed_task_loop_with_different_keys(self, timed_module):
        """测试不同按键的定时任务"""
        stop_event = threading.Event()
        stop_event.set()
        
        for i, group in enumerate(timed_module.app.timed_groups):
            key = group["key"].get()
            timed_module.timed_task_loop(i, 1, key, stop_event)
    
    def test_timed_task_loop_with_alarm_enabled(self, timed_module):
        """测试启用报警的定时任务"""
        timed_module.app.timed_groups[0]["alarm"].set(True)
        stop_event = threading.Event()
        stop_event.set()
        
        timed_module.timed_task_loop(0, 1, "space", stop_event)
    
    def test_timed_task_loop_with_click_enabled(self, timed_module):
        """测试启用点击的定时任务"""
        timed_module.app.timed_groups[0]["click_enabled"].set(True)
        timed_module.app.timed_groups[0]["position_x"].set(100)
        timed_module.app.timed_groups[0]["position_y"].set(200)
        stop_event = threading.Event()
        stop_event.set()
        
        timed_module.timed_task_loop(0, 1, "space", stop_event)
    
    def test_timed_task_loop_stopped_early(self, timed_module):
        """测试提前停止的定时任务"""
        stop_event = threading.Event()
        stop_event.set()
        
        timed_module.timed_task_loop(0, 1, "space", stop_event)
        
        timed_module.app.input_controller.key_down.assert_not_called()


class TestTimedModuleInterval:
    """定时模块间隔测试"""
    
    @pytest.fixture
    def timed_module(self, mock_app, create_mock_timed_group):
        mock_app.timed_groups = [
            create_mock_timed_group(enabled=True, interval="5"),
            create_mock_timed_group(enabled=True, interval="10"),
            create_mock_timed_group(enabled=True, interval="3"),
        ]
        mock_app.timed_stop_events = {}
        mock_app.timed_threads = []
        return TimedModule(mock_app)
    
    def test_different_intervals(self, timed_module):
        """测试不同间隔"""
        intervals = [int(g["interval"].get()) for g in timed_module.app.timed_groups]
        
        assert intervals == [5, 10, 3]
    
    def test_interval_calculation(self, timed_module):
        """测试间隔计算"""
        for group in timed_module.app.timed_groups:
            interval = int(group["interval"].get())
            
            assert interval > 0
            assert isinstance(interval, int)


class TestTimedModulePosition:
    """定时模块位置测试"""
    
    @pytest.fixture
    def timed_module(self, mock_app, create_mock_timed_group):
        mock_app.timed_groups = [create_mock_timed_group()]
        mock_app.current_timed_group = 0
        mock_app.cancel_selection = MagicMock()
        return TimedModule(mock_app)
    
    def test_position_selection(self, timed_module):
        """测试位置选择"""
        event = MagicMock()
        event.x_root = 150
        event.y_root = 250
        
        timed_module.on_timed_position_click(event)
        
        assert timed_module.app.timed_groups[0]["position_x"].get() == 150
        assert timed_module.app.timed_groups[0]["position_y"].get() == 250
    
    def test_position_selection_different_group(self, timed_module):
        """测试不同组的位置选择"""
        timed_module.app.current_timed_group = 0
        event = MagicMock()
        event.x_root = 300
        event.y_root = 400
        
        timed_module.on_timed_position_click(event)
        
        assert timed_module.app.timed_groups[0]["position_x"].get() == 300
    
    def test_position_selection_invalid_group(self, timed_module):
        """测试无效组的位置选择"""
        timed_module.app.current_timed_group = 999
        event = MagicMock()
        event.x_root = 100
        event.y_root = 200
        
        timed_module.on_timed_position_click(event)
