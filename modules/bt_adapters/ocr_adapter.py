"""
OCR 条件节点适配器

将 OCR 识别能力封装为行为树条件节点
"""

from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING

from modules.behavior_tree.nodes import ConditionNode, NodeStatus

if TYPE_CHECKING:
    from modules.behavior_tree.context import ExecutionContext


class OCRConditionNode(ConditionNode):
    """
    OCR 条件节点
    
    检测指定区域是否包含目标关键词
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.region = tuple(self.config.get("region", (0, 0, 100, 100)))
        self.keywords = self.config.get("keywords", "")
        self.language = self.config.get("language", "eng")
        self.match_mode = self.config.get("match_mode", "any")
        self.save_position = self.config.get("save_position", True)
        self.position_key = self.config.get("position_key", "last_ocr_position")
    
    def tick(self, context: "ExecutionContext") -> NodeStatus:
        """
        执行 OCR 条件检测
        
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
                context.log(f"OCR节点 {self.name}: 截图失败")
                self._status = NodeStatus.FAILURE
                return NodeStatus.FAILURE
            
            from utils.recognition import OCRRecognizer
            
            matched, position = OCRRecognizer.recognize(
                screenshot,
                self.keywords,
                self.language,
                log_func=context.log
            )
            
            if matched:
                if self.save_position and position:
                    context.blackboard.set(self.position_key, position)
                context.log(f"OCR节点 {self.name}: 检测到关键词")
                self._status = NodeStatus.SUCCESS
                return NodeStatus.SUCCESS
            else:
                context.log(f"OCR节点 {self.name}: 未检测到关键词")
                self._status = NodeStatus.FAILURE
                return NodeStatus.FAILURE
                
        except Exception as e:
            context.log(f"OCR节点 {self.name}: 执行出错 - {e}")
            self._status = NodeStatus.FAILURE
            return NodeStatus.FAILURE
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"] = {
            **self.config,
            "region": list(self.region),
            "keywords": self.keywords,
            "language": self.language,
            "match_mode": self.match_mode,
            "save_position": self.save_position,
            "position_key": self.position_key,
        }
        return data
