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
        self.key = self.config.get("key", "")
        self.action = self.config.get("action", "press")
        self.duration = self.config.get("duration", 0)
    
    def _execute_action(self, context: "ExecutionContext") -> NodeStatus:
        if not self.key:
            context.log(f"按键节点 {self.name}: 未配置按键")
            return NodeStatus.FAILURE
        
        try:
            success = context.execute_key_press(self.key, self.action, self.duration)
            
            if success:
                context.log(f"按键节点 {self.name}: 执行按键 {self.key}")
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
            "key": self.key,
            "action": self.action,
            "duration": self.duration,
        }
        return data


class MouseClickNode(ActionNode):
    """
    鼠标点击动作节点
    
    执行鼠标点击操作
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.button = self.config.get("button", "left")
        self.position = self.config.get("position")
        self.use_blackboard = self.config.get("use_blackboard", False)
        self.position_key = self.config.get("position_key", "last_ocr_position")
    
    def _execute_action(self, context: "ExecutionContext") -> NodeStatus:
        try:
            click_position = self.position
            
            if self.use_blackboard:
                click_position = context.blackboard.get(self.position_key)
            
            success = context.execute_mouse_click(self.button, click_position)
            
            if success:
                pos_str = click_position if click_position else "当前位置"
                context.log(f"鼠标节点 {self.name}: 执行点击 {self.button} @ {pos_str}")
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
            "button": self.button,
            "position": self.position,
            "use_blackboard": self.use_blackboard,
            "position_key": self.position_key,
        }
        return data


class MouseMoveNode(ActionNode):
    """
    鼠标移动动作节点
    
    移动鼠标到指定位置
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.position = self.config.get("position")
        self.use_blackboard = self.config.get("use_blackboard", False)
        self.position_key = self.config.get("position_key", "last_ocr_position")
        self.relative = self.config.get("relative", False)
        self.smooth = self.config.get("smooth", True)
    
    def _execute_action(self, context: "ExecutionContext") -> NodeStatus:
        try:
            move_position = self.position
            
            if self.use_blackboard:
                move_position = context.blackboard.get(self.position_key)
            
            if not move_position:
                context.log(f"鼠标移动节点 {self.name}: 未指定位置")
                return NodeStatus.FAILURE
            
            if context.input_controller is None:
                context.log(f"鼠标移动节点 {self.name}: 输入控制器不可用")
                return NodeStatus.FAILURE
            
            if self.relative:
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
            "position": self.position,
            "use_blackboard": self.use_blackboard,
            "position_key": self.position_key,
            "relative": self.relative,
            "smooth": self.smooth,
        }
        return data


class DelayNode(ActionNode):
    """
    延时动作节点
    
    非阻塞延时：每次tick检查是否到达指定时间
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.duration_ms = self.config.get("duration_ms", 1000)
        self._delay_start: Optional[float] = None
    
    def _execute_action(self, context: "ExecutionContext") -> NodeStatus:
        if self._delay_start is None:
            self._delay_start = time.time() * 1000
            context.log(f"延时节点 {self.name}: 开始延时 {self.duration_ms}ms")
        
        elapsed = time.time() * 1000 - self._delay_start
        
        if elapsed >= self.duration_ms:
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
            "duration_ms": self.duration_ms,
        }
        return data


class SetVariableNode(ActionNode):
    """
    设置变量动作节点
    
    设置黑板变量的值
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.variable_name = self.config.get("variable_name", "")
        self.value = self.config.get("value")
        self.value_type = self.config.get("value_type", "static")
        self.operation = self.config.get("operation", "set")
    
    def _execute_action(self, context: "ExecutionContext") -> NodeStatus:
        if not self.variable_name:
            context.log(f"设置变量节点 {self.name}: 未配置变量名")
            return NodeStatus.FAILURE
        
        try:
            if self.operation == "set":
                context.blackboard.set(self.variable_name, self.value)
                context.log(f"设置变量节点 {self.name}: 设置 {self.variable_name} = {self.value}")
            
            elif self.operation == "increment":
                result = context.blackboard.increment(self.variable_name, self.value if isinstance(self.value, (int, float)) else 1)
                context.log(f"设置变量节点 {self.name}: {self.variable_name} += {self.value if isinstance(self.value, (int, float)) else 1} = {result}")
            
            elif self.operation == "delete":
                context.blackboard.delete(self.variable_name)
                context.log(f"设置变量节点 {self.name}: 删除变量 {self.variable_name}")
            
            elif self.operation == "clear":
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
            "variable_name": self.variable_name,
            "value": self.value,
            "value_type": self.value_type,
            "operation": self.operation,
        }
        return data


class CodeNode(ActionNode):
    """
    代码动作节点
    
    执行外部代码文件（Python/Batch/PowerShell）
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.code_path = self.config.get("code_path", "")
        self.code_type = self.config.get("code_type", "auto")
        self.args = self.config.get("args", [])
    
    def _execute_action(self, context: "ExecutionContext") -> NodeStatus:
        if not self.code_path:
            context.log(f"代码节点 {self.name}: 未配置代码路径")
            return NodeStatus.FAILURE
        
        try:
            import subprocess
            from pathlib import Path
            
            code_path = Path(self.code_path)
            if not code_path.exists():
                context.log(f"代码节点 {self.name}: 代码文件不存在 {self.code_path}")
                return NodeStatus.FAILURE
            
            if self.code_type == "auto":
                if code_path.suffix == ".py":
                    cmd = ["python", str(code_path)] + self.args
                elif code_path.suffix in [".bat", ".cmd"]:
                    cmd = [str(code_path)] + self.args
                elif code_path.suffix == ".ps1":
                    cmd = ["powershell", "-File", str(code_path)] + self.args
                else:
                    cmd = [str(code_path)] + self.args
            else:
                cmd = [str(code_path)] + self.args
            
            context.log(f"代码节点 {self.name}: 执行代码 {self.code_path}")
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
            "code_path": self.code_path,
            "code_type": self.code_type,
            "args": self.args,
        }
        return data


class ScriptNode(ActionNode):
    """
    脚本动作节点
    
    执行原项目脚本格式的txt文件，支持按键、鼠标、延时等命令
    """
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.script_path = self.config.get("script_path", "")
        self.loop = self.config.get("loop", False)
    
    def _execute_action(self, context: "ExecutionContext") -> NodeStatus:
        if not self.script_path:
            context.log(f"脚本节点 {self.name}: 未配置脚本路径")
            return NodeStatus.FAILURE
        
        try:
            from pathlib import Path
            from modules.script import ScriptExecutor
            
            script_path = Path(self.script_path)
            if not script_path.exists():
                context.log(f"脚本节点 {self.name}: 脚本文件不存在 {self.script_path}")
                return NodeStatus.FAILURE
            
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            if not script_content.strip():
                context.log(f"脚本节点 {self.name}: 脚本内容为空")
                return NodeStatus.FAILURE
            
            context.log(f"脚本节点 {self.name}: 执行脚本 {self.script_path}")
            
            executor = ScriptExecutor(context.app)
            executor.run_script_once(script_content)
            
            import time
            while executor.is_running:
                if not context.check_running():
                    executor.stop_script()
                    return NodeStatus.ABORTED
                time.sleep(0.1)
            
            context.log(f"脚本节点 {self.name}: 执行完成")
            return NodeStatus.SUCCESS
                
        except Exception as e:
            context.log(f"脚本节点 {self.name}: 执行出错 - {e}")
            return NodeStatus.FAILURE
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"] = {
            **self.config,
            "script_path": self.script_path,
            "loop": self.loop,
        }
        return data
