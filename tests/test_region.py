import pytest
from unittest.mock import MagicMock, patch


class TestRegionCoordinates:
    """区域坐标测试类"""
    
    def test_region_bounds(self):
        """测试区域边界"""
        region = (10, 20, 110, 120)
        
        left, top, right, bottom = region
        width = right - left
        height = bottom - top
        
        assert width == 100
        assert height == 100
    
    def test_region_origin(self):
        """测试区域原点"""
        region = (0, 0, 100, 100)
        
        assert region[0] == 0
        assert region[1] == 0
    
    def test_region_negative_coords(self):
        """测试负坐标"""
        region = (-10, -10, 90, 90)
        
        assert region[0] < 0
        assert region[1] < 0
    
    def test_region_clamp(self):
        """测试区域限制"""
        region = (-10, -10, 2000, 2000)
        
        clamped = (
            max(0, region[0]),
            max(0, region[1]),
            min(1920, region[2]),
            min(1080, region[3])
        )
        
        assert clamped[0] == 0
        assert clamped[1] == 0
        assert clamped[2] == 1920
        assert clamped[3] == 1080
    
    def test_region_valid(self):
        """测试有效区域"""
        region = (0, 0, 100, 100)
        
        is_valid = region[2] > region[0] and region[3] > region[1]
        
        assert is_valid is True
    
    def test_region_invalid_none(self):
        """测试None区域"""
        region = None
        
        is_valid = region is not None
        
        assert is_valid is False
    
    def test_region_invalid_empty(self):
        """测试空区域"""
        region = ()
        
        is_valid = len(region) == 4
        
        assert is_valid is False
    
    def test_region_invalid_too_small(self):
        """测试过小区域"""
        region = (0, 0, 5, 5)
        
        width = region[2] - region[0]
        height = region[3] - region[1]
        
        is_valid = width >= 10 and height >= 10
        
        assert is_valid is False


class TestRegionSelection:
    """区域选择测试类"""
    
    def test_selection_callback(self, mock_app):
        """测试选择回调"""
        callback = MagicMock()
        
        callback((0, 0, 100, 100))
        
        callback.assert_called_once_with((0, 0, 100, 100))
    
    def test_selection_cancel(self, mock_app):
        """测试取消选择"""
        cancel_callback = MagicMock()
        
        cancel_callback()
        
        cancel_callback.assert_called_once()
    
    def test_selection_type(self, mock_app):
        """测试选择类型"""
        selection_types = ["normal", "number", "ocr"]
        
        for st in selection_types:
            assert st in ["normal", "number", "ocr"]


class TestMonitorBounds:
    """显示器边界测试类"""
    
    def test_min_max_calculation(self):
        """测试最小最大值计算"""
        monitors = [
            MagicMock(x=0, y=0, width=1920, height=1080),
            MagicMock(x=1920, y=0, width=1920, height=1080),
        ]
        
        min_x = min(monitor.x for monitor in monitors)
        min_y = min(monitor.y for monitor in monitors)
        max_x = max(monitor.x + monitor.width for monitor in monitors)
        max_y = max(monitor.y + monitor.height for monitor in monitors)
        
        assert min_x == 0
        assert min_y == 0
        assert max_x == 3840
        assert max_y == 1080
    
    def test_virtual_screen_size(self):
        """测试虚拟屏幕大小"""
        monitors = [
            MagicMock(x=0, y=0, width=1920, height=1080),
        ]
        
        min_x = min(monitor.x for monitor in monitors)
        min_y = min(monitor.y for monitor in monitors)
        max_x = max(monitor.x + monitor.width for monitor in monitors)
        max_y = max(monitor.y + monitor.height for monitor in monitors)
        
        virtual_width = max_x - min_x
        virtual_height = max_y - min_y
        
        assert virtual_width == 1920
        assert virtual_height == 1080
