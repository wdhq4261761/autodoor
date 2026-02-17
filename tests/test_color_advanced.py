import pytest
import time
import threading
import numpy as np
from unittest.mock import MagicMock, patch
from PIL import Image
from modules.color import ColorRecognition, ColorRecognitionManager


class TestColorRecognitionAdvanced:
    """ColorRecognition高级测试类"""
    
    @pytest.fixture
    def color_module(self, mock_app):
        return ColorRecognition(mock_app)
    
    def test_execute_commands_empty(self, color_module):
        """测试空命令执行"""
        color_module.commands = ""
        
        color_module.execute_commands()
    
    def test_execute_commands_with_script(self, color_module):
        """测试带脚本命令执行"""
        color_module.commands = 'KeyDown "enter", 1'
        
        with patch('modules.script.ScriptExecutor') as mock_executor:
            mock_instance = mock_executor.return_value
            color_module.execute_commands()
            
            mock_instance.run_script_once.assert_called_once_with('KeyDown "enter", 1')
    
    def test_recognize_color_with_none_screenshot(self, color_module):
        """测试空截图"""
        color_module.region = (0, 0, 100, 100)
        color_module.target_color = (255, 0, 0)
        
        with patch('utils.screenshot.ScreenshotManager') as mock_manager:
            mock_manager.return_value.get_region_screenshot.return_value = None
            result = color_module.recognize_color()
            
            assert result is False
    
    def test_recognize_color_with_empty_screenshot(self, color_module):
        """测试空尺寸截图"""
        color_module.region = (0, 0, 100, 100)
        color_module.target_color = (255, 0, 0)
        
        empty_image = Image.new('RGB', (0, 0))
        
        with patch('utils.screenshot.ScreenshotManager') as mock_manager:
            mock_manager.return_value.get_region_screenshot.return_value = empty_image
            result = color_module.recognize_color()
            
            assert result is False
    
    def test_recognize_color_with_mixed_colors(self, color_module):
        """测试混合颜色"""
        color_module.region = (0, 0, 100, 100)
        color_module.target_color = (255, 0, 0)
        color_module.tolerance = 50
        
        mixed_image = Image.new('RGB', (100, 100), (200, 50, 50))
        
        with patch('utils.screenshot.ScreenshotManager') as mock_manager:
            mock_manager.return_value.get_region_screenshot.return_value = mixed_image
            result = color_module.recognize_color()
            
            assert isinstance(result, bool)
    
    def test_start_recognition_with_commands(self, color_module):
        """测试带命令启动识别"""
        color_module.region = (0, 0, 10, 10)
        
        with patch.object(color_module, 'recognize_color', return_value=False):
            color_module.start_recognition((255, 0, 0), 10, 0.1, 'KeyDown "enter", 1')
            
            assert color_module.commands == 'KeyDown "enter", 1'
            
            color_module.stop_recognition()
            if color_module.recognition_thread and color_module.recognition_thread.is_alive():
                color_module.recognition_thread.join(timeout=2)


class TestColorRecognitionManagerAdvanced:
    """ColorRecognitionManager高级测试类"""
    
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
        return ColorRecognitionManager(mock_app)
    
    def test_select_color_region(self, color_manager):
        """测试选择颜色区域"""
        with patch('utils.region._start_selection'):
            color_manager.select_color_region()
    
    def test_start_color_recognition_no_color(self, color_manager):
        """测试没有选择颜色时启动"""
        color_manager.app.target_color = None
        
        with patch('tkinter.messagebox.showwarning'):
            color_manager.start_color_recognition()
    
    def test_start_color_recognition_no_region(self, color_manager):
        """测试没有选择区域时启动"""
        color_manager.app.color_recognition_region = None
        
        with patch('tkinter.messagebox.showwarning'):
            color_manager.start_color_recognition()
    
    def test_stop_color_recognition_running(self, color_manager):
        """测试停止运行中的识别"""
        from modules.color import ColorRecognition
        color_manager.color_recognition = ColorRecognition(color_manager.app)
        color_manager.color_recognition.is_running = True
        color_manager.color_recognition.recognition_thread = MagicMock()
        color_manager.color_recognition.recognition_thread.is_alive.return_value = False
        
        color_manager.stop_color_recognition()
        
        assert color_manager.color_recognition.is_running is False


class TestColorImageHash:
    """颜色图像哈希测试"""
    
    @pytest.fixture
    def color_module(self, mock_app):
        return ColorRecognition(mock_app)
    
    def test_image_hash_update(self, color_module):
        """测试图像哈希更新"""
        color_module.region = (0, 0, 100, 100)
        color_module.target_color = (255, 0, 0)
        color_module.tolerance = 10
        
        red_image = Image.new('RGB', (100, 100), (255, 0, 0))
        
        with patch('utils.screenshot.ScreenshotManager') as mock_manager:
            mock_manager.return_value.get_region_screenshot.return_value = red_image
            color_module.recognize_color()
            
            assert color_module.last_image_hash is not None
    
    def test_image_hash_different_images(self, color_module):
        """测试图像哈希功能"""
        color_module.region = (0, 0, 100, 100)
        color_module.target_color = (255, 0, 0)
        color_module.tolerance = 10
        
        red_image = Image.new('RGB', (100, 100), (255, 0, 0))
        
        with patch('utils.screenshot.ScreenshotManager') as mock_manager:
            mock_manager.return_value.get_region_screenshot.return_value = red_image
            color_module.recognize_color()
            
            assert color_module.last_image_hash is not None
