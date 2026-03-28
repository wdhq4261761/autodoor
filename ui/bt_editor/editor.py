"""
行为树编辑器

整合所有编辑器组件
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Any, Dict, Optional, TYPE_CHECKING

from ui.theme import Theme
from ui.bt_editor.canvas import BehaviorTreeCanvas
from ui.bt_editor.palette import NodePalette
from ui.bt_editor.property import PropertyPanel
from ui.bt_editor.toolbar import EditorToolbar

if TYPE_CHECKING:
    from autodoor import AutoDoorOCR


class BehaviorTreeEditor(ctk.CTkFrame):
    """行为树编辑器"""
    
    def __init__(self, master, app: "AutoDoorOCR", **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        
        self.tree_data: Dict[str, Any] = {}
        self.file_path: Optional[str] = None
        self._node_counter = 0
        
        self._create_ui()
    
    def _create_ui(self):
        """创建UI"""
        self.toolbar = EditorToolbar(
            self,
            self.app,
            on_new=self._on_new,
            on_load=self._on_load,
            on_save=self._on_save,
            on_run=self._on_run,
            on_stop=self._on_stop
        )
        self.toolbar.pack(fill="x", pady=(0, 5))
        
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.palette = NodePalette(
            main_frame,
            on_node_add=self._on_node_add,
            width=180
        )
        self.palette.pack(side="left", fill="y")
        
        self.canvas = BehaviorTreeCanvas(
            main_frame,
            self.app,
            on_node_select=self._on_node_select
        )
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.property_panel = PropertyPanel(
            main_frame,
            self.app,
            on_change=self._on_property_change,
            width=220
        )
        self.property_panel.pack(side="right", fill="y")
    
    def _on_new(self):
        """新建"""
        self.tree_data = {"name": "未命名", "nodes": {}}
        self.file_path = None
        self.canvas.clear_canvas()
        self._node_counter = 0
        self.toolbar.set_status("新建")
    
    def _on_load(self, file_path: str):
        """加载"""
        from modules.behavior_tree import BehaviorTreeEngine
        
        engine = BehaviorTreeEngine(self.app)
        if engine.load_from_file(file_path):
            self.tree_data = engine.get_status()
            self.canvas.load_tree(self.tree_data)
            self.toolbar.set_status(f"已加载: {self.tree_data.get('name', '未命名')}")
        else:
            messagebox.showerror("加载失败", "无法加载行为树文件")
    
    def _on_save(self):
        """保存"""
        if not self.file_path:
            file_path = filedialog.asksaveasfilename(
                title="保存行为树",
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
            )
            if file_path:
                self._save_to_file(file_path)
    
    def _save_to_file(self, file_path: str):
        """保存到文件"""
        from modules.behavior_tree import BehaviorTreeEngine
        
        engine = BehaviorTreeEngine(self.app)
        engine.load_tree(self.tree_data)
        if engine.save_to_file(file_path):
            self.file_path = file_path
            self.toolbar.set_status("已保存")
        else:
            messagebox.showerror("保存失败", "无法保存行为树")
    
    def _on_run(self):
        """运行"""
        from modules.behavior_tree import BehaviorTreeEngine
        
        engine = BehaviorTreeEngine(self.app)
        engine.load_tree(self.canvas.get_tree_data())
        engine.start()
        self.toolbar.set_running(True)
    
    def _on_stop(self):
        """停止"""
        from modules.behavior_tree import BehaviorTreeEngine
        
        engine = BehaviorTreeEngine(self.app)
        engine.stop()
        self.toolbar.set_running(False)
    
    def _on_node_add(self, node_type: str):
        """添加节点"""
        self._node_counter += 1
        node_id = f"node_{self._node_counter}"
        
        import random
        x = 200 + random.randint(0, 200)
        y = 100 + random.randint(0, 100)
        
        self.canvas.add_node(node_id, node_type, x, y)
    
    def _on_node_select(self, node_id: str, node_type: str):
        """节点选中"""
        node_data = {
            "id": node_id,
            "type": node_type,
            "name": "",
            "enabled": True,
            "config": {}
        }
        self.property_panel.load_node(node_id, node_type, node_data)
    
    def _on_property_change(self, node_id: str, key: str, value: Any):
        """属性变更"""
        pass
