import pytest
import time
import threading
import queue
from unittest.mock import MagicMock, patch
from core.events import EventManager


class TestEventManager:
    """EventManager测试类"""
    
    @pytest.fixture
    def event_manager(self, mock_app):
        return EventManager(mock_app)
    
    def test_init(self, event_manager):
        """测试初始化"""
        assert event_manager.event_queue is not None
        assert event_manager.is_event_running is False
    
    def test_start_event_thread(self, event_manager):
        """测试启动事件线程"""
        event_manager.start_event_thread()
        
        assert event_manager.is_event_running is True
        assert event_manager.event_thread is not None
        
        event_manager.is_event_running = False
        if event_manager.event_thread and event_manager.event_thread.is_alive():
            event_manager.event_thread.join(timeout=2)
    
    def test_add_event(self, event_manager):
        """测试添加事件"""
        event = ("keypress", {"key": "a"})
        
        event_manager.add_event(event, module_info=("script", 0), priority=5)
        
        assert event_manager.event_queue.qsize() == 1
    
    def test_add_event_with_priority(self, event_manager):
        """测试带优先级添加事件"""
        event1 = ("keypress", {"key": "a"})
        event2 = ("keypress", {"key": "b"})
        
        event_manager.add_event(event1, priority=5)
        event_manager.add_event(event2, priority=10)
        
        assert event_manager.event_queue.qsize() == 2
    
    def test_clear_events(self, event_manager):
        """测试清空事件队列"""
        event = ("keypress", {"key": "a"})
        
        event_manager.add_event(event, priority=5)
        event_manager.add_event(event, priority=5)
        
        event_manager.clear_events()
        
        assert event_manager.event_queue.qsize() == 0


class TestEventProcessing:
    """事件处理测试"""
    
    @pytest.fixture
    def event_manager(self, mock_app):
        return EventManager(mock_app)
    
    def test_process_single_event(self, event_manager):
        """测试处理单个事件"""
        event = ("keypress", {"key": "a"})
        
        event_manager.add_event(event, priority=5)
        
        assert event_manager.event_queue.qsize() == 1
    
    def test_process_multiple_events(self, event_manager):
        """测试处理多个事件"""
        for i in range(5):
            event = ("keypress", f"key{i}")
            event_manager.add_event(event, priority=5)
        
        assert event_manager.event_queue.qsize() == 5
    
    def test_priority_order(self, event_manager):
        """测试优先级顺序"""
        event1 = ("keypress", {"key": "a"})
        event2 = ("keypress", {"key": "b"})
        event3 = ("keypress", {"key": "c"})
        
        event_manager.add_event(event1, priority=1)
        event_manager.add_event(event2, priority=10)
        event_manager.add_event(event3, priority=5)
        
        first_event = event_manager.event_queue.get()
        
        assert first_event[0] == -10


class TestEventQueue:
    """事件队列测试"""
    
    def test_priority_queue_order(self):
        """测试优先级队列顺序"""
        pq = queue.PriorityQueue()
        
        pq.put((-10, "event2", None))
        pq.put((-5, "event1", None))
        pq.put((-1, "event3", None))
        
        first = pq.get()
        second = pq.get()
        third = pq.get()
        
        assert first[0] == -10
        assert second[0] == -5
        assert third[0] == -1
    
    def test_queue_size(self):
        """测试队列大小"""
        pq = queue.PriorityQueue()
        
        assert pq.qsize() == 0
        
        pq.put((-5, "event", None))
        
        assert pq.qsize() == 1
        
        pq.get()
        
        assert pq.qsize() == 0
