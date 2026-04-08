"""
图像条件节点适配器

将图像识别能力封装为行为树条件节点
"""

from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING

from modules.behavior_tree.nodes import ConditionNode, NodeStatus

if TYPE_CHECKING:
    from modules.behavior_tree.context import ExecutionContext


class ImageConditionNode(ConditionNode):
    """
    图像条件节点
    
    使用模板匹配检测指定区域是否包含目标图像
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self._template = None
        self._template_path = None
    
    def _load_template(self, template_path: str):
        if self._template is not None and self._template_path == template_path:
            return self._template
        
        if not template_path:
            return None
        
        try:
            import cv2
            self._template = cv2.imread(template_path, cv2.IMREAD_COLOR)
            self._template_path = template_path
            return self._template
        except Exception:
            return None
    
    def _execute_condition(self, context: "ExecutionContext") -> NodeStatus:
        region_config = self.config.get("region", (0, 0, 100, 100))
        region = self._parse_region(region_config)
        
        template_path = self.config.get("template_path", "")
        threshold_percent = self.config.get("threshold", 80)
        threshold = float(threshold_percent) / 100.0
        save_position = self.config.get("save_position", True)
        position_key = self.config.get("position_key", "last_detection_position")
        
        context.log(f"图像节点 {self.name}: 开始执行, region={region}, template={template_path}, threshold={threshold:.0%}")
        
        try:
            template = self._load_template(template_path)
            if template is None:
                context.log(f"图像节点 {self.name}: 模板加载失败")
                return NodeStatus.FAILURE
            
            screenshot = context.get_screenshot(region)
            
            if screenshot is None:
                context.log(f"图像节点 {self.name}: 截图失败")
                return NodeStatus.FAILURE
            
            from utils.recognition import ImageRecognizer
            
            matched, position, score = ImageRecognizer.match_template(
                screenshot,
                template,
                threshold,
                log_func=context.log
            )
            
            if matched and position:
                if save_position:
                    abs_x = region[0] + position[0]
                    abs_y = region[1] + position[1]
                    context.blackboard.set(position_key, (abs_x, abs_y))
                context.log(f"图像节点 {self.name}: 匹配成功 ({score:.0%})")
                return NodeStatus.SUCCESS
            else:
                context.log(f"图像节点 {self.name}: 未匹配到目标图像 (最高匹配度: {score:.0%})")
                return NodeStatus.FAILURE
                
        except Exception as e:
            context.log(f"图像节点 {self.name}: 执行出错 - {e}")
            return NodeStatus.FAILURE
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"] = {
            **self.config,
            "region": list(self.config.get("region", (0, 0, 100, 100))),
            "template_path": self.config.get("template_path", ""),
            "threshold": self.config.get("threshold", 80),
            "save_position": self.config.get("save_position", True),
            "position_key": self.config.get("position_key", "last_detection_position"),
        }
        return data
