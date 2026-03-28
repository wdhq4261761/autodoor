"""
连线管理模块

管理节点之间的连接关系和可视化
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ConnectionType(Enum):
    """连线类型"""
    CHILD = "child"
    FLOW = "flow"


@dataclass
class Connection:
    """连线数据"""
    parent_id: str
    child_id: str
    connection_type: ConnectionType = ConnectionType.CHILD
    order: int = 0
    
    def to_tuple(self) -> Tuple[str, str]:
        return (self.parent_id, self.child_id)
    
    def __hash__(self):
        return hash((self.parent_id, self.child_id))
    
    def __eq__(self, other):
        if isinstance(other, Connection):
            return self.parent_id == other.parent_id and self.child_id == other.child_id
        return False


class ConnectionManager:
    """
    连线管理器
    
    管理节点之间的连接关系，提供验证和查询功能
    """
    
    def __init__(self):
        self._connections: Dict[str, Set[str]] = {}
        self._reverse_connections: Dict[str, str] = {}
        self._connection_data: Dict[Tuple[str, str], Connection] = {}
    
    def add_connection(self, parent_id: str, child_id: str, 
                       connection_type: ConnectionType = ConnectionType.CHILD,
                       order: int = 0) -> bool:
        """
        添加连线
        
        Args:
            parent_id: 父节点ID
            child_id: 子节点ID
            connection_type: 连线类型
            order: 顺序（用于多子节点排序）
            
        Returns:
            是否添加成功
        """
        if not self._validate_connection(parent_id, child_id):
            return False
        
        if parent_id not in self._connections:
            self._connections[parent_id] = set()
        
        if child_id in self._reverse_connections:
            return False
        
        self._connections[parent_id].add(child_id)
        self._reverse_connections[child_id] = parent_id
        
        conn = Connection(parent_id, child_id, connection_type, order)
        self._connection_data[(parent_id, child_id)] = conn
        
        return True
    
    def remove_connection(self, parent_id: str, child_id: str) -> bool:
        """
        移除连线
        
        Args:
            parent_id: 父节点ID
            child_id: 子节点ID
            
        Returns:
            是否移除成功
        """
        key = (parent_id, child_id)
        
        if parent_id in self._connections:
            self._connections[parent_id].discard(child_id)
            if not self._connections[parent_id]:
                del self._connections[parent_id]
        
        if child_id in self._reverse_connections:
            del self._reverse_connections[child_id]
        
        if key in self._connection_data:
            del self._connection_data[key]
            return True
        
        return False
    
    def remove_node_connections(self, node_id: str) -> List[Tuple[str, str]]:
        """
        移除与指定节点相关的所有连线
        
        Args:
            node_id: 节点ID
            
        Returns:
            被移除的连线列表
        """
        removed = []
        
        children = self.get_children(node_id)
        for child_id in children:
            self.remove_connection(node_id, child_id)
            removed.append((node_id, child_id))
        
        parent_id = self.get_parent(node_id)
        if parent_id:
            self.remove_connection(parent_id, node_id)
            removed.append((parent_id, node_id))
        
        return removed
    
    def get_children(self, parent_id: str) -> List[str]:
        """
        获取子节点列表
        
        Args:
            parent_id: 父节点ID
            
        Returns:
            子节点ID列表（按顺序排序）
        """
        if parent_id not in self._connections:
            return []
        
        children = list(self._connections[parent_id])
        children.sort(key=lambda c: self._connection_data.get((parent_id, c), Connection("", "")).order)
        return children
    
    def get_parent(self, child_id: str) -> Optional[str]:
        """
        获取父节点
        
        Args:
            child_id: 子节点ID
            
        Returns:
            父节点ID，如果没有则返回None
        """
        return self._reverse_connections.get(child_id)
    
    def has_connection(self, parent_id: str, child_id: str) -> bool:
        """检查是否存在连线"""
        return (parent_id, child_id) in self._connection_data
    
    def get_all_connections(self) -> List[Tuple[str, str]]:
        """获取所有连线"""
        return list(self._connection_data.keys())
    
    def get_connection_count(self) -> int:
        """获取连线数量"""
        return len(self._connection_data)
    
    def _validate_connection(self, parent_id: str, child_id: str) -> bool:
        """
        验证连线是否有效
        
        Args:
            parent_id: 父节点ID
            child_id: 子节点ID
            
        Returns:
            是否有效
        """
        if parent_id == child_id:
            return False
        
        if self._would_create_cycle(parent_id, child_id):
            return False
        
        return True
    
    def _would_create_cycle(self, parent_id: str, child_id: str) -> bool:
        """
        检查添加连线是否会创建循环
        
        Args:
            parent_id: 父节点ID
            child_id: 子节点ID
            
        Returns:
            是否会创建循环
        """
        visited = set()
        current = parent_id
        
        while current:
            if current == child_id:
                return True
            if current in visited:
                break
            visited.add(current)
            current = self.get_parent(current)
        
        return False
    
    def clear(self):
        """清空所有连线"""
        self._connections.clear()
        self._reverse_connections.clear()
        self._connection_data.clear()
    
    def get_root_nodes(self, node_ids: List[str]) -> List[str]:
        """
        获取根节点列表
        
        Args:
            node_ids: 所有节点ID列表
            
        Returns:
            根节点ID列表（没有父节点的节点）
        """
        return [nid for nid in node_ids if nid not in self._reverse_connections]
    
    def get_leaf_nodes(self, node_ids: List[str]) -> List[str]:
        """
        获取叶子节点列表
        
        Args:
            node_ids: 所有节点ID列表
            
        Returns:
            叶子节点ID列表（没有子节点的节点）
        """
        return [nid for nid in node_ids if nid not in self._connections or not self._connections[nid]]
    
    def get_node_depth(self, node_id: str) -> int:
        """
        获取节点深度
        
        Args:
            node_id: 节点ID
            
        Returns:
            节点深度（根节点为0）
        """
        depth = 0
        current = self.get_parent(node_id)
        
        while current:
            depth += 1
            current = self.get_parent(current)
        
        return depth
    
    def to_dict(self) -> List[Dict[str, Any]]:
        """
        导出为字典列表
        
        Returns:
            连线数据列表
        """
        return [
            {
                "parent_id": conn.parent_id,
                "child_id": conn.child_id,
                "type": conn.connection_type.value,
                "order": conn.order,
            }
            for conn in self._connection_data.values()
        ]
    
    def from_dict(self, data: List[Dict[str, Any]]):
        """
        从字典列表导入
        
        Args:
            data: 连线数据列表
        """
        self.clear()
        
        for item in data:
            conn_type = ConnectionType(item.get("type", "child"))
            self.add_connection(
                item["parent_id"],
                item["child_id"],
                conn_type,
                item.get("order", 0)
            )


def calculate_connection_path(
    start_x: float, start_y: float,
    end_x: float, end_y: float,
    style: str = "bezier"
) -> List[Tuple[float, float]]:
    """
    计算连线路径点
    
    Args:
        start_x: 起点X
        start_y: 起点Y
        end_x: 终点X
        end_y: 终点Y
        style: 路径样式 (bezier/straight/step)
        
    Returns:
        路径点列表
    """
    if style == "straight":
        return [(start_x, start_y), (end_x, end_y)]
    
    elif style == "step":
        mid_y = (start_y + end_y) / 2
        return [
            (start_x, start_y),
            (start_x, mid_y),
            (end_x, mid_y),
            (end_x, end_y)
        ]
    
    else:
        mid_y = (start_y + end_y) / 2
        return [
            (start_x, start_y),
            (start_x, mid_y),
            (end_x, mid_y),
            (end_x, end_y)
        ]
