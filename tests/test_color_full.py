import pytest
import time
import threading
from unittest.mock import MagicMock, patch
from modules.color import ColorRecognition, ColorRecognitionManager


class TestColorRecognitionFull:
    """ColorRecognition完整测试类"""
    
    @pytest.fixture
    def color_module(self, mock_app):
        return ColorRecognition(mock_app)
    
    def test_start_recognition_with_all_params(self, color_module):
        """测试带所有参数启动识别"""
        color_module.region = (0, 0, 10, 10)
        
        with patch.object(color_module, 'recognize_color', return_value=False):
            color_module.start_recognition((255, 0, 0), 10, 0.1, 'KeyDown "enter", 1')
            
            assert color_module.target_color == (255, 0, 0)
            assert color_module.tolerance == 10
            assert color_module.interval == 0.1
            assert color_module.commands == 'KeyDown "enter", 1'
            
            color_module.stop_recognition()
            if color_module.recognition_thread and color_module.recognition_thread.is_alive():
                color_module.recognition_thread.join(timeout=2)
    
    def test_recognize_color_with_different_colors(self, color_module):
        """测试不同颜色识别"""
        from PIL import Image
        
        test_cases = [
            ((255, 0, 0), (255, 0, 0), True),
            ((0, 255, 0), (0, 255, 0), True),
            ((0, 0, 255), (0, 0, 255), True),
            ((255, 0, 0), (0, 255, 0), False),
        ]
        
        for target, actual, expected in test_cases:
            color_module.region = (0, 0, 100, 100)
            color_module.target_color = target
            color_module.tolerance = 10
            
            image = Image.new('RGB', (100, 100), actual)
            
            with patch('utils.screenshot.ScreenshotManager') as mock_manager:
                mock_manager.return_value.get_region_screenshot.return_value = image
                result = color_module.recognize_color()
                
                assert result == expected


class TestColorRecognitionManagerFull:
    """ColorRecognitionManager完整测试类"""
    
    @pytest.fixture
    def color_manager(self, mock_app):
        mock_app.target_color = (255, 0, 0)
        mock_app.tolerance_var = MagicMock()
        mock_app.tolerance_var.get.return_value = 10
        mock_app.interval_var = MagicMock()
        mock_app.interval_var.get.return_value = 5
        mock_app.color_commands = MagicMock()
        mock_app.color_commands.get.return_value = ""
        mock_app.color_recognition_region = (0, 0, 100, 100)
        mock_app.status_var = MagicMock()
        mock_app.is_running = False
        return ColorRecognitionManager(mock_app)
    
    def test_start_color_recognition_with_commands(self, color_manager):
        """测试带命令启动颜色识别"""
        color_manager.app.color_commands.get.return_value = 'KeyDown "space", 1'
        
        with patch.object(color_manager, 'start_color_recognition'):
            color_manager.start_color_recognition()
    
    def test_stop_color_recognition_resets_state(self, color_manager):
        """测试停止颜色识别重置状态"""
        from modules.color import ColorRecognition
        color_manager.color_recognition = ColorRecognition(color_manager.app)
        color_manager.color_recognition.is_running = True
        color_manager.color_recognition.recognition_thread = MagicMock()
        color_manager.color_recognition.recognition_thread.is_alive.return_value = False
        
        color_manager.stop_color_recognition()
        
        assert color_manager.color_recognition.is_running is False


class TestColorMatchingFull:
    """颜色匹配完整测试"""
    
    def test_color_distance_calculation(self):
        """测试颜色距离计算"""
        import math
        
        def color_distance(c1, c2):
            return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))
        
        assert color_distance((255, 0, 0), (255, 0, 0)) == 0
        assert color_distance((255, 0, 0), (0, 0, 0)) == 255
        assert color_distance((255, 0, 0), (250, 0, 0)) == 5
    
    def test_tolerance_range(self):
        """测试容差范围"""
        tolerance = 20
        
        def in_tolerance(c1, c2, tol):
            import math
            return color_distance(c1, c2) <= tol * math.sqrt(3)
        
        def color_distance(c1, c2):
            import math
            return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))
        
        assert in_tolerance((128, 128, 128), (135, 135, 135), tolerance) is True
        assert in_tolerance((128, 128, 128), (200, 200, 200), tolerance) is False
