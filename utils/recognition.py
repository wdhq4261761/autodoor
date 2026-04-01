import numpy as np
import pytesseract
from typing import Optional, Tuple, List

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class OCRRecognizer:
    """统一的OCR识别器"""
    
    TESSERACT_CONFIG = r'--psm 6 --oem 3'
    
    @staticmethod
    def recognize(image, keywords: str, language: str = "eng", 
                  log_func=None, group_index: int = None, 
                  return_text: bool = False) -> Tuple[bool, Optional[Tuple[int, int]], Optional[str]]:
        """
        执行OCR识别并查找关键词
        
        Args:
            image: PIL.Image 处理后的图像
            keywords: 关键词字符串，逗号分隔
            language: 识别语言
            log_func: 日志函数
            group_index: 组索引（用于日志）
            return_text: 是否返回识别的文本
        
        Returns:
            tuple: (matched, click_position, recognized_text)
                - matched: 是否匹配到关键词
                - click_position: 点击位置（相对于图像），未匹配返回None
                - recognized_text: 识别的文本（仅当return_text=True时返回）
        """
        if not keywords:
            if return_text:
                return (False, None, None)
            return (False, None, None)
        
        try:
            keyword_list = [k.strip().lower() for k in keywords.split(",") if k.strip()]
            if not keyword_list:
                if return_text:
                    return (False, None, None)
                return (False, None, None)
            
            text = pytesseract.image_to_string(image, lang=language, config=OCRRecognizer.TESSERACT_CONFIG)
            text_lower = text.lower()
            
            if not any(kw in text_lower for kw in keyword_list):
                if return_text:
                    return (False, None, text.strip())
                return (False, None, None)
            
            if log_func:
                prefix = f"监控组{group_index + 1}" if group_index is not None else ""
                log_func(f"{prefix}识别到关键词: {text.strip()}")
            
            click_pos = OCRRecognizer.find_keyword_position(image, keyword_list, language)
            if return_text:
                return (True, click_pos, text.strip())
            return (True, click_pos, None)
            
        except Exception as e:
            if log_func:
                prefix = f"监控组{group_index + 1}" if group_index is not None else ""
                log_func(f"{prefix}OCR识别失败: {str(e)}")
            if return_text:
                return (False, None, None)
            return (False, None, None)
    
    @staticmethod
    def find_keyword_position(image, keywords: List[str], language: str = "eng") -> Optional[Tuple[int, int]]:
        """
        查找关键词在图像中的位置
        
        Args:
            image: PIL.Image 处理后的图像
            keywords: 关键词列表（已转为小写）
            language: 识别语言
        
        Returns:
            tuple: (center_x, center_y) 关键词中心位置，未找到返回None
        """
        try:
            data = pytesseract.image_to_data(
                image, lang=language, 
                config=OCRRecognizer.TESSERACT_CONFIG, 
                output_type=pytesseract.Output.DICT
            )
            
            for i in range(len(data['text'])):
                word = data['text'][i].lower().strip()
                if word in keywords or any(keyword in word for keyword in keywords):
                    left_word = data['left'][i]
                    top_word = data['top'][i]
                    width = data['width'][i]
                    height = data['height'][i]
                    center_x = left_word + width // 2
                    center_y = top_word + height // 2
                    return (center_x, center_y)
            
            return None
            
        except Exception:
            return None
    
    @staticmethod
    def get_text(image, language: str = "eng") -> Optional[str]:
        """
        获取图像中的所有文字
        
        Args:
            image: PIL.Image 处理后的图像
            language: 识别语言
        
        Returns:
            str: 识别的文字，失败返回None
        """
        try:
            return pytesseract.image_to_string(image, lang=language, config=OCRRecognizer.TESSERACT_CONFIG)
        except Exception:
            return None


class ImageRecognizer:
    """统一的图像识别器"""
    
    @staticmethod
    def match_template(screenshot, template, threshold: float = 0.8,
                       log_func=None, group_index: int = None) -> Tuple[bool, Optional[Tuple[int, int]], float]:
        """
        模板匹配识别
        
        Args:
            screenshot: PIL.Image 截图图像
            template: numpy.ndarray 模板图像 (BGR格式)
            threshold: 匹配阈值 (0.0-1.0)
            log_func: 日志函数
            group_index: 组索引（用于日志）
        
        Returns:
            tuple: (matched, click_position, match_score)
                - matched: 是否匹配成功
                - click_position: 点击位置（相对于截图），未匹配返回None
                - match_score: 匹配分数
        """
        if not CV2_AVAILABLE:
            if log_func:
                log_func("OpenCV未安装，无法使用图像识别功能")
            return (False, None, 0.0)
        
        if template is None:
            return (False, None, 0.0)
        
        try:
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            template_h, template_w = template.shape[:2]
            screenshot_h, screenshot_w = screenshot_cv.shape[:2]
            
            if template_w > screenshot_w or template_h > screenshot_h:
                return (False, None, 0.0)
            
            result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                if log_func:
                    prefix = f"检测组{group_index + 1}" if group_index is not None else ""
                    log_func(f"{prefix}图像匹配成功: {max_val:.2%}")
                
                center_x = max_loc[0] + template_w // 2
                center_y = max_loc[1] + template_h // 2
                return (True, (center_x, center_y), max_val)
            
            return (False, None, max_val)
            
        except Exception as e:
            if log_func:
                prefix = f"检测组{group_index + 1}" if group_index is not None else ""
                log_func(f"{prefix}图像识别失败: {str(e)}")
            return (False, None, 0.0)


class ColorRecognizer:
    """统一的颜色识别器"""
    
    @staticmethod
    def match_color(image, target_color: Tuple[int, int, int], tolerance: int = 10,
                    log_func=None, group_index: int = None) -> Tuple[bool, Optional[Tuple[int, int]], int]:
        """
        颜色匹配识别
        
        Args:
            image: PIL.Image 截图图像
            target_color: 目标颜色 (R, G, B)
            tolerance: 颜色容差
            log_func: 日志函数
            group_index: 组索引（用于日志）
        
        Returns:
            tuple: (matched, click_position, match_pixels)
                - matched: 是否匹配成功
                - click_position: 第一个匹配像素的位置，未匹配返回None
                - match_pixels: 匹配的像素数量
        """
        if not target_color:
            return (False, None, 0)
        
        try:
            img_array = np.array(image)
            
            valid_target_color = np.clip(np.array(target_color), 0, 255)
            lower_bound = np.maximum(0, valid_target_color - tolerance)
            upper_bound = np.minimum(255, valid_target_color + tolerance)
            
            sample_step = 2
            sampled_array = img_array[::sample_step, ::sample_step]
            
            is_match = np.all((sampled_array >= lower_bound) & (sampled_array <= upper_bound), axis=2)
            match_pixels = np.sum(is_match)
            
            if match_pixels > 0:
                if log_func:
                    prefix = f"监控组{group_index + 1}" if group_index is not None else ""
                    log_func(f"{prefix}颜色匹配成功: {match_pixels}个像素")
                
                match_positions = np.where(is_match)
                first_match_y = match_positions[0][0] * sample_step
                first_match_x = match_positions[1][0] * sample_step
                return (True, (first_match_x, first_match_y), match_pixels)
            
            return (False, None, 0)
            
        except Exception as e:
            if log_func:
                prefix = f"监控组{group_index + 1}" if group_index is not None else ""
                log_func(f"{prefix}颜色识别失败: {str(e)}")
            return (False, None, 0)
    
    @staticmethod
    def get_pixel_color(image, x: int, y: int) -> Optional[Tuple[int, int, int]]:
        """
        获取图像指定位置的颜色
        
        Args:
            image: PIL.Image 图像
            x: x坐标
            y: y坐标
        
        Returns:
            tuple: (R, G, B) 颜色值，失败返回None
        """
        try:
            if x < 0 or y < 0:
                return None
            
            img_array = np.array(image)
            if y >= img_array.shape[0] or x >= img_array.shape[1]:
                return None
            
            pixel = img_array[y, x]
            return tuple(pixel[:3])
        except Exception:
            return None


class NumberRecognizer:
    """统一的数字识别器"""
    
    NUMBER_CONFIG = r'--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789/'
    
    @staticmethod
    def recognize(image, whitelist: str = "0123456789/") -> Optional[str]:
        """
        数字OCR识别
        
        Args:
            image: PIL.Image 图像
            whitelist: 允许的字符白名单
        
        Returns:
            str: 识别的数字字符串，失败返回None
        """
        try:
            import pytesseract
            
            config = f'--psm 7 --oem 3 -c tessedit_char_whitelist={whitelist}'
            text = pytesseract.image_to_string(image, lang='eng', config=config)
            
            text = text.strip().replace('\n', '').replace('\r', '')
            
            return text
        except Exception:
            return None
    
    @staticmethod
    def parse_number(text: str, cache: dict = None) -> Optional[int]:
        """
        从文本中解析数字（支持分数格式）
        
        Args:
            text: 文本字符串
            cache: 缓存字典（可选）
        
        Returns:
            int: 解析的数字，失败返回None
        """
        import re
        
        if not text:
            return None
        
        text = text.strip()
        if not text:
            return None
        
        if cache is not None:
            cache_key = text.lower()
            if cache_key in cache:
                return cache[cache_key]
        
        number = None
        try:
            match = re.search(r'^\s*(\d+)\s*/', text)
            if match:
                number = int(match.group(1))
        except Exception:
            number = None
        
        if cache is not None and number is not None:
            cache[text.lower()] = number
        
        return number
    
    @staticmethod
    def extract_number(text: str, mode: str = "basic", pattern: str = "") -> Optional[int]:
        """
        根据模式从文本中提取数字
        
        Args:
            text: 文本字符串
            mode: 提取模式
                - "无规则" / "basic": 基本识别，直接采集识别到的第一个数字
                - "x/y" / "fraction_x": 识别x/y格式中的x值
                - "y/x" / "fraction_y": 识别x/y格式中的y值
                - "自定义" / "custom": 自定义通配符模式
            pattern: 自定义通配符模式（仅 mode="自定义" 时使用）
                - 使用 * 表示数字部分
                - 例如: "HP: */MAX" 表示匹配 "HP: 100/MAX" 并提取 100
                - 例如: "(*/*)" 表示匹配 "(50/100)" 并提取 50
        
        Returns:
            int: 提取的数字，失败返回None
        """
        import re
        
        if not text:
            return None
        
        text = text.strip()
        if not text:
            return None
        
        try:
            if mode in ("basic", "无规则"):
                match = re.search(r'-?\d+', text)
                if match:
                    return int(match.group())
            
            elif mode in ("fraction_x", "x/y"):
                match = re.search(r'(\d+)\s*/\s*\d+', text)
                if match:
                    return int(match.group(1))
            
            elif mode in ("fraction_y", "y/x"):
                match = re.search(r'\d+\s*/\s*(\d+)', text)
                if match:
                    return int(match.group(1))
            
            elif mode in ("custom", "自定义") and pattern:
                regex_pattern = ""
                i = 0
                while i < len(pattern):
                    if pattern[i] == '*':
                        regex_pattern += r'(-?\d+)'
                    elif pattern[i] in r'\.^$*+?{}[]|()':
                        regex_pattern += '\\' + pattern[i]
                    else:
                        regex_pattern += pattern[i]
                    i += 1
                
                match = re.search(regex_pattern, text)
                if match:
                    return int(match.group(1))
        
        except Exception:
            pass
        
        return None
