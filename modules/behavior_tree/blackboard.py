"""
黑板系统

提供节点间数据共享能力
"""

from typing import Any, Dict, List, Callable, Optional


class Blackboard:
    """
    黑板 - 节点间数据共享存储
    
    支持功能：
    - 变量读写
    - 变量变化订阅
    - 内置变量
    """
    
    BUILTIN_VARS = {
        "last_ocr_position": None,
        "last_image_position": None,
        "last_color_position": None,
        "last_number_value": None,
        "execution_count": 0,
    }
    
    def __init__(self):
        self._data: Dict[str, Any] = dict(self.BUILTIN_VARS)
        self._callbacks: Dict[str, List[Callable]] = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取变量
        
        Args:
            key: 变量名
            default: 默认值
            
        Returns:
            变量值，不存在则返回默认值
        """
        return self._data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        设置变量
        
        Args:
            key: 变量名
            value: 变量值
        """
        old_value = self._data.get(key)
        self._data[key] = value
        self._notify_change(key, old_value, value)
    
    def has(self, key: str) -> bool:
        """检查变量是否存在"""
        return key in self._data
    
    def delete(self, key: str) -> None:
        """删除变量"""
        if key in self._data and key not in self.BUILTIN_VARS:
            old_value = self._data[key]
            del self._data[key]
            self._notify_change(key, old_value, None)
    
    def clear(self) -> None:
        """清空所有用户变量（保留内置变量）"""
        user_vars = [k for k in self._data if k not in self.BUILTIN_VARS]
        for key in user_vars:
            self.delete(key)
    
    def increment(self, key: str, amount: int = 1) -> int:
        """
        递增变量
        
        Args:
            key: 变量名
            amount: 递增量
            
        Returns:
            递增后的值
        """
        current = self.get(key, 0)
        if isinstance(current, (int, float)):
            new_value = current + amount
            self.set(key, new_value)
            return new_value
        return current
    
    def subscribe(self, key: str, callback: Callable[[str, Any, Any], None]) -> None:
        """
        订阅变量变化
        
        Args:
            key: 变量名
            callback: 回调函数 (key, old_value, new_value)
        """
        if key not in self._callbacks:
            self._callbacks[key] = []
        self._callbacks[key].append(callback)
    
    def unsubscribe(self, key: str, callback: Callable) -> None:
        """取消订阅"""
        if key in self._callbacks and callback in self._callbacks[key]:
            self._callbacks[key].remove(callback)
    
    def _notify_change(self, key: str, old_value: Any, new_value: Any) -> None:
        """通知变量变化"""
        if key in self._callbacks:
            for callback in self._callbacks[key]:
                try:
                    callback(key, old_value, new_value)
                except Exception:
                    pass
    
    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return self._data.copy()
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """从字典导入"""
        self._data.update(data)
    
    def __repr__(self) -> str:
        return f"Blackboard({self._data})"
