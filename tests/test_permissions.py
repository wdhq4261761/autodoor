import pytest
import threading
from unittest.mock import MagicMock, patch
from input.permissions import PermissionManager


class TestPermissionManagerInit:
    """PermissionManager初始化测试"""
    
    def test_init(self, mock_app):
        """测试初始化"""
        manager = PermissionManager(mock_app)
        
        assert manager.app is not None


class TestPermissionManagerCheck:
    """权限检查测试"""
    
    @pytest.fixture
    def permission_manager(self, mock_app):
        mock_app.logging_manager = MagicMock()
        return PermissionManager(mock_app)
    
    def test_check_accessibility_success(self, permission_manager):
        """测试辅助功能权限检查成功"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        
        with patch('subprocess.run', return_value=mock_result):
            result = permission_manager.check_accessibility()
            
            assert result is True
    
    def test_check_accessibility_failure(self, permission_manager):
        """测试辅助功能权限检查失败"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        
        with patch('subprocess.run', return_value=mock_result):
            result = permission_manager.check_accessibility()
            
            assert result is False
    
    def test_check_accessibility_exception(self, permission_manager):
        """测试辅助功能权限检查异常"""
        with patch('subprocess.run', side_effect=Exception("Error")):
            result = permission_manager.check_accessibility()
            
            assert result is False
    
    def test_check_screen_recording_success(self, permission_manager):
        """测试屏幕录制权限检查成功"""
        import numpy as np
        from PIL import Image
        
        mock_image = Image.new('RGB', (10, 10), color='red')
        
        with patch('PIL.ImageGrab.grab', return_value=mock_image):
            result = permission_manager.check_screen_recording()
            
            assert result is True
    
    def test_check_screen_recording_black_screen(self, permission_manager):
        """测试屏幕录制权限检查-黑屏"""
        from PIL import Image
        
        mock_image = Image.new('RGB', (10, 10), color='black')
        
        with patch('PIL.ImageGrab.grab', return_value=mock_image):
            result = permission_manager.check_screen_recording()
            
            assert result is False
    
    def test_check_screen_recording_wrong_size(self, permission_manager):
        """测试屏幕录制权限检查-错误尺寸"""
        from PIL import Image
        
        mock_image = Image.new('RGB', (5, 5), color='red')
        
        with patch('PIL.ImageGrab.grab', return_value=mock_image):
            result = permission_manager.check_screen_recording()
            
            assert result is False
    
    def test_check_screen_recording_exception(self, permission_manager):
        """测试屏幕录制权限检查异常"""
        with patch('PIL.ImageGrab.grab', side_effect=Exception("Error")):
            result = permission_manager.check_screen_recording()
            
            assert result is False
    
    def test_check_all_success(self, permission_manager):
        """测试所有权限检查成功"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        
        from PIL import Image
        mock_image = Image.new('RGB', (10, 10), color='red')
        
        with patch('subprocess.run', return_value=mock_result):
            with patch('PIL.ImageGrab.grab', return_value=mock_image):
                result = permission_manager.check_all()
                
                assert result is True
    
    def test_check_all_partial_failure(self, permission_manager):
        """测试部分权限检查失败"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        
        from PIL import Image
        mock_image = Image.new('RGB', (10, 10), color='red')
        
        with patch('subprocess.run', return_value=mock_result):
            with patch('PIL.ImageGrab.grab', return_value=mock_image):
                result = permission_manager.check_all()
                
                assert result is False


class TestPermissionManagerPrompt:
    """权限提示测试"""
    
    @pytest.fixture
    def permission_manager(self, mock_app):
        mock_app.logging_manager = MagicMock()
        mock_app.show_message = MagicMock()
        return PermissionManager(mock_app)
    
    def test_prompt_accessibility(self, permission_manager):
        """测试辅助功能权限提示"""
        permission_manager.prompt_accessibility()
        
        permission_manager.app.show_message.assert_called_once()
    
    def test_prompt_screen_recording(self, permission_manager):
        """测试屏幕录制权限提示"""
        permission_manager.prompt_screen_recording()
        
        permission_manager.app.show_message.assert_called_once()


class TestPermissionManagerAsync:
    """异步权限检查测试"""
    
    @pytest.fixture
    def permission_manager(self, mock_app):
        mock_app.logging_manager = MagicMock()
        mock_app.show_progress = MagicMock()
        mock_app.hide_progress = MagicMock()
        mock_app.root = MagicMock()
        mock_app.root.after = MagicMock()
        return PermissionManager(mock_app)
    
    def test_check_macos_permissions_starts_thread(self, permission_manager):
        """测试macOS权限检查启动线程"""
        permission_manager.check_macos_permissions()
        
        permission_manager.app.show_progress.assert_called_once()
    
    def test_check_permissions_async(self, permission_manager):
        """测试异步权限检查"""
        callback = MagicMock()
        
        permission_manager.check_permissions_async(callback)
        
        permission_manager.app.logging_manager.log_message.assert_called()
    
    def test_on_permissions_checked_success(self, permission_manager):
        """测试权限检查完成回调-成功"""
        callback = MagicMock()
        
        permission_manager._on_permissions_checked(True, True, callback)
        
        permission_manager.app.hide_progress.assert_called_once()
        callback.assert_called_once_with(True)
    
    def test_on_permissions_checked_failure(self, permission_manager):
        """测试权限检查完成回调-失败"""
        permission_manager._guide_permission_setup = MagicMock()
        
        permission_manager._on_permissions_checked(False, True)
        
        permission_manager.app.hide_progress.assert_called_once()
        permission_manager._guide_permission_setup.assert_called_once()
    
    def test_on_permissions_checked_no_callback(self, permission_manager):
        """测试权限检查完成回调-无回调"""
        permission_manager._on_permissions_checked(True, True)
        
        permission_manager.app.hide_progress.assert_called_once()


class TestPermissionManagerGuide:
    """权限引导测试"""
    
    @pytest.fixture
    def permission_manager(self, mock_app):
        mock_app.logging_manager = MagicMock()
        mock_app.show_message = MagicMock()
        return PermissionManager(mock_app)
    
    def test_guide_permission_setup_both(self, permission_manager):
        """测试引导设置两种权限"""
        permission_manager._guide_accessibility_setup = MagicMock()
        permission_manager._guide_screen_recording_setup = MagicMock()
        
        permission_manager._guide_permission_setup(False, False)
        
        permission_manager._guide_accessibility_setup.assert_called_once()
        permission_manager._guide_screen_recording_setup.assert_called_once()
    
    def test_guide_permission_setup_accessibility_only(self, permission_manager):
        """测试只引导辅助功能权限"""
        permission_manager._guide_accessibility_setup = MagicMock()
        permission_manager._guide_screen_recording_setup = MagicMock()
        
        permission_manager._guide_permission_setup(False, True)
        
        permission_manager._guide_accessibility_setup.assert_called_once()
        permission_manager._guide_screen_recording_setup.assert_not_called()
    
    def test_guide_permission_setup_screen_only(self, permission_manager):
        """测试只引导屏幕录制权限"""
        permission_manager._guide_accessibility_setup = MagicMock()
        permission_manager._guide_screen_recording_setup = MagicMock()
        
        permission_manager._guide_permission_setup(True, False)
        
        permission_manager._guide_accessibility_setup.assert_not_called()
        permission_manager._guide_screen_recording_setup.assert_called_once()


class TestPermissionManagerCompatibility:
    """兼容性方法测试"""
    
    @pytest.fixture
    def permission_manager(self, mock_app):
        return PermissionManager(mock_app)
    
    def test_check_accessibility_permission(self, permission_manager):
        """测试兼容性辅助功能权限检查"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        
        with patch('subprocess.run', return_value=mock_result):
            result = permission_manager._check_accessibility_permission()
            
            assert result is True
    
    def test_check_screen_recording_permission(self, permission_manager):
        """测试兼容性屏幕录制权限检查"""
        from PIL import Image
        
        mock_image = Image.new('RGB', (10, 10), color='red')
        
        with patch('PIL.ImageGrab.grab', return_value=mock_image):
            result = permission_manager._check_screen_recording_permission()
            
            assert result is True
