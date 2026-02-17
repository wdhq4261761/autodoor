import pytest
import time
import threading
from unittest.mock import MagicMock, patch
from modules.timed import TimedModule


class TestTimedModuleStartFunc:
    """测试start_timed_tasks内部start_func"""
    
    @pytest.fixture
    def timed_module(self, mock_app, create_mock_timed_group):
        mock_app.timed_groups = [
            create_mock_timed_group(enabled=True, interval="1", key="space"),
            create_mock_timed_group(enabled=False, interval="2", key="enter"),
            create_mock_timed_group(enabled=True, interval="3", key="a"),
        ]
        mock_app.timed_stop_events = {}
        mock_app.timed_threads = []
        mock_app.platform_adapter = MagicMock()
        mock_app.platform_adapter.platform = "Windows"
        mock_app.start_module = MagicMock()
        return TimedModule(mock_app)
    
    def test_start_func_creates_threads_for_enabled_groups(self, timed_module):
        """测试只为启用的组创建线程"""
        start_func = None
        
        def capture_start_func(module_name, func):
            nonlocal start_func
            start_func = func
            return func()
        
        timed_module.app.start_module = MagicMock(side_effect=capture_start_func)
        
        timed_module.start_timed_tasks()
        
        assert len(timed_module.app.timed_stop_events) == 2
        assert len(timed_module.app.timed_threads) == 2
        
        for stop_event in timed_module.app.timed_stop_events.values():
            stop_event.set()
        timed_module.app.timed_threads.clear()
    
    def test_start_func_handles_invalid_interval(self, timed_module):
        """测试处理无效间隔值"""
        timed_module.app.timed_groups[0]["interval"].set("invalid")
        
        start_func = None
        
        def capture_start_func(module_name, func):
            nonlocal start_func
            start_func = func
            return func()
        
        timed_module.app.start_module = MagicMock(side_effect=capture_start_func)
        
        timed_module.start_timed_tasks()
        
        assert len(timed_module.app.timed_threads) == 2
        
        for stop_event in timed_module.app.timed_stop_events.values():
            stop_event.set()
        timed_module.app.timed_threads.clear()
    
    def test_start_func_returns_correct_count(self, timed_module):
        """测试返回正确的启动数量"""
        start_func = None
        
        def capture_start_func(module_name, func):
            nonlocal start_func
            start_func = func
            return func()
        
        timed_module.app.start_module = MagicMock(side_effect=capture_start_func)
        
        timed_module.start_timed_tasks()
        
        timed_module.app.start_module.assert_called()


class TestTimedTaskLoopFull:
    """测试timed_task_loop完整逻辑"""
    
    @pytest.fixture
    def timed_module(self, mock_app, create_mock_timed_group):
        mock_app.timed_groups = [create_mock_timed_group(enabled=True, interval="1", key="space")]
        mock_app.timed_stop_events = {}
        mock_app.timed_threads = []
        mock_app.platform_adapter = MagicMock()
        mock_app.platform_adapter.platform = "Windows"
        return TimedModule(mock_app)
    
    def test_task_loop_with_click_enabled(self, timed_module):
        """测试启用点击的任务循环"""
        timed_module.app.timed_groups[0]["click_enabled"].set(True)
        timed_module.app.timed_groups[0]["position_x"].set(100)
        timed_module.app.timed_groups[0]["position_y"].set(200)
        
        stop_event = threading.Event()
        stop_event.set()
        
        timed_module.timed_task_loop(0, 1, "space", stop_event)
    
    def test_task_loop_with_alarm_enabled(self, timed_module):
        """测试启用报警的任务循环"""
        timed_module.app.timed_groups[0]["alarm"].set(True)
        
        stop_event = threading.Event()
        stop_event.set()
        
        timed_module.timed_task_loop(0, 1, "space", stop_event)
    
    def test_task_loop_with_empty_key(self, timed_module):
        """测试空按键的任务循环"""
        stop_event = threading.Event()
        stop_event.set()
        
        timed_module.timed_task_loop(0, 1, "", stop_event)
    
    def test_task_loop_with_click_exception(self, timed_module):
        """测试点击异常处理"""
        timed_module.app.timed_groups[0]["click_enabled"].set(True)
        timed_module.app.timed_groups[0]["position_x"].set(100)
        timed_module.app.timed_groups[0]["position_y"].set(200)
        timed_module.app.input_controller.click.side_effect = Exception("Click failed")
        
        stop_event = threading.Event()
        stop_event.set()
        
        timed_module.timed_task_loop(0, 1, "space", stop_event)
    
    def test_task_loop_disabled_during_execution(self, timed_module):
        """测试执行期间禁用"""
        stop_event = threading.Event()
        
        def disable_after_delay():
            time.sleep(0.3)
            timed_module.app.timed_groups[0]["enabled"].set(False)
            stop_event.set()
        
        disable_thread = threading.Thread(target=disable_after_delay)
        disable_thread.start()
        
        timed_module.timed_task_loop(0, 1, "space", stop_event)
        
        disable_thread.join()


class TestTimedPositionSelection:
    """测试定时位置选择"""
    
    @pytest.fixture
    def timed_module(self, mock_app, create_mock_timed_group):
        mock_app.timed_groups = [create_mock_timed_group()]
        mock_app.current_timed_group = 0
        mock_app.cancel_selection = MagicMock()
        mock_app.save_config = MagicMock()
        mock_app.logging_manager = MagicMock()
        mock_app.is_selecting = False
        return TimedModule(mock_app)
    
    def test_on_timed_position_click_saves_position(self, timed_module):
        """测试点击保存位置"""
        event = MagicMock()
        event.x_root = 150
        event.y_root = 250
        
        timed_module.on_timed_position_click(event)
        
        assert timed_module.app.timed_groups[0]["position_x"].get() == 150
        assert timed_module.app.timed_groups[0]["position_y"].get() == 250
    
    def test_on_timed_position_click_invalid_index(self, timed_module):
        """测试无效索引"""
        timed_module.app.current_timed_group = 999
        event = MagicMock()
        event.x_root = 100
        event.y_root = 200
        
        timed_module.on_timed_position_click(event)
    
    def test_on_timed_position_click_negative_index(self, timed_module):
        """测试负索引"""
        timed_module.app.current_timed_group = -1
        event = MagicMock()
        event.x_root = 100
        event.y_root = 200
        
        timed_module.on_timed_position_click(event)
    
    def test_on_timed_position_click_calls_save_config(self, timed_module):
        """测试调用保存配置"""
        event = MagicMock()
        event.x_root = 100
        event.y_root = 200
        
        timed_module.on_timed_position_click(event)
        
        timed_module.app.save_config.assert_called_once()
    
    def test_on_timed_position_click_save_config_exception(self, timed_module):
        """测试保存配置异常"""
        timed_module.app.save_config.side_effect = Exception("Save failed")
        event = MagicMock()
        event.x_root = 100
        event.y_root = 200
        
        timed_module.on_timed_position_click(event)


class TestTimedStopTasks:
    """测试停止定时任务"""
    
    @pytest.fixture
    def timed_module(self, mock_app, create_mock_timed_group):
        mock_app.timed_groups = [create_mock_timed_group()]
        mock_app.timed_stop_events = {}
        mock_app.timed_threads = []
        mock_app.status_labels = {"timed": MagicMock()}
        return TimedModule(mock_app)
    
    def test_stop_tasks_clears_events(self, timed_module):
        """测试清除事件"""
        timed_module.app.timed_stop_events = {0: threading.Event(), 1: threading.Event()}
        
        timed_module.stop_timed_tasks()
        
        assert len(timed_module.app.timed_stop_events) == 0
    
    def test_stop_tasks_clears_threads(self, timed_module):
        """测试清除线程"""
        timed_module.app.timed_threads = [MagicMock(), MagicMock()]
        
        timed_module.stop_timed_tasks()
        
        assert len(timed_module.app.timed_threads) == 0
    
    def test_stop_tasks_updates_status(self, timed_module):
        """测试更新状态"""
        timed_module.stop_timed_tasks()
        
        timed_module.app.status_labels["timed"].set.assert_called_with("定时功能: 未运行")
