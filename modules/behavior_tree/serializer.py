"""
行为树序列化器

支持 JSON、YAML 和文本格式的序列化与反序列化
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


class BehaviorTreeSerializer:
    """
    行为树序列化器
    
    支持多种格式的序列化与反序列化
    """
    
    FORMAT_JSON = "json"
    FORMAT_YAML = "yaml"
    FORMAT_TEXT = "text"
    
    @staticmethod
    def serialize(tree_data: Dict[str, Any], format: str = "json") -> str:
        """
        序列化行为树数据
        
        Args:
            tree_data: 行为树数据
            format: 输出格式 (json/yaml/text)
            
        Returns:
            序列化后的字符串
        """
        if format == BehaviorTreeSerializer.FORMAT_JSON:
            return BehaviorTreeSerializer._to_json(tree_data)
        elif format == BehaviorTreeSerializer.FORMAT_YAML:
            return BehaviorTreeSerializer._to_yaml(tree_data)
        elif format == BehaviorTreeSerializer.FORMAT_TEXT:
            return BehaviorTreeSerializer._to_text(tree_data)
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    @staticmethod
    def deserialize(data: str, format: str = "json") -> Dict[str, Any]:
        """
        反序列化行为树数据
        
        Args:
            data: 序列化的数据字符串
            format: 输入格式 (json/yaml/text)
            
        Returns:
            行为树数据字典
        """
        if format == BehaviorTreeSerializer.FORMAT_JSON:
            return BehaviorTreeSerializer._from_json(data)
        elif format == BehaviorTreeSerializer.FORMAT_YAML:
            return BehaviorTreeSerializer._from_yaml(data)
        elif format == BehaviorTreeSerializer.FORMAT_TEXT:
            return BehaviorTreeSerializer._from_text(data)
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    @staticmethod
    def _to_json(tree_data: Dict[str, Any]) -> str:
        """转换为JSON格式"""
        return json.dumps(tree_data, ensure_ascii=False, indent=2)
    
    @staticmethod
    def _from_json(data: str) -> Dict[str, Any]:
        """从JSON格式解析"""
        return json.loads(data)
    
    @staticmethod
    def _to_yaml(tree_data: Dict[str, Any]) -> str:
        """转换为YAML格式"""
        try:
            import yaml
            return yaml.dump(tree_data, allow_unicode=True, default_flow_style=False, sort_keys=False)
        except ImportError:
            raise ImportError("需要安装 PyYAML 库: pip install pyyaml")
    
    @staticmethod
    def _from_yaml(data: str) -> Dict[str, Any]:
        """从YAML格式解析"""
        try:
            import yaml
            return yaml.safe_load(data)
        except ImportError:
            raise ImportError("需要安装 PyYAML 库: pip install pyyaml")
    
    @staticmethod
    def _to_text(tree_data: Dict[str, Any]) -> str:
        """转换为文本脚本格式"""
        lines = []
        lines.append("; 行为树脚本 v1.0")
        lines.append(f"; 名称: {tree_data.get('name', '未命名')}")
        lines.append("")
        
        root_id = tree_data.get("root_node")
        nodes_data = tree_data.get("nodes", {})
        
        if root_id and root_id in nodes_data:
            BehaviorTreeSerializer._serialize_node_text(lines, root_id, nodes_data, 0)
        
        return "\n".join(lines)
    
    @staticmethod
    def _serialize_node_text(lines: List[str], node_id: str, nodes_data: Dict, indent: int):
        """递归序列化节点为文本格式"""
        if node_id not in nodes_data:
            return
        
        node_data = nodes_data[node_id]
        node_type = node_data.get("type", "Node")
        node_name = node_data.get("name", "")
        config = node_data.get("config", {})
        
        prefix = "  " * indent
        short_type = BehaviorTreeSerializer._get_type_shortcut(node_type)
        
        lines.append(f"{prefix}[{short_type}]")
        if node_name:
            lines.append(f"{prefix}  Name: {node_name}")
        
        for key, value in config.items():
            if value is not None and value != "":
                if isinstance(value, dict):
                    lines.append(f"{prefix}  {key}: {json.dumps(value)}")
                elif isinstance(value, list):
                    lines.append(f"{prefix}  {key}: {','.join(map(str, value))}")
                else:
                    lines.append(f"{prefix}  {key}: {value}")
        
        children = node_data.get("children", [])
        for child_id in children:
            BehaviorTreeSerializer._serialize_node_text(lines, child_id, nodes_data, indent + 1)
        
        if "child" in node_data:
            BehaviorTreeSerializer._serialize_node_text(lines, node_data["child"], nodes_data, indent + 1)
    
    @staticmethod
    def _get_type_shortcut(node_type: str) -> str:
        """获取节点类型的简写"""
        shortcuts = {
            "SequenceNode": "Sequence",
            "SelectorNode": "Selector",
            "ParallelNode": "Parallel",
            "InverterNode": "Inverter",
            "RepeaterNode": "Repeater",
            "RetryNode": "Retry",
            "TimeoutNode": "Timeout",
            "OCRConditionNode": "Condition:OCR",
            "ImageConditionNode": "Condition:Image",
            "ColorConditionNode": "Condition:Color",
            "NumberConditionNode": "Condition:Number",
            "VariableConditionNode": "Condition:Variable",
            "KeyPressNode": "Action:Key",
            "MouseClickNode": "Action:Click",
            "MouseMoveNode": "Action:Move",
            "DelayNode": "Delay",
            "SetVariableNode": "Action:SetVar",
            "ScriptNode": "Action:Script",
        }
        return shortcuts.get(node_type, node_type)
    
    @staticmethod
    def _from_text(data: str) -> Dict[str, Any]:
        """从文本脚本格式解析"""
        lines = data.strip().split("\n")
        
        tree_data = {
            "version": "1.0",
            "name": "未命名",
            "nodes": {},
        }
        
        node_stack: List[Dict] = []
        node_counter = 0
        
        for line in lines:
            line = line.strip()
            
            if not line or line.startswith(";"):
                if line.startswith("; 名称:"):
                    tree_data["name"] = line[5:].strip()
                continue
            
            indent_match = re.match(r'^(\s*)', line)
            indent = len(indent_match.group(1)) if indent_match else 0
            indent_level = indent // 2
            
            node_match = re.match(r'\[(.+)\]', line)
            if node_match:
                node_type = BehaviorTreeSerializer._parse_type_shortcut(node_match.group(1))
                node_counter += 1
                node_id = f"node_{node_counter}"
                
                node_data = {
                    "id": node_id,
                    "type": node_type,
                    "name": "",
                    "config": {},
                }
                
                while len(node_stack) > indent_level:
                    node_stack.pop()
                
                if node_stack:
                    parent = node_stack[-1]
                    if "children" not in parent:
                        parent["children"] = []
                    parent["children"].append(node_id)
                else:
                    tree_data["root_node"] = node_id
                
                tree_data["nodes"][node_id] = node_data
                node_stack.append(node_data)
            
            elif ":" in line:
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip()
                
                if node_stack:
                    if value.startswith("$"):
                        node_stack[-1]["config"][key] = {"variable": value[1:]}
                    elif value.isdigit():
                        node_stack[-1]["config"][key] = int(value)
                    elif re.match(r'^\d+\.\d+$', value):
                        node_stack[-1]["config"][key] = float(value)
                    else:
                        node_stack[-1]["config"][key] = value
        
        return tree_data
    
    @staticmethod
    def _parse_type_shortcut(shortcut: str) -> str:
        """解析节点类型简写"""
        type_map = {
            "Sequence": "SequenceNode",
            "Selector": "SelectorNode",
            "Parallel": "ParallelNode",
            "Inverter": "InverterNode",
            "Repeater": "RepeaterNode",
            "Retry": "RetryNode",
            "Timeout": "TimeoutNode",
            "Condition:OCR": "OCRConditionNode",
            "Condition:Image": "ImageConditionNode",
            "Condition:Color": "ColorConditionNode",
            "Condition:Number": "NumberConditionNode",
            "Condition:Variable": "VariableConditionNode",
            "Action:Key": "KeyPressNode",
            "Action:Click": "MouseClickNode",
            "Action:Move": "MouseMoveNode",
            "Delay": "DelayNode",
            "Action:SetVar": "SetVariableNode",
            "Action:Script": "ScriptNode",
        }
        return type_map.get(shortcut, shortcut + "Node")
    
    @staticmethod
    def save_to_file(tree_data: Dict[str, Any], file_path: str, format: Optional[str] = None) -> bool:
        """
        保存行为树到文件
        
        Args:
            tree_data: 行为树数据
            file_path: 文件路径
            format: 格式 (自动检测或指定)
            
        Returns:
            是否保存成功
        """
        try:
            path = Path(file_path)
            
            if format is None:
                suffix = path.suffix.lower()
                if suffix == ".yaml" or suffix == ".yml":
                    format = BehaviorTreeSerializer.FORMAT_YAML
                elif suffix == ".txt" or suffix == ".bt":
                    format = BehaviorTreeSerializer.FORMAT_TEXT
                else:
                    format = BehaviorTreeSerializer.FORMAT_JSON
            
            data = BehaviorTreeSerializer.serialize(tree_data, format)
            
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(data)
            
            return True
        except Exception as e:
            print(f"保存文件失败: {e}")
            return False
    
    @staticmethod
    def load_from_file(file_path: str) -> Optional[Dict[str, Any]]:
        """
        从文件加载行为树
        
        Args:
            file_path: 文件路径
            
        Returns:
            行为树数据，失败返回None
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            
            with open(path, "r", encoding="utf-8") as f:
                data = f.read()
            
            suffix = path.suffix.lower()
            if suffix == ".yaml" or suffix == ".yml":
                format = BehaviorTreeSerializer.FORMAT_YAML
            elif suffix == ".txt" or suffix == ".bt":
                format = BehaviorTreeSerializer.FORMAT_TEXT
            else:
                format = BehaviorTreeSerializer.FORMAT_JSON
            
            return BehaviorTreeSerializer.deserialize(data, format)
        except Exception as e:
            print(f"加载文件失败: {e}")
            return None
