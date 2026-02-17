import pytest
import time
from unittest.mock import MagicMock, patch
from modules.number import NumberModule


class TestNumberModuleComprehensive:
    """NumberModule综合测试类"""
    
    @pytest.fixture
    def number_module(self, mock_app, create_mock_number_region):
        mock_app._number_cache = {}
        mock_app.number_regions = [
            create_mock_number_region(enabled=True, threshold="500", key="f5"),
            create_mock_number_region(enabled=True, threshold="1000", key="f6"),
        ]
        mock_app.number_stop_events = {}
        mock_app.number_threads = []
        mock_app.is_running = True
        mock_app.platform_adapter = MagicMock()
        mock_app.platform_adapter.platform = "Windows"
        return NumberModule(mock_app)
    
    def test_start_number_recognition_success(self, number_module):
        """测试成功启动数字识别"""
        number_module.app.start_module = MagicMock(return_value=2)
        
        number_module.start_number_recognition()
        
        number_module.app.start_module.assert_called_once()
    
    def test_stop_number_recognition(self, number_module):
        """测试停止数字识别"""
        number_module.app.number_stop_events = {0: MagicMock(), 1: MagicMock()}
        number_module.app.number_threads = [MagicMock(), MagicMock()]
        
        number_module.stop_number_recognition()
        
        assert len(number_module.app.number_stop_events) == 0
        assert len(number_module.app.number_threads) == 0
    
    def test_number_recognition_loop_disabled(self, number_module):
        """测试禁用区域的循环"""
        number_module.app.number_regions[0]["enabled"].set(False)
        stop_event = MagicMock()
        stop_event.is_set.return_value = True
        
        number_module.number_recognition_loop(0, (0, 0, 100, 30), 500, "f5", stop_event)
    
    def test_number_recognition_loop_stopped(self, number_module):
        """测试停止的循环"""
        number_module.app.is_running = False
        stop_event = MagicMock()
        stop_event.is_set.return_value = False
        
        number_module.number_recognition_loop(0, (0, 0, 100, 30), 500, "f5", stop_event)


class TestNumberParsingComprehensive:
    """数字解析综合测试"""
    
    @pytest.fixture
    def number_module(self, mock_app):
        mock_app._number_cache = {}
        return NumberModule(mock_app)
    
    def test_parse_various_formats(self, number_module):
        """测试各种格式解析"""
        test_cases = [
            ("100/500", 100),
            ("0/100", 0),
            ("999/1000", 999),
            ("  50 / 100  ", 50),
        ]
        
        for text, expected in test_cases:
            result = number_module.parse_number(text)
            assert result == expected
    
    def test_parse_invalid_formats(self, number_module):
        """测试无效格式"""
        invalid_cases = [
            "invalid",
            "",
            "/500",
            "abc/def",
        ]
        
        for text in invalid_cases:
            result = number_module.parse_number(text)
            assert result is None
    
    def test_cache_functionality(self, number_module):
        """测试缓存功能"""
        number_module.parse_number("100/500")
        
        assert "100/500" in number_module.app._number_cache
        
        number_module.parse_number("100/500")
        
        assert number_module.app._number_cache["100/500"] == 100


class TestNumberThresholdComparisonComprehensive:
    """数字阈值比较综合测试"""
    
    @pytest.fixture
    def number_module(self, mock_app, create_mock_number_region):
        mock_app._number_cache = {}
        mock_app.number_regions = [
            create_mock_number_region(enabled=True, threshold="500"),
            create_mock_number_region(enabled=True, threshold="1000"),
        ]
        return NumberModule(mock_app)
    
    def test_threshold_comparison_above(self, number_module):
        """测试阈值比较-高于"""
        threshold = int(number_module.app.number_regions[0]["threshold"].get())
        current = 600
        
        assert current >= threshold
    
    def test_threshold_comparison_below(self, number_module):
        """测试阈值比较-低于"""
        threshold = int(number_module.app.number_regions[0]["threshold"].get())
        current = 400
        
        assert current < threshold
    
    def test_threshold_comparison_equal(self, number_module):
        """测试阈值比较-等于"""
        threshold = int(number_module.app.number_regions[0]["threshold"].get())
        current = 500
        
        assert current == threshold
    
    def test_different_thresholds(self, number_module):
        """测试不同阈值"""
        thresholds = [int(r["threshold"].get()) for r in number_module.app.number_regions]
        
        assert thresholds[0] == 500
        assert thresholds[1] == 1000


class TestNumberOCRComprehensive:
    """数字OCR综合测试"""
    
    @pytest.fixture
    def number_module(self, mock_app):
        mock_app._number_cache = {}
        return NumberModule(mock_app)
    
    def test_ocr_with_various_results(self, number_module):
        """测试各种OCR结果"""
        from PIL import Image
        
        test_cases = [
            ("100/500", 100),
            ("0/100", 0),
            ("999/1000", 999),
        ]
        
        for ocr_result, expected in test_cases:
            with patch('pytesseract.image_to_string', return_value=ocr_result):
                test_image = Image.new('RGB', (100, 30), color='white')
                result = number_module.ocr_number(test_image)
                
                assert result == ocr_result
    
    def test_ocr_with_whitespace(self, number_module):
        """测试带空白的OCR结果"""
        from PIL import Image
        
        with patch('pytesseract.image_to_string', return_value="  100/500  \n"):
            test_image = Image.new('RGB', (100, 30), color='white')
            result = number_module.ocr_number(test_image)
            
            assert result == "100/500"
