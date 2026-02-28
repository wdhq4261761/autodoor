import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import numpy as np
import os
import tempfile

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


@pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not installed")
class TestImageDetection:
    """图像检测类测试"""
    
    @pytest.fixture
    def mock_app(self):
        """创建模拟应用实例"""
        app = Mock()
        app.logging_manager = Mock()
        app.platform_adapter = Mock()
        app.platform_adapter.platform = "Windows"
        app.input_controller = Mock()
        app.alarm_module = Mock()
        app.status_var = Mock()
        app.root = Mock()
        app.event_queue = Mock()
        app.event_queue.empty = Mock(return_value=True)
        app.image_groups = []
        return app
    
    @pytest.fixture
    def image_detection(self, mock_app):
        """创建图像检测实例"""
        from modules.image import ImageDetection
        return ImageDetection(mock_app)
    
    def test_init(self, image_detection):
        """测试初始化"""
        assert image_detection.is_running == False
        assert image_detection.region is None
        assert image_detection.template_image is None
        assert image_detection.threshold == 0.8
        assert image_detection.interval == 5.0
        assert image_detection.pause == 180
    
    def test_set_region(self, image_detection):
        """测试设置区域"""
        region = (100, 100, 300, 200)
        image_detection.set_region(region)
        assert image_detection.region == region
    
    def test_set_reference_image_valid(self, image_detection):
        """测试设置参考图像 - 有效图像"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
            image = Image.new('RGB', (50, 50), color='white')
            image.save(temp_path)
        
        try:
            result = image_detection.set_reference_image(temp_path)
            assert result == True
            assert image_detection.template_image is not None
            assert image_detection.template_path == temp_path
        finally:
            os.unlink(temp_path)
    
    def test_set_reference_image_invalid_path(self, image_detection):
        """测试设置参考图像 - 无效路径"""
        result = image_detection.set_reference_image("/nonexistent/path.png")
        assert result == False
        assert image_detection.template_image is None
    
    def test_detect_image_no_region(self, image_detection):
        """测试图像检测 - 无区域"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
            image = Image.new('RGB', (50, 50), color='white')
            image.save(temp_path)
        
        try:
            image_detection.set_reference_image(temp_path)
            result = image_detection.detect_image()
            assert result is None
        finally:
            os.unlink(temp_path)
    
    def test_detect_image_no_template(self, image_detection):
        """测试图像检测 - 无模板"""
        image_detection.region = (0, 0, 100, 100)
        result = image_detection.detect_image()
        assert result is None
    
    @patch('utils.screenshot.ScreenshotManager.get_region_screenshot')
    def test_detect_image_match(self, mock_capture, image_detection):
        """测试图像检测 - 匹配情况"""
        template = np.zeros((50, 50, 3), dtype=np.uint8)
        template[:] = (255, 255, 255)
        image_detection.template_image = template
        image_detection.region = (0, 0, 100, 100)
        image_detection.threshold = 0.8
        
        screenshot = Image.new('RGB', (100, 100), color='white')
        mock_capture.return_value = screenshot
        
        result = image_detection.detect_image()
        assert result is not None
        assert len(result) == 3
    
    def test_stop_detection(self, image_detection):
        """测试停止检测"""
        image_detection.is_running = True
        image_detection.stop_detection()
        assert image_detection.is_running == False


@pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not installed")
class TestImageDetectionManager:
    """图像检测管理器测试"""
    
    @pytest.fixture
    def mock_app(self):
        """创建模拟应用实例"""
        app = Mock()
        app.logging_manager = Mock()
        app.image_groups = []
        app.status_var = Mock()
        app.status_labels = {}
        return app
    
    @pytest.fixture
    def manager(self, mock_app):
        """创建管理器实例"""
        from modules.image import ImageDetectionManager
        return ImageDetectionManager(mock_app)
    
    def test_init(self, manager):
        """测试初始化"""
        assert manager.image_detections == {}
    
    def test_start_all_detection_no_groups(self, manager, mock_app):
        """测试开始所有检测 - 无检测组"""
        from tkinter import messagebox
        with patch.object(messagebox, 'showwarning') as mock_warning:
            manager.start_all_detection()
            mock_warning.assert_called_once()
    
    def test_stop_all_detection(self, manager, mock_app):
        """测试停止所有检测"""
        manager.image_detections = {0: Mock()}
        manager.stop_all_detection()
        assert len(manager.image_detections) == 0


class TestTemplateMatching:
    """模板匹配测试"""
    
    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not installed")
    def test_template_matching_identical(self):
        """测试相同图像的模板匹配"""
        template = np.zeros((50, 50, 3), dtype=np.uint8)
        template[:] = (255, 255, 255)
        
        screenshot = np.zeros((100, 100, 3), dtype=np.uint8)
        screenshot[:] = (255, 255, 255)
        
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        assert max_val > 0.99
    
    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not installed")
    def test_template_matching_partial(self):
        """测试部分匹配的模板匹配"""
        template = np.zeros((50, 50, 3), dtype=np.uint8)
        template[:] = (255, 255, 255)
        
        screenshot = np.zeros((100, 100, 3), dtype=np.uint8)
        screenshot[25:75, 25:75] = (255, 255, 255)
        
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        assert max_val > 0.5
    
    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not installed")
    def test_template_size_check(self):
        """测试模板尺寸检查"""
        template = np.zeros((50, 50, 3), dtype=np.uint8)
        screenshot = np.zeros((100, 100, 3), dtype=np.uint8)
        
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        
        assert result.shape == (51, 51)
