"""
颜色条件节点适配器

将颜色识别能力封装为行为树条件节点
"""

from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING

from modules.behavior_tree.nodes import ConditionNode, NodeStatus

if TYPE_CHECKING:
    from modules.behavior_tree.context import ExecutionContext


class ColorConditionNode(ConditionNode):
    """
    颜色条件节点
    
    检测指定区域是否包含目标颜色
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
    
    def _execute_condition(self, context: "ExecutionContext") -> NodeStatus:
        region = tuple(self.config.get("region", (0, 0, 100, 100)))
        target_color = tuple(self.config.get("target_color", (255, 0, 0)))
        tolerance = self.config.get("tolerance", 10)
        min_pixels = self.config.get("min_pixels", 1)
        save_position = self.config.get("save_position", True)
        position_key = self.config.get("position_key", "last_color_position")
        
        try:
            screenshot = context.get_screenshot(region)
            
            if screenshot is None:
                context.log(f"颜色节点 {self.name}: 截图失败")
                return NodeStatus.FAILURE
            
            from utils.recognition import ColorRecognizer
            
            matched, position, match_pixels = ColorRecognizer.match_color(
                screenshot,
                target_color,
                tolerance,
                log_func=context.log
            )
            
            if matched and match_pixels >= min_pixels:
                if save_position and position:
                    abs_x = region[0] + position[0]
                    abs_y = region[1] + position[1]
                    context.blackboard.set(position_key, (abs_x, abs_y))
                context.log(f"颜色节点 {self.name}: 匹配成功 ({match_pixels}像素)")
                return NodeStatus.SUCCESS
            else:
                context.log(f"颜色节点 {self.name}: 未匹配到目标颜色")
                return NodeStatus.FAILURE
                
        except Exception as e:
            context.log(f"颜色节点 {self.name}: 执行出错 - {e}")
            return NodeStatus.FAILURE
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"] = {
            **self.config,
            "region": list(self.config.get("region", (0, 0, 100, 100))),
            "target_color": list(self.config.get("target_color", (255, 0, 0))),
            "tolerance": self.config.get("tolerance", 10),
            "min_pixels": self.config.get("min_pixels", 1),
            "save_position": self.config.get("save_position", True),
            "position_key": self.config.get("position_key", "last_color_position"),
        }
        return data
