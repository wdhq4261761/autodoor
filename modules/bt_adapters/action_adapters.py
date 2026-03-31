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
        position = self.config.get("position")
        use_blackboard = self.config.get("use_blackboard", False)
        position_key = self.config.get("position_key", "last_ocr_position")
        
        try:
            click_position = position
            
            if use_blackboard:
                click_position = context.blackboard.get(position_key)
            
            success = context.execute_mouse_click(button, click_position)
            
            if success:
                pos_str = click_position if click_position else "当前位置"
                context.log(f"鼠标节点 {self.name}: 执行点击 {button} @ {pos_str}")
                return NodeStatus.SUCCESS
            else:
                context.log(f"鼠标节点 {self.name}: 点击执行失败")
                return NodeStatus.FAILURE
                
        except Exception as e:
            context.log(f"鼠标节点 {self.name}: 执行出错 - {e}")
            return NodeStatus.FAILURE
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"] = {
            **self.config,
            "button": self.config.get("button", "left"),
            "position": self.config.get("position"),
            "use_blackboard": self.config.get("use_blackboard", False),
            "position_key": self.config.get("position_key", "last_ocr_position"),
        }
        return data


class MouseMoveNode(ActionNode):
    """
    鼠标移动动作节点
    
    移动鼠标到指定位置
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
    
    def _execute_action(self, context: "ExecutionContext") -> NodeStatus:
        position = self.config.get("position")
        use_blackboard = self.config.get("use_blackboard", False)
        position_key = self.config.get("position_key", "last_ocr_position")
        relative = self.config.get("relative", False)
        smooth = self.config.get("smooth", True)
        
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
            
            if relative:
                context.input_controller.move_relative(move_position[0], move_position[1])
            else:
                context.input_controller.move_to(move_position[0], move_position[1])
            
            context.log(f"鼠标移动节点 {self.name}: 移动到 {move_position}")
            return NodeStatus.SUCCESS
                
        except Exception as e:
            context.log(f"鼠标移动节点 {self.name}: 执行出错 - {e}")
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
    
    def _execute_action(self, context: "ExecutionContext") -> NodeStatus:
        duration_ms = self.config.get("duration_ms", 1000)
        
        if self._delay_start is None:
            self._delay_start = time.time() * 1000
            context.log(f"延时节点 {self.name}: 开始延时 {duration_ms}ms")
        
        elapsed = time.time() * 1000 - self._delay_start
        
        if elapsed >= duration_ms:
            context.log(f"延时节点 {self.name}: 延时完成")
            self._delay_start = None
            return NodeStatus.SUCCESS
        
        return NodeStatus.RUNNING
    
    def reset(self) -> None:
        super().reset()
        self._delay_start = None
    
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
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
    
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
            
            code_file = Path(code_path)
            if not code_file.exists():
                context.log(f"代码节点 {self.name}: 代码文件不存在 {code_path}")
                return NodeStatus.FAILURE
            
            if code_type == "auto":
                if code_file.suffix == ".py":
                    cmd = ["python", str(code_file)] + args
                elif code_file.suffix in [".bat", ".cmd"]:
                    cmd = [str(code_file)] + args
                elif code_file.suffix == ".ps1":
                    cmd = ["powershell", "-File", str(code_file)] + args
                else:
                    cmd = [str(code_file)] + args
            else:
                cmd = [str(code_file)] + args
            
            context.log(f"代码节点 {self.name}: 执行代码 {code_path}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                context.log(f"代码节点 {self.name}: 执行成功")
                return NodeStatus.SUCCESS
            else:
                context.log(f"代码节点 {self.name}: 执行失败 - {result.stderr}")
                return NodeStatus.FAILURE
                
        except subprocess.TimeoutExpired:
            context.log(f"代码节点 {self.name}: 执行超时")
            return NodeStatus.FAILURE
        except Exception as e:
            context.log(f"代码节点 {self.name}: 执行出错 - {e}")
            return NodeStatus.FAILURE
    
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
