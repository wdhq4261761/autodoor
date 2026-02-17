import pytest
import time
import threading
from unittest.mock import MagicMock, patch
from modules.script import ScriptExecutor


class TestScriptExecutorComprehensive:
    """ScriptExecutor综合测试类"""
    
    @pytest.fixture
    def script_executor(self, mock_app):
        mock_app.script_text = MagicMock()
        mock_app.script_text.get.return_value = 'KeyDown "a", 1'
        mock_app.root = MagicMock()
        mock_app.status_var = MagicMock()
        mock_app.status_labels = {"script": MagicMock()}
        return ScriptExecutor(mock_app)
    
    def test_parse_all_key_commands(self, script_executor):
        """测试解析所有按键命令"""
        commands = [
            ('KeyDown "a", 1', "keydown", "a"),
            ('KeyUp "a", 1', "keyup", "a"),
            ('KeyDown "space", 2', "keydown", "space"),
            ('KeyUp "enter", 1', "keyup", "enter"),
        ]
        
        for cmd, expected_type, expected_key in commands:
            result = script_executor.parse_line(cmd)
            assert result is not None
            assert result["type"] == expected_type
            assert result["key"] == expected_key
    
    def test_parse_all_mouse_commands(self, script_executor):
        """测试解析所有鼠标命令"""
        commands = [
            ("MoveTo 100, 200", "moveto"),
            ("LeftDown 1", "mouse_down"),
            ("LeftUp 1", "mouse_up"),
            ("RightDown 1", "mouse_down"),
            ("RightUp 1", "mouse_up"),
            ("MiddleDown 1", "mouse_down"),
            ("MiddleUp 1", "mouse_up"),
        ]
        
        for cmd, expected_type in commands:
            result = script_executor.parse_line(cmd)
            assert result is not None
            assert result["type"] == expected_type
    
    def test_parse_control_commands(self, script_executor):
        """测试解析控制命令"""
        commands = [
            ("StopScript", "stopscript"),
            ("StartScript", "startscript"),
        ]
        
        for cmd, expected_type in commands:
            result = script_executor.parse_line(cmd)
            assert result is not None
            assert result["type"] == expected_type
    
    def test_run_script_with_loop(self, script_executor):
        """测试循环运行脚本"""
        script = 'KeyDown "a", 1\nDelay 50\nKeyUp "a", 1'
        
        script_executor.run_script(script)
        time.sleep(0.3)
        
        assert script_executor.is_running is True
        
        script_executor.stop_script()
        if script_executor.execution_thread and script_executor.execution_thread.is_alive():
            script_executor.execution_thread.join(timeout=2)
    
    def test_run_script_once_vs_loop(self, script_executor):
        """测试单次运行与循环运行"""
        script = 'KeyDown "a", 1'
        
        script_executor.run_script_once(script)
        time.sleep(0.2)
        
        script_executor.stop_script()
        
        script_executor.run_script(script)
        time.sleep(0.2)
        
        script_executor.stop_script()
        if script_executor.execution_thread and script_executor.execution_thread.is_alive():
            script_executor.execution_thread.join(timeout=2)
    
    def test_script_with_multiple_delays(self, script_executor):
        """测试多个延迟"""
        script = '''Delay 100
Delay 200
Delay 50'''
        
        script_executor.run_script_once(script)
        time.sleep(0.5)
        
        script_executor.stop_script()
    
    def test_script_with_mouse_movements(self, script_executor):
        """测试鼠标移动"""
        script = '''MoveTo 100, 100
LeftDown 1
Delay 50
LeftUp 1
MoveTo 200, 200'''
        
        script_executor.run_script_once(script)
        time.sleep(0.3)
        
        script_executor.stop_script()
    
    def test_script_pause_resume_cycle(self, script_executor):
        """测试暂停恢复循环"""
        script = 'Delay 5000'
        
        script_executor.run_script(script)
        time.sleep(0.1)
        
        for _ in range(3):
            script_executor.pause_script()
            assert script_executor.is_paused is True
            time.sleep(0.05)
            script_executor.resume_script()
            assert script_executor.is_paused is False
            time.sleep(0.05)
        
        script_executor.stop_script()
    
    def test_script_with_special_keys(self, script_executor):
        """测试特殊按键"""
        special_keys = ["space", "enter", "tab", "escape", "backspace"]
        
        for key in special_keys:
            script = f'KeyDown "{key}", 1\nDelay 10\nKeyUp "{key}", 1'
            
            script_executor.run_script_once(script)
            time.sleep(0.1)
            
            script_executor.stop_script()
    
    def test_script_with_function_keys(self, script_executor):
        """测试功能键"""
        for i in range(1, 13):
            script = f'KeyDown "f{i}", 1\nDelay 10\nKeyUp "f{i}", 1'
            
            script_executor.run_script_once(script)
            time.sleep(0.05)
            
            script_executor.stop_script()
    
    def test_script_error_handling(self, script_executor):
        """测试错误处理"""
        invalid_script = "InvalidCommand 123"
        
        script_executor.run_script_once(invalid_script)
        time.sleep(0.2)
        
        script_executor.stop_script()
    
    def test_empty_script_handling(self, script_executor):
        """测试空脚本处理"""
        script_executor.run_script("")
        time.sleep(0.1)
        
        assert script_executor.is_running is False
    
    def test_whitespace_script_handling(self, script_executor):
        """测试空白脚本处理"""
        script_executor.run_script("   \n   \n   ")
        time.sleep(0.1)
        
        assert script_executor.is_running is False


class TestScriptExecutorState:
    """ScriptExecutor状态测试类"""
    
    @pytest.fixture
    def script_executor(self, mock_app):
        return ScriptExecutor(mock_app)
    
    def test_initial_state(self, script_executor):
        """测试初始状态"""
        assert script_executor.is_running is False
        assert script_executor.is_paused is False
        assert script_executor.execution_thread is None
    
    def test_state_after_start(self, script_executor):
        """测试启动后状态"""
        script = 'KeyDown "a", 1'
        
        script_executor.run_script(script)
        time.sleep(0.1)
        
        assert script_executor.is_running is True
        
        script_executor.stop_script()
        if script_executor.execution_thread and script_executor.execution_thread.is_alive():
            script_executor.execution_thread.join(timeout=2)
    
    def test_state_after_stop(self, script_executor):
        """测试停止后状态"""
        script = 'Delay 5000'
        
        script_executor.run_script(script)
        time.sleep(0.1)
        
        script_executor.stop_script()
        
        assert script_executor.is_running is False
        assert script_executor.is_paused is False
    
    def test_state_during_pause(self, script_executor):
        """测试暂停期间状态"""
        script = 'Delay 5000'
        
        script_executor.run_script(script)
        time.sleep(0.1)
        
        script_executor.pause_script()
        
        assert script_executor.is_running is True
        assert script_executor.is_paused is True
        
        script_executor.stop_script()
