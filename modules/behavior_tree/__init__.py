"""
行为树模块

提供完整的行为树执行能力，支持：
- 组合节点：Sequence, Selector, Parallel（含重试、重复、超时装饰参数）
- 条件节点：OCR, Image, Color, Number, Variable（含取反、重试装饰参数）
- 动作节点：KeyPress, MouseClick, MouseMove, Delay, SetVariable, Script, Code（含重复、超时装饰参数）
- 序列化：JSON, YAML, TEXT 格式
"""

from .nodes import (
    Node,
    NodeStatus,
    CompositeNode,
    ConditionNode,
    ActionNode,
    SequenceNode,
    SelectorNode,
    ParallelNode,
    NODE_TYPE_MAP,
)
from .blackboard import Blackboard
from .context import ExecutionContext
from .engine import BehaviorTreeEngine
from .serializer import BehaviorTreeSerializer

__all__ = [
    "Node",
    "NodeStatus",
    "CompositeNode",
    "ConditionNode",
    "ActionNode",
    "SequenceNode",
    "SelectorNode",
    "ParallelNode",
    "NODE_TYPE_MAP",
    "Blackboard",
    "ExecutionContext",
    "BehaviorTreeEngine",
    "BehaviorTreeSerializer",
]
