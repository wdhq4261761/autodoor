"""
行为树节点定义

包含所有节点类型的实现：
- Node: 抽象基类
- CompositeNode: 组合节点基类
- DecoratorNode: 装饰节点基类
- ConditionNode: 条件节点基类
- ActionNode: 动作节点基类
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .context import ExecutionContext


class NodeStatus(Enum):
    """节点执行状态"""
    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"
    ABORTED = "aborted"


class Node(ABC):
    """节点抽象基类"""
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        self.node_id = node_id
        self.config = config or {}
        self.name = self.config.get("name", "")
        self.description = self.config.get("description", "")
        self.enabled = self.config.get("enabled", True)
        self._status = NodeStatus.SUCCESS
    
    @property
    def status(self) -> NodeStatus:
        """获取节点当前状态"""
        return self._status
    
    @status.setter
    def status(self, value: NodeStatus):
        """设置节点状态"""
        self._status = value
    
    @abstractmethod
    def tick(self, context: "ExecutionContext") -> NodeStatus:
        """
        执行节点逻辑
        
        Args:
            context: 执行上下文
            
        Returns:
            节点执行状态
        """
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """重置节点状态"""
        pass
    
    @abstractmethod
    def get_children(self) -> List["Node"]:
        """获取子节点列表"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "id": self.node_id,
            "type": self.__class__.__name__,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "config": self.config,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Node":
        """从字典反序列化"""
        node_type = data.get("type", "")
        node_class = NODE_TYPE_MAP.get(node_type, Node)
        return node_class(
            node_id=data["id"],
            config={
                "name": data.get("name", ""),
                "description": data.get("description", ""),
                "enabled": data.get("enabled", True),
                **data.get("config", {})
            }
        )


class CompositeNode(Node):
    """组合节点基类 - 包含多个子节点"""
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.children: List[Node] = []
        self._current_index = 0
    
    def get_children(self) -> List[Node]:
        """获取子节点列表"""
        return self.children
    
    def add_child(self, child: Node) -> None:
        """添加子节点"""
        self.children.append(child)
    
    def remove_child(self, child_id: str) -> None:
        """移除子节点"""
        self.children = [c for c in self.children if c.node_id != child_id]
    
    def clear_children(self) -> None:
        """清空所有子节点"""
        self.children.clear()
    
    def reset(self) -> None:
        """重置节点状态"""
        self._current_index = 0
        self._status = NodeStatus.SUCCESS
        for child in self.children:
            child.reset()
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        data = super().to_dict()
        data["children"] = [child.to_dict() for child in self.children]
        return data


class DecoratorNode(Node):
    """装饰节点基类 - 修饰单个子节点"""
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.child: Optional[Node] = None
    
    def get_children(self) -> List[Node]:
        """获取子节点列表"""
        return [self.child] if self.child else []
    
    def set_child(self, child: Node) -> None:
        """设置子节点"""
        self.child = child
    
    def remove_child(self, child_id: str) -> None:
        """移除子节点"""
        if self.child and self.child.node_id == child_id:
            self.child = None
    
    def reset(self) -> None:
        """重置节点状态"""
        self._status = NodeStatus.SUCCESS
        if self.child:
            self.child.reset()
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        data = super().to_dict()
        if self.child:
            data["child"] = self.child.to_dict()
        return data


class ConditionNode(Node):
    """条件节点基类 - 检查条件是否满足"""
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
    
    def get_children(self) -> List[Node]:
        """条件节点无子节点"""
        return []
    
    def reset(self) -> None:
        """重置节点状态"""
        self._status = NodeStatus.SUCCESS


class ActionNode(Node):
    """动作节点基类 - 执行具体操作"""
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
    
    def get_children(self) -> List[Node]:
        """动作节点无子节点"""
        return []
    
    def reset(self) -> None:
        """重置节点状态"""
        self._status = NodeStatus.SUCCESS


class SequenceNode(CompositeNode):
    """
    顺序节点
    
    按顺序依次执行子节点：
    - 所有子节点成功才返回成功
    - 任一子节点失败立即返回失败
    - 子节点返回 RUNNING 时记录位置并返回 RUNNING
    """
    
    def tick(self, context: "ExecutionContext") -> NodeStatus:
        if not self.enabled:
            return NodeStatus.SUCCESS
        
        if not self.children:
            return NodeStatus.SUCCESS
        
        while self._current_index < len(self.children):
            child = self.children[self._current_index]
            
            if not child.enabled:
                self._current_index += 1
                continue
            
            status = child.tick(context)
            self._status = status
            
            if status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
            
            if status == NodeStatus.FAILURE:
                return NodeStatus.FAILURE
            
            self._current_index += 1
        
        return NodeStatus.SUCCESS
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        return data


class SelectorNode(CompositeNode):
    """
    选择节点
    
    按顺序依次执行子节点：
    - 任一子节点成功立即返回成功
    - 所有子节点失败才返回失败
    - 子节点返回 RUNNING 时记录位置并返回 RUNNING
    """
    
    def tick(self, context: "ExecutionContext") -> NodeStatus:
        if not self.enabled:
            return NodeStatus.FAILURE
        
        if not self.children:
            return NodeStatus.FAILURE
        
        while self._current_index < len(self.children):
            child = self.children[self._current_index]
            
            if not child.enabled:
                self._current_index += 1
                continue
            
            status = child.tick(context)
            self._status = status
            
            if status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
            
            if status == NodeStatus.SUCCESS:
                return NodeStatus.SUCCESS
            
            self._current_index += 1
        
        return NodeStatus.FAILURE


class ParallelNode(CompositeNode):
    """
    并行节点
    
    同时执行所有子节点：
    - RequireAll: 所有子节点成功才成功
    - RequireOne: 任一子节点成功即成功
    """
    
    SUCCESS_POLICY_ALL = "require_all"
    SUCCESS_POLICY_ONE = "require_one"
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.success_policy = self.config.get("success_policy", self.SUCCESS_POLICY_ALL)
        self._running_children: List[int] = []
    
    def tick(self, context: "ExecutionContext") -> NodeStatus:
        if not self.enabled:
            return NodeStatus.SUCCESS
        
        if not self.children:
            return NodeStatus.SUCCESS
        
        success_count = 0
        failure_count = 0
        running_count = 0
        
        for i, child in enumerate(self.children):
            if not child.enabled:
                continue
            
            status = child.tick(context)
            
            if status == NodeStatus.SUCCESS:
                success_count += 1
            elif status == NodeStatus.FAILURE:
                failure_count += 1
            elif status == NodeStatus.RUNNING:
                running_count += 1
        
        if running_count > 0:
            self._status = NodeStatus.RUNNING
            return NodeStatus.RUNNING
        
        if self.success_policy == self.SUCCESS_POLICY_ALL:
            result = NodeStatus.SUCCESS if success_count == len([c for c in self.children if c.enabled]) else NodeStatus.FAILURE
        else:
            result = NodeStatus.SUCCESS if success_count > 0 else NodeStatus.FAILURE
        
        self._status = result
        return result
    
    def reset(self) -> None:
        super().reset()
        self._running_children.clear()


class InverterNode(DecoratorNode):
    """
    取反节点
    
    反转子节点的执行结果：
    - SUCCESS → FAILURE
    - FAILURE → SUCCESS
    - RUNNING → RUNNING
    """
    
    def tick(self, context: "ExecutionContext") -> NodeStatus:
        if not self.enabled:
            return NodeStatus.SUCCESS
        
        if not self.child:
            return NodeStatus.FAILURE
        
        status = self.child.tick(context)
        
        if status == NodeStatus.SUCCESS:
            self._status = NodeStatus.FAILURE
            return NodeStatus.FAILURE
        elif status == NodeStatus.FAILURE:
            self._status = NodeStatus.SUCCESS
            return NodeStatus.SUCCESS
        else:
            self._status = NodeStatus.RUNNING
            return NodeStatus.RUNNING


class RepeaterNode(DecoratorNode):
    """
    重复节点
    
    重复执行子节点指定次数：
    - count > 0: 重复指定次数
    - count == -1: 无限重复
    - 子节点失败时停止
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.repeat_count = self.config.get("count", -1)
        self._current_count = 0
    
    def tick(self, context: "ExecutionContext") -> NodeStatus:
        if not self.enabled:
            return NodeStatus.SUCCESS
        
        if not self.child:
            return NodeStatus.FAILURE
        
        if self.repeat_count == -1:
            status = self.child.tick(context)
            self._status = status
            if status == NodeStatus.FAILURE:
                return NodeStatus.FAILURE
            if status == NodeStatus.SUCCESS:
                self.child.reset()
            return NodeStatus.RUNNING
        
        while self._current_count < self.repeat_count:
            status = self.child.tick(context)
            self._status = status
            
            if status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
            
            if status == NodeStatus.FAILURE:
                return NodeStatus.FAILURE
            
            self._current_count += 1
            self.child.reset()
        
        return NodeStatus.SUCCESS
    
    def reset(self) -> None:
        super().reset()
        self._current_count = 0


class RetryNode(DecoratorNode):
    """
    重试节点
    
    子节点失败时重试指定次数
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.max_retries = self.config.get("max_retries", 3)
        self._retry_count = 0
    
    def tick(self, context: "ExecutionContext") -> NodeStatus:
        if not self.enabled:
            return NodeStatus.SUCCESS
        
        if not self.child:
            return NodeStatus.FAILURE
        
        while self._retry_count <= self.max_retries:
            status = self.child.tick(context)
            self._status = status
            
            if status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
            
            if status == NodeStatus.SUCCESS:
                return NodeStatus.SUCCESS
            
            self._retry_count += 1
            self.child.reset()
        
        return NodeStatus.FAILURE
    
    def reset(self) -> None:
        super().reset()
        self._retry_count = 0


class TimeoutNode(DecoratorNode):
    """
    超时节点
    
    限制子节点的执行时间
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.timeout_ms = self.config.get("timeout_ms", 5000)
        self._start_time: Optional[float] = None
    
    def tick(self, context: "ExecutionContext") -> NodeStatus:
        if not self.enabled:
            return NodeStatus.SUCCESS
        
        if not self.child:
            return NodeStatus.FAILURE
        
        import time
        
        if self._start_time is None:
            self._start_time = time.time() * 1000
        
        elapsed = time.time() * 1000 - self._start_time
        
        if elapsed >= self.timeout_ms:
            self._status = NodeStatus.FAILURE
            return NodeStatus.FAILURE
        
        status = self.child.tick(context)
        self._status = status
        return status
    
    def reset(self) -> None:
        super().reset()
        self._start_time = None


NODE_TYPE_MAP: Dict[str, type] = {
    "SequenceNode": SequenceNode,
    "SelectorNode": SelectorNode,
    "ParallelNode": ParallelNode,
    "InverterNode": InverterNode,
    "RepeaterNode": RepeaterNode,
    "RetryNode": RetryNode,
    "TimeoutNode": TimeoutNode,
    "CompositeNode": CompositeNode,
    "DecoratorNode": DecoratorNode,
    "ConditionNode": ConditionNode,
    "ActionNode": ActionNode,
    "OCRConditionNode": OCRConditionNode,
    "ImageConditionNode": ImageConditionNode,
    "ColorConditionNode": ColorConditionNode,
    "NumberConditionNode": NumberConditionNode,
    "KeyPressNode": KeyPressNode,
    "MouseClickNode": MouseClickNode,
    "DelayNode": DelayNode,
}
