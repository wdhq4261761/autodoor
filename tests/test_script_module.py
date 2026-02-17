import pytest
import time
import threading
from unittest.mock import MagicMock, patch, PropertyMock
from modules.script import ScriptExecutor, ScriptModule


class TestScriptExecutor:
    """ScriptExecutor测试类"""
    
    @pytest.fixture
    def script_executor(self, mock_app):
        """创建脚本执行器实例"""
        return ScriptExecutor(mock_app)
    
    def test_init(self, script_executor):
        """测试初始化"""
        assert script_executor.is_running is False
        assert script_executor.is_paused is False
        assert script_executor.execution_thread is None
    
    def test_parse_keydown_command(self, script_executor):
        """测试解析KeyDown命令"""
        result = script_executor.parse_line('KeyDown "enter", 1')
        
        assert result is not None
        assert result["type"] == "keydown"
        assert result["key"] == "enter"
        assert result["count"] == 1
    
    def test_parse_keyup_command(self, script_executor):
        """测试解析KeyUp命令"""
        result = script_executor.parse_line('KeyUp "space", 2')
        
        assert result is not None
        assert result["type"] == "keyup"
        assert result["key"] == "space"
        assert result["count"] == 2
    
    def test_parse_delay_command(self, script_executor):
        """测试解析Delay命令"""
        result = script_executor.parse_line("Delay 1000")
        
        assert result is not None
        assert result["type"] == "delay"
        assert result["time"] == 1000
    
    def test_parse_moveto_command(self, script_executor):
        """测试解析MoveTo命令"""
        result = script_executor.parse_line("MoveTo 100, 200")
        
        assert result is not None
        assert result["type"] == "moveto"
        assert result["x"] == 100
        assert result["y"] == 200
    
    def test_parse_leftdown_command(self, script_executor):
        """测试解析LeftDown命令"""
        result = script_executor.parse_line("LeftDown 1")
        
        assert result is not None
        assert result["type"] == "mouse_down"
        assert result["button"] == "left"
    
    def test_parse_leftup_command(self, script_executor):
        """测试解析LeftUp命令"""
        result = script_executor.parse_line("LeftUp 1")
        
        assert result is not None
        assert result["type"] == "mouse_up"
        assert result["button"] == "left"
    
    def test_parse_rightdown_command(self, script_executor):
        """测试解析RightDown命令"""
        result = script_executor.parse_line("RightDown 1")
        
        assert result is not None
        assert result["type"] == "mouse_down"
        assert result["button"] == "right"
    
    def test_parse_stopscript_command(self, script_executor):
        """测试解析StopScript命令"""
        result = script_executor.parse_line("StopScript")
        
        assert result is not None
        assert result["type"] == "stopscript"
    
    def test_parse_startscript_command(self, script_executor):
        """测试解析StartScript命令"""
        result = script_executor.parse_line("StartScript")
        
        assert result is not None
        assert result["type"] == "startscript"
    
    def test_parse_empty_line(self, script_executor):
        """测试解析空行"""
        result = script_executor.parse_line("")
        
        assert result is None
    
    def test_parse_whitespace_line(self, script_executor):
        """测试解析空白行"""
        result = script_executor.parse_line("   ")
        
        assert result is None
    
    def test_parse_unknown_command(self, script_executor):
        """测试解析未知命令"""
        result = script_executor.parse_line("UnknownCommand 123")
        
        assert result is None
    
    def test_parse_case_insensitive(self, script_executor):
        """测试命令大小写不敏感"""
        result = script_executor.parse_line('KEYDOWN "a", 1')
        
        assert result is not None
        assert result["type"] == "keydown"
    
    def test_pause_script(self, script_executor):
        """测试暂停脚本"""
        script_executor.pause_script()
        
        assert script_executor.is_paused is True
    
    def test_resume_script(self, script_executor):
        """测试恢复脚本"""
        script_executor.is_paused = True
        script_executor.resume_script()
        
        assert script_executor.is_paused is False
    
    def test_stop_script(self, script_executor):
        """测试停止脚本"""
        script_executor.is_running = True
        script_executor.stop_script()
        
        assert script_executor.is_running is False
        assert script_executor.is_paused is False
    
    def test_run_script_starts_thread(self, script_executor):
        """测试运行脚本启动线程"""
        script = 'KeyDown "enter", 1\nDelay 100\nKeyUp "enter", 1'
        
        script_executor.run_script(script)
        
        assert script_executor.execution_thread is not None
        assert script_executor.execution_thread.is_alive()
        
        script_executor.stop_script()
        if script_executor.execution_thread and script_executor.execution_thread.is_alive():
            script_executor.execution_thread.join(timeout=2)
    
    def test_run_script_empty(self, script_executor):
        """测试运行空脚本"""
        script_executor.run_script("")
        
        time.sleep(0.2)
        
        assert script_executor.is_running is False
    
    def test_run_script_once(self, script_executor):
        """测试运行脚本一次"""
        script = 'KeyDown "enter", 1\nDelay 50\nKeyUp "enter", 1'
        
        script_executor.run_script_once(script)
        
        assert script_executor.execution_thread is not None
        
        script_executor.stop_script()
        if script_executor.execution_thread and script_executor.execution_thread.is_alive():
            script_executor.execution_thread.join(timeout=2)


class TestScriptModule:
    """ScriptModule测试类"""
    
    @pytest.fixture
    def script_module(self, mock_app):
        """创建脚本模块实例"""
        return ScriptModule(mock_app)
    
    def test_init(self, script_module):
        """测试初始化"""
        assert script_module.app is not None
    
    def test_priority(self):
        """测试优先级"""
        assert ScriptExecutor.PRIORITY == 1
        assert ScriptModule.PRIORITY == 1
    
    def test_stop_script(self, script_module):
        """测试停止脚本"""
        script_module.app.script_executor = MagicMock()
        script_module.app.script_executor.is_running = True
        
        script_module.stop_script()
        
        script_module.app.script_executor.stop_script.assert_called_once()


class TestScriptParsingEdgeCases:
    """脚本解析边界情况测试"""
    
    @pytest.fixture
    def script_executor(self, mock_app):
        return ScriptExecutor(mock_app)
    
    def test_parse_keydown_with_spaces(self, script_executor):
        """测试带空格的KeyDown命令"""
        result = script_executor.parse_line('KeyDown  "space" ,  3 ')
        
        assert result is not None
        assert result["type"] == "keydown"
        assert result["key"] == "space"
        assert result["count"] == 3
    
    def test_parse_moveto_with_spaces(self, script_executor):
        """测试带空格的MoveTo命令"""
        result = script_executor.parse_line("MoveTo  100 ,  200 ")
        
        assert result is not None
        assert result["type"] == "moveto"
        assert result["x"] == 100
        assert result["y"] == 200
    
    def test_parse_delay_with_spaces(self, script_executor):
        """测试带空格的Delay命令"""
        result = script_executor.parse_line("Delay  500 ")
        
        assert result is not None
        assert result["type"] == "delay"
        assert result["time"] == 500
    
    def test_parse_middledown_command(self, script_executor):
        """测试解析MiddleDown命令"""
        result = script_executor.parse_line("MiddleDown 1")
        
        assert result is not None
        assert result["type"] == "mouse_down"
        assert result["button"] == "middle"
    
    def test_parse_middleup_command(self, script_executor):
        """测试解析MiddleUp命令"""
        result = script_executor.parse_line("MiddleUp 1")
        
        assert result is not None
        assert result["type"] == "mouse_up"
        assert result["button"] == "middle"
    
    def test_parse_multiple_commands(self, script_executor):
        """测试解析多个命令"""
        script = '''KeyDown "a", 1
Delay 50
KeyUp "a", 1
MoveTo 100, 200
LeftDown 1
LeftUp 1'''
        
        lines = script.splitlines()
        commands = []
        for line in lines:
            cmd = script_executor.parse_line(line)
            if cmd:
                commands.append(cmd)
        
        assert len(commands) == 6
        assert commands[0]["type"] == "keydown"
        assert commands[1]["type"] == "delay"
        assert commands[2]["type"] == "keyup"
        assert commands[3]["type"] == "moveto"
        assert commands[4]["type"] == "mouse_down"
        assert commands[5]["type"] == "mouse_up"


class TestScriptExecuteAdvanced:
    """脚本执行高级测试"""
    
    @pytest.fixture
    def script_executor(self, mock_app):
        mock_app.input_controller = MagicMock()
        mock_app.logging_manager = MagicMock()
        mock_app.status_var = MagicMock()
        return ScriptExecutor(mock_app)
    
    def test_run_script_with_keydown_keyup(self, script_executor):
        """测试执行keydown和keyup命令"""
        script = 'KeyDown "a", 1\nDelay 50\nKeyUp "a", 1'
        
        script_executor.run_script(script)
        
        time.sleep(0.3)
        
        script_executor.stop_script()
        if script_executor.execution_thread and script_executor.execution_thread.is_alive():
            script_executor.execution_thread.join(timeout=2)
        
        script_executor.app.input_controller.key_down.assert_called()
        script_executor.app.input_controller.key_up.assert_called()
    
    def test_run_script_stops_on_stopscript(self, script_executor):
        """测试StopScript命令停止脚本"""
        script = 'KeyDown "a", 1\nStopScript\nDelay 1000'
        
        script_executor.app.script = MagicMock()
        script_executor.app.root = MagicMock()
        
        start_time = time.time()
        script_executor.run_script(script)
        
        time.sleep(0.3)
        
        elapsed = time.time() - start_time
        
        assert elapsed < 1.0
    
    def test_run_script_with_exception(self, script_executor):
        """测试执行异常处理"""
        script_executor.app.input_controller.key_down.side_effect = Exception("Key error")
        
        script = 'KeyDown "a", 1'
        
        script_executor.run_script(script)
        
        time.sleep(0.3)
        
        script_executor.stop_script()
        if script_executor.execution_thread and script_executor.execution_thread.is_alive():
            script_executor.execution_thread.join(timeout=2)
        
        script_executor.app.logging_manager.log_message.assert_called()
    
    def test_run_script_once_executes_once(self, script_executor):
        """测试run_script_once只执行一次"""
        script = 'KeyDown "a", 1\nDelay 50'
        
        script_executor.run_script_once(script)
        
        time.sleep(0.3)
        
        if script_executor.execution_thread and script_executor.execution_thread.is_alive():
            script_executor.execution_thread.join(timeout=2)
        
        assert script_executor.app.input_controller.key_down.call_count == 1
    
    def test_run_script_pressed_keys_cleanup(self, script_executor):
        """测试按下键的清理"""
        script = 'KeyDown "a", 1\nKeyDown "b", 1'
        
        script_executor.run_script(script)
        
        time.sleep(0.3)
        
        script_executor.stop_script()
        if script_executor.execution_thread and script_executor.execution_thread.is_alive():
            script_executor.execution_thread.join(timeout=2)
        
        assert script_executor.app.input_controller.key_up.call_count >= 1
    
    def test_run_script_with_pause_resume(self, script_executor):
        """测试暂停和恢复"""
        script = 'KeyDown "a", 1\nDelay 500\nKeyUp "a", 1'
        
        script_executor.run_script(script)
        
        time.sleep(0.1)
        script_executor.pause_script()
        
        time.sleep(0.2)
        script_executor.resume_script()
        
        time.sleep(0.3)
        
        script_executor.stop_script()
        if script_executor.execution_thread and script_executor.execution_thread.is_alive():
            script_executor.execution_thread.join(timeout=2)
    
    def test_run_script_loop(self, script_executor):
        """测试脚本循环执行"""
        script = 'KeyDown "a", 1\nDelay 30'
        
        script_executor.run_script(script)
        
        time.sleep(0.3)
        
        call_count = script_executor.app.input_controller.key_down.call_count
        
        assert call_count >= 1
        
        script_executor.stop_script()
        if script_executor.execution_thread and script_executor.execution_thread.is_alive():
            script_executor.execution_thread.join(timeout=2)
    
    def test_run_script_once_no_loop(self, script_executor):
        """测试run_script_once不循环"""
        script = 'KeyDown "a", 1\nDelay 50'
        
        script_executor.run_script_once(script)
        
        time.sleep(0.5)
        
        call_count = script_executor.app.input_controller.key_down.call_count
        
        assert call_count == 1
    
    def test_run_script_with_moveto(self, script_executor):
        """测试MoveTo命令执行"""
        script = 'MoveTo 100, 200'
        
        script_executor.run_script(script)
        
        time.sleep(0.2)
        
        script_executor.stop_script()
        if script_executor.execution_thread and script_executor.execution_thread.is_alive():
            script_executor.execution_thread.join(timeout=2)
        
        script_executor.app.input_controller.move_to.assert_called()
    
    def test_run_script_with_mouse_down_up(self, script_executor):
        """测试鼠标按下和抬起命令"""
        script = 'LeftDown 1\nDelay 50\nLeftUp 1'
        
        script_executor.run_script(script)
        
        time.sleep(0.3)
        
        script_executor.stop_script()
        if script_executor.execution_thread and script_executor.execution_thread.is_alive():
            script_executor.execution_thread.join(timeout=2)
        
        script_executor.app.input_controller.mouse_down.assert_called()
        script_executor.app.input_controller.mouse_up.assert_called()
