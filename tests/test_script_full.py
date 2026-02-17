import pytest
import time
import threading
from unittest.mock import MagicMock, patch
from modules.script import ScriptExecutor


class TestScriptExecutorFull:
    """ScriptExecutor完整测试类"""
    
    @pytest.fixture
    def script_executor(self, mock_app):
        mock_app.script_text = MagicMock()
        mock_app.script_text.get.return_value = 'KeyDown "a", 1'
        mock_app.root = MagicMock()
        mock_app.status_var = MagicMock()
        mock_app.status_labels = {"script": MagicMock()}
        mock_app.is_running = False
        return ScriptExecutor(mock_app)
    
    def test_execute_script_with_all_command_types(self, script_executor):
        """测试执行所有类型命令"""
        script = '''KeyDown "a", 1
KeyUp "a", 1
MoveTo 100, 200
LeftDown 1
LeftUp 1
RightDown 1
RightUp 1
MiddleDown 1
MiddleUp 1
Delay 10
StopScript
StartScript'''
        
        script_executor.run_script_once(script)
        time.sleep(0.3)
        
        script_executor.stop_script()
    
    def test_execute_script_with_special_keys(self, script_executor):
        """测试执行特殊按键"""
        special_keys = ["space", "enter", "tab", "escape", "backspace", "insert", "delete", "home", "end"]
        
        for key in special_keys:
            script = f'KeyDown "{key}", 1\nDelay 5\nKeyUp "{key}", 1'
            
            script_executor.run_script_once(script)
            time.sleep(0.1)
            
            script_executor.stop_script()
    
    def test_execute_script_with_function_keys(self, script_executor):
        """测试执行功能键"""
        for i in range(1, 13):
            script = f'KeyDown "f{i}", 1\nDelay 5\nKeyUp "f{i}", 1'
            
            script_executor.run_script_once(script)
            time.sleep(0.05)
            
            script_executor.stop_script()
    
    def test_execute_script_with_arrow_keys(self, script_executor):
        """测试执行方向键"""
        arrow_keys = ["up", "down", "left", "right"]
        
        for key in arrow_keys:
            script = f'KeyDown "{key}", 1\nDelay 5\nKeyUp "{key}", 1'
            
            script_executor.run_script_once(script)
            time.sleep(0.05)
            
            script_executor.stop_script()
    
    def test_execute_script_with_modifiers(self, script_executor):
        """测试执行修饰键"""
        modifiers = ["ctrl", "alt", "shift"]
        
        for mod in modifiers:
            script = f'KeyDown "{mod}", 1\nDelay 5\nKeyUp "{mod}", 1'
            
            script_executor.run_script_once(script)
            time.sleep(0.05)
            
            script_executor.stop_script()
    
    def test_script_recording_playback_cycle(self, script_executor):
        """测试录制回放循环"""
        script_executor.recording_events = [
            {"type": "keydown", "key": "a", "delay": 50},
            {"type": "keyup", "key": "a", "delay": 50},
            {"type": "moveto", "x": 100, "y": 200, "delay": 10},
            {"type": "mouse_down", "button": "left", "x": 100, "y": 200, "delay": 10},
            {"type": "mouse_up", "button": "left", "x": 100, "y": 200, "delay": 10},
        ]
        
        script_executor.generate_recorded_script()
        
        assert len(script_executor.recording_events) == 5


class TestScriptExecutorEdgeCases:
    """ScriptExecutor边界情况测试"""
    
    @pytest.fixture
    def script_executor(self, mock_app):
        return ScriptExecutor(mock_app)
    
    def test_parse_invalid_keydown_format(self, script_executor):
        """测试无效KeyDown格式"""
        invalid_commands = [
            'KeyDown "a"',
            'KeyDown a, 1',
            'KeyDown',
            'KeyDown ""',
        ]
        
        for cmd in invalid_commands:
            result = script_executor.parse_line(cmd)
    
    def test_parse_invalid_delay_format(self, script_executor):
        """测试无效Delay格式"""
        invalid_commands = [
            'Delay',
            'Delay abc',
            'Delay -100',
        ]
        
        for cmd in invalid_commands:
            result = script_executor.parse_line(cmd)
    
    def test_parse_invalid_moveto_format(self, script_executor):
        """测试无效MoveTo格式"""
        invalid_commands = [
            'MoveTo',
            'MoveTo 100',
            'MoveTo abc, def',
        ]
        
        for cmd in invalid_commands:
            result = script_executor.parse_line(cmd)
    
    def test_run_script_with_only_comments(self, script_executor):
        """测试只有注释的脚本"""
        script = "# This is a comment\n# Another comment"
        
        script_executor.run_script_once(script)
        time.sleep(0.1)
        
        script_executor.stop_script()
    
    def test_run_script_with_only_whitespace(self, script_executor):
        """测试只有空白的脚本"""
        script = "   \n   \n   "
        
        script_executor.run_script_once(script)
        time.sleep(0.1)
        
        assert script_executor.is_running is False


class TestScriptExecutorStateManagement:
    """ScriptExecutor状态管理测试"""
    
    @pytest.fixture
    def script_executor(self, mock_app):
        return ScriptExecutor(mock_app)
    
    def test_state_transitions(self, script_executor):
        """测试状态转换"""
        assert script_executor.is_running is False
        assert script_executor.is_paused is False
        
        script = 'Delay 5000'
        script_executor.run_script(script)
        time.sleep(0.1)
        
        assert script_executor.is_running is True
        
        script_executor.pause_script()
        assert script_executor.is_paused is True
        
        script_executor.resume_script()
        assert script_executor.is_paused is False
        
        script_executor.stop_script()
        assert script_executor.is_running is False
        assert script_executor.is_paused is False
    
    def test_multiple_pause_resume_cycles(self, script_executor):
        """测试多次暂停恢复循环"""
        script = 'Delay 10000'
        script_executor.run_script(script)
        time.sleep(0.1)
        
        for _ in range(5):
            script_executor.pause_script()
            assert script_executor.is_paused is True
            time.sleep(0.02)
            
            script_executor.resume_script()
            assert script_executor.is_paused is False
            time.sleep(0.02)
        
        script_executor.stop_script()
    
    def test_stop_during_pause(self, script_executor):
        """测试暂停期间停止"""
        script = 'Delay 10000'
        script_executor.run_script(script)
        time.sleep(0.1)
        
        script_executor.pause_script()
        assert script_executor.is_paused is True
        
        script_executor.stop_script()
        assert script_executor.is_running is False
        assert script_executor.is_paused is False
