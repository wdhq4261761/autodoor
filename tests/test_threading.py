import pytest
import threading
import time
from unittest.mock import MagicMock, patch
from core.threading import ThreadManager


class TestThreadManager:
    """ThreadManager测试类"""
    
    @pytest.fixture
    def thread_manager(self, mock_app):
        """创建线程管理器实例"""
        return ThreadManager(mock_app)
    
    def test_init(self, thread_manager):
        """测试初始化"""
        assert thread_manager.threads is not None
        assert isinstance(thread_manager.threads, dict)
    
    def test_add_thread(self, thread_manager):
        """测试添加线程"""
        mock_thread = MagicMock()
        
        thread_manager.add_thread("test_module", mock_thread)
        
        assert "test_module" in thread_manager.threads
        assert mock_thread in thread_manager.threads["test_module"]
    
    def test_get_threads(self, thread_manager):
        """测试获取线程"""
        mock_thread = MagicMock()
        thread_manager.add_thread("test_module", mock_thread)
        
        threads = thread_manager.get_threads("test_module")
        
        assert len(threads) == 1
        assert threads[0] == mock_thread
    
    def test_get_threads_empty(self, thread_manager):
        """测试获取空线程列表"""
        threads = thread_manager.get_threads("nonexistent")
        
        assert threads == []
    
    def test_stop(self, thread_manager):
        """测试停止模块线程"""
        mock_stop_func = MagicMock()
        
        thread_manager.stop("test_module", mock_stop_func, "测试模块")
        
        mock_stop_func.assert_called_once()
    
    def test_stop_clears_threads(self, thread_manager):
        """测试停止后清空线程列表"""
        mock_thread = MagicMock()
        thread_manager.add_thread("test_module", mock_thread)
        
        thread_manager.stop("test_module", MagicMock(), "测试模块")
        
        assert len(thread_manager.threads["test_module"]) == 0
    
    def test_start_module(self, thread_manager):
        """测试启动模块"""
        mock_start_func = MagicMock(return_value=1)
        
        result = thread_manager.start("test_module", mock_start_func, MagicMock(), "测试模块")
        
        assert result == 1
        mock_start_func.assert_called_once()
    
    def test_start_module_zero_count(self, thread_manager):
        """测试启动模块返回零"""
        mock_start_func = MagicMock(return_value=0)
        
        result = thread_manager.start("test_module", mock_start_func, MagicMock(), "测试模块")
        
        assert result == 0
    
    def test_stop_all(self, thread_manager):
        """测试停止所有线程"""
        thread_manager.threads = {
            "module1": [MagicMock()],
            "module2": [MagicMock()],
        }
        
        thread_manager.stop_all()
        
        assert len(thread_manager.threads["module1"]) == 0
        assert len(thread_manager.threads["module2"]) == 0


class TestThreadManagerIntegration:
    """线程管理器集成测试"""
    
    @pytest.fixture
    def thread_manager(self, mock_app):
        mock_app.status_labels = {}
        return ThreadManager(mock_app)
    
    def test_multiple_threads_same_module(self, thread_manager):
        """测试同一模块多个线程"""
        thread1 = MagicMock()
        thread2 = MagicMock()
        
        thread_manager.add_thread("module", thread1)
        thread_manager.add_thread("module", thread2)
        
        threads = thread_manager.get_threads("module")
        
        assert len(threads) == 2
    
    def test_multiple_modules(self, thread_manager):
        """测试多个模块"""
        thread_manager.add_thread("module1", MagicMock())
        thread_manager.add_thread("module2", MagicMock())
        thread_manager.add_thread("module3", MagicMock())
        
        assert len(thread_manager.threads) == 3
