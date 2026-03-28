"""
行为树执行引擎

负责行为树的加载、执行、暂停、停止等控制
"""

import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional, TYPE_CHECKING

from .nodes import Node, NodeStatus, NODE_TYPE_MAP
from .context import ExecutionContext
from .blackboard import Blackboard

if TYPE_CHECKING:
    from autodoor import AutoDoorOCR


class BehaviorTreeEngine:
    """
    行为树执行引擎
    
    功能：
    - 加载/保存行为树
    - 启动/停止/暂停/恢复执行
    - 状态监控
    """
    
    def __init__(self, app: "AutoDoorOCR"):
        self.app = app
        self.root_node: Optional[Node] = None
        self.context: Optional[ExecutionContext] = None
        self.execution_thread: Optional[threading.Thread] = None
        
        self.tick_interval: float = 0.05
        self._is_running = False
        self._is_paused = False
        self._tree_name = ""
        self._file_path: Optional[str] = None
    
    @property
    def is_running(self) -> bool:
        return self._is_running
    
    @property
    def is_paused(self) -> bool:
        return self._is_paused
    
    @property
    def tree_name(self) -> str:
        return self._tree_name
    
    def load_tree(self, tree_data: Dict[str, Any]) -> bool:
        """
        加载行为树
        
        Args:
            tree_data: 行为树数据（字典格式）
            
        Returns:
            是否加载成功
        """
        try:
            self._tree_name = tree_data.get("name", "未命名")
            root_data = tree_data.get("root_node")
            
            if not root_data:
                return False
            
            nodes_data = tree_data.get("nodes", {})
            self.root_node = self._build_tree(root_data, nodes_data)
            
            if self.root_node:
                self._file_path = None
                return True
            return False
        except Exception as e:
            if hasattr(self.app, "logging_manager"):
                self.app.logging_manager.log_message(f"[BT] 加载行为树失败: {e}")
            return False
    
    def _build_tree(self, node_id: str, nodes_data: Dict[str, Any]) -> Optional[Node]:
        """
        递归构建行为树
        
        Args:
            node_id: 节点ID
            nodes_data: 所有节点数据
            
        Returns:
            构建的节点
        """
        if node_id not in nodes_data:
            return None
        
        node_data = nodes_data[node_id]
        node_type = node_data.get("type", "")
        
        if node_type not in NODE_TYPE_MAP:
            return None
        
        node_class = NODE_TYPE_MAP[node_type]
        config = node_data.get("config", {})
        config["name"] = node_data.get("name", "")
        config["description"] = node_data.get("description", "")
        config["enabled"] = node_data.get("enabled", True)
        
        node = node_class(node_id, config)
        
        if hasattr(node, "children"):
            for child_id in node_data.get("children", []):
                child = self._build_tree(child_id, nodes_data)
                if child:
                    node.add_child(child)
        
        if hasattr(node, "child") and "child" in node_data:
            child = self._build_tree(node_data["child"], nodes_data)
            if child:
                node.set_child(child)
        
        return node
    
    def load_from_file(self, file_path: str) -> bool:
        """
        从文件加载行为树
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否加载成功
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return False
            
            with open(path, "r", encoding="utf-8") as f:
                tree_data = json.load(f)
            
            if self.load_tree(tree_data):
                self._file_path = file_path
                return True
            return False
        except Exception as e:
            if hasattr(self.app, "logging_manager"):
                self.app.logging_manager.log_message(f"[BT] 从文件加载失败: {e}")
            return False
    
    def save_to_file(self, file_path: Optional[str] = None) -> bool:
        """
        保存行为树到文件
        
        Args:
            file_path: 文件路径，为空则使用当前路径
            
        Returns:
            是否保存成功
        """
        if not self.root_node:
            return False
        
        save_path = file_path or self._file_path
        if not save_path:
            return False
        
        try:
            tree_data = {
                "version": "1.0",
                "name": self._tree_name,
                "description": "",
                "root_node": self.root_node.node_id,
                "nodes": self._collect_nodes(self.root_node),
                "blackboard_defaults": {}
            }
            
            path = Path(save_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, "w", encoding="utf-8") as f:
                json.dump(tree_data, f, ensure_ascii=False, indent=2)
            
            self._file_path = save_path
            return True
        except Exception as e:
            if hasattr(self.app, "logging_manager"):
                self.app.logging_manager.log_message(f"[BT] 保存文件失败: {e}")
            return False
    
    def _collect_nodes(self, node: Node) -> Dict[str, Any]:
        """收集所有节点数据"""
        nodes = {node.node_id: node.to_dict()}
        
        for child in node.get_children():
            nodes.update(self._collect_nodes(child))
        
        return nodes
    
    def start(self) -> None:
        """开始执行行为树"""
        if not self.root_node:
            return
        
        if self._is_running:
            return
        
        self._is_running = True
        self._is_paused = False
        self.context = ExecutionContext(self.app)
        self.context.start()
        
        self.execution_thread = threading.Thread(target=self._execution_loop, daemon=True)
        self.execution_thread.start()
        
        if hasattr(self.app, "logging_manager"):
            self.app.logging_manager.log_message(f"[BT] 开始执行行为树: {self._tree_name}")
    
    def stop(self) -> None:
        """停止执行"""
        self._is_running = False
        self._is_paused = False
        
        if self.context:
            self.context.stop()
        
        if self.root_node:
            self.root_node.reset()
        
        if hasattr(self.app, "logging_manager"):
            self.app.logging_manager.log_message("[BT] 行为树执行已停止")
    
    def pause(self) -> None:
        """暂停执行"""
        self._is_paused = True
        if self.context:
            self.context.pause()
    
    def resume(self) -> None:
        """恢复执行"""
        self._is_paused = False
        if self.context:
            self.context.resume()
    
    def _execution_loop(self) -> None:
        """执行循环（后台线程）"""
        try:
            while self._is_running and self.context:
                if self._is_paused:
                    time.sleep(self.tick_interval)
                    continue
                
                if not self.context.check_running():
                    break
                
                self.context.tick()
                status = self.root_node.tick(self.context)
                
                if status != NodeStatus.RUNNING:
                    self._is_running = False
                    if hasattr(self.app, "logging_manager"):
                        self.app.logging_manager.log_message(
                            f"[BT] 行为树执行完成，状态: {status.value}"
                        )
                    break
                
                time.sleep(self.tick_interval)
        except Exception as e:
            if hasattr(self.app, "logging_manager"):
                self.app.logging_manager.log_message(f"[BT] 执行出错: {e}")
        finally:
            self._is_running = False
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取执行状态
        
        Returns:
            状态信息字典
        """
        return {
            "is_running": self._is_running,
            "is_paused": self._is_paused,
            "tree_name": self._tree_name,
            "tick_count": self.context.tick_count if self.context else 0,
            "elapsed_time": self.context.elapsed_time if self.context else 0,
            "file_path": self._file_path,
        }
