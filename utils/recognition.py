import numpy as np
import pytesseract
from typing import Optional, Tuple, List

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


def check_language_available(lang: str) -> bool:
    """
    检查语言包是否可用
    
    Args:
        lang: 语言代码 (如 'eng', 'chi_sim', 'chi_tra')
    
    Returns:
        bool: 语言包是否可用
    """
    try:
        available_langs = pytesseract.get_languages()
        return lang in available_langs
    except Exception:
        return False


def get_available_languages() -> List[str]:
    """
    获取所有可用的语言包列表
    
    Returns:
        List[str]: 可用语言代码列表
    """
    try:
        return pytesseract.get_languages()
    except Exception:
        return []


class OCRRecognizer:
    """
    统一的OCR识别器
    
    支持多种识别场景，自动选择最优参数：
    - 英文关键词识别
    - 英文多行文本识别
    - 中文关键词识别
    - 中文多行文本识别
    """
    
    # Tesseract配置常量
    # PSM (Page Segmentation Mode):
    #   3 = 完全自动分页（适合复杂布局）
    #   6 = 单一均匀文本块（适合按钮、标签）
    #   7 = 单行文本（适合单行文字）
    #   11 = 稀疏文本（适合散布的文字）
    # OEM (OCR Engine Mode):
    #   3 = LSTM引擎（最佳识别质量）
    
    CONFIG_ENG_KEYWORD = r'--psm 7 --oem 3'
    CONFIG_ENG_TEXT = r'--psm 6 --oem 3'
    CONFIG_CHI_KEYWORD = r'--psm 7 --oem 3'
    CONFIG_CHI_TEXT = r'--psm 3 --oem 3'
    
    @staticmethod
    def _get_tesseract_config(language: str, mode: str = "keyword") -> str:
        """
        根据语言和模式获取最优的tesseract配置
        
        Args:
            language: 语言代码 ('eng', 'chi_sim', 'chi_tra')
            mode: 识别模式
                - "keyword": 关键词识别（按钮、标签等）
                - "text": 多行文本识别（段落、文档等）
        
        Returns:
            str: tesseract配置字符串
        """
        is_chinese = language.startswith('chi')
        
        if mode == "keyword":
            return OCRRecognizer.CONFIG_CHI_KEYWORD if is_chinese else OCRRecognizer.CONFIG_ENG_KEYWORD
        else:
            return OCRRecognizer.CONFIG_CHI_TEXT if is_chinese else OCRRecognizer.CONFIG_ENG_TEXT
    
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
            
            text = pytesseract.image_to_string(image, lang=language, config=OCRRecognizer._get_tesseract_config(language, "keyword"))
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
                config=OCRRecognizer._get_tesseract_config(language, "keyword"), 
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
    def get_text(image, language: str = "eng", mode: str = "keyword") -> Optional[str]:
        """
        获取图像中的所有文字
        
        Args:
            image: PIL.Image 处理后的图像
            language: 识别语言
            mode: 识别模式 ("keyword" 或 "text")
        
        Returns:
            str: 识别的文字，失败返回None
        """
        try:
            if mode == "keyword":
                # 对于关键词识别，尝试多种PSM模式以提高识别率
                # PSM 7: 单行文本
                # PSM 6: 单一文本块
                # PSM 11: 稀疏文本
                psm_modes = [7, 6, 11]
                
                for psm in psm_modes:
                    config = f'--psm {psm} --oem 3'
                    try:
                        text = pytesseract.image_to_string(image, lang=language, config=config)
                        if text and text.strip():
                            return text
                    except Exception:
                        continue
                
                return None
            else:
                # 文本模式使用配置的PSM
                return pytesseract.image_to_string(image, lang=language, config=OCRRecognizer._get_tesseract_config(language, mode))
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
    """
    统一的数字识别器
    
    支持多种数字识别场景：
    - 单行数字识别
    - 多行数字识别
    - 分数格式识别 (x/y)
    - 带符号数字识别 (正负数)
    """
    
    # 数字识别配置
    # PSM 7: 单行文本（适合单行数字）
    # PSM 6: 单一文本块（适合多行数字）
    # PSM 11: 稀疏文本（适合散布的数字）
    
    # 默认数字白名单：数字、小数点、负号、斜杠（分数）
    DEFAULT_WHITELIST = '0123456789.-/'
    
    CONFIG_SINGLE_LINE = r'--psm 7 --oem 3'
    CONFIG_MULTI_LINE = r'--psm 6 --oem 3'
    CONFIG_SPARSE = r'--psm 11 --oem 3'
    
    @staticmethod
    def _get_number_config(mode: str = "single", whitelist: str = None) -> str:
        """
        根据模式获取数字识别配置
        
        Args:
            mode: 识别模式
                - "single": 单行数字（默认）
                - "multi": 多行数字
                - "sparse": 稀疏数字
            whitelist: 字符白名单
        
        Returns:
            str: tesseract配置字符串
        """
        if mode == "multi":
            base_config = NumberRecognizer.CONFIG_MULTI_LINE
        elif mode == "sparse":
            base_config = NumberRecognizer.CONFIG_SPARSE
        else:
            base_config = NumberRecognizer.CONFIG_SINGLE_LINE
        
        if whitelist:
            return f'{base_config} -c tessedit_char_whitelist={whitelist}'
        else:
            return f'{base_config} -c tessedit_char_whitelist={NumberRecognizer.DEFAULT_WHITELIST}'
    
    @staticmethod
    def recognize(image, whitelist: str = None, mode: str = "single") -> Optional[str]:
        """
        数字OCR识别
        
        Args:
            image: PIL.Image 图像
            whitelist: 允许的字符白名单（可选，默认使用数字白名单）
            mode: 识别模式 ("single", "multi", "sparse")
        
        Returns:
            str: 识别的数字字符串，失败返回None
        """
        try:
            import pytesseract
            
            config = NumberRecognizer._get_number_config(mode, whitelist)
            text = pytesseract.image_to_string(image, lang='eng', config=config)
            
            text = text.strip().replace('\n', '').replace('\r', '')
            
            return text
        except Exception:
            return None
    
    @staticmethod
    def recognize_with_confidence(image, whitelist: str = None, mode: str = "single") -> Tuple[str, int, str]:
        """
        数字OCR识别（带置信度）
        
        Args:
            image: PIL.Image 图像
            whitelist: 允许的字符白名单（可选，默认使用数字白名单）
            mode: 识别模式 ("single", "multi", "sparse")
        
        Returns:
            tuple: (高置信度文本, 平均置信度, 全部识别文本)
                - 高置信度文本: 置信度>50的文本拼接
                - 平均置信度: 高置信度文本的平均置信度
                - 全部识别文本: 所有识别到的文本（用于调试）
        """
        try:
            import pytesseract
            
            config = NumberRecognizer._get_number_config(mode, whitelist)
            data = pytesseract.image_to_data(
                image, lang='eng', 
                config=config, 
                output_type=pytesseract.Output.DICT
            )
            
            high_conf_texts = []
            high_conf_values = []
            all_texts = []
            
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                conf = data['conf'][i]
                
                if text:
                    all_texts.append(text)
                    if conf > 50:
                        high_conf_texts.append(text)
                        high_conf_values.append(conf)
            
            all_text = ''.join(all_texts)
            
            if not high_conf_texts:
                return ("", 0, all_text)
            
            result_text = ''.join(high_conf_texts)
            avg_confidence = sum(high_conf_values) // len(high_conf_values) if high_conf_values else 0
            
            return (result_text, avg_confidence, all_text)
            
        except Exception:
            return ("", 0, "")
    
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
    
    @staticmethod
    def find_number_position(image, target_number: int = None, whitelist: str = None, mode: str = "single") -> Optional[Tuple[int, int]]:
        """
        查找数字在图像中的位置
        
        Args:
            image: PIL.Image 处理后的图像
            target_number: 目标数字（可选，如果指定则只查找该数字的位置）
            whitelist: 允许的字符白名单（可选，默认使用数字白名单）
            mode: 识别模式 ("single", "multi", "sparse")
        
        Returns:
            tuple: (center_x, center_y) 数字中心位置，未找到返回None
        """
        try:
            import pytesseract
            import re
            
            config = NumberRecognizer._get_number_config(mode, whitelist)
            data = pytesseract.image_to_data(
                image, lang='eng', 
                config=config, 
                output_type=pytesseract.Output.DICT
            )
            
            for i in range(len(data['text'])):
                word = data['text'][i].strip()
                if not word:
                    continue
                
                if target_number is not None:
                    match = re.search(r'-?\d+', word)
                    if match and int(match.group()) == target_number:
                        left_word = data['left'][i]
                        top_word = data['top'][i]
                        width = data['width'][i]
                        height = data['height'][i]
                        center_x = left_word + width // 2
                        center_y = top_word + height // 2
                        return (center_x, center_y)
                else:
                    match = re.search(r'-?\d+', word)
                    if match:
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
