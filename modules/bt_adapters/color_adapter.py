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
        self.region = tuple(self.config.get("region", (0, 0, 100, 100)))
        self.target_color = tuple(self.config.get("target_color", (255, 0, 0)))
        self.tolerance = self.config.get("tolerance", 10)
        self.min_pixels = self.config.get("min_pixels", 1)
        self.save_position = self.config.get("save_position", True)
        self.position_key = self.config.get("position_key", "last_color_position")
    
    def tick(self, context: "ExecutionContext") -> NodeStatus:
        """
        执行颜色条件检测
        
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
                context.log(f"颜色节点 {self.name}: 截图失败")
                self._status = NodeStatus.FAILURE
                return NodeStatus.FAILURE
            
            from utils.recognition import ColorRecognizer
            
            matched, position, match_pixels = ColorRecognizer.match_color(
                screenshot,
                self.target_color,
                self.tolerance,
                log_func=context.log
            )
            
            if matched and match_pixels >= self.min_pixels:
                if self.save_position and position:
                    abs_x = self.region[0] + position[0]
                    abs_y = self.region[1] + position[1]
                    context.blackboard.set(self.position_key, (abs_x, abs_y))
                context.log(f"颜色节点 {self.name}: 匹配成功 ({match_pixels}像素)")
                self._status = NodeStatus.SUCCESS
                return NodeStatus.SUCCESS
            else:
                context.log(f"颜色节点 {self.name}: 未匹配到目标颜色")
                self._status = NodeStatus.FAILURE
                return NodeStatus.FAILURE
                
        except Exception as e:
            context.log(f"颜色节点 {self.name}: 执行出错 - {e}")
            self._status = NodeStatus.FAILURE
            return NodeStatus.FAILURE
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"] = {
            **self.config,
            "region": list(self.region),
            "target_color": list(self.target_color),
            "tolerance": self.tolerance,
            "min_pixels": self.min_pixels,
            "save_position": self.save_position,
            "position_key": self.position_key,
        }
        return data
