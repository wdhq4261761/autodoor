"""
节点面板组件

提供节点类型选择面板
"""

import customtkinter as ctk
from typing import Dict, List, Callable, Optional

from ui.theme import Theme


NODE_CATEGORIES = {
    "组合节点": [
        ("SequenceNode", "顺序", "#4CAF50"),
        ("SelectorNode", "选择", "#2196F3"),
        ("ParallelNode", "并行", "#9C27B0"),
    ],
    "装饰节点": [
        ("InverterNode", "取反", "#FF9800"),
        ("RepeaterNode", "重复", "#FF5722"),
        ("RetryNode", "重试", "#795548"),
        ("TimeoutNode", "超时", "#607D8B"),
    ],
    "条件节点": [
        ("OCRConditionNode", "OCR", "#E91E63"),
        ("ImageConditionNode", "图像", "#00BCD4"),
        ("ColorConditionNode", "颜色", "#8BC34A"),
        ("NumberConditionNode", "数字", "#3F51B5"),
    ],
    "动作节点": [
        ("KeyPressNode", "按键", "#F44336"),
        ("MouseClickNode", "点击", "#FF4081"),
        ("DelayNode", "延时", "#7C4DFF"),
    ],
}


class NodePalette(ctk.CTkFrame):
    """节点面板"""
    
    def __init__(self, master, on_node_add: Optional[Callable[[str], None]] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_node_add = on_node_add
        
        self._create_ui()
    
    def _create_ui(self):
        """创建UI"""
        title = ctk.CTkLabel(
            self,
            text="节点面板",
            font=Theme.get_font("md"),
            text_color=Theme.COLORS["text_primary"]
        )
        title.pack(pady=(10, 5))
        
        for category, nodes in NODE_CATEGORIES.items():
            self._create_category(category, nodes)
    
    def _create_category(self, category: str, nodes: List[tuple]):
        """创建分类"""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=5, pady=2)
        
        label = ctk.CTkLabel(
            frame,
            text=category,
            font=Theme.get_font("xs"),
            text_color=Theme.COLORS["text_secondary"]
        )
        label.pack(anchor="w", padx=5)
        
        for node_type, display_name, color in nodes:
            btn = ctk.CTkButton(
                frame,
                text=display_name,
                font=Theme.get_font("xs"),
                fg_color=color,
                hover_color=self._darken_color(color),
                height=28,
                corner_radius=4,
                command=lambda t=node_type: self._on_click(t)
            )
            btn.pack(fill="x", padx=5, pady=2)
    
    def _darken_color(self, hex_color: str) -> str:
        """加深颜色"""
        hex_color = hex_color.lstrip("#")
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = max(0, int(r * 0.8))
        g = max(0, int(g * 0.8))
        b = max(0, int(b * 0.8))
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _on_click(self, node_type: str):
        """节点点击"""
        if self.on_node_add:
            self.on_node_add(node_type)
