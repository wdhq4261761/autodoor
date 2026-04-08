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
        region_config = self.config.get("region", (0, 0, 100, 100))
        region = self._parse_region(region_config)
        
        target_color_config = self.config.get("target_color", (255, 0, 0))
        target_color = self._parse_color(target_color_config)
        
        tolerance = self.config.get("tolerance", 10)
        min_pixels = self.config.get("min_pixels", 1)
        save_position = self.config.get("save_position", True)
        position_key = self.config.get("position_key", "last_detection_position")
        
        context.log(f"颜色节点 {self.name}: 开始执行, region={region}, color={target_color}")
        
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
    
    def _parse_color(self, color_config) -> tuple:
        if color_config is None:
            return (255, 0, 0)
        elif isinstance(color_config, (list, tuple)):
            return tuple(int(c) for c in color_config)
        elif isinstance(color_config, str):
            import re
            match = re.search(r'RGB\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', color_config, re.IGNORECASE)
            if match:
                return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
            try:
                parts = [int(x.strip()) for x in color_config.split(",")]
                if len(parts) >= 3:
                    return tuple(parts[:3])
            except (ValueError, AttributeError):
                pass
        return (255, 0, 0)
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"] = {
            **self.config,
            "region": list(self.config.get("region", (0, 0, 100, 100))),
            "target_color": list(self.config.get("target_color", (255, 0, 0))),
            "tolerance": self.config.get("tolerance", 10),
            "min_pixels": self.config.get("min_pixels", 1),
            "save_position": self.config.get("save_position", True),
            "position_key": self.config.get("position_key", "last_detection_position"),
        }
        return data
