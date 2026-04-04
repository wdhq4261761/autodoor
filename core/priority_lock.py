import threading
import heapq
from typing import Optional


class PriorityLock:
    """
    优先级锁实现
    
    确保高优先级的请求优先获取锁。
    优先级数值越大，优先级越高。
    支持超时机制，防止死锁。
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self._waiters = []
        self._sequence = 0
        self._locked = False
    
    def acquire(self, priority: int = 0, timeout: Optional[float] = None):
        """获取锁，返回上下文管理器
        
        Args:
            priority: 优先级，数值越大优先级越高
            timeout: 超时时间（秒），None 表示无限等待
        
        Returns:
            _PriorityLockContext: 上下文管理器，可通过 .acquired 属性检查是否成功获取锁
        """
        return _PriorityLockContext(self, priority, timeout)
    
    def _acquire(self, priority: int, timeout: Optional[float] = None) -> bool:
        """内部获取锁方法
        
        Args:
            priority: 优先级
            timeout: 超时时间（秒），None 表示无限等待
        
        Returns:
            bool: 是否成功获取锁
        """
        event = None
        entry = None
        
        with self._lock:
            if not self._locked and not self._waiters:
                self._locked = True
                return True
            
            self._sequence += 1
            event = threading.Event()
            entry = [-priority, self._sequence, event]
            heapq.heappush(self._waiters, entry)
        
        acquired = event.wait(timeout=timeout)
        
        if not acquired:
            with self._lock:
                try:
                    self._waiters.remove(entry)
                    heapq.heapify(self._waiters)
                except ValueError:
                    acquired = True
        
        return acquired
    
    def _release(self) -> None:
        """内部释放锁方法"""
        with self._lock:
            if not self._waiters:
                self._locked = False
                return
            
            _, _, event = heapq.heappop(self._waiters)
            event.set()
    
    def locked(self) -> bool:
        """检查锁是否被持有"""
        return self._locked


class _PriorityLockContext:
    """优先级锁上下文管理器"""
    
    def __init__(self, lock: PriorityLock, priority: int, timeout: Optional[float] = None):
        self._lock = lock
        self._priority = priority
        self._timeout = timeout
        self.acquired = False
    
    def __enter__(self):
        self.acquired = self._lock._acquire(self._priority, self._timeout)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.acquired:
            self._lock._release()
        return False


MODULE_PRIORITIES = {
    'number': 6,
    'timed': 5,
    'image': 4,
    'ocr': 3,
    'color': 2,
    'background': 1,
    'script': 1,
}


def get_module_priority(module_name: str) -> int:
    """获取模块的默认优先级"""
    return MODULE_PRIORITIES.get(module_name, 0)
