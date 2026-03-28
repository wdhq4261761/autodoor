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
from ui.bt_editor.undo_redo import (
    CommandManager, AddNodeCommand, RemoveNodeCommand, 
    MoveNodeCommand, AddConnectionCommand
)

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
        self._is_modified = False
        
        self.command_manager = CommandManager(max_history=50)
        
        self._dark_colors = Theme.get_dark_colors()
        self.configure(fg_color=self._dark_colors['bg_primary'], corner_radius=0)
        
        self._create_ui()
        self._bind_shortcuts()
    
    def _create_ui(self):
        """创建UI"""
        self.toolbar = EditorToolbar(
            self,
            self.app,
            on_new=self._on_new,
            on_load=self._on_load,
            on_save=self._on_save,
            on_run=self._on_run,
            on_stop=self._on_stop,
            on_undo=self._on_undo,
            on_redo=self._on_redo,
            on_clear=self._on_clear_canvas
        )
        self.toolbar.pack(fill="x")
        
        separator = ctk.CTkFrame(
            self,
            height=1,
            fg_color=self._dark_colors['border']
        )
        separator.pack(fill="x")
        
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True)
        
        left_separator = ctk.CTkFrame(
            main_frame,
            width=1,
            fg_color=self._dark_colors['border']
        )
        left_separator.pack(side="left", fill="y")
        
        self.palette = NodePalette(
            main_frame,
            on_node_add=self._on_node_add
        )
        self.palette.pack(side="left", fill="y")
        
        center_separator = ctk.CTkFrame(
            main_frame,
            width=1,
            fg_color=self._dark_colors['border']
        )
        center_separator.pack(side="left", fill="y")
        
        self.canvas = BehaviorTreeCanvas(
            main_frame,
            self.app,
            on_node_select=self._on_node_select,
            on_node_move=self._on_node_move,
            on_connection_add=self._on_connection_add
        )
        self.canvas.pack(side="left", fill="both", expand=True)
        
        right_separator = ctk.CTkFrame(
            main_frame,
            width=1,
            fg_color=self._dark_colors['border']
        )
        right_separator.pack(side="left", fill="y")
        
        self.property_panel = PropertyPanel(
            main_frame,
            self.app,
            on_change=self._on_property_change
        )
        self.property_panel.pack(side="right", fill="y")
    
    def _bind_shortcuts(self):
        """绑定键盘快捷键"""
        shortcuts = [
            ("<Control-n>", self._on_new),
            ("<Control-o>", self._on_open),
            ("<Control-s>", self._on_save),
            ("<Control-Shift-S>", self._on_save_as),
            ("<Control-z>", self._on_undo),
            ("<Control-y>", self._on_redo),
            ("<Control-Shift-Z>", self._on_redo),
            ("<Delete>", self._on_delete_selected),
            ("<BackSpace>", self._on_delete_selected),
            ("<space>", self._on_toggle_run),
            ("<Escape>", self._on_stop),
            ("<Control-c>", self._on_copy),
            ("<Control-v>", self._on_paste),
            ("<Control-d>", self._on_duplicate),
        ]
        
        def make_handler(cb, key):
            def handler(e):
                cb()
                return "break"
            return handler
        
        root = self.winfo_toplevel()
        for key, callback in shortcuts:
            handler = make_handler(callback, key)
            root.bind(key, handler)
    
    def _on_new(self):
        """新建"""
        if self._is_modified:
            if not messagebox.askyesno("确认", "当前文件未保存，是否继续新建？"):
                return
        
        self.tree_data = {"name": "未命名", "nodes": {}}
        self.file_path = None
        self.canvas.clear_canvas()
        self._node_counter = 0
        self._is_modified = False
        self.command_manager.clear()
        self.toolbar.set_status("新建")
        self._update_undo_redo_buttons()
    
    def _on_open(self):
        """打开文件"""
        file_path = filedialog.askopenfilename(
            title="打开行为树",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if file_path:
            self._on_load(file_path)
    
    def _on_load(self, file_path: str):
        """加载"""
        from modules.behavior_tree import BehaviorTreeEngine
        
        engine = BehaviorTreeEngine(self.app)
        if engine.load_from_file(file_path):
            self.tree_data = engine.get_status()
            self.canvas.load_tree(self.tree_data)
            self.file_path = file_path
            self._is_modified = False
            self.command_manager.clear()
            self.toolbar.set_status(f"已加载: {self.tree_data.get('name', '未命名')}")
            self._update_undo_redo_buttons()
        else:
            messagebox.showerror("加载失败", "无法加载行为树文件")
    
    def _on_save(self):
        """保存"""
        if not self.file_path:
            self._on_save_as()
        else:
            self._save_to_file(self.file_path)
    
    def _on_save_as(self):
        """另存为"""
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
        tree_data = self.canvas.get_tree_data()
        engine.load_tree(tree_data)
        if engine.save_to_file(file_path):
            self.file_path = file_path
            self._is_modified = False
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
    
    def _on_toggle_run(self):
        """切换运行状态"""
        if self.toolbar.is_running:
            self._on_stop()
        else:
            self._on_run()
    
    def _on_clear_canvas(self):
        """清空画布"""
        if self.canvas.nodes:
            if not messagebox.askyesno("确认清空", "确定要清空画布吗？\n此操作不可撤销。"):
                return
        self.canvas.clear_canvas()
        self._node_counter = 0
        self._is_modified = False
        self.command_manager.clear()
        self.toolbar.set_status("画布已清空")
        self._update_undo_redo_buttons()
    
    def _on_node_add(self, node_type: str):
        """添加节点"""
        self._node_counter += 1
        node_id = f"node_{self._node_counter}"
        
        import random
        x = 200 + random.randint(0, 200)
        y = 100 + random.randint(0, 100)
        
        command = AddNodeCommand(
            canvas=self.canvas,
            node_id=node_id,
            node_type=node_type,
            x=x,
            y=y
        )
        self.command_manager.execute(command)
        self._is_modified = True
        self._update_undo_redo_buttons()
    
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
    
    def _on_node_move(self, node_id: str, old_x: float, old_y: float, new_x: float, new_y: float):
        """节点移动"""
        command = MoveNodeCommand(
            canvas=self.canvas,
            node_id=node_id,
            old_x=old_x,
            old_y=old_y,
            new_x=new_x,
            new_y=new_y
        )
        self.command_manager.execute(command)
        self._is_modified = True
    
    def _on_connection_add(self, parent_id: str, child_id: str):
        """添加连线"""
        command = AddConnectionCommand(
            canvas=self.canvas,
            parent_id=parent_id,
            child_id=child_id
        )
        self.command_manager.execute(command)
        self._is_modified = True
        self._update_undo_redo_buttons()
    
    def _on_property_change(self, node_id: str, key: str, value: Any):
        """属性变更"""
        self._is_modified = True
    
    def _on_delete_selected(self):
        """删除选中节点"""
        if self.canvas.selected_node:
            command = RemoveNodeCommand(
                canvas=self.canvas,
                node_id=self.canvas.selected_node
            )
            self.command_manager.execute(command)
            self._is_modified = True
            self._update_undo_redo_buttons()
    
    def _on_undo(self):
        """撤销"""
        if self.command_manager.undo():
            self._is_modified = True
            self.toolbar.set_status(f"撤销: {self.command_manager.get_undo_description() or ''}")
        self._update_undo_redo_buttons()
    
    def _on_redo(self):
        """回退"""
        if self.command_manager.redo():
            self._is_modified = True
            self.toolbar.set_status(f"重做: {self.command_manager.get_redo_description() or ''}")
        self._update_undo_redo_buttons()
    
    def _on_copy(self):
        """复制节点"""
        if self.canvas.selected_node:
            self._clipboard = self.canvas.selected_node
    
    def _on_paste(self):
        """粘贴节点"""
        if hasattr(self, '_clipboard') and self._clipboard:
            if self._clipboard in self.canvas.nodes:
                node = self.canvas.nodes[self._clipboard]
                self._node_counter += 1
                new_id = f"node_{self._node_counter}"
                
                command = AddNodeCommand(
                    canvas=self.canvas,
                    node_id=new_id,
                    node_type=node.node_type,
                    x=node.x + 50,
                    y=node.y + 50
                )
                self.command_manager.execute(command)
                self._is_modified = True
                self._update_undo_redo_buttons()
    
    def _on_duplicate(self):
        """复制并粘贴"""
        self._on_copy()
        self._on_paste()
    
    def _update_undo_redo_buttons(self):
        """更新撤销/回退按钮状态"""
        if hasattr(self.toolbar, 'update_undo_redo'):
            self.toolbar.update_undo_redo(
                can_undo=self.command_manager.can_undo(),
                can_redo=self.command_manager.can_redo(),
                undo_desc=self.command_manager.get_undo_description(),
                redo_desc=self.command_manager.get_redo_description()
            )
    
    def get_tree_data(self) -> Dict[str, Any]:
        """获取行为树数据"""
        return self.canvas.get_tree_data()
    
    def is_modified(self) -> bool:
        """是否已修改"""
        return self._is_modified
