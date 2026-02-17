import pytest
import time
import threading
from unittest.mock import MagicMock, patch
from modules.script import ScriptExecutor, ScriptModule


class TestScriptExecutorAdvanced:
    """ScriptExecutor高级测试类"""
    
    @pytest.fixture
    def script_executor(self, mock_app):
        return ScriptExecutor(mock_app)
    
    def test_run_script_with_moveto(self, script_executor):
        """测试MoveTo命令执行"""
        script = "MoveTo 100, 200"
        
        script_executor.run_script_once(script)
        time.sleep(0.3)
        
        script_executor.app.input_controller.move_to.assert_called()
        
        script_executor.stop_script()
    
    def test_run_script_with_delay(self, script_executor):
        """测试Delay命令执行"""
        script = "Delay 100"
        
        start = time.time()
        script_executor.run_script_once(script)
        time.sleep(0.2)
        elapsed = time.time() - start
        
        script_executor.stop_script()
    
    def test_run_script_with_mouse_down(self, script_executor):
        """测试MouseDown命令执行"""
        script = "LeftDown 1"
        
        script_executor.run_script_once(script)
        time.sleep(0.2)
        
        script_executor.stop_script()
    
    def test_run_script_with_mouse_up(self, script_executor):
        """测试MouseUp命令执行"""
        script = "LeftUp 1"
        
        script_executor.run_script_once(script)
        time.sleep(0.2)
        
        script_executor.stop_script()
    
    def test_run_script_with_multiple_commands(self, script_executor):
        """测试多命令执行"""
        script = '''KeyDown "a", 1
Delay 50
KeyUp "a", 1'''
        
        script_executor.run_script_once(script)
        time.sleep(0.3)
        
        script_executor.stop_script()
    
    def test_pause_and_resume(self, script_executor):
        """测试暂停和恢复"""
        script = "Delay 5000"
        
        script_executor.run_script(script)
        time.sleep(0.1)
        
        script_executor.pause_script()
        assert script_executor.is_paused is True
        
        script_executor.resume_script()
        assert script_executor.is_paused is False
        
        script_executor.stop_script()
    
    def test_optimize_delay(self, script_executor):
        """测试延迟优化"""
        delay_cmd = {"type": "delay", "time": 200}
        keydown_cmd = {"type": "keydown", "key": "a", "count": 1}
        
        result = script_executor._optimize_delay(delay_cmd, keydown_cmd)
        
        assert result["time"] == 100
    
    def test_optimize_delay_no_next(self, script_executor):
        """测试无下一命令时的延迟优化"""
        delay_cmd = {"type": "delay", "time": 200}
        
        result = script_executor._optimize_delay(delay_cmd, None)
        
        assert result["time"] == 200
    
    def test_optimize_delay_non_delay(self, script_executor):
        """测试非延迟命令"""
        keydown_cmd = {"type": "keydown", "key": "a", "count": 1}
        
        result = script_executor._optimize_delay(keydown_cmd, None)
        
        assert result == keydown_cmd


class TestScriptModuleAdvanced:
    """ScriptModule高级测试类"""
    
    @pytest.fixture
    def script_module(self, mock_app):
        mock_app.script_text = MagicMock()
        mock_app.script_text.get.return_value = "KeyDown \"a\", 1"
        mock_app.record_btn = MagicMock()
        mock_app.stop_record_btn = MagicMock()
        mock_app.status_labels = {"script": MagicMock()}
        mock_app.status_var = MagicMock()
        return ScriptModule(mock_app)
    
    def test_start_script_empty(self, script_module):
        """测试空脚本启动"""
        script_module.app.script_text.get.return_value = ""
        
        with patch('tkinter.messagebox.showwarning'):
            script_module.start_script()
    
    def test_stop_script_not_running(self, script_module):
        """测试停止未运行的脚本"""
        script_module.app.script_executor = None
        
        script_module.stop_script()
    
    def test_start_recording(self, script_module):
        """测试开始录制"""
        script_module.app.platform_adapter = MagicMock()
        script_module.app.platform_adapter.platform = "Darwin"
        
        script_module.start_recording()
        
        assert script_module.app.script_executor is not None
    
    def test_stop_recording(self, script_module):
        """测试停止录制"""
        script_module.app.platform_adapter = MagicMock()
        script_module.app.platform_adapter.platform = "Darwin"
        
        script_module.start_recording()
        time.sleep(0.1)
        script_module.stop_recording()


class TestScriptKeycodeConversion:
    """按键码转换测试"""
    
    @pytest.fixture
    def script_executor(self, mock_app):
        return ScriptExecutor(mock_app)
    
    def test_keycode_to_name_letters(self, script_executor):
        """测试字母键码转换"""
        assert script_executor._keycode_to_name(0) == 'a'
        assert script_executor._keycode_to_name(1) == 's'
        assert script_executor._keycode_to_name(2) == 'd'
    
    def test_keycode_to_name_numbers(self, script_executor):
        """测试数字键码转换"""
        assert script_executor._keycode_to_name(18) == '1'
        assert script_executor._keycode_to_name(19) == '2'
        assert script_executor._keycode_to_name(20) == '3'
    
    def test_keycode_to_name_special(self, script_executor):
        """测试特殊键码转换"""
        assert script_executor._keycode_to_name(36) == 'return'
        assert script_executor._keycode_to_name(48) == 'tab'
        assert script_executor._keycode_to_name(49) == 'space'
    
    def test_keycode_to_name_unknown(self, script_executor):
        """测试未知键码"""
        result = script_executor._keycode_to_name(999)
        
        assert result == "key_999"


class TestScriptGenerateRecordedScript:
    """生成录制脚本测试"""
    
    @pytest.fixture
    def script_executor(self, mock_app):
        mock_app.script_text = MagicMock()
        mock_app.root = MagicMock()
        return ScriptExecutor(mock_app)
    
    def test_generate_recorded_script_keydown(self, script_executor):
        """测试生成KeyDown脚本"""
        script_executor.recording_events = [
            {"type": "keydown", "key": "a", "delay": 100}
        ]
        
        script_executor.generate_recorded_script()
    
    def test_generate_recorded_script_keyup(self, script_executor):
        """测试生成KeyUp脚本"""
        script_executor.recording_events = [
            {"type": "keyup", "key": "a", "delay": 50}
        ]
        
        script_executor.generate_recorded_script()
    
    def test_generate_recorded_script_moveto(self, script_executor):
        """测试生成MoveTo脚本"""
        script_executor.recording_events = [
            {"type": "moveto", "x": 100, "y": 200, "delay": 0}
        ]
        
        script_executor.generate_recorded_script()
    
    def test_generate_recorded_script_mouse_down(self, script_executor):
        """测试生成MouseDown脚本"""
        script_executor.recording_events = [
            {"type": "mouse_down", "button": "left", "x": 100, "y": 200, "delay": 0}
        ]
        
        script_executor.generate_recorded_script()
    
    def test_generate_recorded_script_mouse_up(self, script_executor):
        """测试生成MouseUp脚本"""
        script_executor.recording_events = [
            {"type": "mouse_up", "button": "left", "x": 100, "y": 200, "delay": 0}
        ]
        
        script_executor.generate_recorded_script()
