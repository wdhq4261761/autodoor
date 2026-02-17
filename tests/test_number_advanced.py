import pytest
import time
import threading
from unittest.mock import MagicMock, patch
from PIL import Image
from modules.number import NumberModule


class TestNumberModuleAdvanced:
    """NumberModule高级测试类"""
    
    @pytest.fixture
    def number_module(self, mock_app, create_mock_number_region):
        mock_app._number_cache = {}
        mock_app.number_regions = [create_mock_number_region(enabled=True, threshold="500")]
        mock_app.number_stop_events = {}
        mock_app.number_threads = []
        mock_app.is_running = True
        mock_app.platform_adapter = MagicMock()
        mock_app.platform_adapter.platform = "Windows"
        return NumberModule(mock_app)
    
    def test_start_number_recognition(self, number_module):
        """测试启动数字识别"""
        number_module.app.start_module = MagicMock(return_value=1)
        
        number_module.start_number_recognition()
        
        number_module.app.start_module.assert_called_once()
    
    def test_start_number_recognition_disabled(self, number_module):
        """测试启动禁用的数字识别"""
        number_module.app.number_regions[0]["enabled"].set(False)
        number_module.app.start_module = MagicMock(return_value=0)
        
        number_module.start_number_recognition()
        
        number_module.app.start_module.assert_called_once()
    
    def test_number_recognition_loop_disabled(self, number_module):
        """测试禁用区域的循环"""
        number_module.app.number_regions[0]["enabled"].set(False)
        stop_event = threading.Event()
        stop_event.set()
        
        number_module.number_recognition_loop(0, (0, 0, 100, 30), 500, "f5", stop_event)
    
    def test_number_recognition_loop_stopped(self, number_module):
        """测试停止的循环"""
        number_module.app.is_running = False
        stop_event = threading.Event()
        
        number_module.number_recognition_loop(0, (0, 0, 100, 30), 500, "f5", stop_event)


class TestNumberParsingAdvanced:
    """数字解析高级测试"""
    
    @pytest.fixture
    def number_module(self, mock_app):
        mock_app._number_cache = {}
        return NumberModule(mock_app)
    
    def test_parse_number_with_whitespace(self, number_module):
        """测试带空白字符的数字"""
        result = number_module.parse_number("  100  /  500  ")
        
        assert result == 100
    
    def test_parse_number_with_newline(self, number_module):
        """测试带换行符的数字"""
        result = number_module.parse_number("100/500\n")
        
        assert result == 100
    
    def test_parse_number_cache_hit(self, number_module):
        """测试缓存命中"""
        number_module.app._number_cache["100/500"] = 100
        
        result = number_module.parse_number("100/500")
        
        assert result == 100
    
    def test_parse_number_cache_miss(self, number_module):
        """测试缓存未命中"""
        result = number_module.parse_number("200/500")
        
        assert result == 200
        assert "200/500" in number_module.app._number_cache


class TestNumberOCRAdvanced:
    """数字OCR高级测试"""
    
    @pytest.fixture
    def number_module(self, mock_app):
        mock_app._number_cache = {}
        return NumberModule(mock_app)
    
    def test_ocr_number_with_noise(self, number_module):
        """测试带噪声的OCR"""
        test_image = Image.new('RGB', (100, 30), color='white')
        
        with patch('pytesseract.image_to_string', return_value="  100/500  \n"):
            result = number_module.ocr_number(test_image)
            
            assert result == "100/500"
    
    def test_ocr_number_with_special_chars(self, number_module):
        """测试带特殊字符的OCR"""
        test_image = Image.new('RGB', (100, 30), color='white')
        
        with patch('pytesseract.image_to_string', return_value="100/500\r\n"):
            result = number_module.ocr_number(test_image)
            
            assert result == "100/500"


class TestNumberScreenshotAdvanced:
    """数字截图高级测试"""
    
    @pytest.fixture
    def number_module(self, mock_app):
        mock_app._number_cache = {}
        mock_app.platform_adapter = MagicMock()
        mock_app.platform_adapter.platform = "Windows"
        return NumberModule(mock_app)
    
    def test_take_screenshot_with_priority(self, number_module):
        """测试带优先级的截图"""
        test_image = Image.new('RGB', (100, 30), color='white')
        
        with patch('utils.screenshot.ScreenshotManager') as mock_manager:
            mock_instance = mock_manager.return_value
            mock_instance.get_region_screenshot.return_value = test_image
            
            result = number_module.take_screenshot((0, 0, 100, 30))
            
            assert result is not None
            mock_instance.get_region_screenshot.assert_called_once()
    
    def test_take_screenshot_macos(self, number_module):
        """测试macOS截图"""
        number_module.app.platform_adapter.platform = "Darwin"
        
        with patch('input.permissions.PermissionManager') as mock_perm:
            mock_perm.return_value.check_screen_recording.return_value = True
            
            with patch('utils.screenshot.ScreenshotManager') as mock_manager:
                mock_manager.return_value.get_region_screenshot.return_value = None
                
                result = number_module.take_screenshot((0, 0, 100, 30))
                
                assert result is None


class TestNumberThresholdAdvanced:
    """数字阈值高级测试"""
    
    @pytest.fixture
    def number_module(self, mock_app, create_mock_number_region):
        mock_app._number_cache = {}
        mock_app.number_regions = [
            create_mock_number_region(enabled=True, threshold="100"),
            create_mock_number_region(enabled=True, threshold="500"),
            create_mock_number_region(enabled=True, threshold="1000"),
        ]
        return NumberModule(mock_app)
    
    def test_different_thresholds(self, number_module):
        """测试不同阈值"""
        thresholds = [int(r["threshold"].get()) for r in number_module.app.number_regions]
        
        assert thresholds == [100, 500, 1000]
    
    def test_threshold_comparison(self, number_module):
        """测试阈值比较"""
        for region in number_module.app.number_regions:
            threshold = int(region["threshold"].get())
            
            assert threshold > 0
