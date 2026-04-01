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
        on_undo: Optional[Callable] = None,
        on_redo: Optional[Callable] = None,
        on_clear: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.app = app
        self.on_new = on_new
        self.on_load = on_load
        self.on_save = on_save
        self.on_undo = on_undo
        self.on_redo = on_redo
        self.on_clear = on_clear
        self.is_running = False
        
        self._dark_colors = Theme.get_dark_colors()
        self.configure(fg_color=self._dark_colors['header_bg'], corner_radius=0)
        self._create_ui()
    
    def _create_ui(self):
        """创建UI"""
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="x", padx=Theme.DIMENSIONS['spacing_md'], pady=Theme.DIMENSIONS['spacing_sm'])
        
        left_section = ctk.CTkFrame(main_container, fg_color="transparent")
        left_section.pack(side="left")
        
        self._create_file_buttons(left_section)
        self._create_separator(left_section)
        self._create_edit_buttons(left_section)
        
        right_section = ctk.CTkFrame(main_container, fg_color="transparent")
        right_section.pack(side="right")
        
        self._create_status_section(right_section)
    
    def _create_file_buttons(self, parent):
        """创建文件操作按钮"""
        file_frame = ctk.CTkFrame(parent, fg_color="transparent")
        file_frame.pack(side="left")
        
        btn_config = {
            'font': Theme.get_font('sm'),
            'height': Theme.DIMENSIONS['button_height'],
            'corner_radius': Theme.DIMENSIONS['button_corner_radius'],
        }
        
        ctk.CTkButton(
            file_frame,
            text="新建",
            width=70,
            fg_color=self._dark_colors['bg_tertiary'],
            hover_color=self._dark_colors['border'],
            text_color=self._dark_colors['text_primary'],
            command=self._on_new_click,
            **btn_config
        ).pack(side="left", padx=Theme.DIMENSIONS['spacing_xs'])
        
        ctk.CTkButton(
            file_frame,
            text="打开",
            width=70,
            fg_color=self._dark_colors['bg_tertiary'],
            hover_color=self._dark_colors['border'],
            text_color=self._dark_colors['text_primary'],
            command=self._on_load_click,
            **btn_config
        ).pack(side="left", padx=Theme.DIMENSIONS['spacing_xs'])
        
        ctk.CTkButton(
            file_frame,
            text="保存",
            width=70,
            fg_color=self._dark_colors['primary'],
            hover_color=self._dark_colors['primary_hover'],
            command=self._on_save_click,
            **btn_config
        ).pack(side="left", padx=Theme.DIMENSIONS['spacing_xs'])
    
    def _create_edit_buttons(self, parent):
        """创建编辑操作按钮"""
        edit_frame = ctk.CTkFrame(parent, fg_color="transparent")
        edit_frame.pack(side="left")
        
        btn_config = {
            'font': Theme.get_font('sm'),
            'height': Theme.DIMENSIONS['button_height'],
            'corner_radius': Theme.DIMENSIONS['button_corner_radius'],
            'width': 70,
            'fg_color': self._dark_colors['bg_tertiary'],
            'hover_color': self._dark_colors['border'],
            'text_color': self._dark_colors['text_primary'],
        }
        
        self.undo_btn = ctk.CTkButton(
            edit_frame,
            text="撤销",
            command=self._on_undo_click,
            state="disabled",
            **btn_config
        )
        self.undo_btn.pack(side="left", padx=Theme.DIMENSIONS['spacing_xs'])
        
        self.redo_btn = ctk.CTkButton(
            edit_frame,
            text="回退",
            command=self._on_redo_click,
            state="disabled",
            **btn_config
        )
        self.redo_btn.pack(side="left", padx=Theme.DIMENSIONS['spacing_xs'])
        
        self.clear_btn = ctk.CTkButton(
            edit_frame,
            text="清空",
            command=self._on_clear_click,
            **btn_config
        )
        self.clear_btn.pack(side="left", padx=Theme.DIMENSIONS['spacing_xs'])
    
    def _create_separator(self, parent):
        """创建分隔线"""
        sep = ctk.CTkFrame(
            parent,
            width=1,
            height=Theme.DIMENSIONS['button_height'],
            fg_color=self._dark_colors['border']
        )
        sep.pack(side="left", padx=Theme.DIMENSIONS['spacing_md'])
    
    def _create_status_section(self, parent):
        """创建状态显示区域"""
        status_frame = ctk.CTkFrame(parent, fg_color="transparent")
        status_frame.pack(side="left")
        
        self.file_path_label = ctk.CTkLabel(
            status_frame,
            text="未保存",
            font=Theme.get_font('sm'),
            text_color=self._dark_colors['text_muted']
        )
        self.file_path_label.pack(side="left", padx=(0, Theme.DIMENSIONS['spacing_md']))
        
        self.status_indicator = ctk.CTkFrame(
            status_frame,
            width=8,
            height=8,
            fg_color=self._dark_colors['success'],
            corner_radius=4
        )
        self.status_indicator.pack(side="left", padx=(0, Theme.DIMENSIONS['spacing_sm']))
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="就绪",
            font=Theme.get_font('sm'),
            text_color=self._dark_colors['text_secondary']
        )
        self.status_label.pack(side="left")
    
    def _on_new_click(self):
        """新建"""
        if self.on_new:
            self.on_new()
    
    def _on_load_click(self):
        """打开"""
        import os
        initial_dir = None
        if hasattr(self.app, 'behavior_tree') and hasattr(self.app.behavior_tree, 'editor'):
            editor = self.app.behavior_tree.editor
            if editor.file_path:
                initial_dir = os.path.dirname(editor.file_path)
        
        file_path = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="打开行为树",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if file_path and self.on_load:
            self.on_load(file_path)
    
    def _on_save_click(self):
        """保存"""
        if self.on_save:
            self.on_save()
    
    def _on_undo_click(self):
        """撤销"""
        if self.on_undo:
            self.on_undo()
    
    def _on_redo_click(self):
        """回退"""
        if self.on_redo:
            self.on_redo()
    
    def _on_clear_click(self):
        """清空画布"""
        if self.on_clear:
            self.on_clear()
    
    def update_undo_redo(self, can_undo: bool, can_redo: bool, 
                         undo_desc: Optional[str] = None, 
                         redo_desc: Optional[str] = None):
        """更新撤销/回退按钮状态"""
        self.undo_btn.configure(state="normal" if can_undo else "disabled")
        self.redo_btn.configure(state="normal" if can_redo else "disabled")
    
    def set_running(self, running: bool):
        """设置运行状态"""
        self.is_running = running
        if running:
            self.status_indicator.configure(fg_color=self._dark_colors['warning'])
            self.status_label.configure(text="运行中", text_color=self._dark_colors['warning'])
        else:
            self.status_indicator.configure(fg_color=self._dark_colors['success'])
            self.status_label.configure(text="就绪", text_color=self._dark_colors['text_secondary'])
    
    def set_status(self, text: str, color: Optional[str] = None):
        """设置状态"""
        self.status_label.configure(text=text)
        if color:
            self.status_indicator.configure(fg_color=color)
            self.status_label.configure(text_color=color)
    
    def set_file_path(self, file_path: Optional[str]):
        """设置文件路径显示"""
        if file_path:
            self.file_path_label.configure(text=file_path)
        else:
            self.file_path_label.configure(text="未保存")
