import pytest
import time
import threading
from unittest.mock import MagicMock, patch
from PIL import Image
from modules.number import NumberModule


class TestNumberModuleStartFunc:
    """测试start_number_recognition内部start_func"""
    
    @pytest.fixture
    def number_module(self, mock_app, create_mock_number_region):
        mock_app.number_regions = [
            create_mock_number_region(enabled=True, threshold="500", key="f5"),
            create_mock_number_region(enabled=False, threshold="1000", key="f6"),
            create_mock_number_region(enabled=True, threshold="300", key="f7"),
        ]
        mock_app.number_stop_events = {}
        mock_app.number_threads = []
        mock_app.start_module = MagicMock()
        mock_app.platform_adapter = MagicMock()
        mock_app.platform_adapter.platform = "Windows"
        return NumberModule(mock_app)
    
    def test_start_func_creates_threads_for_enabled_regions(self, number_module):
        """测试只为启用的区域创建线程"""
        start_func = None
        
        def capture_start_func(module_name, func):
            nonlocal start_func
            start_func = func
            return func()
        
        number_module.app.start_module = MagicMock(side_effect=capture_start_func)
        
        number_module.start_number_recognition()
        
        assert len(number_module.app.number_stop_events) == 2
        assert len(number_module.app.number_threads) == 2
        
        for stop_event in number_module.app.number_stop_events.values():
            stop_event.set()
        number_module.app.number_threads.clear()
    
    def test_start_func_handles_invalid_threshold(self, number_module):
        """测试处理无效阈值"""
        number_module.app.number_regions[0]["threshold"].set("invalid")
        
        start_func = None
        
        def capture_start_func(module_name, func):
            nonlocal start_func
            start_func = func
            return func()
        
        number_module.app.start_module = MagicMock(side_effect=capture_start_func)
        
        number_module.start_number_recognition()
        
        assert len(number_module.app.number_threads) == 2
        
        for stop_event in number_module.app.number_stop_events.values():
            stop_event.set()
        number_module.app.number_threads.clear()
    
    def test_start_func_handles_no_region(self, number_module):
        """测试处理无区域"""
        number_module.app.number_regions[0]["region"] = None
        
        start_func = None
        
        def capture_start_func(module_name, func):
            nonlocal start_func
            start_func = func
            return func()
        
        number_module.app.start_module = MagicMock(side_effect=capture_start_func)
        
        number_module.start_number_recognition()
        
        assert len(number_module.app.number_threads) == 1
        
        for stop_event in number_module.app.number_stop_events.values():
            stop_event.set()
        number_module.app.number_threads.clear()


class TestNumberModuleStop:
    """测试停止数字识别"""
    
    @pytest.fixture
    def number_module(self, mock_app, create_mock_number_region):
        mock_app.number_regions = [create_mock_number_region()]
        mock_app.number_stop_events = {}
        mock_app.number_threads = []
        mock_app.status_labels = {"number": MagicMock()}
        return NumberModule(mock_app)
    
    def test_stop_number_recognition_clears_events(self, number_module):
        """测试清除事件"""
        number_module.app.number_stop_events = {0: threading.Event(), 1: threading.Event()}
        
        number_module.stop_number_recognition()
        
        assert len(number_module.app.number_stop_events) == 0
    
    def test_stop_number_recognition_clears_threads(self, number_module):
        """测试清除线程"""
        number_module.app.number_threads = [MagicMock(), MagicMock()]
        
        number_module.stop_number_recognition()
        
        assert len(number_module.app.number_threads) == 0
    
    def test_stop_number_recognition_updates_status(self, number_module):
        """测试更新状态"""
        number_module.stop_number_recognition()
        
        number_module.app.status_labels["number"].set.assert_called_with("数字识别: 未运行")


class TestNumberModuleRecognitionLoop:
    """测试数字识别循环"""
    
    @pytest.fixture
    def number_module(self, mock_app, create_mock_number_region):
        mock_region = create_mock_number_region(enabled=True, threshold="500", key="f5")
        mock_region["alarm"] = MagicMock()
        mock_region["alarm"].get.return_value = False
        mock_app.number_regions = [mock_region]
        mock_app.number_stop_events = {}
        mock_app.number_threads = []
        mock_app.is_running = True
        mock_app.platform_adapter = MagicMock()
        mock_app.platform_adapter.platform = "Windows"
        mock_app._number_cache = {}
        return NumberModule(mock_app)
    
    def test_recognition_loop_disabled_region(self, number_module):
        """测试禁用区域的循环"""
        number_module.app.number_regions[0]["enabled"].set(False)
        stop_event = threading.Event()
        stop_event.set()
        
        number_module.number_recognition_loop(0, (0, 0, 100, 30), 500, "f5", stop_event)
    
    def test_recognition_loop_stopped_app(self, number_module):
        """测试应用停止的循环"""
        number_module.app.is_running = False
        stop_event = threading.Event()
        
        number_module.number_recognition_loop(0, (0, 0, 100, 30), 500, "f5", stop_event)
    
    def test_recognition_loop_with_alarm(self, number_module):
        """测试带报警的识别循环"""
        number_module.app.number_regions[0]["alarm"].get.return_value = True
        stop_event = threading.Event()
        stop_event.set()
        
        number_module.number_recognition_loop(0, (0, 0, 100, 30), 500, "f5", stop_event)
    
    def test_recognition_loop_empty_key(self, number_module):
        """测试空按键的识别循环"""
        stop_event = threading.Event()
        stop_event.set()
        
        number_module.number_recognition_loop(0, (0, 0, 100, 30), 500, "", stop_event)


class TestNumberModuleTakeScreenshot:
    """测试截图功能"""
    
    @pytest.fixture
    def number_module(self, mock_app):
        mock_app.platform_adapter = MagicMock()
        mock_app.platform_adapter.platform = "Windows"
        mock_app.logging_manager = MagicMock()
        return NumberModule(mock_app)
    
    def test_take_screenshot_windows(self, number_module):
        """测试Windows截图"""
        test_image = Image.new('RGB', (100, 30), color='white')
        
        with patch('utils.screenshot.ScreenshotManager') as mock_manager:
            mock_instance = MagicMock()
            mock_manager.return_value = mock_instance
            mock_instance.get_region_screenshot.return_value = test_image
            
            result = number_module.take_screenshot((0, 0, 100, 30))
            
            assert result is not None
    
    def test_take_screenshot_macos_with_permission(self, number_module):
        """测试macOS有权限截图"""
        number_module.app.platform_adapter.platform = "Darwin"
        test_image = Image.new('RGB', (100, 30), color='white')
        
        with patch('input.permissions.PermissionManager') as mock_pm:
            mock_pm_instance = MagicMock()
            mock_pm.return_value = mock_pm_instance
            mock_pm_instance.check_screen_recording.return_value = True
            
            with patch('utils.screenshot.ScreenshotManager') as mock_manager:
                mock_instance = MagicMock()
                mock_manager.return_value = mock_instance
                mock_instance.get_region_screenshot.return_value = test_image
                
                result = number_module.take_screenshot((0, 0, 100, 30))
                
                assert result is not None
    
    def test_take_screenshot_macos_no_permission(self, number_module):
        """测试macOS无权限截图"""
        number_module.app.platform_adapter.platform = "Darwin"
        number_module.app.root = MagicMock()
        number_module.app.root.after = MagicMock()
        number_module.app._guide_screen_recording_setup = MagicMock()
        
        with patch('modules.number.PermissionManager') as mock_pm:
            mock_pm_instance = MagicMock()
            mock_pm.return_value = mock_pm_instance
            mock_pm_instance.check_screen_recording.return_value = False
            
            result = number_module.take_screenshot((0, 0, 100, 30))
            
            assert result is None
    
    def test_take_screenshot_exception(self, number_module):
        """测试截图异常"""
        with patch('utils.screenshot.ScreenshotManager') as mock_manager:
            mock_manager.return_value.get_region_screenshot.side_effect = Exception("Screenshot failed")
            
            result = number_module.take_screenshot((0, 0, 100, 30))
            
            assert result is None


class TestNumberModuleOCR:
    """测试OCR功能"""
    
    @pytest.fixture
    def number_module(self, mock_app):
        return NumberModule(mock_app)
    
    def test_ocr_number_success(self, number_module):
        """测试OCR成功"""
        test_image = Image.new('RGB', (100, 30), color='white')
        
        with patch('pytesseract.image_to_string', return_value="100/500"):
            result = number_module.ocr_number(test_image)
            
            assert result == "100/500"
    
    def test_ocr_number_with_newlines(self, number_module):
        """测试OCR带换行符"""
        test_image = Image.new('RGB', (100, 30), color='white')
        
        with patch('pytesseract.image_to_string', return_value="100/500\n"):
            result = number_module.ocr_number(test_image)
            
            assert result == "100/500"
    
    def test_ocr_number_empty(self, number_module):
        """测试OCR空结果"""
        test_image = Image.new('RGB', (100, 30), color='white')
        
        with patch('pytesseract.image_to_string', return_value=""):
            result = number_module.ocr_number(test_image)
            
            assert result == ""
    
    def test_ocr_number_converts_to_grayscale(self, number_module):
        """测试转换为灰度图"""
        test_image = Image.new('RGB', (100, 30), color='red')
        
        with patch('pytesseract.image_to_string', return_value="test") as mock_ocr:
            number_module.ocr_number(test_image)
            
            assert mock_ocr.called


class TestNumberModuleParseNumber:
    """测试数字解析"""
    
    @pytest.fixture
    def number_module(self, mock_app):
        mock_app._number_cache = {}
        mock_app.logging_manager = MagicMock()
        return NumberModule(mock_app)
    
    def test_parse_number_valid(self, number_module):
        """测试有效数字解析"""
        result = number_module.parse_number("100/500")
        
        assert result == 100
    
    def test_parse_number_with_spaces(self, number_module):
        """测试带空格的数字"""
        result = number_module.parse_number("  50 / 100  ")
        
        assert result == 50
    
    def test_parse_number_empty(self, number_module):
        """测试空字符串"""
        result = number_module.parse_number("")
        
        assert result is None
    
    def test_parse_number_whitespace_only(self, number_module):
        """测试只有空白"""
        result = number_module.parse_number("   ")
        
        assert result is None
    
    def test_parse_number_invalid_format(self, number_module):
        """测试无效格式"""
        result = number_module.parse_number("invalid")
        
        assert result is None
    
    def test_parse_number_cache_hit(self, number_module):
        """测试缓存命中"""
        number_module.app._number_cache["100/500"] = 100
        
        result = number_module.parse_number("100/500")
        
        assert result == 100
    
    def test_parse_number_caches_result(self, number_module):
        """测试缓存结果"""
        number_module.parse_number("200/500")
        
        assert "200/500" in number_module.app._number_cache
        assert number_module.app._number_cache["200/500"] == 200
    
    def test_parse_number_case_insensitive_cache(self, number_module):
        """测试缓存大小写不敏感"""
        number_module.app._number_cache["100/500"] = 100
        
        result = number_module.parse_number("100/500")
        
        assert result == 100
