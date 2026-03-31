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
    
    def _execute_condition(self, context: "ExecutionContext") -> NodeStatus:
        region = tuple(self.config.get("region", (0, 0, 100, 100)))
        keywords = self.config.get("keywords", "")
        language = self.config.get("language", "eng")
        save_position = self.config.get("save_position", True)
        position_key = self.config.get("position_key", "last_ocr_position")
        
        try:
            screenshot = context.get_screenshot(region)
            
            if screenshot is None:
                context.log(f"OCR节点 {self.name}: 截图失败")
                return NodeStatus.FAILURE
            
            from utils.recognition import OCRRecognizer
            
            matched, position = OCRRecognizer.recognize(
                screenshot,
                keywords,
                language,
                log_func=context.log
            )
            
            if matched:
                if save_position and position:
                    context.blackboard.set(position_key, position)
                context.log(f"OCR节点 {self.name}: 检测到关键词")
                return NodeStatus.SUCCESS
            else:
                context.log(f"OCR节点 {self.name}: 未检测到关键词")
                return NodeStatus.FAILURE
                
        except Exception as e:
            context.log(f"OCR节点 {self.name}: 执行出错 - {e}")
            return NodeStatus.FAILURE
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"] = {
            **self.config,
            "region": list(self.config.get("region", (0, 0, 100, 100))),
            "keywords": self.config.get("keywords", ""),
            "language": self.config.get("language", "eng"),
            "match_mode": self.config.get("match_mode", "any"),
            "save_position": self.config.get("save_position", True),
            "position_key": self.config.get("position_key", "last_ocr_position"),
        }
        return data
