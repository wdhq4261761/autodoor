"""
行为树编辑器画布组件

提供可视化节点编辑功能
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import Dict, List, Optional, Any, Callable

from ui.theme import Theme


NODE_COLORS = {
    "SequenceNode": "#4CAF50",
    "SelectorNode": "#2196F3",
    "ParallelNode": "#9C27B0",
    "InverterNode": "#FF9800",
    "RepeaterNode": "#FF9800",
    "RetryNode": "#FF9800",
    "TimeoutNode": "#FF9800",
    "OCRConditionNode": "#E91E63",
    "ImageConditionNode": "#E91E63",
    "ColorConditionNode": "#E91E63",
    "NumberConditionNode": "#E91E63",
    "KeyPressNode": "#00BCD4",
    "MouseClickNode": "#00BCD4",
    "DelayNode": "#00BCD4",
    "default": "#607D8B",
}


class NodeItem:
    """画布节点项"""
    
    def __init__(self, canvas: tk.Canvas, node_id: str, node_type: str, x: float, y: float):
        self.canvas = canvas
        self.node_id = node_id
        self.node_type = node_type
        self.x = x
        self.y = y
        self.width = 120
        self.height = 50
        
        color = NODE_COLORS.get(node_type, NODE_COLORS["default"])
        
        self.rect = canvas.create_rectangle(
            x - self.width/2, y - self.height/2,
            x + self.width/2, y + self.height/2,
            fill=color, outline="#FFFFFF", width=2,
            tags=("node", node_id)
        )
        
        display_name = node_type.replace("Node", "").replace("Condition", "").replace("Action", "")
        self.text = canvas.create_text(
            x, y,
            text=display_name,
            fill="#FFFFFF",
            font=("Arial", 10, "bold"),
            tags=("node_text", node_id)
        )
    
    def move_to(self, x: float, y: float):
        """移动节点"""
        dx = x - self.x
        dy = y - self.y
        self.x = x
        self.y = y
        self.canvas.move(self.node_id, dx, dy)
    
    def get_bounds(self) -> tuple:
        """获取边界"""
        return (
            self.x - self.width/2, self.y - self.height/2,
            self.x + self.width/2, self.y + self.height/2
        )
    
    def contains_point(self, x: float, y: float) -> bool:
        """检查点是否在节点内"""
        x1, y1, x2, y2 = self.get_bounds()
        return x1 <= x <= x2 and y1 <= y <= y2
    
    def set_selected(self, selected: bool):
        """设置选中状态"""
        outline = "#FFD700" if selected else "#FFFFFF"
        width = 3 if selected else 2
        self.canvas.itemconfig(self.rect, outline=outline, width=width)


class BehaviorTreeCanvas(ctk.CTkFrame):
    """行为树画布"""
    
    def __init__(self, master, app, on_node_select: Optional[Callable] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        
        self.nodes: Dict[str, NodeItem] = {}
        self.connections: List[tuple] = []
        self.selected_node: Optional[str] = None
        self.on_node_select = on_node_select
        
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        
        self._dragging = False
        self._drag_node: Optional[str] = None
        self._drag_start = (0, 0)
        
        self._create_canvas()
        self._bind_events()
    
    def _create_canvas(self):
        """创建画布"""
        self.canvas = tk.Canvas(
            self,
            bg="#1E1E1E",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
    
    def _bind_events(self):
        """绑定事件"""
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<MouseWheel>", self._on_scroll)
        self.canvas.bind("<Button-3>", self._on_right_click)
    
    def _on_click(self, event):
        """点击事件"""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        for node_id, node in self.nodes.items():
            if node.contains_point(x, y):
                self._select_node(node_id)
                self._dragging = True
                self._drag_node = node_id
                self._drag_start = (x - node.x, y - node.y)
                return
        
        self._deselect_all()
    
    def _on_drag(self, event):
        """拖拽事件"""
        if self._dragging and self._drag_node:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            node = self.nodes[self._drag_node]
            node.move_to(x - self._drag_start[0], y - self._drag_start[1])
            self._redraw_connections()
    
    def _on_release(self, event):
        """释放事件"""
        self._dragging = False
        self._drag_node = None
    
    def _on_scroll(self, event):
        """滚轮事件"""
        if event.delta > 0:
            self.zoom *= 1.1
        else:
            self.zoom /= 1.1
        self.zoom = max(0.25, min(4.0, self.zoom))
        scale_factor = 1.1 if event.delta > 0 else 0.9
        self.canvas.scale("all", event.x, event.y, scale_factor, scale_factor)
    
    def _on_right_click(self, event):
        """右键菜单"""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="添加节点", command=lambda: self._show_add_dialog(x, y))
        menu.add_separator()
        menu.add_command(label="清空画布", command=self.clear_canvas)
        menu.post(event.x_root, event.y_root)
    
    def _select_node(self, node_id: str):
        """选中节点"""
        self._deselect_all()
        self.selected_node = node_id
        node = self.nodes[node_id]
        node.set_selected(True)
        
        if self.on_node_select:
            self.on_node_select(node_id, node.node_type)
    
    def _deselect_all(self):
        """取消所有选中"""
        self.selected_node = None
        for node in self.nodes.values():
            node.set_selected(False)
    
    def _show_add_dialog(self, x: float, y: float):
        """显示添加节点对话框"""
        pass
    
    def add_node(self, node_id: str, node_type: str, x: float, y: float) -> NodeItem:
        """添加节点"""
        node = NodeItem(self.canvas, node_id, node_type, x, y)
        self.nodes[node_id] = node
        return node
    
    def remove_node(self, node_id: str):
        """移除节点"""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            self.canvas.delete(node.node_id)
            del self.nodes[node_id]
            
            self.connections = [
                c for c in self.connections 
                if c[0] != node_id and c[1] != node_id
            ]
            self._redraw_connections()
    
    def add_connection(self, parent_id: str, child_id: str):
        """添加连接线"""
        self.connections.append((parent_id, child_id))
        self._redraw_connections()
    
    def _redraw_connections(self):
        """重绘连接线"""
        self.canvas.delete("connection")
        
        for parent_id, child_id in self.connections:
            if parent_id in self.nodes and child_id in self.nodes:
                parent = self.nodes[parent_id]
                child = self.nodes[child_id]
                
                self.canvas.create_line(
                    parent.x, parent.y + parent.height/2,
                    child.x, child.y - child.height/2,
                    fill="#888888", width=2,
                    arrow=tk.LAST,
                    tags="connection"
                )
        
        self.canvas.tag_lower("connection")
    
    def clear_canvas(self):
        """清空画布"""
        self.canvas.delete("all")
        self.nodes.clear()
        self.connections.clear()
        self.selected_node = None
    
    def load_tree(self, tree_data: Dict[str, Any]):
        """加载行为树数据"""
        self.clear_canvas()
        
        nodes_data = tree_data.get("nodes", {})
        root_id = tree_data.get("root_node")
        
        if not root_id or not nodes_data:
            return
        
        positions = self._calculate_positions(nodes_data, root_id)
        
        for node_id, node_data in nodes_data.items():
            if node_id in positions:
                x, y = positions[node_id]
                self.add_node(node_id, node_data.get("type", "Node"), x, y)
        
        for node_id, node_data in nodes_data.items():
            children = node_data.get("children", [])
            for child_id in children:
                self.add_connection(node_id, child_id)
            
            if "child" in node_data:
                self.add_connection(node_id, node_data["child"])
    
    def _calculate_positions(self, nodes_data: Dict, root_id: str) -> Dict[str, tuple]:
        """计算节点位置"""
        positions = {}
        y_offset = 80
        x_center = 400
        
        def layout_node(node_id: str, x: float, y: float, width: float):
            positions[node_id] = (x, y)
            
            if node_id not in nodes_data:
                return
            
            node_data = nodes_data[node_id]
            children = node_data.get("children", [])
            
            if not children:
                return
            
            child_width = width / len(children)
            start_x = x - width/2 + child_width/2
            
            for i, child_id in enumerate(children):
                child_x = start_x + i * child_width
                layout_node(child_id, child_x, y + y_offset, child_width)
            
            if "child" in node_data:
                layout_node(node_data["child"], x, y + y_offset, width)
        
        layout_node(root_id, x_center, 50, 600)
        return positions
    
    def get_tree_data(self) -> Dict[str, Any]:
        """获取行为树数据"""
        nodes_data = {}
        
        for node_id, node in self.nodes.items():
            nodes_data[node_id] = {
                "id": node_id,
                "type": node.node_type,
                "name": "",
                "config": {}
            }
        
        for parent_id, child_id in self.connections:
            if parent_id in nodes_data:
                if "children" not in nodes_data[parent_id]:
                    nodes_data[parent_id]["children"] = []
                nodes_data[parent_id]["children"].append(child_id)
        
        root_id = None
        all_children = {c for _, c in self.connections}
        for node_id in self.nodes:
            if node_id not in all_children:
                root_id = node_id
                break
        
        return {
            "name": "未命名",
            "root_node": root_id,
            "nodes": nodes_data
        }
