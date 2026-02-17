import pytest
import time
import threading
from unittest.mock import MagicMock, patch
from modules.recorder import RecorderBase


class TestRecorderBase:
    """RecorderBase测试类"""
    
    @pytest.fixture
    def recorder(self, mock_app):
        return RecorderBase(mock_app)
    
    def test_init(self, recorder):
        """测试初始化"""
        assert recorder.app is not None
        assert recorder.resources == []
    
    def test_register_resource(self, recorder):
        """测试注册资源"""
        resource = MagicMock()
        cleanup_func = MagicMock()
        
        recorder.register_resource(resource, cleanup_func)
        
        assert len(recorder.resources) == 1
        assert recorder.resources[0] == (resource, cleanup_func)
    
    def test_cleanup_resources(self, recorder):
        """测试清理资源"""
        resource1 = MagicMock()
        cleanup_func1 = MagicMock()
        resource2 = MagicMock()
        cleanup_func2 = MagicMock()
        
        recorder.register_resource(resource1, cleanup_func1)
        recorder.register_resource(resource2, cleanup_func2)
        
        recorder.cleanup_resources()
        
        cleanup_func1.assert_called_once_with(resource1)
        cleanup_func2.assert_called_once_with(resource2)
        assert len(recorder.resources) == 0
    
    def test_cleanup_resources_with_error(self, recorder):
        """测试清理资源时的错误处理"""
        resource = MagicMock()
        cleanup_func = MagicMock(side_effect=Exception("Cleanup error"))
        
        recorder.register_resource(resource, cleanup_func)
        
        recorder.cleanup_resources()
        
        assert len(recorder.resources) == 0
    
    def test_multiple_resources_cleanup_order(self, recorder):
        """测试多资源清理顺序"""
        cleanup_order = []
        
        def cleanup1(r):
            cleanup_order.append(1)
        
        def cleanup2(r):
            cleanup_order.append(2)
        
        recorder.register_resource("resource1", cleanup1)
        recorder.register_resource("resource2", cleanup2)
        
        recorder.cleanup_resources()
        
        assert cleanup_order == [2, 1]
