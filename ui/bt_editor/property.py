"""
属性面板

用于编辑节点属性
"""

from typing import Any, Callable, Dict, Optional, List

import customtkinter as ctk
import tkinter as tk

from ui.theme import Theme


NODE_CONFIG_SCHEMAS = {
    "OCRConditionNode": [
        {"key": "region", "label": "检测区域", "type": "region"},
        {"key": "keywords", "label": "关键词", "type": "text"},
        {"key": "language", "label": "语言", "type": "select", "options": ["eng", "chi_sim", "jpn"]},
    ],
    "ImageConditionNode": [
        {"key": "region", "label": "检测区域", "type": "region"},
        {"key": "template_path", "label": "模板路径", "type": "file"},
        {"key": "threshold", "label": "匹配阈值", "type": "number", "min": 0, "max": 1, "step": 0.1},
    ],
    "ColorConditionNode": [
        {"key": "region", "label": "检测区域", "type": "region"},
        {"key": "target_color", "label": "目标颜色", "type": "color"},
        {"key": "tolerance", "label": "容差", "type": "number", "min": 0, "max": 100},
    ],
    "NumberConditionNode": [
        {"key": "region", "label": "检测区域", "type": "region"},
        {"key": "compare_mode", "label": "比较模式", "type": "select", "options": ["less_than", "less_equal", "greater_than", "greater_equal", "equal", "not_equal"]},
        {"key": "threshold", "label": "比较值", "type": "number"},
    ],
    "KeyPressNode": [
        {"key": "key", "label": "按键", "type": "key"},
        {"key": "action", "label": "动作", "type": "select", "options": ["press", "down", "up"]},
        {"key": "duration", "label": "按住时长(ms)", "type": "number"},
    ],
    "MouseClickNode": [
        {"key": "button", "label": "按钮", "type": "select", "options": ["left", "right", "middle"]},
        {"key": "position", "label": "位置", "type": "position"},
        {"key": "use_blackboard", "label": "使用黑板位置", "type": "bool"},
    ],
    "DelayNode": [
        {"key": "duration_ms", "label": "延时时长(ms)", "type": "number"},
    ],
    "RepeaterNode": [
        {"key": "count", "label": "重复次数(-1无限)", "type": "number"},
    ],
    "RetryNode": [
        {"key": "max_retries", "label": "最大重试次数", "type": "number"},
    ],
    "TimeoutNode": [
        {"key": "timeout_ms", "label": "超时时间(ms)", "type": "number"},
    ],
    "ParallelNode": [
        {"key": "success_policy", "label": "成功策略", "type": "select", "options": ["require_all", "require_one"]},
    ],
}


class PropertyPanel(ctk.CTkFrame):
    """属性面板"""
    
    def __init__(self, master, app, on_change: Optional[Callable[[str, Any], None]] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        self.on_change = on_change
        
        self.current_node_id: Optional[str] = None
        self.current_node_type: Optional[str] = None
        self.widgets: Dict[str, Any] = {}
        
        self._create_ui()
    
    def _create_ui(self):
        """创建UI"""
        self.title_label = ctk.CTkLabel(
            self,
            text="属性面板",
            font=Theme.get_font("md"),
            text_color=Theme.COLORS["text_primary"]
        )
        self.title_label.pack(pady=(10, 5))
        
        self.content_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self._show_empty()
    
    def _show_empty(self):
        """显示空状态"""
        self._clear_content()
        
        label = ctk.CTkLabel(
            self.content_frame,
            text="请选择一个节点",
            font=Theme.get_font("sm"),
            text_color=Theme.COLORS["text_secondary"]
        )
        label.pack(pady=20)
    
    def _clear_content(self):
        """清空内容"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.widgets.clear()
    
    def load_node(self, node_id: str, node_type: str, node_data: Dict[str, Any]):
        """加载节点属性"""
        self.current_node_id = node_id
        self.current_node_type = node_type
        
        self._clear_content()
        
        self.title_label.configure(text=f"属性: {node_type.replace('Node', '')}")
        
        self._create_base_fields(node_data)
        
        schema = NODE_CONFIG_SCHEMAS.get(node_type, [])
        for field in schema:
            self._create_field(field, node_data.get("config", {}).get(field["key"]))
    
    def _create_base_fields(self, node_data: Dict[str, Any]):
        """创建基础字段"""
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(
            frame,
            text="名称",
            font=Theme.get_font("xs"),
            text_color=Theme.COLORS["text_secondary"],
            width=80,
            anchor="w"
        ).pack(side="left")
        
        name_var = tk.StringVar(value=node_data.get("name", ""))
        entry = ctk.CTkEntry(
            frame,
            textvariable=name_var,
            font=Theme.get_font("xs"),
            height=28
        )
        entry.pack(side="left", fill="x", expand=True, padx=5)
        entry.bind("<FocusOut>", lambda e: self._on_field_change("name", name_var.get()))
        self.widgets["name"] = entry
        
        frame2 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        frame2.pack(fill="x", pady=2)
        
        ctk.CTkLabel(
            frame2,
            text="启用",
            font=Theme.get_font("xs"),
            text_color=Theme.COLORS["text_secondary"],
            width=80,
            anchor="w"
        ).pack(side="left")
        
        enabled_var = tk.BooleanVar(value=node_data.get("enabled", True))
        switch = ctk.CTkSwitch(
            frame2,
            text="",
            variable=enabled_var,
            command=lambda: self._on_field_change("enabled", enabled_var.get())
        )
        switch.pack(side="left", padx=5)
        self.widgets["enabled"] = switch
    
    def _create_field(self, field: Dict[str, Any], value: Any):
        """创建字段"""
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(
            frame,
            text=field["label"],
            font=Theme.get_font("xs"),
            text_color=Theme.COLORS["text_secondary"],
            width=80,
            anchor="w"
        ).pack(side="left")
        
        field_type = field.get("type", "text")
        key = field["key"]
        
        if field_type == "text":
            var = tk.StringVar(value=str(value or ""))
            widget = ctk.CTkEntry(frame, textvariable=var, font=Theme.get_font("xs"), height=28)
            widget.pack(side="left", fill="x", expand=True, padx=5)
            widget.bind("<FocusOut>", lambda e, k=key, v=var: self._on_field_change(k, v.get()))
            self.widgets[key] = widget
        
        elif field_type == "number":
            var = tk.StringVar(value=str(value or field.get("min", 0)))
            widget = ctk.CTkEntry(frame, textvariable=var, font=Theme.get_font("xs"), height=28, width=100)
            widget.pack(side="left", padx=5)
            widget.bind("<FocusOut>", lambda e, k=key, v=var: self._on_field_change(k, self._parse_number(v.get())))
            self.widgets[key] = widget
        
        elif field_type == "select":
            options = field.get("options", [])
            var = tk.StringVar(value=str(value or options[0] if options else ""))
            widget = ctk.CTkOptionMenu(frame, variable=var, values=options, font=Theme.get_font("xs"), height=28, width=100)
            widget.pack(side="left", padx=5)
            widget.bind("<<ComboboxSelected>>", lambda e, k=key, v=var: self._on_field_change(k, v.get()))
            self.widgets[key] = widget
        
        elif field_type == "bool":
            var = tk.BooleanVar(value=bool(value))
            widget = ctk.CTkSwitch(frame, text="", variable=var, command=lambda k=key, v=var: self._on_field_change(k, v.get()))
            widget.pack(side="left", padx=5)
            self.widgets[key] = widget
    
    def _parse_number(self, value: str) -> Any:
        """解析数字"""
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            return 0
    
    def _on_field_change(self, key: str, value: Any):
        """字段变更"""
        if self.on_change and self.current_node_id:
            self.on_change(self.current_node_id, key, value)
