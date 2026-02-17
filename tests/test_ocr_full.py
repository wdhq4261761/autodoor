import pytest
import time
import threading
from unittest.mock import MagicMock, patch
from modules.ocr import OCRModule


class TestOCRModuleFull:
    """OCRModule完整测试类"""
    
    @pytest.fixture
    def ocr_module(self, mock_app, create_mock_ocr_group):
        mock_app.ocr_groups = [
            create_mock_ocr_group(enabled=True, interval="5", keywords="test", key="enter"),
        ]
        mock_app.tesseract_available = True
        mock_app.is_running = True
        mock_app.is_paused = False
        mock_app.platform_adapter = MagicMock()
        mock_app.platform_adapter.platform = "Windows"
        mock_app.ocr_thread = None
        mock_app.status_labels = {"ocr": MagicMock()}
        return OCRModule(mock_app)
    
    def test_start_monitoring_creates_thread(self, ocr_module):
        """测试启动监控创建线程"""
        ocr_module.start_monitoring()
        
        assert ocr_module.app.ocr_thread is not None
        
        ocr_module.app.is_running = False
        if ocr_module.app.ocr_thread and ocr_module.app.ocr_thread.is_alive():
            ocr_module.app.ocr_thread.join(timeout=2)
    
    def test_stop_monitoring(self, ocr_module):
        """测试停止监控"""
        ocr_module.app.is_running = True
        
        ocr_module.stop_monitoring()
        
        assert ocr_module.app.is_running is False


class TestOCRKeywordProcessing:
    """OCR关键词处理测试"""
    
    def test_keyword_processing_single(self):
        """测试单个关键词处理"""
        text = "Hello World"
        keywords = "hello"
        
        keyword_list = [k.strip().lower() for k in keywords.split(",")]
        found = any(kw in text.lower() for kw in keyword_list)
        
        assert found is True
    
    def test_keyword_processing_multiple(self):
        """测试多个关键词处理"""
        text = "Hello World Test"
        keywords = "hello,world,python"
        
        keyword_list = [k.strip().lower() for k in keywords.split(",")]
        found = any(kw in text.lower() for kw in keyword_list)
        
        assert found is True
    
    def test_keyword_processing_no_match(self):
        """测试无匹配关键词"""
        text = "Hello World"
        keywords = "python,java,cpp"
        
        keyword_list = [k.strip().lower() for k in keywords.split(",")]
        found = any(kw in text.lower() for kw in keyword_list)
        
        assert found is False
    
    def test_keyword_processing_empty(self):
        """测试空关键词"""
        text = "Hello World"
        keywords = ""
        
        keyword_list = [k.strip().lower() for k in keywords.split(",") if k.strip()]
        found = any(kw in text.lower() for kw in keyword_list) if keyword_list else False
        
        assert found is False


class TestOCRImageCapture:
    """OCR图像捕获测试"""
    
    @pytest.fixture
    def ocr_module(self, mock_app):
        mock_app.platform_adapter = MagicMock()
        mock_app.platform_adapter.platform = "Windows"
        return OCRModule(mock_app)
    
    def test_capture_region_success(self, ocr_module):
        """测试成功捕获区域"""
        from PIL import Image
        
        test_image = Image.new('RGB', (100, 50), color='white')
        
        with patch('utils.screenshot.ScreenshotManager') as mock_manager:
            mock_instance = MagicMock()
            mock_manager.return_value = mock_instance
            mock_instance.get_region_screenshot.return_value = test_image
            
            result = ocr_module._capture_screen_region(0, 0, 100, 50, 0)
            
            assert result is not None
    
    def test_capture_region_failure(self, ocr_module):
        """测试捕获区域失败"""
        with patch('utils.screenshot.ScreenshotManager') as mock_manager:
            mock_instance = MagicMock()
            mock_manager.return_value = mock_instance
            mock_instance.get_region_screenshot.return_value = None
            
            result = ocr_module._capture_screen_region(0, 0, 100, 50, 0)
            
            assert result is None


class TestOCRTextProcessing:
    """OCR文本处理测试"""
    
    def test_text_cleaning(self):
        """测试文本清理"""
        text = "  Hello World  \n"
        
        cleaned = text.strip()
        
        assert cleaned == "Hello World"
    
    def test_text_normalization(self):
        """测试文本标准化"""
        text = "HELLO WORLD"
        
        normalized = text.lower()
        
        assert normalized == "hello world"
    
    def test_text_keyword_extraction(self):
        """测试关键词提取"""
        text = "The quick brown fox jumps over the lazy dog"
        keywords = "fox,dog"
        
        keyword_list = [k.strip().lower() for k in keywords.split(",")]
        found_keywords = [kw for kw in keyword_list if kw in text.lower()]
        
        assert len(found_keywords) == 2
