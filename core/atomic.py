import threading


class AtomicBool:
    """原子布尔值，线程安全的状态检查"""
    
    __slots__ = ['_value', '_lock']
    
    def __init__(self, value: bool = False):
        self._value = value
        self._lock = threading.Lock()
    
    def get(self) -> bool:
        with self._lock:
            return self._value
    
    def set(self, value: bool) -> None:
        with self._lock:
            self._value = value
    
    def __bool__(self) -> bool:
        return self.get()


class AtomicInt:
    """原子整数，线程安全的计数器"""
    
    __slots__ = ['_value', '_lock']
    
    def __init__(self, value: int = 0):
        self._value = value
        self._lock = threading.Lock()
    
    def get(self) -> int:
        with self._lock:
            return self._value
    
    def set(self, value: int) -> None:
        with self._lock:
            self._value = value
    
    def increment(self, delta: int = 1) -> int:
        with self._lock:
            self._value += delta
            return self._value
    
    def decrement(self, delta: int = 1) -> int:
        with self._lock:
            self._value -= delta
            return self._value
    
    def __int__(self) -> int:
        return self.get()


class AppState:
    """
    应用状态管理器
    使用原子变量替代锁保护的状态变量，减少锁竞争
    """
    
    def __init__(self):
        self._is_running = AtomicBool(False)
        self._is_paused = AtomicBool(False)
    
    @property
    def is_running(self) -> bool:
        return self._is_running.get()
    
    @is_running.setter
    def is_running(self, value: bool) -> None:
        self._is_running.set(value)
    
    @property
    def is_paused(self) -> bool:
        return self._is_paused.get()
    
    @is_paused.setter
    def is_paused(self, value: bool) -> None:
        self._is_paused.set(value)
    
    def check_running(self) -> bool:
        return self._is_running.get()
    
    def check_paused(self) -> bool:
        return self._is_paused.get()
    
    def set_running(self, value: bool) -> None:
        self._is_running.set(value)
    
    def set_paused(self, value: bool) -> None:
        self._is_paused.set(value)
