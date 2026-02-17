import pytest
import time
from unittest.mock import MagicMock, patch
from utils.screenshot import ScreenshotManager


class TestScreenshotManager:
    """ScreenshotManager测试类"""
    
    def test_init(self):
        """测试初始化"""
        ScreenshotManager._instance = None
        manager = ScreenshotManager()
        
        assert manager is not None
    
    def test_get_full_screenshot(self):
        """测试获取全屏截图"""
        ScreenshotManager._instance = None
        manager = ScreenshotManager()
        
        with patch('PIL.ImageGrab.grab') as mock_grab:
            mock_image = MagicMock()
            mock_grab.return_value = mock_image
            mock_image.copy.return_value = mock_image
            
            result = manager.get_full_screenshot()
            
            assert result is not None
    
    def test_get_region_screenshot(self):
        """测试获取区域截图"""
        ScreenshotManager._instance = None
        manager = ScreenshotManager()
        region = (0, 0, 100, 100)
        
        with patch('PIL.ImageGrab.grab') as mock_grab:
            mock_image = MagicMock()
            mock_grab.return_value = mock_image
            mock_image.copy.return_value = mock_image
            mock_image.crop.return_value = mock_image
            
            result = manager.get_region_screenshot(region)
            
            assert result is not None
    
    def test_get_region_screenshot_none_region(self):
        """测试空区域"""
        ScreenshotManager._instance = None
        manager = ScreenshotManager()
        
        result = manager.get_region_screenshot(None)
        
        assert result is None
    
    def test_clear_cache(self):
        """测试清除缓存"""
        ScreenshotManager._instance = None
        manager = ScreenshotManager()
        
        manager.clear_cache()
        
        assert manager.last_full_screenshot is None
    
    def test_set_cache_duration(self):
        """测试设置缓存时间"""
        ScreenshotManager._instance = None
        manager = ScreenshotManager()
        
        manager.set_cache_duration(0.5)
        
        assert manager.cache_duration == 0.5


class TestScreenshotRegion:
    """截图区域测试"""
    
    def test_region_coordinates(self):
        """测试区域坐标"""
        region = (10, 20, 110, 120)
        
        assert region[0] == 10
        assert region[1] == 20
        assert region[2] == 110
        assert region[3] == 120
    
    def test_region_size(self):
        """测试区域大小"""
        region = (0, 0, 100, 50)
        
        width = region[2] - region[0]
        height = region[3] - region[1]
        
        assert width == 100
        assert height == 50
    
    def test_region_valid(self):
        """测试有效区域"""
        region = (0, 0, 100, 100)
        
        is_valid = region[2] > region[0] and region[3] > region[1]
        
        assert is_valid is True
    
    def test_region_invalid(self):
        """测试无效区域"""
        region = (100, 100, 0, 0)
        
        is_valid = region[2] > region[0] and region[3] > region[1]
        
        assert is_valid is False


class TestScreenshotManagerAdvanced:
    """ScreenshotManager高级测试"""
    
    def test_get_full_screenshot_with_cache(self):
        """测试缓存返回"""
        ScreenshotManager._instance = None
        manager = ScreenshotManager()
        manager.cache_duration = 1.0
        
        with patch('PIL.ImageGrab.grab') as mock_grab:
            mock_image = MagicMock()
            mock_grab.return_value = mock_image
            mock_image.copy.return_value = mock_image
            
            result1 = manager.get_full_screenshot()
            
            result2 = manager.get_full_screenshot()
            
            assert mock_grab.call_count == 1
    
    def test_get_full_screenshot_cache_expired(self):
        """测试缓存过期"""
        ScreenshotManager._instance = None
        manager = ScreenshotManager()
        manager.cache_duration = 0.01
        
        with patch('PIL.ImageGrab.grab') as mock_grab:
            mock_image = MagicMock()
            mock_grab.return_value = mock_image
            mock_image.copy.return_value = mock_image
            
            result1 = manager.get_full_screenshot()
            
            time.sleep(0.05)
            
            result2 = manager.get_full_screenshot()
            
            assert mock_grab.call_count == 2
    
    def test_get_full_screenshot_exception(self):
        """测试截图异常"""
        ScreenshotManager._instance = None
        manager = ScreenshotManager()
        
        with patch('PIL.ImageGrab.grab', side_effect=Exception("Screenshot failed")):
            result = manager.get_full_screenshot()
            
            assert result is None
    
    def test_get_full_screenshot_with_priority(self):
        """测试带优先级截图"""
        ScreenshotManager._instance = None
        manager = ScreenshotManager()
        
        with patch('PIL.ImageGrab.grab') as mock_grab:
            mock_image = MagicMock()
            mock_grab.return_value = mock_image
            mock_image.copy.return_value = mock_image
            
            result = manager.get_full_screenshot(priority=5)
            
            assert result is not None
    
    def test_get_region_screenshot_swapped_coords(self):
        """测试交换坐标区域截图"""
        ScreenshotManager._instance = None
        manager = ScreenshotManager()
        region = (100, 100, 0, 0)
        
        with patch('PIL.ImageGrab.grab') as mock_grab:
            mock_image = MagicMock()
            mock_grab.return_value = mock_image
            mock_image.copy.return_value = mock_image
            mock_image.crop.return_value = mock_image
            
            result = manager.get_region_screenshot(region)
            
            assert result is not None
            mock_image.crop.assert_called_once_with((0, 0, 100, 100))
    
    def test_get_region_screenshot_full_screenshot_none(self):
        """测试全屏截图返回None"""
        ScreenshotManager._instance = None
        manager = ScreenshotManager()
        region = (0, 0, 100, 100)
        
        with patch.object(manager, 'get_full_screenshot', return_value=None):
            result = manager.get_region_screenshot(region)
            
            assert result is None
    
    def test_get_region_screenshot_with_priority(self):
        """测试带优先级区域截图"""
        ScreenshotManager._instance = None
        manager = ScreenshotManager()
        region = (0, 0, 100, 100)
        
        with patch('PIL.ImageGrab.grab') as mock_grab:
            mock_image = MagicMock()
            mock_grab.return_value = mock_image
            mock_image.copy.return_value = mock_image
            mock_image.crop.return_value = mock_image
            
            result = manager.get_region_screenshot(region, priority=5)
            
            assert result is not None
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        ScreenshotManager._instance = None
        
        manager1 = ScreenshotManager()
        manager2 = ScreenshotManager()
        
        assert manager1 is manager2
    
    def test_clear_cache_resets_state(self):
        """测试清除缓存重置状态"""
        ScreenshotManager._instance = None
        manager = ScreenshotManager()
        
        with patch('PIL.ImageGrab.grab') as mock_grab:
            mock_image = MagicMock()
            mock_grab.return_value = mock_image
            mock_image.copy.return_value = mock_image
            
            manager.get_full_screenshot()
            
            manager.clear_cache()
            
            assert manager.last_full_screenshot is None
            assert manager.last_time == 0
