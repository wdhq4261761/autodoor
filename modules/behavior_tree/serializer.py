"""
行为树序列化器

支持 JSON、YAML 和文本格式的序列化与反序列化
支持元数据、编辑器状态的持久化
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

CURRENT_VERSION = "2.0"


class BehaviorTreeSerializer:
    """
    行为树序列化器
    
    支持多种格式的序列化与反序列化
    支持元数据和编辑器状态
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
            "CodeNode": "Action:Code",
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
            "Action:Code": "CodeNode",
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
            
            tree_data = BehaviorTreeSerializer.deserialize(data, format)
            return BehaviorTreeSerializer.migrate_data(tree_data)
        except Exception as e:
            print(f"加载文件失败: {e}")
            return None
    
    @staticmethod
    def create_empty_tree(name: str = "未命名") -> Dict[str, Any]:
        """
        创建空的行为树数据结构
        
        Args:
            name: 行为树名称
            
        Returns:
            空的行为树数据
        """
        now = datetime.now().isoformat()
        return {
            "version": CURRENT_VERSION,
            "format_type": "behavior_tree_editor",
            "metadata": {
                "created_at": now,
                "modified_at": now,
                "app_version": "1.0.0",
                "save_type": "new",
                "checksum": ""
            },
            "canvas": {
                "name": name,
                "description": "",
                "viewport": {
                    "zoom": 1.0,
                    "offset_x": 0,
                    "offset_y": 0
                },
                "grid": {
                    "enabled": True,
                    "size": 20
                }
            },
            "nodes": {},
            "connections": [],
            "root_node": None,
            "editor_state": {
                "selected_node": None,
                "selected_connection": None,
                "clipboard": None,
                "undo_stack": [],
                "redo_stack": []
            }
        }
    
    @staticmethod
    def migrate_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        迁移旧版本数据到当前版本
        
        Args:
            data: 原始数据
            
        Returns:
            迁移后的数据
        """
        if not data:
            return data
        
        version = data.get("version", "1.0")
        
        if version == CURRENT_VERSION:
            return data
        
        if version == "1.0" or "version" not in data:
            data = BehaviorTreeSerializer._migrate_v1_to_v2(data)
        
        return data
    
    @staticmethod
    def _migrate_v1_to_v2(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        从v1.0迁移到v2.0
        """
        data["version"] = CURRENT_VERSION
        data["format_type"] = "behavior_tree_editor"
        
        now = datetime.now().isoformat()
        
        if "metadata" not in data:
            data["metadata"] = {
                "created_at": data.get("created_at", now),
                "modified_at": now,
                "app_version": "1.0.0",
                "save_type": "migrated",
                "checksum": ""
            }
        
        if "canvas" not in data:
            data["canvas"] = {
                "name": data.get("name", "未命名"),
                "description": "",
                "viewport": {
                    "zoom": 1.0,
                    "offset_x": 0,
                    "offset_y": 0
                },
                "grid": {
                    "enabled": True,
                    "size": 20
                }
            }
        
        if "connections" not in data:
            data["connections"] = []
            nodes = data.get("nodes", {})
            for node_id, node in nodes.items():
                children = node.get("children", [])
                for i, child_id in enumerate(children):
                    data["connections"].append({
                        "id": f"conn_{node_id}_{child_id}",
                        "parent_id": node_id,
                        "child_id": child_id,
                        "order": i
                    })
        
        if "editor_state" not in data:
            data["editor_state"] = {
                "selected_node": None,
                "selected_connection": None,
                "clipboard": None,
                "undo_stack": [],
                "redo_stack": []
            }
        
        return data
    
    @staticmethod
    def update_metadata(
        data: Dict[str, Any],
        save_type: str = "auto",
        app_version: str = "1.0.0"
    ) -> Dict[str, Any]:
        """
        更新元数据
        
        Args:
            data: 行为树数据
            save_type: 保存类型
            app_version: 应用版本
            
        Returns:
            更新后的数据
        """
        if "metadata" not in data:
            data["metadata"] = {}
        
        now = datetime.now().isoformat()
        
        if not data["metadata"].get("created_at"):
            data["metadata"]["created_at"] = now
        
        data["metadata"]["modified_at"] = now
        data["metadata"]["app_version"] = app_version
        data["metadata"]["save_type"] = save_type
        
        data["version"] = CURRENT_VERSION
        data["format_type"] = "behavior_tree_editor"
        
        return data
    
    @staticmethod
    def update_editor_state(
        data: Dict[str, Any],
        selected_node: Optional[str] = None,
        selected_connection: Optional[str] = None,
        clipboard: Optional[Dict] = None,
        undo_stack: Optional[List] = None,
        redo_stack: Optional[List] = None
    ) -> Dict[str, Any]:
        """
        更新编辑器状态
        
        Args:
            data: 行为树数据
            selected_node: 选中的节点ID
            selected_connection: 选中的连线ID
            clipboard: 剪贴板内容
            undo_stack: 撤销栈
            redo_stack: 重做栈
            
        Returns:
            更新后的数据
        """
        if "editor_state" not in data:
            data["editor_state"] = {}
        
        if selected_node is not None:
            data["editor_state"]["selected_node"] = selected_node
        if selected_connection is not None:
            data["editor_state"]["selected_connection"] = selected_connection
        if clipboard is not None:
            data["editor_state"]["clipboard"] = clipboard
        if undo_stack is not None:
            data["editor_state"]["undo_stack"] = undo_stack
        if redo_stack is not None:
            data["editor_state"]["redo_stack"] = redo_stack
        
        return data
    
    @staticmethod
    def update_viewport(
        data: Dict[str, Any],
        zoom: Optional[float] = None,
        offset_x: Optional[float] = None,
        offset_y: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        更新视口状态
        
        Args:
            data: 行为树数据
            zoom: 缩放比例
            offset_x: X偏移
            offset_y: Y偏移
            
        Returns:
            更新后的数据
        """
        if "canvas" not in data:
            data["canvas"] = {"viewport": {}}
        if "viewport" not in data["canvas"]:
            data["canvas"]["viewport"] = {}
        
        if zoom is not None:
            data["canvas"]["viewport"]["zoom"] = zoom
        if offset_x is not None:
            data["canvas"]["viewport"]["offset_x"] = offset_x
        if offset_y is not None:
            data["canvas"]["viewport"]["offset_y"] = offset_y
        
        return data
