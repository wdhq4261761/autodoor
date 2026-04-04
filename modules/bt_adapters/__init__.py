"""
行为树适配器模块

将现有识别能力封装为行为树条件节点
"""

from .ocr_adapter import OCRConditionNode
from .image_adapter import ImageConditionNode
from .color_adapter import ColorConditionNode
from .number_adapter import NumberConditionNode
from .variable_adapter import VariableConditionNode
from .action_adapters import (
    KeyPressNode, MouseClickNode, MouseMoveNode,
    DelayNode, SetVariableNode, ScriptNode, CodeNode
)

__all__ = [
    "OCRConditionNode",
    "ImageConditionNode",
    "ColorConditionNode",
    "NumberConditionNode",
    "VariableConditionNode",
    "KeyPressNode",
    "MouseClickNode",
    "MouseMoveNode",
    "DelayNode",
    "SetVariableNode",
    "ScriptNode",
    "CodeNode",
]
