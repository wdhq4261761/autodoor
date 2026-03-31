"""
数字条件节点适配器

将数字识别能力封装为行为树条件节点
"""

from typing import Any, Dict, Optional, TYPE_CHECKING

from modules.behavior_tree.nodes import ConditionNode, NodeStatus

if TYPE_CHECKING:
    from modules.behavior_tree.context import ExecutionContext


class NumberConditionNode(ConditionNode):
    """
    数字条件节点
    
    检测指定区域是否识别到数字并比较
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
    
    def _execute_condition(self, context: "ExecutionContext") -> NodeStatus:
        region = tuple(self.config.get("region", (0, 0, 100, 100)))
        compare_mode = self.config.get("compare_mode", "less_than")
        threshold = self.config.get("threshold", 0)
        save_value = self.config.get("save_value", True)
        value_key = self.config.get("value_key", "last_number_value")
        
        try:
            screenshot = context.get_screenshot(region)
            
            if screenshot is None:
                context.log(f"数字节点 {self.name}: 截图失败")
                return NodeStatus.FAILURE
            
            from utils.recognition import NumberRecognizer
            
            text = NumberRecognizer.recognize(screenshot)
            
            if text is None:
                context.log(f"数字节点 {self.name}: OCR识别失败")
                return NodeStatus.FAILURE
            
            number = NumberRecognizer.parse_number(text)
            
            if number is None:
                context.log(f"数字节点 {self.name}: 无法解析数字 '{text}'")
                return NodeStatus.FAILURE
            
            if save_value:
                context.blackboard.set(value_key, number)
            
            result = self._compare(number, threshold, compare_mode)
            
            if result:
                context.log(f"数字节点 {self.name}: 条件满足 ({number} {compare_mode} {threshold})")
                return NodeStatus.SUCCESS
            else:
                context.log(f"数字节点 {self.name}: 条件不满足 ({number} {compare_mode} {threshold})")
                return NodeStatus.FAILURE
                
        except Exception as e:
            context.log(f"数字节点 {self.name}: 执行出错 - {e}")
            return NodeStatus.FAILURE
    
    def _compare(self, value: int, threshold: int, mode: str) -> bool:
        if mode == "less_than":
            return value < threshold
        elif mode == "less_equal":
            return value <= threshold
        elif mode == "greater_than":
            return value > threshold
        elif mode == "greater_equal":
            return value >= threshold
        elif mode == "equal":
            return value == threshold
        elif mode == "not_equal":
            return value != threshold
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"] = {
            **self.config,
            "region": list(self.config.get("region", (0, 0, 100, 100))),
            "compare_mode": self.config.get("compare_mode", "less_than"),
            "threshold": self.config.get("threshold", 0),
            "save_value": self.config.get("save_value", True),
            "value_key": self.config.get("value_key", "last_number_value"),
        }
        return data
