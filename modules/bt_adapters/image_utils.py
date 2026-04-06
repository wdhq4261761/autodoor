"""
图像预处理工具模块

提供统一的图像预处理功能，用于 OCR 和数字识别等场景
"""

from typing import Optional, Tuple
from PIL import Image, ImageEnhance, ImageFilter


class ImagePreprocessor:
    """
    图像预处理器
    
    提供多种预处理模式，增强 OCR 和数字识别的准确性
    """
    
    @staticmethod
    def preprocess(image: Image.Image, mode: str = "standard") -> Optional[Image.Image]:
        """
        图像预处理入口方法
        
        Args:
            image: PIL.Image 原始图像
            mode: 预处理模式
                - "standard": 标准预处理，适用于普通文本
                - "enhanced": 增强预处理，适用于艺术字、粗体、彩色文本
                - "minimal": 最小预处理，仅灰度转换
                
        Returns:
            PIL.Image: 处理后的图像，失败返回 None
        """
        try:
            if mode == "minimal":
                return ImagePreprocessor._minimal_preprocess(image)
            elif mode == "enhanced":
                return ImagePreprocessor._enhanced_preprocess(image)
            else:
                return ImagePreprocessor._standard_preprocess(image)
        except Exception as e:
            return None
    
    @staticmethod
    def _minimal_preprocess(image: Image.Image) -> Image.Image:
        """最小预处理 - 仅灰度转换"""
        return image.convert('L')
    
    @staticmethod
    def _standard_preprocess(image: Image.Image) -> Image.Image:
        """
        标准预处理 - 适用于普通文本数字
        
        处理步骤：
        1. 灰度转换
        2. 对比度增强 (1.5x)
        3. 锐化滤波
        4. 二值化 (阈值 128)
        """
        image = image.convert('L')
        
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        image = image.filter(ImageFilter.SHARPEN)
        
        image = image.point(lambda p: p > 128 and 255)
        
        return image
    
    @staticmethod
    def _enhanced_preprocess(image: Image.Image) -> Image.Image:
        """
        增强预处理 - 适用于艺术字、粗体、彩色文本
        
        处理步骤：
        1. 灰度转换
        2. 自动反色（深色背景时）
        3. 强对比度增强 (2.5x)
        4. 双重锐化
        5. 中值滤波去噪
        6. 二值化 (阈值 150)
        """
        import numpy as np
        
        image = image.convert('L')
        
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
        
        return image
    
    @staticmethod
    def extract_region(image: Image.Image, region: Tuple[int, int, int, int]) -> Optional[Image.Image]:
        """
        从图像中提取指定区域
        
        Args:
            image: PIL.Image 原始图像
            region: (x1, y1, x2, y2) 区域坐标
            
        Returns:
            PIL.Image: 裁剪后的图像
        """
        try:
            x1, y1, x2, y2 = region
            return image.crop((x1, y1, x2, y2))
        except Exception:
            return None
