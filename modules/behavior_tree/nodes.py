"""
行为树节点定义

包含所有节点类型的实现：
- Node: 抽象基类
- CompositeNode: 组合节点基类（含重试、重复、超时装饰参数）
- ConditionNode: 条件节点基类（含取反、重试装饰参数）
- ActionNode: 动作节点基类（含重复、超时装饰参数）
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional, Dict, Any, TYPE_CHECKING
import time

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
    
    def update_config(self, key: str, value: Any) -> None:
        """
        更新配置参数并同步实例属性
        
        Args:
            key: 配置键名
            value: 配置值
        """
        if self.config is None:
            self.config = {}
        self.config[key] = value
        
        if hasattr(self, key):
            try:
                setattr(self, key, value)
            except (AttributeError, TypeError) as e:
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
    """组合节点基类 - 包含多个子节点，支持重试、重复、超时装饰参数"""
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.children: List[Node] = []
        self._current_index = 0
        self.retry_count = self.config.get("retry_count", 0)
        self.repeat_count = self.config.get("repeat_count", 1)
        self.timeout_ms = self.config.get("timeout_ms", 0)
        self.child_interval = self.config.get("child_interval", 0)
        self.continue_on_failure = self.config.get("continue_on_failure", False)
        self._current_retry = 0
        self._current_repeat = 0
        self._start_time: Optional[float] = None
        self._last_child_finish_time: Optional[float] = None
        self._has_failure: bool = False
    
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
    
    def _reset_children(self) -> None:
        """重置所有子节点"""
        for child in self.children:
            child.reset()
    
    def tick(self, context: "ExecutionContext") -> NodeStatus:
        """执行组合节点逻辑，包含重试、重复、超时装饰
        
        新规格：
        1. 当组合节点判定通过时，首先立刻结束当前运行的所有子节点
        2. 然后根据重复次数检查是否要重复进行当前节点
        3. 如果需要则从头重复进行
        4. 如果不需要则立刻完成当前节点
        """
        if not self.enabled:
            return NodeStatus.SUCCESS
        
        if not context.check_running():
            return NodeStatus.ABORTED
        
        if self._status != NodeStatus.RUNNING:
            context.notify_node_status(self.node_id, "running")
        
        if self.timeout_ms > 0:
            if self._start_time is None:
                self._start_time = time.time() * 1000
            
            elapsed = time.time() * 1000 - self._start_time
            if elapsed >= self.timeout_ms:
                context.log(f"{self.name}: 执行超时")
                self._status = NodeStatus.FAILURE
                context.notify_node_status(self.node_id, "failure")
                return NodeStatus.FAILURE
        
        status = self._execute_composite(context)
        self._status = status
        
        if status == NodeStatus.RUNNING:
            return NodeStatus.RUNNING
        
        if status == NodeStatus.FAILURE:
            if self._current_retry < self.retry_count:
                self._current_retry += 1
                context.log(f"{self.name}: 重试 {self._current_retry}/{self.retry_count}")
                self._reset_children()
                self._current_index = 0
                self._has_failure = False
                return NodeStatus.RUNNING
            self._current_retry = 0
            self._current_repeat = 0
            self._start_time = None
            self._has_failure = False
            context.notify_node_status(self.node_id, "failure")
            return NodeStatus.FAILURE
        
        self._reset_children()
        self._current_index = 0
        self._has_failure = False
        
        if self.repeat_count == -1:
            return NodeStatus.RUNNING
        
        self._current_repeat += 1
        if self._current_repeat < self.repeat_count:
            return NodeStatus.RUNNING
        
        self._current_retry = 0
        self._current_repeat = 0
        self._start_time = None
        self._status = NodeStatus.SUCCESS
        context.notify_node_status(self.node_id, "success")
        return NodeStatus.SUCCESS
    
    def _execute_composite(self, context: "ExecutionContext") -> NodeStatus:
        """子类实现的组合执行逻辑"""
        raise NotImplementedError
    
    def reset(self) -> None:
        """重置节点状态"""
        self._current_index = 0
        self._current_retry = 0
        self._current_repeat = 0
        self._start_time = None
        self._status = NodeStatus.SUCCESS
        self._has_failure = False
        for child in self.children:
            child.reset()
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        data = super().to_dict()
        data["children"] = [child.to_dict() for child in self.children]
        return data


class ConditionNode(Node):
    """条件节点基类 - 检查条件是否满足，支持取反、重试装饰参数，支持子节点串联执行"""
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.invert = self.config.get("invert", False)
        self.retry_count = self.config.get("retry_count", 0)
        self._current_retry = 0
        self.children: List[Node] = []
        self._current_child_index = 0
        self._condition_done = False
    
    def get_children(self) -> List[Node]:
        """获取子节点列表"""
        return self.children
    
    def add_child(self, child: Node) -> None:
        """添加子节点"""
        self.children.append(child)
    
    def remove_child(self, child_id: str) -> None:
        """移除子节点"""
        self.children = [c for c in self.children if c.node_id != child_id]
    
    def tick(self, context: "ExecutionContext") -> NodeStatus:
        """执行条件节点逻辑，包含取反、重试装饰，成功后执行子节点"""
        if not self.enabled:
            return NodeStatus.SUCCESS
        
        if not context.check_running():
            return NodeStatus.ABORTED
        
        if self._status != NodeStatus.RUNNING:
            context.notify_node_status(self.node_id, "running")
        
        if not self._condition_done:
            if self._current_retry > self.retry_count:
                self._current_retry = 0
                self._status = NodeStatus.FAILURE
                context.notify_node_status(self.node_id, "failure")
                return NodeStatus.FAILURE
            
            status = self._execute_condition(context)
            
            if self.invert:
                if status == NodeStatus.SUCCESS:
                    status = NodeStatus.FAILURE
                elif status == NodeStatus.FAILURE:
                    status = NodeStatus.SUCCESS
            
            if status == NodeStatus.RUNNING:
                self._status = status
                return status
            
            if status == NodeStatus.FAILURE:
                self._current_retry += 1
                if self._current_retry <= self.retry_count:
                    context.log(f"{self.name}: 重试 {self._current_retry}/{self.retry_count}")
                    self._reset_for_retry()
                    return NodeStatus.RUNNING
                
                self._current_retry = 0
                self._status = NodeStatus.FAILURE
                context.notify_node_status(self.node_id, "failure")
                return NodeStatus.FAILURE
            
            self._current_retry = 0
            self._condition_done = True
            
            if not self.children:
                self._condition_done = False
                self._status = NodeStatus.SUCCESS
                context.notify_node_status(self.node_id, "success")
                return NodeStatus.SUCCESS
            
            return NodeStatus.RUNNING
        
        while self._current_child_index < len(self.children):
            child = self.children[self._current_child_index]
            
            if not child.enabled:
                self._current_child_index += 1
                continue
            
            status = child.tick(context)
            self._status = status
            
            if status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
            
            if status == NodeStatus.FAILURE:
                context.notify_node_status(self.node_id, "failure")
                return NodeStatus.FAILURE
            
            self._current_child_index += 1
        
        self._current_child_index = 0
        self._condition_done = False
        self._status = NodeStatus.SUCCESS
        context.notify_node_status(self.node_id, "success")
        return NodeStatus.SUCCESS
    
    def _execute_condition(self, context: "ExecutionContext") -> NodeStatus:
        """子类实现的条件检测逻辑"""
        raise NotImplementedError
    
    def _parse_region(self, region_config) -> tuple:
        """
        解析区域配置
        
        Args:
            region_config: 区域配置，支持 None、list、tuple、str 格式
            
        Returns:
            tuple: (x1, y1, x2, y2) 区域坐标
        """
        if region_config is None:
            return (0, 0, 100, 100)
        elif isinstance(region_config, (list, tuple)):
            return tuple(region_config)
        elif isinstance(region_config, str):
            try:
                parts = [int(x.strip()) for x in region_config.split(",")]
                if len(parts) == 4:
                    return tuple(parts)
            except (ValueError, AttributeError):
                pass
        return (0, 0, 100, 100)
    
    def _reset_for_retry(self) -> None:
        """重试时重置状态（保留重试计数器）"""
        self._status = NodeStatus.SUCCESS
        self._current_child_index = 0
        self._condition_done = False
        for child in self.children:
            child.reset()
    
    def reset(self) -> None:
        """重置节点状态"""
        self._current_retry = 0
        self._status = NodeStatus.SUCCESS
        self._current_child_index = 0
        self._condition_done = False
        for child in self.children:
            child.reset()
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        data = super().to_dict()
        if self.children:
            data["children"] = [child.to_dict() for child in self.children]
        return data


class ActionNode(Node):
    """动作节点基类 - 执行具体操作，支持重复、超时装饰参数，支持子节点串联执行"""
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        repeat_val = self.config.get("repeat_count", 1)
        self.repeat_count = repeat_val if repeat_val == -1 else max(1, repeat_val)
        self.timeout_ms = self.config.get("timeout_ms", 0)
        self._current_repeat = 0
        self._start_time: Optional[float] = None
        self.children: List[Node] = []
        self._current_child_index = 0
        self._action_done = False
    
    def get_children(self) -> List[Node]:
        """获取子节点列表"""
        return self.children
    
    def add_child(self, child: Node) -> None:
        """添加子节点"""
        self.children.append(child)
    
    def remove_child(self, child_id: str) -> None:
        """移除子节点"""
        self.children = [c for c in self.children if c.node_id != child_id]
    
    def tick(self, context: "ExecutionContext") -> NodeStatus:
        """执行动作节点逻辑，包含重复、超时装饰，成功后执行子节点"""
        if not self.enabled:
            return NodeStatus.SUCCESS
        
        if not context.check_running():
            return NodeStatus.ABORTED
        
        if self._status != NodeStatus.RUNNING:
            context.notify_node_status(self.node_id, "running")
        
        if self.timeout_ms > 0:
            if self._start_time is None:
                self._start_time = time.time() * 1000
            
            elapsed = time.time() * 1000 - self._start_time
            if elapsed >= self.timeout_ms:
                context.log(f"{self.name}: 执行超时")
                self._status = NodeStatus.FAILURE
                context.notify_node_status(self.node_id, "failure")
                return NodeStatus.FAILURE
        
        if not self._action_done:
            if self.repeat_count == -1:
                status = self._execute_action(context)
                self._status = status
                if status == NodeStatus.SUCCESS:
                    self._action_done = True
                    if self.children:
                        return NodeStatus.RUNNING
                    self._action_done = False
                    return NodeStatus.RUNNING
                if status == NodeStatus.FAILURE:
                    context.notify_node_status(self.node_id, "failure")
                return status
            
            if self._current_repeat >= self.repeat_count:
                self._current_repeat = 0
                self._start_time = None
                self._action_done = True
                if not self.children:
                    self._action_done = False
                    self._status = NodeStatus.SUCCESS
                    context.notify_node_status(self.node_id, "success")
                    return NodeStatus.SUCCESS
                return NodeStatus.RUNNING
            
            status = self._execute_action(context)
            self._status = status
            
            if status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
            
            if status == NodeStatus.FAILURE:
                self._current_repeat = 0
                self._start_time = None
                context.notify_node_status(self.node_id, "failure")
                return NodeStatus.FAILURE
            
            self._current_repeat += 1
            if self._current_repeat < self.repeat_count:
                self._start_time = None
                return NodeStatus.RUNNING
            
            self._current_repeat = 0
            self._start_time = None
            self._action_done = True
            if not self.children:
                self._action_done = False
                self._status = NodeStatus.SUCCESS
                context.notify_node_status(self.node_id, "success")
                return NodeStatus.SUCCESS
            return NodeStatus.RUNNING
        
        while self._current_child_index < len(self.children):
            child = self.children[self._current_child_index]
            
            if not child.enabled:
                self._current_child_index += 1
                continue
            
            status = child.tick(context)
            self._status = status
            
            if status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
            
            if status == NodeStatus.FAILURE:
                context.notify_node_status(self.node_id, "failure")
                return NodeStatus.FAILURE
            
            self._current_child_index += 1
        
        self._current_child_index = 0
        self._action_done = False
        
        if self.repeat_count == -1:
            self._status = NodeStatus.RUNNING
            return NodeStatus.RUNNING
        
        self._status = NodeStatus.SUCCESS
        context.notify_node_status(self.node_id, "success")
        return NodeStatus.SUCCESS
    
    def _execute_action(self, context: "ExecutionContext") -> NodeStatus:
        """子类实现的动作执行逻辑"""
        raise NotImplementedError
    
    def reset(self) -> None:
        """重置节点状态"""
        self._current_repeat = 0
        self._start_time = None
        self._status = NodeStatus.SUCCESS
        self._current_child_index = 0
        self._action_done = False
        for child in self.children:
            child.reset()
    
    def reset_all(self) -> None:
        """完全重置节点状态（包括重复计数）"""
        self._current_repeat = 0
        self._start_time = None
        self._status = NodeStatus.SUCCESS
        self._current_child_index = 0
        self._action_done = False
        for child in self.children:
            child.reset()
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        data = super().to_dict()
        if self.children:
            data["children"] = [child.to_dict() for child in self.children]
        return data


class SequenceNode(CompositeNode):
    """
    顺序节点
    
    按顺序依次执行子节点：
    - 所有子节点成功才返回成功
    - 任一子节点失败立即返回失败（默认行为）
    - 开启 continue_on_failure 后，失败仍继续执行，最终根据是否有失败决定结果
    - 子节点返回 RUNNING 时记录位置并返回 RUNNING
    """
    
    def _execute_composite(self, context: "ExecutionContext") -> NodeStatus:
        if not self.children:
            return NodeStatus.SUCCESS
        
        while self._current_index < len(self.children):
            child = self.children[self._current_index]
            
            if not child.enabled:
                self._current_index += 1
                continue
            
            if self.child_interval > 0 and self._last_child_finish_time is not None:
                elapsed = (time.time() * 1000) - self._last_child_finish_time
                if elapsed < self.child_interval:
                    return NodeStatus.RUNNING
            
            status = child.tick(context)
            self._status = status
            
            if status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
            
            if status == NodeStatus.FAILURE:
                if self.continue_on_failure:
                    self._has_failure = True
                    self._current_index += 1
                    if self.child_interval > 0:
                        self._last_child_finish_time = time.time() * 1000
                    continue
                return NodeStatus.FAILURE
            
            self._current_index += 1
            if self.child_interval > 0:
                self._last_child_finish_time = time.time() * 1000
        
        self._current_index = 0
        self._last_child_finish_time = None
        
        if self._has_failure:
            return NodeStatus.FAILURE
        
        return NodeStatus.SUCCESS


class SelectorNode(CompositeNode):
    """
    选择节点
    
    按顺序依次执行子节点：
    - 任一子节点成功立即返回成功
    - 所有子节点失败才返回失败
    - 子节点返回 RUNNING 时记录位置并返回 RUNNING
    """
    
    def _execute_composite(self, context: "ExecutionContext") -> NodeStatus:
        if not self.children:
            return NodeStatus.FAILURE
        
        while self._current_index < len(self.children):
            child = self.children[self._current_index]
            
            if not child.enabled:
                self._current_index += 1
                continue
            
            if self.child_interval > 0 and self._last_child_finish_time is not None:
                elapsed = (time.time() * 1000) - self._last_child_finish_time
                if elapsed < self.child_interval:
                    return NodeStatus.RUNNING
            
            status = child.tick(context)
            self._status = status
            
            if status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
            
            if status == NodeStatus.SUCCESS:
                self._last_child_finish_time = None
                return NodeStatus.SUCCESS
            
            self._current_index += 1
            if self.child_interval > 0:
                self._last_child_finish_time = time.time() * 1000
        
        self._last_child_finish_time = None
        return NodeStatus.FAILURE


class ParallelNode(CompositeNode):
    """
    并行节点
    
    同时执行所有子节点：
    - RequireAll: 所有子节点成功才成功
    - RequireOne: 任一子节点成功即成功
    - 已完成的子节点不会重复执行
    """
    
    SUCCESS_POLICY_ALL = "require_all"
    SUCCESS_POLICY_ONE = "require_one"
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.success_policy = self.config.get("success_policy", self.SUCCESS_POLICY_ALL)
        self._child_statuses: Dict[int, NodeStatus] = {}
    
    def _execute_composite(self, context: "ExecutionContext") -> NodeStatus:
        if not self.children:
            return NodeStatus.SUCCESS
        
        success_count = 0
        failure_count = 0
        running_count = 0
        
        for i, child in enumerate(self.children):
            if not child.enabled:
                continue
            
            if i in self._child_statuses:
                cached_status = self._child_statuses[i]
                if cached_status == NodeStatus.SUCCESS:
                    success_count += 1
                    continue
                elif cached_status == NodeStatus.FAILURE:
                    failure_count += 1
                    continue
            
            status = child.tick(context)
            
            if status == NodeStatus.SUCCESS:
                self._child_statuses[i] = NodeStatus.SUCCESS
                success_count += 1
            elif status == NodeStatus.FAILURE:
                self._child_statuses[i] = NodeStatus.FAILURE
                failure_count += 1
            elif status == NodeStatus.RUNNING:
                running_count += 1
        
        if self.success_policy == self.SUCCESS_POLICY_ONE:
            if success_count > 0:
                self._status = NodeStatus.SUCCESS
                return NodeStatus.SUCCESS
        
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
        self._child_statuses.clear()
    
    def _reset_children(self) -> None:
        """重置所有子节点和状态缓存"""
        super()._reset_children()
        self._child_statuses.clear()


NODE_TYPE_MAP: Dict[str, type] = {
    "SequenceNode": SequenceNode,
    "SelectorNode": SelectorNode,
    "ParallelNode": ParallelNode,
    "CompositeNode": CompositeNode,
    "ConditionNode": ConditionNode,
    "ActionNode": ActionNode,
}
