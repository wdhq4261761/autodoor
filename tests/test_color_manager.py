import pytest
from unittest.mock import MagicMock, patch
from modules.color import ColorRecognitionManager, ColorRecognition


class TestColorRecognitionManagerInit:
    """ColorRecognitionManager初始化测试"""
    
    def test_init(self, mock_app):
        """测试初始化"""
        manager = ColorRecognitionManager(mock_app)
        
        assert manager.app is not None
        assert manager.color_recognition is None


class TestColorRecognitionManagerSelectRegion:
    """选择区域测试"""
    
    @pytest.fixture
    def color_manager(self, mock_app):
        mock_app.logging_manager = MagicMock()
        return ColorRecognitionManager(mock_app)
    
    def test_select_color_region(self, color_manager):
        """测试选择颜色识别区域"""
        with patch('utils.region._start_selection') as mock_start:
            color_manager.select_color_region()
            
            mock_start.assert_called_once_with(color_manager.app, "color", 0)


class TestColorRecognitionManagerSelectColor:
    """选择颜色测试"""
    
    @pytest.fixture
    def color_manager(self, mock_app):
        mock_app.logging_manager = MagicMock()
        mock_app.root = MagicMock()
        return ColorRecognitionManager(mock_app)
    
    def test_select_color(self, color_manager):
        """测试选择颜色"""
        with patch.object(color_manager, 'create_color_selection_window'):
            color_manager.select_color()
            
            color_manager.app.logging_manager.log_message.assert_called()
    
    def test_create_color_selection_window(self, color_manager):
        """测试创建颜色选择窗口"""
        import tkinter as tk
        
        with patch('screeninfo.get_monitors') as mock_monitors:
            mock_monitor = MagicMock()
            mock_monitor.x = 0
            mock_monitor.y = 0
            mock_monitor.width = 1920
            mock_monitor.height = 1080
            mock_monitors.return_value = [mock_monitor]
            
            with patch('tkinter.Toplevel') as mock_toplevel:
                mock_window = MagicMock()
                mock_toplevel.return_value = mock_window
                
                with patch('tkinter.Canvas') as mock_canvas:
                    mock_canvas_instance = MagicMock()
                    mock_canvas.return_value = mock_canvas_instance
                    
                    color_manager.create_color_selection_window()
                    
                    assert color_manager.color_selection_window is not None
    
    def test_create_color_selection_window_no_screeninfo(self, color_manager):
        """测试无screeninfo时创建窗口"""
        with patch('screeninfo.get_monitors', side_effect=ImportError("No screeninfo")):
            with patch('tkinter.messagebox.showerror') as mock_error:
                color_manager.create_color_selection_window()
                
                mock_error.assert_called_once()
    
    def test_cancel_color_selection(self, color_manager):
        """测试取消颜色选择"""
        color_manager.color_selection_window = MagicMock()
        color_manager.color_selection_window.winfo_exists.return_value = True
        color_manager.app.logging_manager = MagicMock()
        
        color_manager.cancel_color_selection()
        
        color_manager.color_selection_window.destroy.assert_called_once()
    
    def test_cancel_color_selection_window_not_exists(self, color_manager):
        """测试窗口不存在时取消"""
        color_manager.color_selection_window = MagicMock()
        color_manager.color_selection_window.winfo_exists.return_value = False
        color_manager.app.logging_manager = MagicMock()
        
        color_manager.cancel_color_selection()
        
        color_manager.color_selection_window.destroy.assert_not_called()


class TestColorRecognitionManagerOnColorSelect:
    """颜色选择事件测试"""
    
    @pytest.fixture
    def color_manager(self, mock_app):
        mock_app.logging_manager = MagicMock()
        mock_app.target_color = None
        mock_app.color_var = MagicMock()
        mock_app.color_display = MagicMock()
        mock_app.root = MagicMock()
        return ColorRecognitionManager(mock_app)
    
    def test_on_color_select(self, color_manager):
        """测试颜色选择事件"""
        color_manager.color_selection_window = MagicMock()
        
        event = MagicMock()
        event.x_root = 100
        event.y_root = 200
        
        from PIL import Image
        mock_image = Image.new('RGB', (1920, 1080), color='red')
        
        with patch('utils.screenshot.ScreenshotManager') as mock_manager:
            mock_instance = MagicMock()
            mock_manager.return_value = mock_instance
            mock_instance.get_full_screenshot.return_value = mock_image
            
            with patch('screeninfo.get_monitors') as mock_monitors:
                mock_monitor = MagicMock()
                mock_monitor.x = 0
                mock_monitor.y = 0
                mock_monitors.return_value = [mock_monitor]
                
                color_manager.on_color_select(event)
                
                assert color_manager.app.target_color is not None
    
    def test_on_color_select_with_screenshot_exception(self, color_manager):
        """测试截图异常时的颜色选择"""
        color_manager.color_selection_window = MagicMock()
        
        event = MagicMock()
        event.x_root = 100
        event.y_root = 200
        
        from PIL import Image
        mock_image = Image.new('RGB', (1920, 1080), color='blue')
        
        with patch('utils.screenshot.ScreenshotManager') as mock_manager:
            mock_manager.return_value.get_full_screenshot.side_effect = Exception("Screenshot error")
            
            with patch('PIL.ImageGrab.grab', return_value=mock_image):
                with patch('screeninfo.get_monitors') as mock_monitors:
                    mock_monitor = MagicMock()
                    mock_monitor.x = 0
                    mock_monitor.y = 0
                    mock_monitors.return_value = [mock_monitor]
                    
                    color_manager.on_color_select(event)
                    
                    assert color_manager.app.target_color is not None


class TestColorRecognitionManagerStartStop:
    """启动停止测试"""
    
    @pytest.fixture
    def color_manager(self, mock_app):
        mock_app.logging_manager = MagicMock()
        mock_app.target_color = (255, 0, 0)
        mock_app.tolerance_var = MagicMock()
        mock_app.tolerance_var.get.return_value = "10"
        mock_app.interval_var = MagicMock()
        mock_app.interval_var.get.return_value = "5"
        mock_app.color_commands = MagicMock()
        mock_app.color_commands.get.return_value = ""
        mock_app.color_recognition_region = (0, 0, 100, 100)
        mock_app.status_var = MagicMock()
        return ColorRecognitionManager(mock_app)
    
    def test_start_color_recognition_no_color(self, color_manager):
        """测试无目标颜色时启动"""
        color_manager.app.target_color = None
        
        with patch('tkinter.messagebox.showwarning'):
            color_manager.start_color_recognition()
    
    def test_start_color_recognition_no_region(self, color_manager):
        """测试无区域时启动"""
        color_manager.app.color_recognition_region = None
        
        with patch('tkinter.messagebox.showwarning'):
            color_manager.start_color_recognition()
    
    def test_start_color_recognition_invalid_tolerance(self, color_manager):
        """测试无效容差时启动"""
        color_manager.app.tolerance_var.get.return_value = "invalid"
        
        with patch('tkinter.messagebox.showwarning'):
            color_manager.start_color_recognition()
    
    def test_start_color_recognition_success(self, color_manager):
        """测试成功启动颜色识别"""
        with patch.object(ColorRecognition, 'start_recognition'):
            color_manager.start_color_recognition()
            
            assert color_manager.color_recognition is not None
    
    def test_stop_color_recognition_not_running(self, color_manager):
        """测试停止未运行的颜色识别"""
        color_manager.stop_color_recognition()
    
    def test_stop_color_recognition_running(self, color_manager):
        """测试停止运行中的颜色识别"""
        color_manager.color_recognition = MagicMock()
        color_manager.color_recognition.is_running = True
        color_manager.color_recognition.stop_recognition = MagicMock()
        
        color_manager.stop_color_recognition()
        
        color_manager.color_recognition.stop_recognition.assert_called_once()
    
    def test_stop_color_recognition_thread_alive(self, color_manager):
        """测试停止线程仍存活的颜色识别"""
        color_manager.color_recognition = MagicMock()
        color_manager.color_recognition.is_running = False
        color_manager.color_recognition.recognition_thread = MagicMock()
        color_manager.color_recognition.recognition_thread.is_alive.return_value = True
        
        color_manager.stop_color_recognition()
        
        assert color_manager.color_recognition.is_running is False


class TestColorRecognitionManagerIntegration:
    """集成测试"""
    
    @pytest.fixture
    def color_manager(self, mock_app):
        mock_app.logging_manager = MagicMock()
        mock_app.root = MagicMock()
        return ColorRecognitionManager(mock_app)
    
    def test_full_start_stop_cycle(self, color_manager):
        """测试完整启动停止循环"""
        color_manager.app.target_color = (255, 0, 0)
        color_manager.app.tolerance_var = MagicMock()
        color_manager.app.tolerance_var.get.return_value = "10"
        color_manager.app.interval_var = MagicMock()
        color_manager.app.interval_var.get.return_value = "5"
        color_manager.app.color_commands = MagicMock()
        color_manager.app.color_commands.get.return_value = ""
        color_manager.app.color_recognition_region = (0, 0, 100, 100)
        color_manager.app.status_var = MagicMock()
        
        with patch.object(ColorRecognition, 'start_recognition'):
            color_manager.start_color_recognition()
            
            assert color_manager.color_recognition is not None
        
        color_manager.color_recognition.is_running = True
        color_manager.color_recognition.stop_recognition = MagicMock()
        
        color_manager.stop_color_recognition()
        
        color_manager.color_recognition.stop_recognition.assert_called_once()
