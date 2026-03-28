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
        self.region = tuple(self.config.get("region", (0, 0, 100, 100)))
        self.compare_mode = self.config.get("compare_mode", "less_than")
        self.threshold = self.config.get("threshold", 0)
        self.save_value = self.config.get("save_value", True)
        self.value_key = self.config.get("value_key", "last_number_value")
    
    def tick(self, context: "ExecutionContext") -> NodeStatus:
        """
        执行数字条件检测
        
        Args:
            context: 执行上下文
            
        Returns:
            检测结果状态
        """
        if not self.enabled:
            return NodeStatus.SUCCESS
        
        if not context.check_running():
            return NodeStatus.ABORTED
        
        try:
            screenshot = context.get_screenshot(self.region)
            
            if screenshot is None:
                context.log(f"数字节点 {self.name}: 截图失败")
                self._status = NodeStatus.FAILURE
                return NodeStatus.FAILURE
            
            from utils.recognition import NumberRecognizer
            
            text = NumberRecognizer.recognize(screenshot)
            
            if text is None:
                context.log(f"数字节点 {self.name}: OCR识别失败")
                self._status = NodeStatus.FAILURE
                return NodeStatus.FAILURE
            
            number = NumberRecognizer.parse_number(text)
            
            if number is None:
                context.log(f"数字节点 {self.name}: 无法解析数字 '{text}'")
                self._status = NodeStatus.FAILURE
                return NodeStatus.FAILURE
            
            if self.save_value:
                context.blackboard.set(self.value_key, number)
            
            result = self._compare(number, self.threshold, self.compare_mode)
            
            if result:
                context.log(f"数字节点 {self.name}: 条件满足 ({number} {self.compare_mode} {self.threshold})")
                self._status = NodeStatus.SUCCESS
                return NodeStatus.SUCCESS
            else:
                context.log(f"数字节点 {self.name}: 条件不满足 ({number} {self.compare_mode} {self.threshold})")
                self._status = NodeStatus.FAILURE
                return NodeStatus.FAILURE
                
        except Exception as e:
            context.log(f"数字节点 {self.name}: 执行出错 - {e}")
            self._status = NodeStatus.FAILURE
            return NodeStatus.FAILURE
    
    def _compare(self, value: int, threshold: int, mode: str) -> bool:
        """比较数字"""
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
            "region": list(self.region),
            "compare_mode": self.compare_mode,
            "threshold": self.threshold,
            "save_value": self.save_value,
            "value_key": self.value_key,
        }
        return data
