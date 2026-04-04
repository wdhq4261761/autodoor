"""
动作节点适配器

将输入操作封装为行为树动作节点
"""

import time
from typing import Any, Dict, Optional, TYPE_CHECKING

from modules.behavior_tree.nodes import ActionNode, NodeStatus

if TYPE_CHECKING:
    from modules.behavior_tree.context import ExecutionContext


class KeyPressNode(ActionNode):
    """
    按键动作节点
    
    执行按键操作
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
    
    def _execute_action(self, context: "ExecutionContext") -> NodeStatus:
        key = self.config.get("key", "")
        action = self.config.get("action", "press")
        duration = self.config.get("duration", 0)
        
        if not key:
            context.log(f"按键节点 {self.name}: 未配置按键")
            return NodeStatus.FAILURE
        
        try:
            success = context.execute_key_press(key, action, duration)
            
            if success:
                context.log(f"按键节点 {self.name}: 执行按键 {key}")
                return NodeStatus.SUCCESS
            else:
                context.log(f"按键节点 {self.name}: 按键执行失败")
                return NodeStatus.FAILURE
                
        except Exception as e:
            context.log(f"按键节点 {self.name}: 执行出错 - {e}")
            return NodeStatus.FAILURE
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"] = {
            **self.config,
            "key": self.config.get("key", ""),
            "action": self.config.get("action", "press"),
            "duration": self.config.get("duration", 0),
        }
        return data


class MouseClickNode(ActionNode):
    """
    鼠标点击动作节点
    
    执行鼠标点击操作
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
    
    def _execute_action(self, context: "ExecutionContext") -> NodeStatus:
        button = self.config.get("button", "left")
        action = self.config.get("action", "press")
        duration = self.config.get("duration", 0)
        position = self.config.get("position")
        use_blackboard = self.config.get("use_blackboard", False)
        position_key = self.config.get("position_key") or "last_detection_position"
        click_count = self.config.get("click_count", 1)
        click_interval = self.config.get("click_interval", 100)
        
        try:
            click_position = position
            
            if use_blackboard:
                click_position = context.blackboard.get(position_key)
            
            if click_count == -1:
                click_index = 0
                while context.check_running():
                    success = context.execute_mouse_click(button, action, click_position, duration)
                    
                    if not success:
                        return NodeStatus.FAILURE
                    
                    click_index += 1
                    time.sleep(click_interval / 1000.0)
                
                pos_str = click_position if click_position else "当前位置"
                context.log(f"鼠标: {button} @ {pos_str} (点击{click_index}次)")
                return NodeStatus.SUCCESS
            elif click_count > 1:
                for i in range(click_count):
                    if not context.check_running():
                        return NodeStatus.ABORTED
                    
                    success = context.execute_mouse_click(button, action, click_position, duration)
                    
                    if not success:
                        return NodeStatus.FAILURE
                    
                    if i < click_count - 1:
                        time.sleep(click_interval / 1000.0)
                
                pos_str = click_position if click_position else "当前位置"
                context.log(f"鼠标: {click_count}击 {button} @ {pos_str}")
                return NodeStatus.SUCCESS
            else:
                success = context.execute_mouse_click(button, action, click_position, duration)
                
                if success:
                    pos_str = click_position if click_position else "当前位置"
                    context.log(f"鼠标: {button} @ {pos_str}")
                    return NodeStatus.SUCCESS
                else:
                    return NodeStatus.FAILURE
                
        except Exception as e:
            context.log(f"鼠标: 执行出错 - {e}")
            return NodeStatus.FAILURE
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"] = {
            **self.config,
            "button": self.config.get("button", "left"),
            "action": self.config.get("action", "press"),
            "duration": self.config.get("duration", 0),
            "position": self.config.get("position"),
            "use_blackboard": self.config.get("use_blackboard", False),
            "position_key": self.config.get("position_key", "last_detection_position"),
            "click_count": self.config.get("click_count", 1),
            "click_interval": self.config.get("click_interval", 100),
        }
        return data


class MouseMoveNode(ActionNode):
    """
    鼠标移动动作节点
    
    移动鼠标到指定位置，支持拖拽操作
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
    
    def _execute_action(self, context: "ExecutionContext") -> NodeStatus:
        position = self.config.get("position")
        use_blackboard = self.config.get("use_blackboard", False)
        position_key = self.config.get("position_key", "last_ocr_position")
        relative = self.config.get("relative", False)
        smooth = self.config.get("smooth", True)
        move_type = self.config.get("move_type", "移动")
        drag_button = self.config.get("drag_button", "left")
        end_position = self.config.get("end_position")
        use_blackboard_end = self.config.get("use_blackboard_end", False)
        position_key_end = self.config.get("position_key_end", "")
        drag_duration = self.config.get("drag_duration", 0)
        
        try:
            move_position = position
            
            if use_blackboard:
                move_position = context.blackboard.get(position_key)
            
            if not move_position:
                context.log(f"鼠标移动节点 {self.name}: 未指定位置")
                return NodeStatus.FAILURE
            
            if context.input_controller is None:
                context.log(f"鼠标移动节点 {self.name}: 输入控制器不可用")
                return NodeStatus.FAILURE
            
            
            if move_type == "拖拽":
                drag_end_position = end_position
                
                if use_blackboard_end:
                    drag_end_position = context.blackboard.get(position_key_end)
                
                if not drag_end_position:
                    context.log(f"鼠标移动节点 {self.name}: 未指定拖拽终点")
                    return NodeStatus.FAILURE
                
                
                context.input_controller.move_to(move_position[0], move_position[1])
                time.sleep(0.05)
                
                context.input_controller.mouse_down(drag_button)
                time.sleep(0.05)
                
                if drag_duration > 0:
                    steps = max(10, drag_duration // 50)
                    dx = (drag_end_position[0] - move_position[0]) / steps
                    dy = (drag_end_position[1] - move_position[1]) / steps
                    
                    for i in range(steps):
                        if not context.check_running():
                            context.input_controller.mouse_up(drag_button)
                            return NodeStatus.ABORTED
                        
                        
                        current_x = int(move_position[0] + dx * (i + 1))
                        current_y = int(move_position[1] + dy * (i + 1))
                        context.input_controller.move_to(current_x, current_y)
                        time.sleep(drag_duration / 1000.0 / steps)
                else:
                    steps = 20
                    dx = (drag_end_position[0] - move_position[0]) / steps
                    dy = (drag_end_position[1] - move_position[1]) / steps
                    
                    for i in range(steps):
                        if not context.check_running():
                            context.input_controller.mouse_up(drag_button)
                            return NodeStatus.ABORTED
                        
                        current_x = int(move_position[0] + dx * (i + 1))
                        current_y = int(move_position[1] + dy * (i + 1))
                        context.input_controller.move_to(current_x, current_y)
                        time.sleep(0.02)
                
                time.sleep(0.05)
                context.input_controller.mouse_up(drag_button)
                
                context.log(f"鼠标移动节点 {self.name}: 从 {move_position} 拖拽到 {drag_end_position}")
                return NodeStatus.SUCCESS
            else:
                if relative:
                    context.input_controller.move_relative(move_position[0], move_position[1])
                else:
                    context.input_controller.move_to(move_position[0], move_position[1])
                
                context.log(f"鼠标移动节点 {self.name}: 移动到 {move_position}")
                return NodeStatus.SUCCESS
                
        except Exception as e:
            context.log(f"鼠标移动节点 {self.name}: 执行出错 - {e}")
            try:
                context.input_controller.mouse_up(drag_button)
            except:
                pass
            return NodeStatus.FAILURE
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"] = {
            **self.config,
            "position": self.config.get("position"),
            "use_blackboard": self.config.get("use_blackboard", False),
            "position_key": self.config.get("position_key", "last_ocr_position"),
            "relative": self.config.get("relative", False),
            "smooth": self.config.get("smooth", True),
            "move_type": self.config.get("move_type", "移动"),
            "drag_button": self.config.get("drag_button", "left"),
            "end_position": self.config.get("end_position"),
            "use_blackboard_end": self.config.get("use_blackboard_end", False),
            "position_key_end": self.config.get("position_key_end", ""),
            "drag_duration": self.config.get("drag_duration", 0),
        }
        return data


class MouseScrollNode(ActionNode):
    """
    鼠标滚轮动作节点
    
    执行鼠标滚轮滚动操作
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
    
    def _execute_action(self, context: "ExecutionContext") -> NodeStatus:
        distance = self.config.get("distance", 5)
        clicks = self.config.get("clicks", 1)
        direction = self.config.get("direction", "向上")
        
        try:
            scroll_distance = distance
            scroll_direction = "垂直"
            
            if direction == "向上":
                scroll_distance = abs(distance)
                scroll_direction = "垂直"
            elif direction == "向下":
                scroll_distance = -abs(distance)
                scroll_direction = "垂直"
            elif direction == "向左":
                scroll_distance = -abs(distance)
                scroll_direction = "水平"
            elif direction == "向右":
                scroll_distance = abs(distance)
                scroll_direction = "水平"
            
            success = context.execute_mouse_scroll(scroll_distance, clicks, scroll_direction)
            
            if success:
                context.log(f"鼠标滚轮节点 {self.name}: {direction}滚动 {abs(distance)}距离 × {clicks}次")
                return NodeStatus.SUCCESS
            else:
                context.log(f"鼠标滚轮节点 {self.name}: 滚轮执行失败")
                return NodeStatus.FAILURE
                
        except Exception as e:
            context.log(f"鼠标滚轮节点 {self.name}: 执行出错 - {e}")
            return NodeStatus.FAILURE
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"] = {
            **self.config,
            "distance": self.config.get("distance", 5),
            "clicks": self.config.get("clicks", 1),
            "direction": self.config.get("direction", "向上"),
        }
        return data


class DelayNode(ActionNode):
    """
    延时动作节点
    
    非阻塞延时：每次tick检查是否到达指定时间
    """

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self._delay_start: Optional[float] = None
        self._delay_completed: bool = False
    
    def _execute_action(self, context: "ExecutionContext") -> NodeStatus:
        if self._delay_completed:
            return NodeStatus.SUCCESS
        
        duration_ms = self.config.get("duration_ms", 1000)
        
        if self._delay_start is None:
            self._delay_start = time.time() * 1000
            context.log(f"延时节点 {self.name}: 开始延时 {duration_ms}ms")
        
        elapsed = time.time() * 1000 - self._delay_start
        
        if elapsed >= duration_ms:
            context.log(f"延时节点 {self.name}: 延时完成")
            self._delay_completed = True
            return NodeStatus.SUCCESS
        
        return NodeStatus.RUNNING
    
    def reset(self) -> None:
        super().reset()
        self._delay_start = None
        self._delay_completed = False
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"] = {
            **self.config,
            "duration_ms": self.config.get("duration_ms", 1000),
        }
        return data


class SetVariableNode(ActionNode):
    """
    设置变量动作节点
    
    设置黑板变量的值
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
    
    def _execute_action(self, context: "ExecutionContext") -> NodeStatus:
        variable_name = self.config.get("variable_name", "")
        value = self.config.get("value")
        value_type = self.config.get("value_type", "static")
        self.operation = self.config.get("operation", "set")
    
    def _execute_action(self, context: "ExecutionContext") -> NodeStatus:
        variable_name = self.config.get("variable_name", "")
        value = self.config.get("value")
        value_type = self.config.get("value_type", "static")
        operation = self.config.get("operation", "set")
        
        if not variable_name:
            context.log(f"设置变量节点 {self.name}: 未配置变量名")
            return NodeStatus.FAILURE
        
        try:
            if operation == "set":
                context.blackboard.set(variable_name, value)
                context.log(f"设置变量节点 {self.name}: 设置 {variable_name} = {value}")
            
            elif operation == "increment":
                result = context.blackboard.increment(variable_name, value if isinstance(value, (int, float)) else 1)
                context.log(f"设置变量节点 {self.name}: {variable_name} += {value if isinstance(value, (int, float)) else 1} = {result}")
            
            elif operation == "delete":
                context.blackboard.delete(variable_name)
                context.log(f"设置变量节点 {self.name}: 删除变量 {variable_name}")
            
            elif operation == "clear":
                context.blackboard.clear()
                context.log(f"设置变量节点 {self.name}: 清空黑板")
            
            return NodeStatus.SUCCESS
                
        except Exception as e:
            context.log(f"设置变量节点 {self.name}: 执行出错 - {e}")
            return NodeStatus.FAILURE
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"] = {
            **self.config,
            "variable_name": self.config.get("variable_name", ""),
            "value": self.config.get("value"),
            "value_type": self.config.get("value_type", "static"),
            "operation": self.config.get("operation", "set"),
        }
        return data


class CodeNode(ActionNode):
    """
    代码动作节点
    
    执行外部代码文件（Python/Batch/PowerShell）
    非阻塞模式：每次tick检查进程是否完成
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self._process: Optional[Any] = None
        self._code_started = False
        self._stdout_buffer = ""
        self._stderr_buffer = ""
    
    def _execute_action(self, context: "ExecutionContext") -> NodeStatus:
        code_path = self.config.get("code_path", "")
        code_type = self.config.get("code_type", "auto")
        args = self.config.get("args", [])
        
        if not code_path:
            context.log(f"代码节点 {self.name}: 未配置代码路径")
            return NodeStatus.FAILURE
        
        try:
            import subprocess
            from pathlib import Path
            import select
            
            if not self._code_started:
                code_file = Path(code_path)
                if not code_file.exists():
                    context.log(f"代码节点 {self.name}: 代码文件不存在 {code_path}")
                    return NodeStatus.FAILURE
                
                if code_type == "auto":
                    if code_file.suffix == ".py":
                        cmd = ["python", "-u", str(code_file)] + args
                    elif code_file.suffix in [".bat", ".cmd"]:
                        cmd = [str(code_file)] + args
                    elif code_file.suffix == ".ps1":
                        cmd = ["powershell", "-File", str(code_file)] + args
                    else:
                        cmd = [str(code_file)] + args
                else:
                    cmd = [str(code_file)] + args
                
                context.log(f"代码节点 {self.name}: 启动代码 {code_path}")
                context.log(f"代码节点 {self.name}: 命令: {' '.join(cmd)}")
                self._process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                self._code_started = True
                self._stdout_buffer = ""
                self._stderr_buffer = ""
                return NodeStatus.RUNNING
            
            if self._process is None:
                return NodeStatus.FAILURE
            
            if not context.check_running():
                self._process.terminate()
                self._process = None
                self._code_started = False
                return NodeStatus.ABORTED
            
            import threading
            import queue
            
            def read_output(pipe, queue_out):
                try:
                    for line in iter(pipe.readline, ''):
                        if line:
                            queue_out.put(line)
                finally:
                    pipe.close()
            
            if not hasattr(self, '_stdout_queue'):
                self._stdout_queue = queue.Queue()
                self._stderr_queue = queue.Queue()
                self._stdout_thread = threading.Thread(target=read_output, args=(self._process.stdout, self._stdout_queue), daemon=True)
                self._stderr_thread = threading.Thread(target=read_output, args=(self._process.stderr, self._stderr_queue), daemon=True)
                self._stdout_thread.start()
                self._stderr_thread.start()
            
            while not self._stdout_queue.empty():
                try:
                    line = self._stdout_queue.get_nowait()
                    context.log(f"[stdout] {line.rstrip()}")
                except queue.Empty:
                    break
            
            while not self._stderr_queue.empty():
                try:
                    line = self._stderr_queue.get_nowait()
                    context.log(f"[stderr] {line.rstrip()}")
                except queue.Empty:
                    break
            
            poll_result = self._process.poll()
            if poll_result is None:
                return NodeStatus.RUNNING
            
            while not self._stdout_queue.empty():
                try:
                    line = self._stdout_queue.get_nowait()
                    context.log(f"[stdout] {line.rstrip()}")
                except queue.Empty:
                    break
            
            while not self._stderr_queue.empty():
                try:
                    line = self._stderr_queue.get_nowait()
                    context.log(f"[stderr] {line.rstrip()}")
                except queue.Empty:
                    break
            
            self._process = None
            self._code_started = False
            if hasattr(self, '_stdout_queue'):
                delattr(self, '_stdout_queue')
                delattr(self, '_stderr_queue')
            
            if poll_result == 0:
                context.log(f"代码节点 {self.name}: 执行成功 (退出码: 0)")
                return NodeStatus.SUCCESS
            else:
                context.log(f"代码节点 {self.name}: 执行失败 (退出码: {poll_result})")
                return NodeStatus.FAILURE
                
        except Exception as e:
            context.log(f"代码节点 {self.name}: 执行出错 - {e}")
            self._process = None
            self._code_started = False
            return NodeStatus.FAILURE
    
    def reset(self) -> None:
        super().reset()
        if self._process is not None:
            try:
                self._process.terminate()
            except:
                pass
        self._process = None
        self._code_started = False
        self._stdout_buffer = ""
        self._stderr_buffer = ""
        if hasattr(self, '_stdout_queue'):
            delattr(self, '_stdout_queue')
            delattr(self, '_stderr_queue')
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"] = {
            **self.config,
            "code_path": self.config.get("code_path", ""),
            "code_type": self.config.get("code_type", "auto"),
            "args": self.config.get("args", []),
        }
        return data


class ScriptNode(ActionNode):
    """
    脚本动作节点
    
    执行原项目脚本格式的txt文件，支持按键、鼠标、延时等命令
    非阻塞模式：每次tick检查脚本是否完成
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self._executor: Optional[Any] = None
        self._script_started = False
    
    def _execute_action(self, context: "ExecutionContext") -> NodeStatus:
        script_path = self.config.get("script_path", "")
        
        if not script_path:
            context.log(f"脚本节点 {self.name}: 未配置脚本路径")
            return NodeStatus.FAILURE
        
        try:
            if not self._script_started:
                from pathlib import Path
                from modules.script import ScriptExecutor
                
                script_file = Path(script_path)
                if not script_file.exists():
                    context.log(f"脚本节点 {self.name}: 脚本文件不存在 {script_path}")
                    return NodeStatus.FAILURE
                
                with open(script_file, 'r', encoding='utf-8') as f:
                    script_content = f.read()
                
                if not script_content.strip():
                    context.log(f"脚本节点 {self.name}: 脚本内容为空")
                    return NodeStatus.FAILURE
                
                context.log(f"脚本节点 {self.name}: 开始执行脚本 {script_path}")
                
                self._executor = ScriptExecutor(context.app)
                self._executor.run_script_once(script_content)
                self._script_started = True
                return NodeStatus.RUNNING
            
            if self._executor and self._executor.is_running:
                if not context.check_running():
                    self._executor.stop_script()
                    return NodeStatus.ABORTED
                return NodeStatus.RUNNING
            
            context.log(f"脚本节点 {self.name}: 脚本执行完成")
            return NodeStatus.SUCCESS
                
        except Exception as e:
            context.log(f"脚本节点 {self.name}: 执行出错 - {e}")
            return NodeStatus.FAILURE
    
    def reset(self) -> None:
        super().reset()
        if self._executor and self._executor.is_running:
            try:
                self._executor.stop_script()
            except Exception:
                pass
        self._executor = None
        self._script_started = False
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"] = {
            **self.config,
            "script_path": self.config.get("script_path", ""),
            "loop": self.config.get("loop", False),
        }
        return data


class AlarmNode(ActionNode):
    """
    报警动作节点
    
    播放报警音效
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
    
    def _execute_action(self, context: "ExecutionContext") -> NodeStatus:
        sound_path = self.config.get("sound_path", "")
        volume = self.config.get("volume")
        repeat_count = self.config.get("repeat_count", 1)
        interval_ms = self.config.get("interval_ms", 0)
        wait_complete = self.config.get("wait_complete", True)
        
        try:
            actual_sound_path = sound_path if sound_path else None
            actual_volume = volume if volume is not None else None
            
            success = context.play_alarm(
                sound_path=actual_sound_path,
                volume=actual_volume,
                repeat_count=repeat_count,
                interval_ms=interval_ms,
                wait_complete=wait_complete
            )
            
            if success:
                sound_info = sound_path if sound_path else "默认报警音"
                volume_info = f"音量{volume}%" if volume is not None else "全局音量"
                wait_info = "等待完成" if wait_complete else "异步播放"
                context.log(f"报警节点 {self.name}: 播放 {sound_info}, {volume_info}, {repeat_count}次, {wait_info}")
                return NodeStatus.SUCCESS
            else:
                context.log(f"报警节点 {self.name}: 播放失败")
                return NodeStatus.FAILURE
                
        except Exception as e:
            context.log(f"报警节点 {self.name}: 执行出错 - {e}")
            return NodeStatus.FAILURE
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"] = {
            **self.config,
            "sound_path": self.config.get("sound_path", ""),
            "volume": self.config.get("volume"),
            "repeat_count": self.config.get("repeat_count", 1),
            "interval_ms": self.config.get("interval_ms", 0),
            "wait_complete": self.config.get("wait_complete", True),
        }
        return data
