import pytest
import time
import threading
from unittest.mock import MagicMock, patch
from modules.timed import TimedModule


class TestTimedModule:
    """TimedModule测试类"""
    
    @pytest.fixture
    def timed_module(self, mock_app):
        """创建定时模块实例"""
        return TimedModule(mock_app)
    
    def test_init(self, timed_module):
        """测试初始化"""
        assert timed_module.app is not None
    
    def test_priority(self):
        """测试优先级"""
        assert TimedModule.PRIORITY == 4
    
    def test_stop_timed_tasks(self, timed_module):
        """测试停止定时任务"""
        timed_module.app.timed_stop_events = {0: threading.Event(), 1: threading.Event()}
        timed_module.app.timed_threads = [MagicMock(), MagicMock()]
        
        timed_module.stop_timed_tasks()
        
        assert len(timed_module.app.timed_stop_events) == 0
        assert len(timed_module.app.timed_threads) == 0
    
    def test_stop_timed_tasks_empty(self, timed_module):
        """测试停止空的定时任务"""
        timed_module.app.timed_stop_events = {}
        timed_module.app.timed_threads = []
        
        timed_module.stop_timed_tasks()
        
        assert len(timed_module.app.timed_stop_events) == 0


class TestTimedTaskLoop:
    """定时任务循环测试"""
    
    @pytest.fixture
    def timed_module(self, mock_app, create_mock_timed_group):
        """创建定时模块实例"""
        mock_app.timed_groups = [create_mock_timed_group(enabled=True, interval="1", key="space")]
        mock_app.timed_stop_events = {}
        mock_app.timed_threads = []
        mock_app.platform_adapter = MagicMock()
        mock_app.platform_adapter.platform = "Windows"
        return TimedModule(mock_app)
    
    def test_timed_task_loop_with_stop_event(self, timed_module):
        """测试停止事件中断循环"""
        stop_event = threading.Event()
        stop_event.set()
        
        timed_module.timed_task_loop(0, 1, "space", stop_event)
        
        timed_module.app.input_controller.key_down.assert_not_called()
    
    def test_timed_task_loop_disabled_group(self, timed_module):
        """测试禁用组的循环"""
        timed_module.app.timed_groups[0]["enabled"].set(False)
        stop_event = threading.Event()
        
        timed_module.timed_task_loop(0, 1, "space", stop_event)
        
        timed_module.app.input_controller.key_down.assert_not_called()


class TestTimedPositionSelection:
    """定时位置选择测试"""
    
    @pytest.fixture
    def timed_module(self, mock_app, create_mock_timed_group):
        mock_app.timed_groups = [create_mock_timed_group()]
        mock_app.current_timed_group = 0
        mock_app.cancel_selection = MagicMock()
        return TimedModule(mock_app)
    
    def test_on_timed_position_click(self, timed_module):
        """测试位置点击"""
        event = MagicMock()
        event.x_root = 100
        event.y_root = 200
        
        timed_module.on_timed_position_click(event)
        
        assert timed_module.app.timed_groups[0]["position_x"].get() == 100
        assert timed_module.app.timed_groups[0]["position_y"].get() == 200
    
    def test_on_timed_position_click_invalid_group(self, timed_module):
        """测试无效组的位置点击"""
        timed_module.app.current_timed_group = 999
        event = MagicMock()
        event.x_root = 100
        event.y_root = 200
        
        timed_module.on_timed_position_click(event)


class TestTimedGroupValidation:
    """定时组验证测试"""
    
    def test_group_enabled_check(self, create_mock_timed_group):
        """测试组启用检查"""
        group = create_mock_timed_group(enabled=True)
        
        assert group["enabled"].get() is True
    
    def test_group_disabled_check(self, create_mock_timed_group):
        """测试组禁用检查"""
        group = create_mock_timed_group(enabled=False)
        
        assert group["enabled"].get() is False
    
    def test_group_interval_setting(self, create_mock_timed_group):
        """测试组间隔设置"""
        group = create_mock_timed_group(interval="10")
        
        assert group["interval"].get() == "10"
    
    def test_group_key_setting(self, create_mock_timed_group):
        """测试组按键设置"""
        group = create_mock_timed_group(key="enter")
        
        assert group["key"].get() == "enter"


class TestTimedMultipleGroups:
    """多定时组测试"""
    
    @pytest.fixture
    def timed_module(self, mock_app, create_mock_timed_group):
        mock_app.timed_groups = [
            create_mock_timed_group(enabled=True, interval="1", key="space"),
            create_mock_timed_group(enabled=False, interval="2", key="enter"),
            create_mock_timed_group(enabled=True, interval="3", key="a"),
        ]
        mock_app.timed_stop_events = {}
        mock_app.timed_threads = []
        return TimedModule(mock_app)
    
    def test_multiple_groups_count(self, timed_module):
        """测试多组数量"""
        assert len(timed_module.app.timed_groups) == 3
    
    def test_enabled_groups_count(self, timed_module):
        """测试启用组数量"""
        enabled_count = sum(1 for g in timed_module.app.timed_groups if g["enabled"].get())
        
        assert enabled_count == 2
    
    def test_stop_all_groups(self, timed_module):
        """测试停止所有组"""
        for i in range(3):
            timed_module.app.timed_stop_events[i] = threading.Event()
        
        timed_module.stop_timed_tasks()
        
        assert len(timed_module.app.timed_stop_events) == 0


class TestTimedTaskLoopAdvanced:
    """定时任务循环高级测试"""
    
    @pytest.fixture
    def timed_module(self, mock_app, create_mock_timed_group):
        mock_app.timed_groups = [create_mock_timed_group(enabled=True, interval="1", key="space")]
        mock_app.timed_stop_events = {}
        mock_app.timed_threads = []
        mock_app.platform_adapter = MagicMock()
        mock_app.platform_adapter.platform = "Windows"
        mock_app.alarm_module = MagicMock()
        mock_app.input_controller = MagicMock()
        return TimedModule(mock_app)
    
    def test_timed_task_loop_with_click_enabled(self, timed_module):
        """测试启用点击"""
        timed_module.app.timed_groups[0]["click_enabled"].set(True)
        timed_module.app.timed_groups[0]["position_x"].set(100)
        timed_module.app.timed_groups[0]["position_y"].set(200)
        
        stop_event = threading.Event()
        
        def stop_after_delay():
            time.sleep(0.3)
            stop_event.set()
        
        stop_thread = threading.Thread(target=stop_after_delay)
        stop_thread.start()
        
        timed_module.timed_task_loop(0, 1, "space", stop_event)
        
        stop_thread.join()
    
    def test_timed_task_loop_with_click_zero_position(self, timed_module):
        """测试点击位置为零"""
        timed_module.app.timed_groups[0]["click_enabled"].set(True)
        timed_module.app.timed_groups[0]["position_x"].set(0)
        timed_module.app.timed_groups[0]["position_y"].set(0)
        
        stop_event = threading.Event()
        
        def stop_after_delay():
            time.sleep(0.3)
            stop_event.set()
        
        stop_thread = threading.Thread(target=stop_after_delay)
        stop_thread.start()
        
        timed_module.timed_task_loop(0, 1, "space", stop_event)
        
        stop_thread.join()
    
    def test_timed_task_loop_click_exception(self, timed_module):
        """测试点击异常"""
        timed_module.app.timed_groups[0]["click_enabled"].set(True)
        timed_module.app.timed_groups[0]["position_x"].set(100)
        timed_module.app.timed_groups[0]["position_y"].set(200)
        timed_module.app.input_controller.click.side_effect = Exception("Click failed")
        
        stop_event = threading.Event()
        
        def stop_after_delay():
            time.sleep(1.5)
            stop_event.set()
        
        stop_thread = threading.Thread(target=stop_after_delay)
        stop_thread.start()
        
        timed_module.timed_task_loop(0, 1, "space", stop_event)
        
        stop_thread.join()
        
        assert timed_module.app.logging_manager.log_message.called
    
    def test_timed_task_loop_no_key(self, timed_module):
        """测试无按键"""
        timed_module.app.timed_groups[0]["key"].set("")
        
        stop_event = threading.Event()
        
        def stop_after_delay():
            time.sleep(0.3)
            stop_event.set()
        
        stop_thread = threading.Thread(target=stop_after_delay)
        stop_thread.start()
        
        timed_module.timed_task_loop(0, 1, "", stop_event)
        
        stop_thread.join()
    
    def test_timed_task_loop_stop_during_interval(self, timed_module):
        """测试间隔期间停止"""
        stop_event = threading.Event()
        
        def stop_after_delay():
            time.sleep(0.1)
            stop_event.set()
        
        stop_thread = threading.Thread(target=stop_after_delay)
        stop_thread.start()
        
        timed_module.timed_task_loop(0, 10, "space", stop_event)
        
        stop_thread.join()
        
        timed_module.app.input_controller.key_down.assert_not_called()
    
    def test_timed_task_loop_alarm_called(self, timed_module):
        """测试报警调用"""
        timed_module.app.timed_groups[0]["alarm"].set(True)
        
        stop_event = threading.Event()
        
        def stop_after_delay():
            time.sleep(1.5)
            stop_event.set()
        
        stop_thread = threading.Thread(target=stop_after_delay)
        stop_thread.start()
        
        timed_module.timed_task_loop(0, 1, "space", stop_event)
        
        stop_thread.join()
        
        assert timed_module.app.alarm_module.play_alarm_sound.called or timed_module.app.logging_manager.log_message.called
