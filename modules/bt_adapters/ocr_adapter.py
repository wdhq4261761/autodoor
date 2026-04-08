"""
OCR 条件节点适配器

将 OCR 识别能力封装为行为树条件节点
"""

from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING

from modules.behavior_tree.nodes import ConditionNode, NodeStatus
from modules.bt_adapters.image_utils import ImagePreprocessor

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
        region_config = self.config.get("region", (0, 0, 100, 100))
        region = self._parse_region(region_config)
        
        keywords = self.config.get("keywords", "")
        language = self.config.get("language", "eng")
        save_position = self.config.get("save_position", True)
        position_key = self.config.get("position_key", "last_detection_position")
        
        preprocess_mode = "chinese" if language.startswith('chi') else "standard"
        
        try:
            screenshot = context.get_screenshot(region)
            
            if screenshot is None:
                context.log(f"OCR节点 {self.name}: 截图失败")
                return NodeStatus.FAILURE
            
            context.log(f"OCR节点 {self.name}: 原始图像尺寸 {screenshot.size}, 模式 {screenshot.mode}")
            
            processed_image = ImagePreprocessor.preprocess(screenshot, preprocess_mode)
            if processed_image is None:
                context.log(f"OCR节点 {self.name}: 图像预处理失败")
                return NodeStatus.FAILURE
            
            context.log(f"OCR节点 {self.name}: 预处理后图像尺寸 {processed_image.size}, 模式 {processed_image.mode}")
            
            from utils.recognition import OCRRecognizer
            
            text = OCRRecognizer.get_text(processed_image, language)
            
            if text:
                context.log(f"OCR节点 {self.name}: 识别到文字 '{text.strip()}'")
            else:
                context.log(f"OCR节点 {self.name}: 未识别到任何文字")
                context.log(f"OCR节点 {self.name}: 语言={language}, 预处理={preprocess_mode}, 区域={region}")
            
            if not keywords:
                return NodeStatus.SUCCESS
            
            keyword_list = [k.strip().lower() for k in keywords.split(",") if k.strip()]
            text_lower = text.lower() if text else ""
            
            matched = any(kw in text_lower for kw in keyword_list)
            
            if matched:
                position = OCRRecognizer.find_keyword_position(processed_image, keyword_list, language)
                if save_position and position:
                    abs_x = region[0] + position[0]
                    abs_y = region[1] + position[1]
                    context.blackboard.set(position_key, (abs_x, abs_y))
                context.log(f"OCR节点 {self.name}: 检测到关键词 '{keywords}'")
                return NodeStatus.SUCCESS
            else:
                context.log(f"OCR节点 {self.name}: 未检测到关键词 '{keywords}'")
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
            "position_key": self.config.get("position_key", "last_detection_position"),
        }
        return data
