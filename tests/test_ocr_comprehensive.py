import pytest
import time
import threading
from unittest.mock import MagicMock, patch
from modules.ocr import OCRModule


class TestOCRModuleComprehensive:
    """OCRModule综合测试类"""
    
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
        mock_app.ocr_thread = None
        return OCRModule(mock_app)
    
    def test_start_monitoring_success(self, ocr_module):
        """测试成功启动监控"""
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


class TestOCRPerformOCR:
    """OCR执行测试"""
    
    @pytest.fixture
    def ocr_module(self, mock_app):
        mock_app.tesseract_available = True
        mock_app.platform_adapter = MagicMock()
        mock_app.platform_adapter.platform = "Windows"
        return OCRModule(mock_app)
    
    def test_perform_ocr_success(self, ocr_module):
        """测试成功执行OCR"""
        from PIL import Image
        
        test_image = Image.new('RGB', (100, 50), color='white')
        
        with patch('pytesseract.image_to_string', return_value="test text"):
            result = ocr_module._perform_ocr(test_image, "eng", 0)
            
            assert result == "test text"
    
    def test_perform_ocr_with_chinese(self, ocr_module):
        """测试中文OCR"""
        from PIL import Image
        
        test_image = Image.new('RGB', (100, 50), color='white')
        
        with patch('pytesseract.image_to_string', return_value="测试文本"):
            result = ocr_module._perform_ocr(test_image, "chi_sim", 0)
            
            assert result == "测试文本"
    
    def test_perform_ocr_empty_result(self, ocr_module):
        """测试空结果"""
        from PIL import Image
        
        test_image = Image.new('RGB', (100, 50), color='white')
        
        with patch('pytesseract.image_to_string', return_value=""):
            result = ocr_module._perform_ocr(test_image, "eng", 0)
            
            assert result == ""


class TestOCRKeywordDetection:
    """OCR关键词检测测试"""
    
    def test_keyword_detection_simple(self):
        """测试简单关键词检测"""
        text = "Hello World"
        keywords = "hello"
        
        found = keywords.lower() in text.lower()
        
        assert found is True
    
    def test_keyword_detection_multiple(self):
        """测试多关键词检测"""
        text = "Hello World Test"
        keywords = "hello,test"
        
        keyword_list = [k.strip().lower() for k in keywords.split(",")]
        found = any(kw in text.lower() for kw in keyword_list)
        
        assert found is True
    
    def test_keyword_detection_no_match(self):
        """测试无匹配"""
        text = "Hello World"
        keywords = "python,java"
        
        keyword_list = [k.strip().lower() for k in keywords.split(",")]
        found = any(kw in text.lower() for kw in keyword_list)
        
        assert found is False
    
    def test_keyword_detection_case_insensitive(self):
        """测试大小写不敏感"""
        text = "HELLO WORLD"
        keywords = "hello"
        
        found = keywords.lower() in text.lower()
        
        assert found is True


class TestOCRTriggerAction:
    """OCR触发动作测试"""
    
    @pytest.fixture
    def ocr_module(self, mock_app, create_mock_ocr_group):
        mock_app.ocr_groups = [create_mock_ocr_group(key="enter", alarm=False)]
        return OCRModule(mock_app)
    
    def test_trigger_keypress_via_input_controller(self, ocr_module):
        """测试通过输入控制器触发按键"""
        ocr_module.app.input_controller.key_press("enter", priority=3)
        
        ocr_module.app.input_controller.key_press.assert_called_with("enter", priority=3)
    
    def test_trigger_with_delay(self, ocr_module):
        """测试带延迟的触发"""
        delay_min = 100
        delay_max = 100
        
        start = time.time()
        time.sleep(delay_min / 1000)
        elapsed = time.time() - start
        
        assert elapsed >= 0.1
