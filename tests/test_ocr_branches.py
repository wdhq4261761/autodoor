import pytest
from unittest.mock import MagicMock, patch
from PIL import Image
from modules.ocr import OCRModule


class TestOCRPerformOCRException:
    """测试_perform_ocr异常处理"""
    
    @pytest.fixture
    def ocr_module(self, mock_app):
        return OCRModule(mock_app)
    
    def test_perform_ocr_success(self, ocr_module):
        """测试成功OCR"""
        test_image = Image.new('RGB', (100, 50), color='white')
        
        with patch('pytesseract.image_to_string', return_value="test text"):
            result = ocr_module._perform_ocr(test_image, "eng", 0)
            
            assert result == "test text"
    
    def test_perform_ocr_exception(self, ocr_module):
        """测试OCR异常"""
        test_image = Image.new('RGB', (100, 50), color='white')
        
        with patch('pytesseract.image_to_string', side_effect=Exception("OCR error")):
            result = ocr_module._perform_ocr(test_image, "eng", 0)
            
            assert result is None
    
    def test_perform_ocr_import_error(self, ocr_module):
        """测试pytesseract导入错误"""
        test_image = Image.new('RGB', (100, 50), color='white')
        
        with patch.dict('sys.modules', {'pytesseract': None}):
            with patch('builtins.__import__', side_effect=ImportError("No pytesseract")):
                result = ocr_module._perform_ocr(test_image, "eng", 0)
                
                assert result is None
    
    def test_perform_ocr_with_chinese(self, ocr_module):
        """测试中文OCR"""
        test_image = Image.new('RGB', (100, 50), color='white')
        
        with patch('pytesseract.image_to_string', return_value="测试文本"):
            result = ocr_module._perform_ocr(test_image, "chi_sim", 0)
            
            assert result == "测试文本"


class TestOCRValidateOCRGroupInput:
    """测试_validate_ocr_group_input函数"""
    
    @pytest.fixture
    def ocr_module(self, mock_app):
        return OCRModule(mock_app)
    
    def test_validate_ocr_group_input_none_group(self, ocr_module):
        """测试空组"""
        with patch('tkinter.StringVar') as mock_stringvar:
            mock_stringvar_instance = MagicMock()
            mock_stringvar_instance.get.return_value = ""
            mock_stringvar.return_value = mock_stringvar_instance
            
            valid, region, keywords, lang, click = ocr_module._validate_ocr_group_input(None, 0)
            
            assert valid is False
    
    def test_validate_ocr_group_input_no_region(self, ocr_module):
        """测试无区域"""
        group = {"region": None}
        
        with patch('tkinter.StringVar') as mock_stringvar, \
             patch('tkinter.BooleanVar') as mock_boolvar:
            mock_stringvar_instance = MagicMock()
            mock_stringvar_instance.get.return_value = ""
            mock_stringvar.return_value = mock_stringvar_instance
            
            mock_boolvar_instance = MagicMock()
            mock_boolvar_instance.get.return_value = False
            mock_boolvar.return_value = mock_boolvar_instance
            
            valid, region, keywords, lang, click = ocr_module._validate_ocr_group_input(group, 0)
            
            assert valid is False
    
    def test_validate_ocr_group_input_valid(self, ocr_module):
        """测试有效输入"""
        group = {
            "region": (0, 0, 100, 100),
            "keywords": MagicMock(),
            "language": MagicMock(),
            "click": MagicMock(),
        }
        group["keywords"].get.return_value = "test"
        group["language"].get.return_value = "eng"
        group["click"].get.return_value = False
        
        with patch('tkinter.StringVar') as mock_stringvar, \
             patch('tkinter.BooleanVar') as mock_boolvar:
            mock_stringvar_instance = MagicMock()
            mock_stringvar_instance.get.return_value = ""
            mock_stringvar.return_value = mock_stringvar_instance
            
            mock_boolvar_instance = MagicMock()
            mock_boolvar_instance.get.return_value = False
            mock_boolvar.return_value = mock_boolvar_instance
            
            valid, region, keywords, lang, click = ocr_module._validate_ocr_group_input(group, 0)
            
            assert valid is True
            assert region == (0, 0, 100, 100)
            assert keywords == "test"
            assert lang == "eng"
            assert click is False
    
    def test_validate_ocr_group_input_empty_keywords(self, ocr_module):
        """测试空关键词"""
        group = {
            "region": (0, 0, 100, 100),
            "keywords": MagicMock(),
            "language": MagicMock(),
            "click": MagicMock(),
        }
        group["keywords"].get.return_value = ""
        group["language"].get.return_value = "eng"
        group["click"].get.return_value = False
        
        with patch('tkinter.StringVar') as mock_stringvar, \
             patch('tkinter.BooleanVar') as mock_boolvar:
            mock_stringvar_instance = MagicMock()
            mock_stringvar_instance.get.return_value = ""
            mock_stringvar.return_value = mock_stringvar_instance
            
            mock_boolvar_instance = MagicMock()
            mock_boolvar_instance.get.return_value = False
            mock_boolvar.return_value = mock_boolvar_instance
            
            valid, region, keywords, lang, click = ocr_module._validate_ocr_group_input(group, 0)
            
            assert valid is True
            assert keywords == ""
    
    def test_validate_ocr_group_input_click_enabled(self, ocr_module):
        """测试启用点击"""
        group = {
            "region": (0, 0, 100, 100),
            "keywords": MagicMock(),
            "language": MagicMock(),
            "click": MagicMock(),
        }
        group["keywords"].get.return_value = "test"
        group["language"].get.return_value = "eng"
        group["click"].get.return_value = True
        
        with patch('tkinter.StringVar') as mock_stringvar, \
             patch('tkinter.BooleanVar') as mock_boolvar:
            mock_stringvar_instance = MagicMock()
            mock_stringvar_instance.get.return_value = ""
            mock_stringvar.return_value = mock_stringvar_instance
            
            mock_boolvar_instance = MagicMock()
            mock_boolvar_instance.get.return_value = False
            mock_boolvar.return_value = mock_boolvar_instance
            
            valid, region, keywords, lang, click = ocr_module._validate_ocr_group_input(group, 0)
            
            assert valid is True
            assert click is True


class TestOCRCalculateMinInterval:
    """测试_calculate_min_interval函数"""
    
    @pytest.fixture
    def ocr_module(self, mock_app):
        return OCRModule(mock_app)
    
    def test_calculate_min_interval_no_groups(self, ocr_module):
        """测试无组"""
        ocr_module.app.ocr_groups = []
        
        result = ocr_module._calculate_min_interval()
        
        assert result == 5
    
    def test_calculate_min_interval_single_group(self, ocr_module):
        """测试单个组"""
        ocr_module.app.ocr_groups = [{
            "enabled": MagicMock(),
            "interval": MagicMock(),
        }]
        ocr_module.app.ocr_groups[0]["enabled"].get.return_value = True
        ocr_module.app.ocr_groups[0]["interval"].get.return_value = "3"
        
        result = ocr_module._calculate_min_interval()
        
        assert result == 3
    
    def test_calculate_min_interval_multiple_groups(self, ocr_module):
        """测试多个组"""
        ocr_module.app.ocr_groups = [
            {"enabled": MagicMock(), "interval": MagicMock()},
            {"enabled": MagicMock(), "interval": MagicMock()},
            {"enabled": MagicMock(), "interval": MagicMock()},
        ]
        for i, group in enumerate(ocr_module.app.ocr_groups):
            group["enabled"].get.return_value = True
            group["interval"].get.return_value = str(5 + i * 2)
        
        result = ocr_module._calculate_min_interval()
        
        assert result == 5
    
    def test_calculate_min_interval_disabled_groups(self, ocr_module):
        """测试禁用组"""
        ocr_module.app.ocr_groups = [
            {"enabled": MagicMock(), "interval": MagicMock()},
            {"enabled": MagicMock(), "interval": MagicMock()},
        ]
        ocr_module.app.ocr_groups[0]["enabled"].get.return_value = False
        ocr_module.app.ocr_groups[0]["interval"].get.return_value = "1"
        ocr_module.app.ocr_groups[1]["enabled"].get.return_value = True
        ocr_module.app.ocr_groups[1]["interval"].get.return_value = "10"
        
        result = ocr_module._calculate_min_interval()
        
        assert result == 10
    
    def test_calculate_min_interval_invalid_interval(self, ocr_module):
        """测试无效间隔"""
        ocr_module.app.ocr_groups = [{
            "enabled": MagicMock(),
            "interval": MagicMock(),
        }]
        ocr_module.app.ocr_groups[0]["enabled"].get.return_value = True
        ocr_module.app.ocr_groups[0]["interval"].get.return_value = "invalid"
        
        result = ocr_module._calculate_min_interval()
        
        assert result == 5


class TestOCRShouldProcessGroup:
    """测试_should_process_group函数"""
    
    @pytest.fixture
    def ocr_module(self, mock_app):
        ocr_module_instance = OCRModule(mock_app)
        ocr_module_instance.last_recognition_times = {0: 0}
        ocr_module_instance.last_trigger_times = {0: 0}
        return ocr_module_instance
    
    def test_should_process_group_disabled(self, ocr_module):
        """测试禁用组"""
        group = {
            "enabled": MagicMock(),
            "region": (0, 0, 100, 100),
            "pause": MagicMock(),
            "interval": MagicMock(),
        }
        group["enabled"].get.return_value = False
        group["pause"].get.return_value = "180"
        group["interval"].get.return_value = "5"
        
        result = ocr_module._should_process_group(group, 0, 1000)
        
        assert result is False
    
    def test_should_process_group_no_region(self, ocr_module):
        """测试无区域"""
        group = {
            "enabled": MagicMock(),
            "region": None,
            "pause": MagicMock(),
            "interval": MagicMock(),
        }
        group["enabled"].get.return_value = True
        group["pause"].get.return_value = "180"
        group["interval"].get.return_value = "5"
        
        result = ocr_module._should_process_group(group, 0, 1000)
        
        assert result is False
    
    def test_should_process_group_in_pause_period(self, ocr_module):
        """测试暂停期"""
        group = {
            "enabled": MagicMock(),
            "region": (0, 0, 100, 100),
            "pause": MagicMock(),
            "interval": MagicMock(),
        }
        group["enabled"].get.return_value = True
        group["pause"].get.return_value = "180"
        group["interval"].get.return_value = "5"
        
        ocr_module.last_trigger_times[0] = 900
        
        result = ocr_module._should_process_group(group, 0, 1000)
        
        assert result is False
    
    def test_should_process_group_interval_not_elapsed(self, ocr_module):
        """测试间隔未到"""
        group = {
            "enabled": MagicMock(),
            "region": (0, 0, 100, 100),
            "pause": MagicMock(),
            "interval": MagicMock(),
        }
        group["enabled"].get.return_value = True
        group["pause"].get.return_value = "180"
        group["interval"].get.return_value = "10"
        
        ocr_module.last_recognition_times[0] = 995
        
        result = ocr_module._should_process_group(group, 0, 1000)
        
        assert result is False
    
    def test_should_process_group_valid(self, ocr_module):
        """测试有效处理"""
        group = {
            "enabled": MagicMock(),
            "region": (0, 0, 100, 100),
            "pause": MagicMock(),
            "interval": MagicMock(),
        }
        group["enabled"].get.return_value = True
        group["pause"].get.return_value = "180"
        group["interval"].get.return_value = "5"
        
        ocr_module.last_recognition_times[0] = 0
        ocr_module.last_trigger_times[0] = 0
        
        result = ocr_module._should_process_group(group, 0, 1000)
        
        assert result is True
    
    def test_should_process_group_invalid_pause(self, ocr_module):
        """测试无效暂停值"""
        group = {
            "enabled": MagicMock(),
            "region": (0, 0, 100, 100),
            "pause": MagicMock(),
            "interval": MagicMock(),
        }
        group["enabled"].get.return_value = True
        group["pause"].get.return_value = "invalid"
        group["interval"].get.return_value = "5"
        
        ocr_module.last_recognition_times[0] = 0
        ocr_module.last_trigger_times[0] = 0
        
        result = ocr_module._should_process_group(group, 0, 1000)
        
        assert result is True
