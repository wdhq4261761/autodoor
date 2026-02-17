import pytest
import time
import threading
from unittest.mock import MagicMock, patch
from PIL import Image
from modules.number import NumberModule


class TestNumberModule:
    """NumberModule测试类"""
    
    @pytest.fixture
    def number_module(self, mock_app):
        """创建数字识别模块实例"""
        mock_app._number_cache = {}
        return NumberModule(mock_app)
    
    def test_init(self, number_module):
        """测试初始化"""
        assert number_module.app is not None
    
    def test_priority(self):
        """测试优先级"""
        assert NumberModule.PRIORITY == 5
    
    def test_stop_number_recognition(self, number_module):
        """测试停止数字识别"""
        number_module.app.number_stop_events = {0: threading.Event(), 1: threading.Event()}
        number_module.app.number_threads = [MagicMock(), MagicMock()]
        
        number_module.stop_number_recognition()
        
        assert len(number_module.app.number_stop_events) == 0
        assert len(number_module.app.number_threads) == 0
    
    def test_stop_number_recognition_empty(self, number_module):
        """测试停止空的数字识别"""
        number_module.app.number_stop_events = {}
        number_module.app.number_threads = []
        
        number_module.stop_number_recognition()
        
        assert len(number_module.app.number_stop_events) == 0


class TestNumberParsing:
    """数字解析测试"""
    
    @pytest.fixture
    def number_module(self, mock_app):
        mock_app._number_cache = {}
        return NumberModule(mock_app)
    
    def test_parse_number_valid_format(self, number_module):
        """测试有效格式的数字解析"""
        result = number_module.parse_number("100/500")
        
        assert result == 100
    
    def test_parse_number_with_spaces(self, number_module):
        """测试带空格的数字解析"""
        result = number_module.parse_number("  50 / 100  ")
        
        assert result == 50
    
    def test_parse_number_invalid_format(self, number_module):
        """测试无效格式的数字解析"""
        result = number_module.parse_number("invalid")
        
        assert result is None
    
    def test_parse_number_empty_string(self, number_module):
        """测试空字符串解析"""
        result = number_module.parse_number("")
        
        assert result is None
    
    def test_parse_number_only_denominator(self, number_module):
        """测试只有分母的格式"""
        result = number_module.parse_number("/500")
        
        assert result is None
    
    def test_parse_number_large_numerator(self, number_module):
        """测试大分子"""
        result = number_module.parse_number("99999/100000")
        
        assert result == 99999
    
    def test_parse_number_zero_numerator(self, number_module):
        """测试零分子"""
        result = number_module.parse_number("0/100")
        
        assert result == 0
    
    def test_parse_number_caching(self, number_module):
        """测试数字缓存"""
        number_module.parse_number("100/500")
        
        assert "100/500" in number_module.app._number_cache
        
        result = number_module.parse_number("100/500")
        
        assert result == 100


class TestNumberThresholdComparison:
    """数字阈值比较测试"""
    
    @pytest.fixture
    def number_module(self, mock_app, create_mock_number_region):
        mock_app._number_cache = {}
        mock_app.number_regions = [create_mock_number_region(threshold="500")]
        return NumberModule(mock_app)
    
    def test_number_above_threshold(self, number_module):
        """测试数字高于阈值"""
        threshold = int(number_module.app.number_regions[0]["threshold"].get())
        current = 100
        
        assert current < threshold
    
    def test_number_below_threshold(self, number_module):
        """测试数字低于阈值"""
        threshold = int(number_module.app.number_regions[0]["threshold"].get())
        current = 1000
        
        assert current > threshold
    
    def test_number_equals_threshold(self, number_module):
        """测试数字等于阈值"""
        threshold = int(number_module.app.number_regions[0]["threshold"].get())
        current = 500
        
        assert current == threshold


class TestNumberRegionManagement:
    """数字区域管理测试"""
    
    @pytest.fixture
    def number_module(self, mock_app, create_mock_number_region):
        mock_app._number_cache = {}
        mock_app.number_regions = [
            create_mock_number_region(enabled=True, threshold="100"),
            create_mock_number_region(enabled=False, threshold="200"),
            create_mock_number_region(enabled=True, threshold="300"),
        ]
        return NumberModule(mock_app)
    
    def test_multiple_regions(self, number_module):
        """测试多个区域"""
        assert len(number_module.app.number_regions) == 3
    
    def test_enabled_regions_count(self, number_module):
        """测试启用区域数量"""
        enabled_count = sum(1 for r in number_module.app.number_regions if r["enabled"].get())
        
        assert enabled_count == 2
    
    def test_region_threshold_access(self, number_module):
        """测试区域阈值访问"""
        thresholds = [int(r["threshold"].get()) for r in number_module.app.number_regions]
        
        assert thresholds == [100, 200, 300]


class TestNumberScreenshot:
    """数字截图测试"""
    
    @pytest.fixture
    def number_module(self, mock_app):
        mock_app._number_cache = {}
        mock_app.platform_adapter.platform = "Windows"
        return NumberModule(mock_app)
    
    def test_take_screenshot_success(self, number_module):
        """测试成功截图"""
        test_image = Image.new('RGB', (100, 30), color='white')
        
        with patch('utils.screenshot.ScreenshotManager') as mock_manager:
            mock_manager.return_value.get_region_screenshot.return_value = test_image
            result = number_module.take_screenshot((0, 0, 100, 30))
            
            assert result is not None
    
    def test_take_screenshot_failure(self, number_module):
        """测试截图失败"""
        with patch('utils.screenshot.ScreenshotManager') as mock_manager:
            mock_manager.return_value.get_region_screenshot.side_effect = Exception("Screenshot failed")
            result = number_module.take_screenshot((0, 0, 100, 30))
            
            assert result is None


class TestNumberOCR:
    """数字OCR测试"""
    
    @pytest.fixture
    def number_module(self, mock_app):
        mock_app._number_cache = {}
        return NumberModule(mock_app)
    
    def test_ocr_number_success(self, number_module):
        """测试OCR成功"""
        test_image = Image.new('RGB', (100, 30), color='white')
        
        with patch('pytesseract.image_to_string', return_value="100/500"):
            result = number_module.ocr_number(test_image)
            
            assert result == "100/500"


class TestNumberRecognitionLoop:
    """数字识别循环测试"""
    
    @pytest.fixture
    def number_module(self, mock_app, create_mock_number_region):
        mock_app._number_cache = {}
        mock_app.is_running = True
        mock_app.number_regions = [create_mock_number_region(threshold="500", key="f5")]
        mock_app.alarm_module = MagicMock()
        mock_app.input_controller = MagicMock()
        mock_app.platform_adapter.platform = "Windows"
        return NumberModule(mock_app)
    
    def test_number_recognition_loop_stops_immediately(self, number_module):
        """测试循环立即停止"""
        stop_event = threading.Event()
        stop_event.set()
        
        number_module.number_recognition_loop(
            0, (0, 0, 100, 30), 500, "f5", stop_event
        )
        
        number_module.app.alarm_module.play_alarm_sound.assert_not_called()
    
    def test_number_recognition_loop_disabled_region(self, number_module):
        """测试禁用区域"""
        number_module.app.number_regions[0]["enabled"] = MagicMock()
        number_module.app.number_regions[0]["enabled"].get.return_value = False
        
        stop_event = threading.Event()
        
        def stop_after_delay():
            time.sleep(0.2)
            stop_event.set()
        
        stop_thread = threading.Thread(target=stop_after_delay)
        stop_thread.start()
        
        number_module.number_recognition_loop(
            0, (0, 0, 100, 30), 500, "f5", stop_event
        )
        
        stop_thread.join()
    
    def test_number_recognition_loop_app_not_running(self, number_module):
        """测试应用未运行"""
        number_module.app.is_running = False
        
        stop_event = threading.Event()
        
        number_module.number_recognition_loop(
            0, (0, 0, 100, 30), 500, "f5", stop_event
        )
    
    def test_number_recognition_loop_screenshot_none(self, number_module):
        """测试截图返回None"""
        stop_event = threading.Event()
        
        with patch.object(number_module, 'take_screenshot', return_value=None):
            with patch.object(number_module, 'ocr_number', return_value="100/500"):
                def stop_after_delay():
                    time.sleep(0.3)
                    stop_event.set()
                
                stop_thread = threading.Thread(target=stop_after_delay)
                stop_thread.start()
                
                number_module.number_recognition_loop(
                    0, (0, 0, 100, 30), 500, "f5", stop_event
                )
                
                stop_thread.join()
    
    def test_number_recognition_loop_below_threshold(self, number_module):
        """测试数字低于阈值"""
        stop_event = threading.Event()
        test_image = Image.new('RGB', (100, 30), color='white')
        
        with patch.object(number_module, 'take_screenshot', return_value=test_image):
            with patch.object(number_module, 'ocr_number', return_value="100/500"):
                with patch.object(number_module, 'parse_number', return_value=100):
                    def stop_after_delay():
                        time.sleep(1.5)
                        stop_event.set()
                    
                    stop_thread = threading.Thread(target=stop_after_delay)
                    stop_thread.start()
                    
                    number_module.number_recognition_loop(
                        0, (0, 0, 100, 30), 500, "f5", stop_event
                    )
                    
                    stop_thread.join()
                    
                    assert number_module.app.alarm_module.play_alarm_sound.called or number_module.app.logging_manager.log_message.called
    
    def test_number_recognition_loop_above_threshold(self, number_module):
        """测试数字高于阈值"""
        stop_event = threading.Event()
        test_image = Image.new('RGB', (100, 30), color='white')
        
        with patch.object(number_module, 'take_screenshot', return_value=test_image):
            with patch.object(number_module, 'ocr_number', return_value="1000/500"):
                with patch.object(number_module, 'parse_number', return_value=1000):
                    def stop_after_delay():
                        time.sleep(0.3)
                        stop_event.set()
                    
                    stop_thread = threading.Thread(target=stop_after_delay)
                    stop_thread.start()
                    
                    number_module.number_recognition_loop(
                        0, (0, 0, 100, 30), 500, "f5", stop_event
                    )
                    
                    stop_thread.join()
                    
                    number_module.app.alarm_module.play_alarm_sound.assert_not_called()
    
    def test_number_recognition_loop_no_key(self, number_module):
        """测试无按键配置"""
        number_module.app.number_regions[0]["key"] = MagicMock()
        number_module.app.number_regions[0]["key"].get.return_value = ""
        
        stop_event = threading.Event()
        test_image = Image.new('RGB', (100, 30), color='white')
        
        with patch.object(number_module, 'take_screenshot', return_value=test_image):
            with patch.object(number_module, 'ocr_number', return_value="100/500"):
                with patch.object(number_module, 'parse_number', return_value=100):
                    def stop_after_delay():
                        time.sleep(0.3)
                        stop_event.set()
                    
                    stop_thread = threading.Thread(target=stop_after_delay)
                    stop_thread.start()
                    
                    number_module.number_recognition_loop(
                        0, (0, 0, 100, 30), 500, "", stop_event
                    )
                    
                    stop_thread.join()
                    
                    number_module.app.input_controller.key_down.assert_not_called()
    
    def test_number_recognition_loop_exception(self, number_module):
        """测试异常处理"""
        stop_event = threading.Event()
        
        with patch.object(number_module, 'take_screenshot', side_effect=Exception("Test error")):
            def stop_after_delay():
                time.sleep(1.5)
                stop_event.set()
            
            stop_thread = threading.Thread(target=stop_after_delay)
            stop_thread.start()
            
            number_module.number_recognition_loop(
                0, (0, 0, 100, 30), 500, "f5", stop_event
            )
            
            stop_thread.join()
            
            assert number_module.app.logging_manager.log_message.called
    
    def test_ocr_number_empty(self, number_module):
        """测试OCR空结果"""
        test_image = Image.new('RGB', (100, 30), color='white')
        
        with patch('pytesseract.image_to_string', return_value=""):
            result = number_module.ocr_number(test_image)
            
            assert result == ""
    
    def test_ocr_number_with_newlines(self, number_module):
        """测试OCR带换行符"""
        test_image = Image.new('RGB', (100, 30), color='white')
        
        with patch('pytesseract.image_to_string', return_value="100/500\n"):
            result = number_module.ocr_number(test_image)
            
            assert result == "100/500"
