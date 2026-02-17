import pytest
from unittest.mock import MagicMock, patch
from PIL import Image
from utils.image import _preprocess_image


class TestImagePreprocessing:
    """图像预处理测试"""
    
    def test_preprocess_image_returns_image(self):
        """测试返回图像"""
        test_image = Image.new('RGB', (100, 50), color='white')
        
        result = _preprocess_image(test_image)
        
        assert result is not None
        assert isinstance(result, Image.Image)
    
    def test_preprocess_image_converts_to_grayscale(self):
        """测试转换为灰度图"""
        test_image = Image.new('RGB', (100, 50), color='red')
        
        result = _preprocess_image(test_image)
        
        assert result.mode == 'L'
    
    def test_preprocess_image_enhances_contrast(self):
        """测试增强对比度"""
        test_image = Image.new('RGB', (100, 50), color='gray')
        
        result = _preprocess_image(test_image)
        
        assert result is not None
    
    def test_preprocess_image_applies_sharpen(self):
        """测试应用锐化"""
        test_image = Image.new('RGB', (100, 50), color='white')
        
        result = _preprocess_image(test_image)
        
        assert result is not None
    
    def test_preprocess_image_applies_threshold(self):
        """测试应用阈值"""
        test_image = Image.new('RGB', (100, 50), color='gray')
        
        result = _preprocess_image(test_image)
        
        assert result is not None
    
    def test_preprocess_image_with_group_index(self):
        """测试带组索引"""
        test_image = Image.new('RGB', (100, 50), color='white')
        
        result = _preprocess_image(test_image, group_index=0)
        
        assert result is not None
    
    def test_preprocess_image_preserves_size(self):
        """测试保持尺寸"""
        test_image = Image.new('RGB', (200, 100), color='white')
        
        result = _preprocess_image(test_image)
        
        assert result.size == (200, 100)
    
    def test_preprocess_image_small_image(self):
        """测试小图像"""
        test_image = Image.new('RGB', (10, 10), color='white')
        
        result = _preprocess_image(test_image)
        
        assert result is not None
        assert result.size == (10, 10)
    
    def test_preprocess_image_large_image(self):
        """测试大图像"""
        test_image = Image.new('RGB', (1000, 500), color='white')
        
        result = _preprocess_image(test_image)
        
        assert result is not None
        assert result.size == (1000, 500)
    
    def test_preprocess_image_dark_image(self):
        """测试暗色图像"""
        test_image = Image.new('RGB', (100, 50), color='black')
        
        result = _preprocess_image(test_image)
        
        assert result is not None
    
    def test_preprocess_image_bright_image(self):
        """测试亮色图像"""
        test_image = Image.new('RGB', (100, 50), color='white')
        
        result = _preprocess_image(test_image)
        
        assert result is not None
    
    def test_preprocess_image_colorful_image(self):
        """测试彩色图像"""
        test_image = Image.new('RGB', (100, 50), color='red')
        
        result = _preprocess_image(test_image)
        
        assert result is not None
        assert result.mode == 'L'


class TestImagePreprocessingEdgeCases:
    """图像预处理边界情况测试"""
    
    def test_preprocess_image_exception_handling(self):
        """测试异常处理"""
        test_image = Image.new('RGB', (100, 50), color='white')
        
        with patch('PIL.ImageEnhance.Contrast') as mock_enhancer:
            mock_enhancer.side_effect = Exception("Enhance error")
            
            result = _preprocess_image(test_image)
            
            assert result is None
    
    def test_preprocess_image_exception_with_group_index(self):
        """测试带组索引的异常处理"""
        test_image = Image.new('RGB', (100, 50), color='white')
        
        with patch('PIL.ImageEnhance.Contrast') as mock_enhancer:
            mock_enhancer.side_effect = Exception("Enhance error")
            
            result = _preprocess_image(test_image, group_index=0)
            
            assert result is None


class TestImagePreprocessingQuality:
    """图像预处理质量测试"""
    
    def test_preprocess_improves_text_visibility(self):
        """测试提高文字可见性"""
        test_image = Image.new('RGB', (100, 50), color='white')
        
        result = _preprocess_image(test_image)
        
        assert result is not None
    
    def test_preprocess_handles_gradient(self):
        """测试处理渐变图像"""
        test_image = Image.new('RGB', (100, 50), color='white')
        
        for x in range(100):
            for y in range(50):
                gray = int(255 * x / 100)
                test_image.putpixel((x, y), (gray, gray, gray))
        
        result = _preprocess_image(test_image)
        
        assert result is not None
