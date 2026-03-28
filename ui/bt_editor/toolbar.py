"""
编辑器工具栏
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Optional, Callable, TYPE_CHECKING

from ui.theme import Theme

if TYPE_CHECKING:
    from autodoor import AutoDoorOCR


class EditorToolbar(ctk.CTkFrame):
    """编辑器工具栏"""
    
    def __init__(
        self,
        master,
        app: "AutoDoorOCR",
        on_new: Optional[Callable] = None,
        on_load: Optional[Callable] = None,
        on_save: Optional[Callable] = None,
        on_run: Optional[Callable] = None,
        on_stop: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.app = app
        self.on_new = on_new
        self.on_load = on_load
        self.on_save = on_save
        self.on_run = on_run
        self.on_stop = on_stop
        
        self._create_ui()
    
    def _create_ui(self):
        """创建UI"""
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkButton(
            btn_frame,
            text="新建",
            font=Theme.get_font("xs"),
            width=60,
            height=28,
            fg_color=Theme.COLORS["primary"],
            hover_color=Theme.COLORS["primary_hover"],
            command=self._on_new_click
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            btn_frame,
            text="打开",
            font=Theme.get_font("xs"),
            width=60,
            height=28,
            fg_color=Theme.COLORS["info"],
            hover_color=Theme.COLORS["info_hover"],
            command=self._on_load_click
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            btn_frame,
            text="保存",
            font=Theme.get_font("xs"),
            width=60,
            height=28,
            fg_color=Theme.COLORS["success"],
            hover_color=Theme.COLORS["primary_hover"],
            command=self._on_save_click
        ).pack(side="left", padx=2)
        
        ctk.CTkFrame(btn_frame, width=1, fg_color=Theme.COLORS["border"]).pack(side="left", fill="y", padx=5)
        
        self.run_btn = ctk.CTkButton(
            btn_frame,
            text="运行",
            font=Theme.get_font("xs"),
            width=60,
            height=28,
            fg_color=Theme.COLORS["success"],
            hover_color=Theme.COLORS["primary_hover"],
            command=self._on_run_click
        )
        self.run_btn.pack(side="left", padx=2)
        
        self.stop_btn = ctk.CTkButton(
            btn_frame,
            text="停止",
            font=Theme.get_font("xs"),
            width=60,
            height=28,
            fg_color=Theme.COLORS["error"],
            hover_color=Theme.COLORS["error"],
            command=self._on_stop_click,
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=2)
        
        self.status_label = ctk.CTkLabel(
            btn_frame,
            text="就绪",
            font=Theme.get_font("xs"),
            text_color=Theme.COLORS["text_secondary"]
        )
        self.status_label.pack(side="right", padx=10)
    
    def _on_new_click(self):
        """新建"""
        if self.on_new:
            self.on_new()
    
    def _on_load_click(self):
        """打开"""
        file_path = filedialog.askopenfilename(
            title="打开行为树",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if file_path and self.on_load:
            self.on_load(file_path)
    
    def _on_save_click(self):
        """保存"""
        if self.on_save:
            self.on_save()
    
    def _on_run_click(self):
        """运行"""
        if self.on_run:
            self.on_run()
            self.set_running(True)
    
    def _on_stop_click(self):
        """停止"""
        if self.on_stop:
            self.on_stop()
            self.set_running(False)
    
    def set_running(self, running: bool):
        """设置运行状态"""
        if running:
            self.run_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.status_label.configure(text="运行中", text_color=Theme.COLORS["success"])
        else:
            self.run_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.status_label.configure(text="就绪", text_color=Theme.COLORS["text_secondary"])
    
    def set_status(self, text: str, color: Optional[str] = None):
        """设置状态"""
        self.status_label.configure(text=text)
        if color:
            self.status_label.configure(text_color=color)
