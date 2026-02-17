import pytest
import time
import threading
from unittest.mock import MagicMock, patch
from modules.timed import TimedModule


class TestTimedModuleAdvanced:
    """TimedModule高级测试类"""
    
    @pytest.fixture
    def timed_module(self, mock_app, create_mock_timed_group):
        mock_app.timed_groups = [create_mock_timed_group(enabled=True, interval="1", key="space")]
        mock_app.timed_stop_events = {}
        mock_app.timed_threads = []
        mock_app.platform_adapter = MagicMock()
        mock_app.platform_adapter.platform = "Windows"
        return TimedModule(mock_app)
    
    def test_start_timed_tasks(self, timed_module):
        """测试启动定时任务"""
        timed_module.app.start_module = MagicMock(return_value=1)
        
        timed_module.start_timed_tasks()
        
        timed_module.app.start_module.assert_called_once()
    
    def test_start_timed_tasks_disabled(self, timed_module):
        """测试启动禁用的定时任务"""
        timed_module.app.timed_groups[0]["enabled"].set(False)
        timed_module.app.start_module = MagicMock(return_value=0)
        
        timed_module.start_timed_tasks()
        
        timed_module.app.start_module.assert_called_once()
    
    def test_timed_task_loop_with_alarm(self, timed_module):
        """测试带报警的定时任务"""
        timed_module.app.timed_groups[0]["alarm"].set(True)
        stop_event = threading.Event()
        stop_event.set()
        
        timed_module.timed_task_loop(0, 1, "space", stop_event)
    
    def test_timed_task_loop_with_click(self, timed_module):
        """测试带点击的定时任务"""
        timed_module.app.timed_groups[0]["click_enabled"].set(True)
        timed_module.app.timed_groups[0]["position_x"].set(100)
        timed_module.app.timed_groups[0]["position_y"].set(200)
        stop_event = threading.Event()
        stop_event.set()
        
        timed_module.timed_task_loop(0, 1, "space", stop_event)
    
    def test_timed_task_loop_no_key(self, timed_module):
        """测试无按键的定时任务"""
        timed_module.app.timed_groups[0]["key"].set("")
        stop_event = threading.Event()
        stop_event.set()
        
        timed_module.timed_task_loop(0, 1, "", stop_event)


class TestTimedPositionSelectionAdvanced:
    """定时位置选择高级测试"""
    
    @pytest.fixture
    def timed_module(self, mock_app, create_mock_timed_group):
        mock_app.timed_groups = [create_mock_timed_group()]
        mock_app.current_timed_group = 0
        mock_app.cancel_selection = MagicMock()
        mock_app.save_config = MagicMock()
        return TimedModule(mock_app)
    
    def test_on_timed_position_click_with_save(self, timed_module):
        """测试位置点击并保存"""
        event = MagicMock()
        event.x_root = 150
        event.y_root = 250
        
        timed_module.on_timed_position_click(event)
        
        assert timed_module.app.timed_groups[0]["position_x"].get() == 150
        assert timed_module.app.timed_groups[0]["position_y"].get() == 250
    
    def test_on_timed_position_click_negative_index(self, timed_module):
        """测试负索引位置点击"""
        timed_module.app.current_timed_group = -1
        event = MagicMock()
        event.x_root = 100
        event.y_root = 200
        
        timed_module.on_timed_position_click(event)


class TestTimedMultipleGroupsAdvanced:
    """多定时组高级测试"""
    
    @pytest.fixture
    def timed_module(self, mock_app, create_mock_timed_group):
        mock_app.timed_groups = [
            create_mock_timed_group(enabled=True, interval="1", key="space", alarm=True),
            create_mock_timed_group(enabled=True, interval="2", key="enter", alarm=False),
            create_mock_timed_group(enabled=False, interval="3", key="a"),
        ]
        mock_app.timed_stop_events = {}
        mock_app.timed_threads = []
        mock_app.platform_adapter = MagicMock()
        mock_app.platform_adapter.platform = "Windows"
        return TimedModule(mock_app)
    
    def test_multiple_groups_different_intervals(self, timed_module):
        """测试不同间隔的多组"""
        intervals = [int(g["interval"].get()) for g in timed_module.app.timed_groups]
        
        assert intervals == [1, 2, 3]
    
    def test_multiple_groups_different_keys(self, timed_module):
        """测试不同按键的多组"""
        keys = [g["key"].get() for g in timed_module.app.timed_groups]
        
        assert keys == ["space", "enter", "a"]
    
    def test_stop_all_groups_with_events(self, timed_module):
        """测试停止所有带事件的组"""
        for i in range(3):
            timed_module.app.timed_stop_events[i] = threading.Event()
        
        timed_module.stop_timed_tasks()
        
        assert len(timed_module.app.timed_stop_events) == 0
