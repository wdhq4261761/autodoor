"""
行为树模块

提供完整的行为树执行能力，支持：
- 组合节点：Sequence, Selector, Parallel
- 装饰节点：Inverter, Repeater, Retry, Timeout
- 条件节点：OCR, Image, Color, Number
- 动作节点：KeyPress, MouseClick, Delay
"""

from .nodes import (
    Node,
    NodeStatus,
    CompositeNode,
    DecoratorNode,
    ConditionNode,
    ActionNode,
    SequenceNode,
    SelectorNode,
    ParallelNode,
    InverterNode,
    RepeaterNode,
    RetryNode,
    TimeoutNode,
    NODE_TYPE_MAP,
)
from .blackboard import Blackboard
from .context import ExecutionContext
from .engine import BehaviorTreeEngine

__all__ = [
    "Node",
    "NodeStatus",
    "CompositeNode",
    "DecoratorNode",
    "ConditionNode",
    "ActionNode",
    "SequenceNode",
    "SelectorNode",
    "ParallelNode",
    "InverterNode",
    "RepeaterNode",
    "RetryNode",
    "TimeoutNode",
    "NODE_TYPE_MAP",
    "Blackboard",
    "ExecutionContext",
    "BehaviorTreeEngine",
]
