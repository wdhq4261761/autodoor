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
        region_config = self.config.get("region", (0, 0, 100, 100))
        region = self._parse_region(region_config)
        
        compare_mode = self._parse_compare_mode(self.config.get("compare_mode", "<"))
        threshold = self.config.get("threshold", 0)
        save_value = self.config.get("save_value", True)
        value_key = self.config.get("value_key", "last_number_value")
        extract_mode = self.config.get("extract_mode", "无规则")
        extract_pattern = self.config.get("extract_pattern", "")
        position_key = self.config.get("position_key") or "last_detection_position"
        min_confidence = self.config.get("min_confidence", 50)
        preprocess_mode = self.config.get("preprocess_mode", "普通文本")
        
        try:
            screenshot = context.get_screenshot(region)
            
            if screenshot is None:
                context.log(f"数字节点 {self.name}: 截图失败")
                return NodeStatus.FAILURE
            
            processed_image = self._preprocess_image(screenshot, preprocess_mode)
            if processed_image is None:
                context.log(f"数字节点 {self.name}: 图像预处理失败")
                return NodeStatus.FAILURE
            
            from utils.recognition import NumberRecognizer
            
            high_conf_text, confidence, all_text = NumberRecognizer.recognize_with_confidence(processed_image)
            
            if not all_text:
                context.log(f"数字节点: 未识别到文本")
                return NodeStatus.FAILURE
            
            if not high_conf_text or confidence < min_confidence:
                context.log(f"数字节点: 识别置信度过低")
                return NodeStatus.FAILURE
            
            number = NumberRecognizer.extract_number(high_conf_text, extract_mode, extract_pattern)
            
            if number is None:
                context.log(f"数字节点: 无法解析数字")
                return NodeStatus.FAILURE
            
            if save_value:
                context.blackboard.set(value_key, number)
            
            result = self._compare(number, threshold, compare_mode)
            
            if result:
                position = NumberRecognizer.find_number_position(screenshot, number)
                if position:
                    abs_x = region[0] + position[0]
                    abs_y = region[1] + position[1]
                    context.blackboard.set(position_key, (abs_x, abs_y))
                context.log(f"数字节点: 识别到 {number}")
                return NodeStatus.SUCCESS
            else:
                context.log(f"数字节点: 识别到 {number}，条件不满足")
                return NodeStatus.FAILURE
                
        except Exception as e:
            context.log(f"数字节点: 执行出错 - {e}")
            return NodeStatus.FAILURE
    
    def _preprocess_image(self, image, mode: str = "普通文本"):
        """
        图像预处理 - 根据模式增强数字识别精度
        
        Args:
            image: PIL.Image 原始图像
            mode: 预处理模式
                - "普通文本": 标准预处理，适用于普通文本数字
                - "艺术字": 激进预处理，适用于粗体、彩色、艺术字数字
            
        Returns:
            PIL.Image: 处理后的图像
        """
        try:
            from PIL import ImageEnhance, ImageFilter
            import numpy as np
            
            image = image.convert('L')
            
            if mode == "艺术字":
                img_array = np.array(image)
                background = np.mean(img_array)
                if background < 128:
                    image = Image.eval(image, lambda x: 255 - x)
                
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(2.5)
                
                image = image.filter(ImageFilter.SHARPEN)
                image = image.filter(ImageFilter.SHARPEN)
                
                image = image.filter(ImageFilter.MedianFilter(size=3))
                
                image = image.point(lambda p: p > 150 and 255)
            else:
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.5)
                
                image = image.filter(ImageFilter.SHARPEN)
                
                image = image.point(lambda p: p > 128 and 255)
            
            return image
        except Exception as e:
            return None
    
    def _parse_region(self, region_config) -> tuple:
        if region_config is None:
            return (0, 0, 100, 100)
        elif isinstance(region_config, (list, tuple)):
            return tuple(region_config)
        elif isinstance(region_config, str):
            try:
                parts = [int(x.strip()) for x in region_config.split(",")]
                if len(parts) == 4:
                    return tuple(parts)
            except (ValueError, AttributeError):
                pass
        return (0, 0, 100, 100)
    
    def _parse_compare_mode(self, mode: str) -> str:
        mode_map = {
            "<": "less_than",
            "<=": "less_equal",
            ">": "greater_than",
            ">=": "greater_equal",
            "==": "equal",
            "!=": "not_equal",
        }
        return mode_map.get(mode, mode)
    
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
            "extract_mode": self.config.get("extract_mode", "无规则"),
            "extract_pattern": self.config.get("extract_pattern", ""),
            "position_key": self.config.get("position_key", "last_detection_position"),
            "min_confidence": self.config.get("min_confidence", 50),
            "preprocess_mode": self.config.get("preprocess_mode", "普通文本"),
        }
        return data
