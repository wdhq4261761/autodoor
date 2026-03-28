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
        self.region = tuple(self.config.get("region", (0, 0, 100, 100)))
        self.template_path = self.config.get("template_path", "")
        self.threshold = self.config.get("threshold", 0.8)
        self.save_position = self.config.get("save_position", True)
        self.position_key = self.config.get("position_key", "last_image_position")
        self._template = None
    
    def _load_template(self):
        """加载模板图像"""
        if self._template is not None:
            return self._template
        
        if not self.template_path:
            return None
        
        try:
            import cv2
            self._template = cv2.imread(self.template_path, cv2.IMREAD_COLOR)
            return self._template
        except Exception:
            return None
    
    def tick(self, context: "ExecutionContext") -> NodeStatus:
        """
        执行图像条件检测
        
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
            template = self._load_template()
            if template is None:
                context.log(f"图像节点 {self.name}: 模板加载失败")
                self._status = NodeStatus.FAILURE
                return NodeStatus.FAILURE
            
            screenshot = context.get_screenshot(self.region)
            
            if screenshot is None:
                context.log(f"图像节点 {self.name}: 截图失败")
                self._status = NodeStatus.FAILURE
                return NodeStatus.FAILURE
            
            from utils.recognition import ImageRecognizer
            
            matched, position, score = ImageRecognizer.match_template(
                screenshot,
                template,
                self.threshold,
                log_func=context.log
            )
            
            if matched and position:
                if self.save_position:
                    abs_x = self.region[0] + position[0]
                    abs_y = self.region[1] + position[1]
                    context.blackboard.set(self.position_key, (abs_x, abs_y))
                context.log(f"图像节点 {self.name}: 匹配成功 ({score:.2%})")
                self._status = NodeStatus.SUCCESS
                return NodeStatus.SUCCESS
            else:
                context.log(f"图像节点 {self.name}: 未匹配到目标图像")
                self._status = NodeStatus.FAILURE
                return NodeStatus.FAILURE
                
        except Exception as e:
            context.log(f"图像节点 {self.name}: 执行出错 - {e}")
            self._status = NodeStatus.FAILURE
            return NodeStatus.FAILURE
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"] = {
            **self.config,
            "region": list(self.region),
            "template_path": self.template_path,
            "threshold": self.threshold,
            "save_position": self.save_position,
            "position_key": self.position_key,
        }
        return data
