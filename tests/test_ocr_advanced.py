import pytest
import time
import threading
from unittest.mock import MagicMock, patch
from modules.ocr import OCRModule


class TestOCRModuleAdvanced:
    """OCRModule高级测试类"""
    
    @pytest.fixture
    def ocr_module(self, mock_app, create_mock_ocr_group):
        mock_app.ocr_groups = [
            create_mock_ocr_group(enabled=True, interval="5", keywords="test"),
            create_mock_ocr_group(enabled=True, interval="10", keywords="hello"),
        ]
        mock_app.tesseract_available = True
        mock_app.is_running = True
        mock_app.is_paused = False
        mock_app.platform_adapter = MagicMock()
        mock_app.platform_adapter.platform = "Windows"
        return OCRModule(mock_app)
    
    def test_start_monitoring_no_tesseract(self, ocr_module):
        """测试无Tesseract时启动"""
        ocr_module.app.tesseract_available = False
        
        with patch('tkinter.messagebox.showinfo'):
            ocr_module.start_monitoring()
    
    def test_start_monitoring_no_enabled_groups(self, ocr_module):
        """测试无启用组时启动"""
        for group in ocr_module.app.ocr_groups:
            group["enabled"].set(False)
        
        with patch('tkinter.messagebox.showwarning'):
            ocr_module.start_monitoring()
    
    def test_start_monitoring_success(self, ocr_module):
        """测试成功启动"""
        ocr_module.app.ocr_thread = None
        
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


class TestOCRRegionCapture:
    """OCR区域截图测试"""
    
    @pytest.fixture
    def ocr_module(self, mock_app):
        mock_app.platform_adapter = MagicMock()
        mock_app.platform_adapter.platform = "Windows"
        return OCRModule(mock_app)
    
    def test_capture_screen_region_success(self, ocr_module):
        """测试成功截图"""
        from PIL import Image
        
        test_image = Image.new('RGB', (100, 50), color='white')
        
        with patch('utils.screenshot.ScreenshotManager') as mock_manager:
            mock_instance = MagicMock()
            mock_manager.return_value = mock_instance
            mock_instance.get_region_screenshot.return_value = test_image
            
            result = ocr_module._capture_screen_region(0, 0, 100, 50, 0)
            
            assert result is not None
    
    def test_capture_screen_region_failure(self, ocr_module):
        """测试截图失败"""
        with patch('utils.screenshot.ScreenshotManager') as mock_manager:
            mock_instance = MagicMock()
            mock_manager.return_value = mock_instance
            mock_instance.get_region_screenshot.return_value = None
            
            result = ocr_module._capture_screen_region(0, 0, 100, 50, 0)
            
            assert result is None


class TestOCRKeywordMatching:
    """OCR关键词匹配测试"""
    
    def test_keyword_match_simple(self):
        """测试简单关键词匹配"""
        text = "Hello World"
        keywords = ["hello"]
        
        result = any(kw in text.lower() for kw in keywords)
        
        assert result is True
    
    def test_keyword_match_multiple(self):
        """测试多关键词匹配"""
        text = "Hello World Test"
        keywords = ["hello", "test"]
        
        result = any(kw in text.lower() for kw in keywords)
        
        assert result is True
    
    def test_keyword_no_match(self):
        """测试无匹配"""
        text = "Hello World"
        keywords = ["python", "java"]
        
        result = any(kw in text.lower() for kw in keywords)
        
        assert result is False
    
    def test_keyword_case_insensitive(self):
        """测试大小写不敏感"""
        text = "HELLO WORLD"
        keywords = ["hello"]
        
        result = any(kw in text.lower() for kw in keywords)
        
        assert result is True


class TestOCRIntervalManagement:
    """OCR间隔管理测试"""
    
    @pytest.fixture
    def ocr_module(self, mock_app, create_mock_ocr_group):
        mock_app.ocr_groups = [
            create_mock_ocr_group(enabled=True, interval="3"),
            create_mock_ocr_group(enabled=True, interval="5"),
            create_mock_ocr_group(enabled=False, interval="1"),
        ]
        return OCRModule(mock_app)
    
    def test_min_interval_calculation(self, ocr_module):
        """测试最小间隔计算"""
        result = ocr_module._calculate_min_interval()
        
        assert result == 3
    
    def test_interval_waiting(self, ocr_module):
        """测试间隔等待"""
        ocr_module.app.is_running = True
        
        start = time.time()
        ocr_module._wait_for_interval(1)
        elapsed = time.time() - start
        
        assert elapsed >= 0.9
    
    def test_interval_interrupted(self, ocr_module):
        """测试间隔中断"""
        ocr_module.app.is_running = False
        
        start = time.time()
        ocr_module._wait_for_interval(5)
        elapsed = time.time() - start
        
        assert elapsed < 1
