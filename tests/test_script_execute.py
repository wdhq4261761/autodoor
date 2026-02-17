import pytest
import time
import threading
from unittest.mock import MagicMock, patch
from modules.script import ScriptExecutor


class TestScriptExecuteCommand:
    """测试execute_command函数"""
    
    @pytest.fixture
    def script_executor(self, mock_app):
        mock_app.input_controller = MagicMock()
        mock_app.logging_manager = MagicMock()
        executor = ScriptExecutor(mock_app)
        executor.is_running = True
        executor.is_paused = False
        return executor
    
    def test_execute_keydown_command(self, script_executor):
        """测试执行KeyDown命令"""
        command = {"type": "keydown", "key": "a", "count": 1}
        
        script_executor.execute_command(command)
        
        script_executor.app.input_controller.key_down.assert_called_once_with("a", priority=1)
    
    def test_execute_keyup_command(self, script_executor):
        """测试执行KeyUp命令"""
        command = {"type": "keyup", "key": "a", "count": 1}
        
        script_executor.execute_command(command)
        
        script_executor.app.input_controller.key_up.assert_called_once_with("a", priority=1)
    
    def test_execute_keydown_multiple_count(self, script_executor):
        """测试多次KeyDown命令"""
        command = {"type": "keydown", "key": "a", "count": 3}
        
        script_executor.execute_command(command)
        
        assert script_executor.app.input_controller.key_down.call_count == 3
    
    def test_execute_keydown_not_running(self, script_executor):
        """测试未运行时不执行KeyDown"""
        script_executor.is_running = False
        command = {"type": "keydown", "key": "a", "count": 1}
        
        script_executor.execute_command(command)
        
        script_executor.app.input_controller.key_down.assert_not_called()
    
    def test_execute_keydown_paused(self, script_executor):
        """测试暂停时不执行KeyDown"""
        script_executor.is_paused = True
        command = {"type": "keydown", "key": "a", "count": 1}
        
        def check_paused():
            script_executor.is_running = False
        
        time.sleep(0.15)
        script_executor.is_running = False
        
        script_executor.execute_command(command)
    
    def test_execute_mouse_down_command(self, script_executor):
        """测试执行MouseDown命令"""
        command = {"type": "mouse_down", "button": "left", "count": 1}
        
        script_executor.execute_command(command)
        
        script_executor.app.input_controller.mouse_down.assert_called_once_with(button="left", priority=1)
    
    def test_execute_mouse_up_command(self, script_executor):
        """测试执行MouseUp命令"""
        command = {"type": "mouse_up", "button": "right", "count": 1}
        
        script_executor.execute_command(command)
        
        script_executor.app.input_controller.mouse_up.assert_called_once_with(button="right", priority=1)
    
    def test_execute_mouse_down_multiple_count(self, script_executor):
        """测试多次MouseDown命令"""
        command = {"type": "mouse_down", "button": "middle", "count": 2}
        
        script_executor.execute_command(command)
        
        assert script_executor.app.input_controller.mouse_down.call_count == 2
    
    def test_execute_mouse_down_not_running(self, script_executor):
        """测试未运行时不执行MouseDown"""
        script_executor.is_running = False
        command = {"type": "mouse_down", "button": "left", "count": 1}
        
        script_executor.execute_command(command)
        
        script_executor.app.input_controller.mouse_down.assert_not_called()
    
    def test_execute_moveto_command(self, script_executor):
        """测试执行MoveTo命令"""
        command = {"type": "moveto", "x": 100, "y": 200}
        
        script_executor.execute_command(command)
        
        script_executor.app.input_controller.move_to.assert_called_once_with(100, 200, priority=1)
    
    def test_execute_moveto_not_running(self, script_executor):
        """测试未运行时不执行MoveTo"""
        script_executor.is_running = False
        command = {"type": "moveto", "x": 100, "y": 200}
        
        script_executor.execute_command(command)
        
        script_executor.app.input_controller.move_to.assert_not_called()
    
    def test_execute_moveto_paused(self, script_executor):
        """测试暂停时不执行MoveTo"""
        script_executor.is_paused = True
        command = {"type": "moveto", "x": 100, "y": 200}
        
        script_executor.execute_command(command)
        
        script_executor.app.input_controller.move_to.assert_not_called()
    
    def test_execute_delay_command(self, script_executor):
        """测试执行Delay命令"""
        command = {"type": "delay", "time": 50}
        
        start = time.time()
        script_executor.execute_command(command)
        elapsed = time.time() - start
        
        assert elapsed >= 0.05
    
    def test_execute_delay_not_running(self, script_executor):
        """测试未运行时中断Delay"""
        script_executor.is_running = False
        command = {"type": "delay", "time": 5000}
        
        start = time.time()
        script_executor.execute_command(command)
        elapsed = time.time() - start
        
        assert elapsed < 0.1
    
    def test_execute_stopscript_command(self, script_executor):
        """测试执行StopScript命令"""
        command = {"type": "stopscript"}
        script_executor.app.script = MagicMock()
        script_executor.app.root = MagicMock()
        
        script_executor.execute_command(command)
        
        script_executor.app.root.after.assert_called_once()
    
    def test_execute_startscript_command(self, script_executor):
        """测试执行StartScript命令"""
        command = {"type": "startscript"}
        
        script_executor.execute_command(command)
        
        assert script_executor.is_running is True
    
    def test_execute_unknown_command(self, script_executor):
        """测试未知命令类型"""
        command = {"type": "unknown"}
        
        script_executor.execute_command(command)
        
        script_executor.app.input_controller.key_down.assert_not_called()


class TestScriptExecuteCommandPauseResume:
    """测试execute_command暂停恢复"""
    
    @pytest.fixture
    def script_executor(self, mock_app):
        mock_app.input_controller = MagicMock()
        mock_app.logging_manager = MagicMock()
        executor = ScriptExecutor(mock_app)
        executor.is_running = True
        executor.is_paused = False
        return executor
    
    def test_delay_interrupted_by_pause(self, script_executor):
        """测试暂停中断延迟"""
        command = {"type": "delay", "time": 5000}
        
        def stop_after_delay():
            time.sleep(0.15)
            script_executor.is_running = False
        
        stop_thread = threading.Thread(target=stop_after_delay)
        stop_thread.start()
        
        start = time.time()
        script_executor.execute_command(command)
        elapsed = time.time() - start
        
        assert elapsed < 1


class TestScriptExecuteCommandEdgeCases:
    """测试execute_command边界情况"""
    
    @pytest.fixture
    def script_executor(self, mock_app):
        mock_app.input_controller = MagicMock()
        mock_app.logging_manager = MagicMock()
        executor = ScriptExecutor(mock_app)
        executor.is_running = True
        executor.is_paused = False
        return executor
    
    def test_execute_keydown_zero_count(self, script_executor):
        """测试零次KeyDown"""
        command = {"type": "keydown", "key": "a", "count": 0}
        
        script_executor.execute_command(command)
        
        script_executor.app.input_controller.key_down.assert_not_called()
    
    def test_execute_moveto_zero_coords(self, script_executor):
        """测试零坐标MoveTo"""
        command = {"type": "moveto", "x": 0, "y": 0}
        
        script_executor.execute_command(command)
        
        script_executor.app.input_controller.move_to.assert_called_once_with(0, 0, priority=1)
    
    def test_execute_delay_zero_time(self, script_executor):
        """测试零延迟"""
        command = {"type": "delay", "time": 0}
        
        start = time.time()
        script_executor.execute_command(command)
        elapsed = time.time() - start
        
        assert elapsed < 0.1
    
    def test_execute_mouse_down_middle_button(self, script_executor):
        """测试中键MouseDown"""
        command = {"type": "mouse_down", "button": "middle", "count": 1}
        
        script_executor.execute_command(command)
        
        script_executor.app.input_controller.mouse_down.assert_called_once_with(button="middle", priority=1)
