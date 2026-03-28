"""
行为树编辑器画布组件

提供可视化节点编辑功能，支持执行状态可视化
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import math

from ui.theme import Theme


class NodeExecutionStatus(Enum):
    """节点执行状态"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    ABORTED = "aborted"


NODE_CATEGORY_MAP = {
    "SequenceNode": "composite",
    "SelectorNode": "composite",
    "ParallelNode": "composite",
    "InverterNode": "decorator",
    "RepeaterNode": "decorator",
    "RetryNode": "decorator",
    "TimeoutNode": "decorator",
    "OCRConditionNode": "condition",
    "ImageConditionNode": "condition",
    "ColorConditionNode": "condition",
    "NumberConditionNode": "condition",
    "VariableConditionNode": "condition",
    "KeyPressNode": "action",
    "MouseClickNode": "action",
    "MouseMoveNode": "action",
    "DelayNode": "action",
    "SetVariableNode": "action",
    "ScriptNode": "action",
}

NODE_DISPLAY_NAMES = {
    "SequenceNode": "顺序",
    "SelectorNode": "选择",
    "ParallelNode": "并行",
    "InverterNode": "取反",
    "RepeaterNode": "重复",
    "RetryNode": "重试",
    "TimeoutNode": "超时",
    "OCRConditionNode": "OCR检测",
    "ImageConditionNode": "图像匹配",
    "ColorConditionNode": "颜色检测",
    "NumberConditionNode": "数字比较",
    "VariableConditionNode": "变量判断",
    "KeyPressNode": "按键",
    "MouseClickNode": "点击",
    "MouseMoveNode": "移动",
    "DelayNode": "延时",
    "SetVariableNode": "设变量",
    "ScriptNode": "脚本",
    "CodeNode": "代码",
}

STATUS_COLORS = {
    NodeExecutionStatus.IDLE: None,
    NodeExecutionStatus.RUNNING: "#F59E0B",
    NodeExecutionStatus.SUCCESS: "#22C55E",
    NodeExecutionStatus.FAILURE: "#EF4444",
    NodeExecutionStatus.ABORTED: "#6B7280",
}

STATUS_ICONS = {
    NodeExecutionStatus.SUCCESS: "✓",
    NodeExecutionStatus.FAILURE: "✗",
    NodeExecutionStatus.RUNNING: "⋯",
    NodeExecutionStatus.ABORTED: "⊘",
}

PORT_RADIUS = 8


class NodeItem:
    """画布节点项"""
    
    def __init__(self, canvas: tk.Canvas, node_id: str, node_type: str, x: float, y: float):
        self.canvas = canvas
        self.node_id = node_id
        self.node_type = node_type
        self.x = x
        self.y = y
        self.width = 140
        self.height = 56
        
        self._status = NodeExecutionStatus.IDLE
        self._selected = False
        self._flash_state = False
        self._flash_job = None
        
        self._dark_colors = Theme.get_dark_colors()
        self._category = NODE_CATEGORY_MAP.get(node_type, "action")
        self._color_config = Theme.get_node_color(self._category)
        
        self._create_visuals()
    
    def _create_visuals(self):
        """创建视觉元素"""
        shadow_offset = 3
        
        self.shadow = self.canvas.create_rectangle(
            self.x - self.width/2 + shadow_offset,
            self.y - self.height/2 + shadow_offset,
            self.x + self.width/2 + shadow_offset,
            self.y + self.height/2 + shadow_offset,
            fill="#000000",
            stipple="gray50",
            outline="",
            tags=("node_shadow", self.node_id)
        )
        
        self.rect = self.canvas.create_rectangle(
            self.x - self.width/2,
            self.y - self.height/2,
            self.x + self.width/2,
            self.y + self.height/2,
            fill=self._dark_colors['node_bg'],
            outline=self._dark_colors['node_border'],
            width=1,
            tags=("node", self.node_id)
        )
        
        self.color_bar = self.canvas.create_rectangle(
            self.x - self.width/2,
            self.y - self.height/2,
            self.x - self.width/2 + 4,
            self.y + self.height/2,
            fill=self._color_config['bg'],
            outline="",
            tags=("node_color", self.node_id)
        )
        
        display_name = self._get_display_name()
        self.text = self.canvas.create_text(
            self.x + 10,
            self.y,
            text=display_name,
            fill=self._dark_colors['text_primary'],
            font=("Microsoft YaHei", 10, "bold"),
            anchor="center",
            tags=("node_text", self.node_id)
        )
        
        self.status_bg = self.canvas.create_oval(
            self.x + self.width/2 - 24,
            self.y - 12,
            self.x + self.width/2 - 4,
            self.y + 12,
            fill=self._dark_colors['bg_tertiary'],
            outline="",
            tags=("node_status_bg", self.node_id)
        )
        
        self.status_icon = self.canvas.create_text(
            self.x + self.width/2 - 14,
            self.y,
            text="",
            fill=self._dark_colors['text_secondary'],
            font=("Arial", 10, "bold"),
            tags=("node_icon", self.node_id)
        )
        
        self.input_port = self.canvas.create_oval(
            self.x - PORT_RADIUS,
            self.y - self.height/2 - PORT_RADIUS,
            self.x + PORT_RADIUS,
            self.y - self.height/2 + PORT_RADIUS,
            fill=self._dark_colors['bg_tertiary'],
            outline=self._dark_colors['border'],
            width=2,
            tags=("node_port_in", self.node_id, "port")
        )
        
        self.output_port = self.canvas.create_oval(
            self.x - PORT_RADIUS,
            self.y + self.height/2 - PORT_RADIUS,
            self.x + PORT_RADIUS,
            self.y + self.height/2 + PORT_RADIUS,
            fill=self._color_config['bg'],
            outline=self._dark_colors['border'],
            width=2,
            tags=("node_port_out", self.node_id, "port")
        )
        
        self._update_outline()
    
    def _get_display_name(self) -> str:
        """获取显示名称"""
        return NODE_DISPLAY_NAMES.get(self.node_type, self.node_type)
    
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
    
    def get_input_port_pos(self) -> tuple:
        """获取输入端口位置"""
        return (self.x, self.y - self.height/2)
    
    def get_output_port_pos(self) -> tuple:
        """获取输出端口位置"""
        return (self.x, self.y + self.height/2)
    
    def is_on_input_port(self, x: float, y: float) -> bool:
        """检查点是否在输入端口上"""
        px, py = self.get_input_port_pos()
        dist = math.sqrt((x - px)**2 + (y - py)**2)
        return dist <= PORT_RADIUS + 4
    
    def is_on_output_port(self, x: float, y: float) -> bool:
        """检查点是否在输出端口上"""
        px, py = self.get_output_port_pos()
        dist = math.sqrt((x - px)**2 + (y - py)**2)
        return dist <= PORT_RADIUS + 4
    
    def set_selected(self, selected: bool):
        """设置选中状态"""
        self._selected = selected
        self._update_outline()
    
    def highlight_port(self, port_type: str, highlight: bool = True):
        """高亮端口"""
        if port_type == "input":
            port = self.input_port
            color = self._dark_colors['node_selected'] if highlight else self._dark_colors['bg_tertiary']
        else:
            port = self.output_port
            color = self._dark_colors['node_selected'] if highlight else self._color_config['bg']
        
        self.canvas.itemconfig(port, outline=color, width=3 if highlight else 2)
    
    def set_status(self, status: NodeExecutionStatus):
        """设置执行状态"""
        self._status = status
        
        if self._flash_job:
            self.canvas.after_cancel(self._flash_job)
            self._flash_job = None
        
        if status == NodeExecutionStatus.RUNNING:
            self._start_flashing()
        else:
            self._flash_state = False
            self._update_outline()
        
        icon = STATUS_ICONS.get(status, "")
        self.canvas.itemconfig(self.status_icon, text=icon)
        
        if status in (NodeExecutionStatus.SUCCESS, NodeExecutionStatus.FAILURE, NodeExecutionStatus.ABORTED):
            status_color = STATUS_COLORS[status]
            if status_color:
                self.canvas.itemconfig(self.status_bg, fill=status_color)
                self.canvas.itemconfig(self.status_icon, fill="#FFFFFF")
        elif status == NodeExecutionStatus.RUNNING:
            self.canvas.itemconfig(self.status_bg, fill=STATUS_COLORS[NodeExecutionStatus.RUNNING])
        else:
            self.canvas.itemconfig(self.status_bg, fill=self._dark_colors['bg_tertiary'])
            self.canvas.itemconfig(self.status_icon, fill=self._dark_colors['text_secondary'])
    
    def _start_flashing(self):
        """开始闪烁动画"""
        self._flash_state = not self._flash_state
        self._update_outline()
        self._flash_job = self.canvas.after(400, self._start_flashing)
    
    def _update_outline(self):
        """更新边框"""
        if self._status == NodeExecutionStatus.RUNNING:
            outline = "#F59E0B" if self._flash_state else "#FBBF24"
            width = 2
        elif self._selected:
            outline = self._dark_colors['node_selected']
            width = 2
        else:
            outline = self._dark_colors['node_border']
            width = 1
        
        self.canvas.itemconfig(self.rect, outline=outline, width=width)
    
    def reset_status(self):
        """重置状态"""
        self._status = NodeExecutionStatus.IDLE
        if self._flash_job:
            self.canvas.after_cancel(self._flash_job)
            self._flash_job = None
        self._flash_state = False
        self._update_outline()
        self.canvas.itemconfig(self.status_icon, text="")
        self.canvas.itemconfig(self.status_bg, fill=self._dark_colors['bg_tertiary'])


class BehaviorTreeCanvas(ctk.CTkFrame):
    """行为树画布"""
    
    def __init__(self, master, app, on_node_select: Optional[Callable] = None,
                 on_node_move: Optional[Callable] = None,
                 on_connection_add: Optional[Callable] = None,
                 **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        
        self.nodes: Dict[str, NodeItem] = {}
        self.connections: List[tuple] = []
        self.connection_items: Dict[tuple, int] = {}
        self.selected_node: Optional[str] = None
        self.selected_nodes: List[str] = []
        self.selected_connection: Optional[tuple] = None
        self.on_node_select = on_node_select
        self.on_node_move = on_node_move
        self.on_connection_add = on_connection_add
        
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        
        self._dragging = False
        self._drag_node: Optional[str] = None
        self._drag_start = (0, 0)
        self._drag_start_pos = (0, 0)
        
        self._connecting = False
        self._connect_start_node: Optional[str] = None
        self._temp_line = None
        
        self._dark_colors = Theme.get_dark_colors()
        self.configure(fg_color=self._dark_colors['canvas_bg'], corner_radius=0)
        
        self._create_canvas()
        self._bind_events()
    
    def _create_canvas(self):
        """创建画布"""
        self.canvas = tk.Canvas(
            self,
            bg=self._dark_colors['canvas_bg'],
            highlightthickness=0,
            cursor="arrow"
        )
        self.canvas.pack(fill="both", expand=True)
        
        self._draw_grid()
    
    def _draw_grid(self):
        """绘制网格背景"""
        grid_size = 20
        grid_color = self._dark_colors['canvas_grid']
        
        self.canvas.delete("grid")
        
        width = self.canvas.winfo_width() or 800
        height = self.canvas.winfo_height() or 600
        
        for x in range(0, width + grid_size, grid_size):
            self.canvas.create_line(
                x, 0, x, height,
                fill=grid_color,
                tags="grid"
            )
        
        for y in range(0, height + grid_size, grid_size):
            self.canvas.create_line(
                0, y, width, y,
                fill=grid_color,
                tags="grid"
            )
        
        self.canvas.tag_lower("grid")
    
    def _bind_events(self):
        """绑定事件"""
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<MouseWheel>", self._on_scroll)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<Control-Button-1>", self._on_ctrl_click)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Motion>", self._on_motion)
    
    def _on_resize(self, event):
        """窗口大小改变"""
        self._draw_grid()
    
    def _on_motion(self, event):
        """鼠标移动事件"""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        for node_id, node in self.nodes.items():
            if node.is_on_output_port(x, y) or node.is_on_input_port(x, y):
                self.canvas.config(cursor="hand2")
                return
        
        self.canvas.config(cursor="arrow")
    
    def _on_click(self, event):
        """点击事件"""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        for node_id, node in self.nodes.items():
            if node.is_on_output_port(x, y):
                self._start_connecting(node_id, x, y)
                return
            
            if node.is_on_input_port(x, y):
                return
            
            if node.contains_point(x, y):
                self._select_node(node_id)
                self._dragging = True
                self._drag_node = node_id
                self._drag_start = (x - node.x, y - node.y)
                self._drag_start_pos = (node.x, node.y)
                return
        
        clicked_connection = self._find_connection_at(x, y)
        if clicked_connection:
            self._select_connection(clicked_connection)
            return
        
        self._deselect_all()
    
    def _on_ctrl_click(self, event):
        """Ctrl+点击事件（多选）"""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        for node_id, node in self.nodes.items():
            if node.contains_point(x, y):
                if node_id in self.selected_nodes:
                    self.selected_nodes.remove(node_id)
                    node.set_selected(False)
                else:
                    self.selected_nodes.append(node_id)
                    node.set_selected(True)
                return
    
    def _start_connecting(self, node_id: str, x: float, y: float):
        """开始连线"""
        self._connecting = True
        self._connect_start_node = node_id
        
        node = self.nodes[node_id]
        start_x, start_y = node.get_output_port_pos()
        
        self._temp_line = self.canvas.create_line(
            start_x, start_y, x, y,
            fill=self._dark_colors.get('connection_line', '#666666'),
            width=2,
            dash=(5, 3),
            arrow=tk.LAST,
            tags="temp_connection"
        )
        
        node.highlight_port("output", True)
        self.canvas.config(cursor="crosshair")
    
    def _update_connecting_line(self, x: float, y: float):
        """更新临时连线"""
        if self._connecting and self._temp_line and self._connect_start_node:
            node = self.nodes[self._connect_start_node]
            start_x, start_y = node.get_output_port_pos()
            
            self.canvas.coords(self._temp_line, start_x, start_y, x, y)
    
    def _finish_connecting(self, target_node_id: str):
        """完成连线"""
        if self._connect_start_node and self._connect_start_node != target_node_id:
            self.add_connection(self._connect_start_node, target_node_id)
            if self.on_connection_add:
                self.on_connection_add(self._connect_start_node, target_node_id)
        
        self._cancel_connecting()
    
    def _cancel_connecting(self):
        """取消连线"""
        if self._temp_line:
            self.canvas.delete(self._temp_line)
            self._temp_line = None
        
        if self._connect_start_node and self._connect_start_node in self.nodes:
            node = self.nodes[self._connect_start_node]
            node.highlight_port("output", False)
        
        self._connecting = False
        self._connect_start_node = None
        self.canvas.config(cursor="arrow")
    
    def _on_drag(self, event):
        """拖拽事件"""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        if self._connecting:
            self._update_connecting_line(x, y)
            
            for node_id, node in self.nodes.items():
                if node_id != self._connect_start_node:
                    if node.is_on_input_port(x, y):
                        node.highlight_port("input", True)
                    else:
                        node.highlight_port("input", False)
            return
        
        if self._dragging and self._drag_node:
            node = self.nodes[self._drag_node]
            node.move_to(x - self._drag_start[0], y - self._drag_start[1])
            self._redraw_connections()
    
    def _on_release(self, event):
        """释放事件"""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        if self._connecting:
            for node_id, node in self.nodes.items():
                if node_id != self._connect_start_node and node.is_on_input_port(x, y):
                    self._finish_connecting(node_id)
                    return
            
            self._cancel_connecting()
            return
        
        if self._dragging and self._drag_node and self.on_node_move:
            node = self.nodes[self._drag_node]
            self.on_node_move(
                self._drag_node,
                self._drag_start_pos[0], self._drag_start_pos[1],
                node.x, node.y
            )
        
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
        
        menu = tk.Menu(self, tearoff=0, bg=self._dark_colors['bg_secondary'], 
                       fg=self._dark_colors['text_primary'],
                       activebackground=self._dark_colors['bg_tertiary'])
        
        if self.selected_node:
            menu.add_command(label="删除节点", command=lambda: self.remove_node(self.selected_node))
            menu.add_command(label="复制节点", command=lambda: self._copy_node(self.selected_node))
        elif self.selected_connection:
            menu.add_command(label="删除连线", command=self.remove_selected_connection)
        
        if menu.index("end") is not None:
            menu.post(event.x_root, event.y_root)
    
    def _on_double_click(self, event):
        """双击事件"""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        for node_id, node in self.nodes.items():
            if node.contains_point(x, y):
                self._edit_node_properties(node_id)
                return
    
    def _select_node(self, node_id: str):
        """选中节点"""
        self._deselect_all()
        self.selected_node = node_id
        self.selected_nodes = [node_id]
        node = self.nodes[node_id]
        node.set_selected(True)
        
        if self.on_node_select:
            self.on_node_select(node_id, node.node_type)
    
    def _deselect_all(self):
        """取消所有选中"""
        self.selected_node = None
        self.selected_nodes = []
        for node in self.nodes.values():
            node.set_selected(False)
        self._deselect_connection()
    
    def _find_connection_at(self, x: float, y: float) -> Optional[tuple]:
        """查找指定位置的连线"""
        for conn_key, line_id in self.connection_items.items():
            coords = self.canvas.coords(line_id)
            if len(coords) >= 4:
                for i in range(0, len(coords) - 2, 2):
                    x1, y1 = coords[i], coords[i + 1]
                    x2, y2 = coords[i + 2], coords[i + 3]
                    
                    dist = self._point_to_line_distance(x, y, x1, y1, x2, y2)
                    if dist < 10:
                        return conn_key
        return None
    
    def _point_to_line_distance(self, px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
        """计算点到线段的距离"""
        line_len_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
        if line_len_sq == 0:
            return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
        
        t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_len_sq))
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)
        
        return math.sqrt((px - proj_x) ** 2 + (py - proj_y) ** 2)
    
    def _select_connection(self, conn_key: tuple):
        """选中连线"""
        self._deselect_all()
        self.selected_connection = conn_key
        
        if conn_key in self.connection_items:
            line_id = self.connection_items[conn_key]
            self.canvas.itemconfig(line_id, fill=self._dark_colors.get('node_selected', '#FFD700'), width=3)
    
    def _deselect_connection(self):
        """取消连线选中"""
        if self.selected_connection and self.selected_connection in self.connection_items:
            line_id = self.connection_items[self.selected_connection]
            self.canvas.itemconfig(line_id, fill=self._dark_colors['connection_line'], width=2)
        self.selected_connection = None
    
    def remove_selected_connection(self):
        """删除选中的连线"""
        if self.selected_connection:
            conn_key = self.selected_connection
            if conn_key in self.connections:
                self.connections.remove(conn_key)
            if conn_key in self.connection_items:
                self.canvas.delete(self.connection_items[conn_key])
                del self.connection_items[conn_key]
            self.selected_connection = None
            self._redraw_connections()
    
    def _show_add_dialog(self, x: float, y: float):
        """显示添加节点对话框"""
        pass
    
    def _edit_node_properties(self, node_id: str):
        """编辑节点属性"""
        pass
    
    def _copy_node(self, node_id: str):
        """复制节点"""
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
            node.reset_status()
            self.canvas.delete(node.node_id)
            del self.nodes[node_id]
            
            if node_id == self.selected_node:
                self.selected_node = None
            
            if node_id in self.selected_nodes:
                self.selected_nodes.remove(node_id)
            
            self.connections = [
                c for c in self.connections 
                if c[0] != node_id and c[1] != node_id
            ]
            self._redraw_connections()
    
    def add_connection(self, parent_id: str, child_id: str):
        """添加连接线"""
        if parent_id in self.nodes and child_id in self.nodes:
            if not any(c[0] == parent_id and c[1] == child_id for c in self.connections):
                self.connections.append((parent_id, child_id))
                self._redraw_connections()
    
    def _redraw_connections(self):
        """重绘连接线"""
        self.canvas.delete("connection")
        self.connection_items.clear()
        
        for parent_id, child_id in self.connections:
            if parent_id in self.nodes and child_id in self.nodes:
                parent = self.nodes[parent_id]
                child = self.nodes[child_id]
                
                start_x, start_y = parent.get_output_port_pos()
                end_x, end_y = child.get_input_port_pos()
                
                mid_y = (start_y + end_y) / 2
                
                is_selected = self.selected_connection == (parent_id, child_id)
                line_color = self._dark_colors.get('node_selected', '#FFD700') if is_selected else self._dark_colors['connection_line']
                line_width = 3 if is_selected else 2
                
                line_id = self.canvas.create_line(
                    start_x, start_y,
                    start_x, mid_y,
                    end_x, mid_y,
                    end_x, end_y,
                    fill=line_color,
                    width=line_width,
                    smooth=True,
                    arrow=tk.LAST,
                    arrowshape=(10, 12, 5),
                    tags="connection"
                )
                
                self.connection_items[(parent_id, child_id)] = line_id
        
        self.canvas.tag_lower("connection")
        self.canvas.tag_lower("grid")
    
    def clear_canvas(self):
        """清空画布"""
        self.canvas.delete("all")
        self.nodes.clear()
        self.connections.clear()
        self.connection_items.clear()
        self.selected_node = None
        self.selected_nodes = []
        self.selected_connection = None
        self._draw_grid()
    
    def set_node_status(self, node_id: str, status: NodeExecutionStatus):
        """设置节点执行状态"""
        if node_id in self.nodes:
            self.nodes[node_id].set_status(status)
    
    def reset_all_status(self):
        """重置所有节点状态"""
        for node in self.nodes.values():
            node.reset_status()
    
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
        y_offset = 100
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
        
        layout_node(root_id, x_center, 60, 600)
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
