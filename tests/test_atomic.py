import pytest
import threading
import time
from core.atomic import AtomicBool, AtomicInt, AppState


class TestAtomicBool:
    """AtomicBool测试类"""
    
    def test_init_default_value(self):
        """测试默认初始化"""
        ab = AtomicBool()
        assert ab.get() is False
    
    def test_init_true_value(self):
        """测试True初始化"""
        ab = AtomicBool(True)
        assert ab.get() is True
    
    def test_init_false_value(self):
        """测试False初始化"""
        ab = AtomicBool(False)
        assert ab.get() is False
    
    def test_set_true(self):
        """测试设置为True"""
        ab = AtomicBool(False)
        ab.set(True)
        assert ab.get() is True
    
    def test_set_false(self):
        """测试设置为False"""
        ab = AtomicBool(True)
        ab.set(False)
        assert ab.get() is False
    
    def test_bool_conversion_true(self):
        """测试布尔转换True"""
        ab = AtomicBool(True)
        assert bool(ab) is True
    
    def test_bool_conversion_false(self):
        """测试布尔转换False"""
        ab = AtomicBool(False)
        assert bool(ab) is False
    
    def test_thread_safety(self):
        """测试线程安全"""
        ab = AtomicBool(False)
        results = []
        
        def toggle():
            for _ in range(100):
                current = ab.get()
                ab.set(not current)
                results.append(ab.get())
        
        threads = [threading.Thread(target=toggle) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(results) == 1000
    
    def test_concurrent_reads(self):
        """测试并发读取"""
        ab = AtomicBool(True)
        results = []
        
        def read_value():
            for _ in range(100):
                results.append(ab.get())
        
        threads = [threading.Thread(target=read_value) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert all(r is True for r in results)
        assert len(results) == 1000


class TestAtomicInt:
    """AtomicInt测试类"""
    
    def test_init_default_value(self):
        """测试默认初始化"""
        ai = AtomicInt()
        assert ai.get() == 0
    
    def test_init_custom_value(self):
        """测试自定义初始化"""
        ai = AtomicInt(42)
        assert ai.get() == 42
    
    def test_set_value(self):
        """测试设置值"""
        ai = AtomicInt(0)
        ai.set(100)
        assert ai.get() == 100
    
    def test_increment_default(self):
        """测试默认增量"""
        ai = AtomicInt(0)
        result = ai.increment()
        assert result == 1
        assert ai.get() == 1
    
    def test_increment_custom_delta(self):
        """测试自定义增量"""
        ai = AtomicInt(0)
        result = ai.increment(5)
        assert result == 5
        assert ai.get() == 5
    
    def test_decrement_default(self):
        """测试默认减量"""
        ai = AtomicInt(10)
        result = ai.decrement()
        assert result == 9
        assert ai.get() == 9
    
    def test_decrement_custom_delta(self):
        """测试自定义减量"""
        ai = AtomicInt(10)
        result = ai.decrement(3)
        assert result == 7
        assert ai.get() == 7
    
    def test_int_conversion(self):
        """测试整数转换"""
        ai = AtomicInt(42)
        assert int(ai) == 42
    
    def test_thread_safety_increment(self):
        """测试线程安全增量"""
        ai = AtomicInt(0)
        
        def increment():
            for _ in range(100):
                ai.increment()
        
        threads = [threading.Thread(target=increment) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert ai.get() == 1000
    
    def test_thread_safety_decrement(self):
        """测试线程安全减量"""
        ai = AtomicInt(1000)
        
        def decrement():
            for _ in range(100):
                ai.decrement()
        
        threads = [threading.Thread(target=decrement) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert ai.get() == 0


class TestAppState:
    """AppState测试类"""
    
    def test_init_default_values(self):
        """测试默认初始化"""
        state = AppState()
        assert state.is_running is False
        assert state.is_paused is False
    
    def test_is_running_property(self):
        """测试is_running属性"""
        state = AppState()
        state.is_running = True
        assert state.is_running is True
        state.is_running = False
        assert state.is_running is False
    
    def test_is_paused_property(self):
        """测试is_paused属性"""
        state = AppState()
        state.is_paused = True
        assert state.is_paused is True
        state.is_paused = False
        assert state.is_paused is False
    
    def test_check_running(self):
        """测试check_running方法"""
        state = AppState()
        assert state.check_running() is False
        state.set_running(True)
        assert state.check_running() is True
    
    def test_check_paused(self):
        """测试check_paused方法"""
        state = AppState()
        assert state.check_paused() is False
        state.set_paused(True)
        assert state.check_paused() is True
    
    def test_set_running(self):
        """测试set_running方法"""
        state = AppState()
        state.set_running(True)
        assert state.is_running is True
    
    def test_set_paused(self):
        """测试set_paused方法"""
        state = AppState()
        state.set_paused(True)
        assert state.is_paused is True
    
    def test_concurrent_access(self):
        """测试并发访问"""
        state = AppState()
        results = []
        
        def toggle_running():
            for _ in range(100):
                current = state.is_running
                state.is_running = not current
                results.append(state.is_running)
        
        threads = [threading.Thread(target=toggle_running) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(results) == 500
