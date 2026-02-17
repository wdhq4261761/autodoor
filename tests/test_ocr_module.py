import pytest
import time
import threading
from unittest.mock import MagicMock, patch
from modules.ocr import OCRModule


class TestOCRModule:
    """OCRModule测试类"""
    
    @pytest.fixture
    def ocr_module(self, mock_app):
        """创建OCR模块实例"""
        return OCRModule(mock_app)
    
    def test_init(self, ocr_module):
        """测试初始化"""
        assert ocr_module.last_recognition_times == {}
        assert ocr_module.last_trigger_times == {}
    
    def test_priority(self):
        """测试优先级"""
        assert OCRModule.PRIORITY == 3
    
    def test_stop_monitoring(self, ocr_module):
        """测试停止监控"""
        ocr_module.app.is_running = True
        
        ocr_module.stop_monitoring()
        
        assert ocr_module.app.is_running is False


class TestOCRIntervalCalculation:
    """OCR间隔计算测试"""
    
    @pytest.fixture
    def ocr_module(self, mock_app, create_mock_ocr_group):
        mock_app.ocr_groups = [
            create_mock_ocr_group(enabled=True, interval="5"),
            create_mock_ocr_group(enabled=True, interval="10"),
            create_mock_ocr_group(enabled=False, interval="3"),
        ]
        return OCRModule(mock_app)
    
    def test_calculate_min_interval(self, ocr_module):
        """测试计算最小间隔"""
        result = ocr_module._calculate_min_interval()
        
        assert result == 5
    
    def test_calculate_min_interval_no_enabled(self, mock_app):
        """测试没有启用组时的间隔"""
        mock_app.ocr_groups = []
        ocr_module = OCRModule(mock_app)
        
        result = ocr_module._calculate_min_interval()
        
        assert result == 5


class TestOCRGroupValidation:
    """OCR组验证测试"""
    
    @pytest.fixture
    def ocr_module(self, mock_app, create_mock_ocr_group):
        mock_app.ocr_groups = [create_mock_ocr_group()]
        return OCRModule(mock_app)
    
    def test_validate_region_coordinates_valid(self, ocr_module):
        """测试有效区域坐标"""
        result = ocr_module._validate_region_coordinates((10, 10, 100, 100), 0)
        
        assert result[0] is True
        assert result[1] == 10
        assert result[2] == 10
        assert result[3] == 100
        assert result[4] == 100
    
    def test_validate_region_coordinates_too_small(self, ocr_module):
        """测试区域太小"""
        result = ocr_module._validate_region_coordinates((0, 0, 5, 5), 0)
        
        assert result[0] is False
    
    def test_validate_region_coordinates_swapped(self, ocr_module):
        """测试交换坐标"""
        result = ocr_module._validate_region_coordinates((100, 100, 10, 10), 0)
        
        assert result[0] is True
        assert result[1] == 10
        assert result[2] == 10
        assert result[3] == 100
        assert result[4] == 100
    
    def test_validate_region_coordinates_invalid_format(self, ocr_module):
        """测试无效格式"""
        result = ocr_module._validate_region_coordinates((10, 10, 100), 0)
        
        assert result[0] is False
    
    def test_validate_region_coordinates_none(self, ocr_module):
        """测试None值"""
        result = ocr_module._validate_region_coordinates(None, 0)
        
        assert result[0] is False


class TestOCRShouldProcessGroup:
    """OCR组处理判断测试"""
    
    @pytest.fixture
    def ocr_module(self, mock_app, create_mock_ocr_group):
        mock_app.ocr_groups = [create_mock_ocr_group(enabled=True, interval="5")]
        ocr_module = OCRModule(mock_app)
        ocr_module.last_recognition_times = {0: 0}
        ocr_module.last_trigger_times = {0: 0}
        return ocr_module
    
    def test_should_process_group_disabled(self, ocr_module):
        """测试禁用组"""
        ocr_module.app.ocr_groups[0]["enabled"].set(False)
        
        result = ocr_module._should_process_group(ocr_module.app.ocr_groups[0], 0, time.time())
        
        assert result is False
    
    def test_should_process_group_no_region(self, ocr_module):
        """测试无区域"""
        ocr_module.app.ocr_groups[0]["region"] = None
        
        result = ocr_module._should_process_group(ocr_module.app.ocr_groups[0], 0, time.time())
        
        assert result is False
    
    def test_should_process_group_in_pause(self, ocr_module):
        """测试暂停期"""
        ocr_module.last_trigger_times[0] = time.time()
        
        result = ocr_module._should_process_group(ocr_module.app.ocr_groups[0], 0, time.time())
        
        assert result is False


class TestOCRWaitForInterval:
    """OCR等待间隔测试"""
    
    @pytest.fixture
    def ocr_module(self, mock_app):
        mock_app.is_running = True
        return OCRModule(mock_app)
    
    def test_wait_for_interval(self, ocr_module):
        """测试等待间隔"""
        start = time.time()
        ocr_module._wait_for_interval(1)
        elapsed = time.time() - start
        
        assert elapsed >= 0.9
    
    def test_wait_for_interval_stopped(self, ocr_module):
        """测试等待期间停止"""
        ocr_module.app.is_running = False
        
        start = time.time()
        ocr_module._wait_for_interval(5)
        elapsed = time.time() - start
        
        assert elapsed < 1


class TestOCRGroupInputValidation:
    """OCR组输入验证测试"""
    
    @pytest.fixture
    def ocr_module(self, mock_app, create_mock_ocr_group):
        mock_app.ocr_groups = [create_mock_ocr_group(keywords="test", language="eng", click=False)]
        return OCRModule(mock_app)
    
    def test_validate_ocr_group_input_none_group(self, ocr_module):
        """测试空组"""
        result = ocr_module._validate_ocr_group_input(None, 0)
        
        assert result[0] is False
    
    def test_validate_ocr_group_input_no_region(self, ocr_module):
        """测试无区域"""
        group = ocr_module.app.ocr_groups[0]
        group["region"] = None
        
        result = ocr_module._validate_ocr_group_input(group, 0)
        
        assert result[0] is False
