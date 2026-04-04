"""
输入控制器抽象基类
定义统一的输入接口规范
"""
from abc import ABC, abstractmethod
from typing import Optional, Tuple


class BaseInputController(ABC):
    """输入控制器抽象基类"""
    
    @abstractmethod
    def key_down(self, key: str, priority: int = 0) -> bool:
        """
        按下按键
        
        Args:
            key: 按键名称（如 'q', 'w', 'space'）
            priority: 优先级（用于锁竞争）
        
        Returns:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    def key_up(self, key: str, priority: int = 0) -> bool:
        """
        释放按键
        
        Args:
            key: 按键名称
            priority: 优先级
        
        Returns:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    def press_key(self, key: str, delay: float = 0, priority: int = 0) -> bool:
        """
        单次按键（按下并释放）
        
        Args:
            key: 按键名称
            delay: 按键间隔
            priority: 优先级
        
        Returns:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    def mouse_move(self, x: int, y: int) -> bool:
        """移动鼠标到绝对坐标"""
        pass
    
    @abstractmethod
    def mouse_move_relative(self, dx: int, dy: int) -> bool:
        """相对移动鼠标"""
        pass
    
    @abstractmethod
    def mouse_click(self, button: str = 'left') -> bool:
        """鼠标点击"""
        pass
    
    @abstractmethod
    def mouse_down(self, button: str = 'left') -> bool:
        """鼠标按下"""
        pass
    
    @abstractmethod
    def mouse_up(self, button: str = 'left') -> bool:
        """鼠标释放"""
        pass
    
    @abstractmethod
    def mouse_scroll(self, clicks: int) -> bool:
        """鼠标滚轮"""
        pass
    
    @property
    @abstractmethod
    def method_name(self) -> str:
        """返回输入方式名称"""
        pass
    
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """返回当前输入方式是否可用"""
        pass
