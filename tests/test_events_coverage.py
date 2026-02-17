import pytest
import time
import threading
import queue
from unittest.mock import MagicMock, patch
from core.events import EventManager


class TestEventManagerProcessEvents:
    """测试事件处理"""
    
    @pytest.fixture
    def event_manager(self, mock_app):
        mock_app.logging_manager = MagicMock()
        return EventManager(mock_app)
    
    def test_process_events_handles_keypress(self, event_manager):
        """测试处理按键事件"""
        event_manager.app.ocr_groups = [{
            'delay_min': MagicMock(),
            'delay_max': MagicMock()
        }]
        event_manager.app.ocr_groups[0]['delay_min'].get.return_value = "100"
        event_manager.app.ocr_groups[0]['delay_max'].get.return_value = "200"
        event_manager.app.input_controller = MagicMock()
        event_manager.app.logging_manager = MagicMock()
        
        event_data = (-3, ('keypress', 'enter'), ('ocr', 0))
        
        event_manager.execute_event(event_data)
        
        event_manager.app.input_controller.key_down.assert_called()
        event_manager.app.input_controller.key_up.assert_called()
    
    def test_process_events_handles_timed_keypress(self, event_manager):
        """测试处理定时按键事件"""
        event_manager.app.timed_groups = [{
            'delay_min': MagicMock(),
            'delay_max': MagicMock()
        }]
        event_manager.app.timed_groups[0]['delay_min'].get.return_value = "100"
        event_manager.app.timed_groups[0]['delay_max'].get.return_value = "200"
        event_manager.app.input_controller = MagicMock()
        event_manager.app.logging_manager = MagicMock()
        
        event_data = (-4, ('keypress', 'space'), ('timed', 0))
        
        event_manager.execute_event(event_data)
        
        event_manager.app.input_controller.key_down.assert_called()
    
    def test_process_events_handles_number_keypress(self, event_manager):
        """测试处理数字识别按键事件"""
        event_manager.app.number_regions = [{
            'delay_min': MagicMock(),
            'delay_max': MagicMock()
        }]
        event_manager.app.number_regions[0]['delay_min'].get.return_value = "100"
        event_manager.app.number_regions[0]['delay_max'].get.return_value = "200"
        event_manager.app.input_controller = MagicMock()
        event_manager.app.logging_manager = MagicMock()
        
        event_data = (-5, ('keypress', 'f5'), ('number', 0))
        
        event_manager.execute_event(event_data)
        
        event_manager.app.input_controller.key_down.assert_called()
    
    def test_process_events_handles_unknown_module(self, event_manager):
        """测试处理未知模块事件"""
        event_manager.app.input_controller = MagicMock()
        event_manager.app.logging_manager = MagicMock()
        
        event_data = (-1, ('keypress', 'a'), ('unknown', 0))
        
        event_manager.execute_event(event_data)
        
        event_manager.app.input_controller.key_down.assert_called()
    
    def test_process_events_handles_no_module_info(self, event_manager):
        """测试处理无模块信息事件"""
        event_manager.app.input_controller = MagicMock()
        event_manager.app.logging_manager = MagicMock()
        
        event_data = (0, ('keypress', 'a'), None)
        
        event_manager.execute_event(event_data)
        
        event_manager.app.input_controller.key_down.assert_called()
    
    def test_process_events_handles_exit_event(self, event_manager):
        """测试处理退出事件"""
        event_data = (0, ('exit', None), None)
        
        event_manager.execute_event(event_data)


class TestEventManagerPriority:
    """测试事件优先级"""
    
    @pytest.fixture
    def event_manager(self, mock_app):
        mock_app.PRIORITIES = {
            "number": 5,
            "timed": 4,
            "ocr": 3,
            "color": 2,
            "script": 1
        }
        return EventManager(mock_app)
    
    def test_add_event_with_module_priority(self, event_manager):
        """测试使用模块优先级添加事件"""
        event_manager.add_event(('keypress', 'a'), module_info=('number', 0))
        
        assert event_manager.event_queue.qsize() == 1
    
    def test_add_event_with_explicit_priority(self, event_manager):
        """测试使用显式优先级添加事件"""
        event_manager.add_event(('keypress', 'a'), priority=10)
        
        assert event_manager.event_queue.qsize() == 1
    
    def test_add_event_no_priority(self, event_manager):
        """测试无优先级添加事件"""
        event_manager.add_event(('keypress', 'a'))
        
        assert event_manager.event_queue.qsize() == 1


class TestEventManagerThread:
    """测试事件线程"""
    
    @pytest.fixture
    def event_manager(self, mock_app):
        mock_app.logging_manager = MagicMock()
        return EventManager(mock_app)
    
    def test_start_event_thread(self, event_manager):
        """测试启动事件线程"""
        event_manager.start_event_thread()
        
        assert event_manager.is_event_running is True
        assert event_manager.event_thread is not None
        
        event_manager.is_event_running = False
        if event_manager.event_thread and event_manager.event_thread.is_alive():
            event_manager.event_thread.join(timeout=2)
    
    def test_process_events_loop(self, event_manager):
        """测试事件处理循环"""
        event_manager.app.logging_manager = MagicMock()
        
        event_manager.add_event(('keypress', 'a'), priority=1)
        
        processed = []
        
        original_execute = event_manager.execute_event
        def track_execute(event_data):
            processed.append(event_data)
            original_execute(event_data)
        
        event_manager.execute_event = track_execute
        event_manager.app.input_controller = MagicMock()
        
        event_manager.is_event_running = True
        
        def stop_after_process():
            time.sleep(0.3)
            event_manager.is_event_running = False
        
        stop_thread = threading.Thread(target=stop_after_process)
        stop_thread.start()
        
        event_manager.process_events()
        
        stop_thread.join()
        
        assert len(processed) >= 1


class TestEventManagerClearEvents:
    """测试清空事件队列"""
    
    @pytest.fixture
    def event_manager(self, mock_app):
        return EventManager(mock_app)
    
    def test_clear_empty_queue(self, event_manager):
        """测试清空空队列"""
        event_manager.clear_events()
        
        assert event_manager.event_queue.qsize() == 0
    
    def test_clear_non_empty_queue(self, event_manager):
        """测试清空非空队列"""
        event_manager.add_event(('keypress', 'a'), priority=1)
        event_manager.add_event(('keypress', 'b'), priority=2)
        event_manager.add_event(('keypress', 'c'), priority=3)
        
        assert event_manager.event_queue.qsize() == 3
        
        event_manager.clear_events()
        
        assert event_manager.event_queue.qsize() == 0


class TestEventManagerErrorHandling:
    """测试错误处理"""
    
    @pytest.fixture
    def event_manager(self, mock_app):
        mock_app.logging_manager = MagicMock()
        return EventManager(mock_app)
    
    def test_execute_event_handles_exception(self, event_manager):
        """测试执行事件异常处理"""
        event_manager.app.input_controller = MagicMock()
        event_manager.app.input_controller.key_down.side_effect = Exception("Key error")
        event_manager.app.logging_manager = MagicMock()
        
        event_data = (0, ('keypress', 'a'), None)
        
        event_manager.execute_event(event_data)
        
        event_manager.app.logging_manager.log_message.assert_called()
    
    def test_process_events_handles_queue_exception(self, event_manager):
        """测试处理队列异常"""
        event_manager.app.logging_manager = MagicMock()
        
        event_manager.is_event_running = True
        
        def stop_after_delay():
            time.sleep(0.3)
            event_manager.is_event_running = False
        
        stop_thread = threading.Thread(target=stop_after_delay)
        stop_thread.start()
        
        event_manager.process_events()
        
        stop_thread.join()


class TestEventManagerProcessEventsAdvanced:
    """测试事件处理高级场景"""
    
    @pytest.fixture
    def event_manager(self, mock_app):
        mock_app.logging_manager = MagicMock()
        mock_app.input_controller = MagicMock()
        return EventManager(mock_app)
    
    def test_process_events_busy_queue(self, event_manager):
        """测试繁忙队列延迟"""
        event_manager.is_event_running = True
        
        for i in range(5):
            event_manager.add_event(('keypress', f'key{i}'), priority=1)
        
        processed_count = []
        original_execute = event_manager.execute_event
        
        def track_execute(event_data):
            processed_count.append(1)
            try:
                original_execute(event_data)
            except Exception:
                pass
        
        event_manager.execute_event = track_execute
        
        def stop_after_delay():
            time.sleep(1.0)
            event_manager.is_event_running = False
        
        stop_thread = threading.Thread(target=stop_after_delay)
        stop_thread.start()
        
        event_manager.process_events()
        
        stop_thread.join()
        
        assert len(processed_count) >= 1
    
    def test_process_events_exception_without_logging_manager(self, mock_app):
        """测试异常处理 - 无logging_manager"""
        mock_app.input_controller = MagicMock()
        mock_app.input_controller.key_down.side_effect = Exception("Test error")
        
        event_manager = EventManager(mock_app)
        event_manager.is_event_running = True
        
        event_manager.add_event(('keypress', 'a'), priority=1)
        
        def stop_after_delay():
            time.sleep(0.3)
            event_manager.is_event_running = False
        
        stop_thread = threading.Thread(target=stop_after_delay)
        stop_thread.start()
        
        event_manager.process_events()
        
        stop_thread.join()
    
    def test_process_events_empty_queue_timeout(self, event_manager):
        """测试空队列超时"""
        event_manager.is_event_running = True
        
        def stop_after_delay():
            time.sleep(1.5)
            event_manager.is_event_running = False
        
        stop_thread = threading.Thread(target=stop_after_delay)
        stop_thread.start()
        
        start_time = time.time()
        event_manager.process_events()
        elapsed = time.time() - start_time
        
        stop_thread.join()
        
        assert elapsed >= 1.0
    
    def test_execute_event_with_2_element_data(self, event_manager):
        """测试执行2元素事件数据"""
        event_manager.app.input_controller = MagicMock()
        
        event_data = (('keypress', 'a'), None)
        
        event_manager.execute_event(event_data)
        
        event_manager.app.input_controller.key_down.assert_called()
    
    def test_execute_event_keypress_exception(self, event_manager):
        """测试按键执行异常"""
        event_manager.app.input_controller = MagicMock()
        event_manager.app.input_controller.key_down.side_effect = Exception("Key error")
        event_manager.app.logging_manager = MagicMock()
        
        event_data = (0, ('keypress', 'a'), None)
        
        event_manager.execute_event(event_data)
        
        event_manager.app.logging_manager.log_message.assert_called()
    
    def test_execute_event_keypress_with_color_module(self, event_manager):
        """测试颜色模块按键事件"""
        event_manager.app.color_groups = [{
            'delay_min': MagicMock(),
            'delay_max': MagicMock()
        }]
        event_manager.app.color_groups[0]['delay_min'].get.return_value = "100"
        event_manager.app.color_groups[0]['delay_max'].get.return_value = "200"
        event_manager.app.input_controller = MagicMock()
        event_manager.app.logging_manager = MagicMock()
        
        event_data = (-2, ('keypress', 'a'), ('color', 0))
        
        event_manager.execute_event(event_data)
        
        event_manager.app.input_controller.key_down.assert_called()
