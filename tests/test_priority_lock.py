import pytest
import threading
import time
from core.priority_lock import PriorityLock, get_module_priority, MODULE_PRIORITIES


class TestPriorityLock:
    """PriorityLock测试类"""
    
    def test_init(self):
        """测试初始化"""
        lock = PriorityLock()
        assert lock.locked() is False
    
    def test_acquire_release(self):
        """测试获取和释放锁"""
        lock = PriorityLock()
        
        with lock.acquire(priority=0):
            assert lock.locked() is True
        
        assert lock.locked() is False
    
    def test_locked_status(self):
        """测试锁定状态"""
        lock = PriorityLock()
        assert lock.locked() is False
        
        lock._acquire(0)
        assert lock.locked() is True
        
        lock._release()
        assert lock.locked() is False
    
    def test_priority_order(self):
        """测试优先级顺序"""
        lock = PriorityLock()
        results = []
        
        def low_priority():
            with lock.acquire(priority=1):
                results.append("low")
        
        def high_priority():
            with lock.acquire(priority=10):
                results.append("high")
        
        lock._acquire(0)
        
        t1 = threading.Thread(target=low_priority)
        t2 = threading.Thread(target=high_priority)
        
        t1.start()
        time.sleep(0.01)
        t2.start()
        time.sleep(0.01)
        
        lock._release()
        
        t1.join()
        t2.join()
        
        assert results == ["high", "low"]
    
    def test_same_priority_fifo(self):
        """测试相同优先级的FIFO顺序"""
        lock = PriorityLock()
        results = []
        
        def worker(name):
            with lock.acquire(priority=5):
                results.append(name)
        
        lock._acquire(0)
        
        threads = [threading.Thread(target=worker, args=(f"t{i}",)) for i in range(5)]
        for t in threads:
            t.start()
            time.sleep(0.01)
        
        lock._release()
        
        for t in threads:
            t.join()
        
        assert results == ["t0", "t1", "t2", "t3", "t4"]
    
    def test_context_manager(self):
        """测试上下文管理器"""
        lock = PriorityLock()
        
        with lock.acquire(priority=5) as ctx:
            assert lock.locked() is True
            assert ctx is not None
        
        assert lock.locked() is False
    
    def test_concurrent_access(self):
        """测试并发访问"""
        lock = PriorityLock()
        counter = [0]
        
        def increment():
            with lock.acquire(priority=1):
                temp = counter[0]
                time.sleep(0.001)
                counter[0] = temp + 1
        
        threads = [threading.Thread(target=increment) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert counter[0] == 10


class TestModulePriorities:
    """模块优先级测试类"""
    
    def test_number_priority(self):
        """测试数字识别优先级"""
        assert get_module_priority('number') == 5
    
    def test_timed_priority(self):
        """测试定时功能优先级"""
        assert get_module_priority('timed') == 4
    
    def test_ocr_priority(self):
        """测试OCR优先级"""
        assert get_module_priority('ocr') == 3
    
    def test_color_priority(self):
        """测试颜色识别优先级"""
        assert get_module_priority('color') == 2
    
    def test_script_priority(self):
        """测试脚本优先级"""
        assert get_module_priority('script') == 1
    
    def test_unknown_module_priority(self):
        """测试未知模块优先级"""
        assert get_module_priority('unknown') == 0
    
    def test_module_priorities_order(self):
        """测试模块优先级顺序"""
        assert MODULE_PRIORITIES['number'] > MODULE_PRIORITIES['timed']
        assert MODULE_PRIORITIES['timed'] > MODULE_PRIORITIES['ocr']
        assert MODULE_PRIORITIES['ocr'] > MODULE_PRIORITIES['color']
        assert MODULE_PRIORITIES['color'] > MODULE_PRIORITIES['script']
