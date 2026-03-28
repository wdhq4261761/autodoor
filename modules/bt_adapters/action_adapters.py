"""
动作节点适配器

将输入操作封装为行为树动作节点
"""

from typing import Any, Dict, Optional, TYPE_CHECKING

from modules.behavior_tree.nodes import ActionNode, NodeStatus

if TYPE_CHECKING:
    from modules.behavior_tree.context import ExecutionContext


class KeyPressNode(ActionNode):
    """
    按键动作节点
    
    执行按键操作
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.key = self.config.get("key", "")
        self.action = self.config.get("action", "press")
        self.duration = self.config.get("duration", 0)
    
    def tick(self, context: "ExecutionContext") -> NodeStatus:
        """
        执行按键操作
        
        Args:
            context: 执行上下文
            
        Returns:
            执行结果状态
        """
        if not self.enabled:
            return NodeStatus.SUCCESS
        
        if not context.check_running():
            return NodeStatus.ABORTED
        
        if not self.key:
            context.log(f"按键节点 {self.name}: 未配置按键")
            self._status = NodeStatus.FAILURE
            return NodeStatus.FAILURE
        
        try:
            success = context.execute_key_press(self.key, self.action, self.duration)
            
            if success:
                context.log(f"按键节点 {self.name}: 执行按键 {self.key}")
                self._status = NodeStatus.SUCCESS
                return NodeStatus.SUCCESS
            else:
                context.log(f"按键节点 {self.name}: 按键执行失败")
                self._status = NodeStatus.FAILURE
                return NodeStatus.FAILURE
                
        except Exception as e:
            context.log(f"按键节点 {self.name}: 执行出错 - {e}")
            self._status = NodeStatus.FAILURE
            return NodeStatus.FAILURE
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"] = {
            **self.config,
            "key": self.key,
            "action": self.action,
            "duration": self.duration,
        }
        return data


class MouseClickNode(ActionNode):
    """
    鼠标点击动作节点
    
    执行鼠标点击操作
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.button = self.config.get("button", "left")
        self.position = self.config.get("position")
        self.use_blackboard = self.config.get("use_blackboard", False)
        self.position_key = self.config.get("position_key", "last_ocr_position")
    
    def tick(self, context: "ExecutionContext") -> NodeStatus:
        """
        执行鼠标点击
        
        Args:
            context: 执行上下文
            
        Returns:
            执行结果状态
        """
        if not self.enabled:
            return NodeStatus.SUCCESS
        
        if not context.check_running():
            return NodeStatus.ABORTED
        
        try:
            click_position = self.position
            
            if self.use_blackboard:
                click_position = context.blackboard.get(self.position_key)
            
            success = context.execute_mouse_click(self.button, click_position)
            
            if success:
                pos_str = click_position if click_position else "当前位置"
                context.log(f"鼠标节点 {self.name}: 执行点击 {self.button} @ {pos_str}")
                self._status = NodeStatus.SUCCESS
                return NodeStatus.SUCCESS
            else:
                context.log(f"鼠标节点 {self.name}: 点击执行失败")
                self._status = NodeStatus.FAILURE
                return NodeStatus.FAILURE
                
        except Exception as e:
            context.log(f"鼠标节点 {self.name}: 执行出错 - {e}")
            self._status = NodeStatus.FAILURE
            return NodeStatus.FAILURE
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"] = {
            **self.config,
            "button": self.button,
            "position": self.position,
            "use_blackboard": self.use_blackboard,
            "position_key": self.position_key,
        }
        return data


class DelayNode(ActionNode):
    """
    延时动作节点
    
    执行延时操作
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.duration_ms = self.config.get("duration_ms", 1000)
    
    def tick(self, context: "ExecutionContext") -> NodeStatus:
        """
        执行延时
        
        Args:
            context: 执行上下文
            
        Returns:
            执行结果状态
        """
        if not self.enabled:
            return NodeStatus.SUCCESS
        
        if not context.check_running():
            return NodeStatus.ABORTED
        
        try:
            context.log(f"延时节点 {self.name}: 延时 {self.duration_ms}ms")
            context.execute_delay(self.duration_ms)
            self._status = NodeStatus.SUCCESS
            return NodeStatus.SUCCESS
        except Exception as e:
            context.log(f"延时节点 {self.name}: 执行出错 - {e}")
            self._status = NodeStatus.FAILURE
            return NodeStatus.FAILURE
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"] = {
            **self.config,
            "duration_ms": self.duration_ms,
        }
        return data
