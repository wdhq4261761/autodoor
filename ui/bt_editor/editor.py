"""
行为树编辑器

整合所有编辑器组件，支持自动保存和崩溃恢复
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Any, Dict, Optional, TYPE_CHECKING

from ui.theme import Theme
from ui.bt_editor.canvas import BehaviorTreeCanvas, NodeExecutionStatus
from ui.bt_editor.palette import NodePalette
from ui.bt_editor.property import PropertyPanel
from ui.bt_editor.toolbar import EditorToolbar
from ui.bt_editor.undo_redo import (
    CommandManager, AddNodeCommand, RemoveNodeCommand, 
    MoveNodeCommand, AddConnectionCommand
)
from modules.persistence import AutoSaveManager, CrashRecoveryHandler, FileRecoveryHandler
from ui.script_tab import askyesnocancel_centered
from modules.behavior_tree.serializer import BehaviorTreeSerializer

if TYPE_CHECKING:
    from autodoor import AutoDoorOCR


class BehaviorTreeEditor(ctk.CTkFrame):
    """行为树编辑器"""
    
    def __init__(self, master, app: "AutoDoorOCR", **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        
        self.tree_data: Dict[str, Any] = BehaviorTreeSerializer.create_empty_tree()
        self.file_path: Optional[str] = None
        self._node_counter = 0
        self._is_modified = False
        
        self.command_manager = CommandManager(max_history=50)
        
        self._dark_colors = Theme.get_dark_colors()
        self.configure(fg_color=self._dark_colors['bg_primary'], corner_radius=0)
        
        self._init_persistence()
        self._create_ui()
        self._bind_shortcuts()
        self._check_recovery()
        
    def _init_persistence(self):
        """初始化持久化功能"""
        self.auto_save_manager = AutoSaveManager(
            get_data_func=self.get_tree_data,
            on_save_callback=self._on_autosave_complete,
            get_file_path_func=lambda: self.file_path
        )
        
        self.crash_recovery_handler = CrashRecoveryHandler(
            get_data_func=self.get_tree_data,
            log_func=self._log
        )
        
        self.file_recovery_handler = FileRecoveryHandler(
            log_func=self._log
        )
        
        self.crash_recovery_handler.install()
        self.auto_save_manager.start()
        
    def _log(self, message: str):
        """日志记录"""
        if hasattr(self.app, 'log'):
            self.app.log(message)
            
    def _check_recovery(self):
        """检查是否有恢复数据"""
        recovery = self.file_recovery_handler.check_and_get_recovery()
        
        if recovery:
            self._load_recovery_data(recovery)
                
    def _load_recovery_data(self, recovery: Dict[str, Any]):
        """加载恢复数据"""
        data = recovery["data"]
        data = BehaviorTreeSerializer.migrate_data(data)
        self.tree_data = data
        self.canvas.load_tree(data)
        self._is_modified = True
        
        max_counter = 0
        for node_id in data.get("nodes", {}).keys():
            if node_id.startswith("node_"):
                try:
                    num = int(node_id[5:])
                    max_counter = max(max_counter, num)
                except ValueError:
                    pass
        self._node_counter = max_counter
        
        self.toolbar.set_status(f"已从{recovery['source']}恢复")
        
    def _on_autosave_complete(self, success: bool):
        """自动保存完成回调"""
        if success:
            self._is_modified = False
    
    def _create_ui(self):
        """创建UI"""
        self.toolbar = EditorToolbar(
            self,
            self.app,
            on_new=self._on_new,
            on_load=self._on_load,
            on_save=self._on_save,
            on_undo=self._on_undo,
            on_redo=self._on_redo,
            on_clear=self._on_clear_canvas,
            on_reset_view=self._on_reset_view
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
            on_connection_add=self._on_connection_add,
            on_node_deselect=self._on_node_deselect
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
            ("<Control-c>", self._on_copy),
            ("<Control-v>", self._on_paste),
            ("<Control-d>", self._on_duplicate),
        ]
        
        def make_handler(cb, key):
            def handler(e):
                if key in ("<Delete>", "<BackSpace>"):
                    focused = self.winfo_toplevel().focus_get()
                    if focused:
                        widget_type = str(type(focused).__name__)
                        if widget_type in ("CTkEntry", "Entry", "CTkTextbox", "Text"):
                            return None
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
            result = askyesnocancel_centered(self.winfo_toplevel(), "保存确认", "当前行为树已修改，是否保存？")
            if result is None:
                return
            elif result:
                self._on_save()
                if self._is_modified:
                    return
        
        self.tree_data = {"name": "未命名", "nodes": {}}
        self.file_path = None
        self.canvas.clear_canvas()
        self._node_counter = 0
        self._is_modified = False
        self.command_manager.clear()
        self.toolbar.set_status("新建")
        self.toolbar.set_file_path(None)
        self._update_undo_redo_buttons()
    
    def _on_open(self):
        """打开文件"""
        if self._is_modified:
            result = askyesnocancel_centered(self.winfo_toplevel(), "保存确认", "当前行为树已修改，是否保存？")
            if result is None:
                return
            elif result:
                self._on_save()
                if self._is_modified:
                    return
        
        import os
        initial_dir = None
        if self.file_path:
            initial_dir = os.path.dirname(self.file_path)
        
        file_path = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="打开行为树",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if file_path:
            self._on_load(file_path)
    
    def _on_load(self, file_path: str):
        """加载"""
        import json
        from pathlib import Path
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree_data = json.load(f)
            
            self.tree_data = tree_data
            self.canvas.load_tree(tree_data)
            self.file_path = file_path
            self._is_modified = False
            self.command_manager.clear()
            
            max_counter = 0
            for node_id in tree_data.get("nodes", {}).keys():
                if node_id.startswith("node_"):
                    try:
                        num = int(node_id[5:])
                        max_counter = max(max_counter, num)
                    except ValueError:
                        pass
            self._node_counter = max_counter
            
            self.toolbar.set_status(f"已加载: {tree_data.get('name', '未命名')}")
            self.toolbar.set_file_path(file_path)
            self._update_undo_redo_buttons()
        except Exception as e:
            messagebox.showerror("加载失败", f"无法加载行为树文件: {e}")
    
    def _on_save(self):
        """保存"""
        if not self.file_path:
            self._on_save_as()
        else:
            self._save_to_file(self.file_path)
    
    def _on_save_as(self):
        """另存为"""
        import os
        initial_dir = None
        if self.file_path:
            initial_dir = os.path.dirname(self.file_path)
        
        file_path = filedialog.asksaveasfilename(
            initialdir=initial_dir,
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
            self.toolbar.set_file_path(file_path)
        else:
            messagebox.showerror("保存失败", "无法保存行为树")
    
    def _on_clear_canvas(self):
        """清空画布"""
        if self.canvas.nodes:
            from ui.script_tab import askyesno_centered
            if not askyesno_centered(self.winfo_toplevel(), "确认清空", "确定要清空画布吗？\n此操作不可撤销。"):
                return
        self.canvas.clear_canvas()
        self._node_counter = 0
        self._is_modified = False
        self.command_manager.clear()
        self.toolbar.set_status("画布已清空")
        self._update_undo_redo_buttons()
    
    def _on_reset_view(self):
        """重置视图"""
        self.canvas.reset_view()
        self.toolbar.set_status("视图已重置")
    
    def _on_node_add(self, node_type: str):
        """添加节点"""
        self._node_counter += 1
        node_id = f"node_{self._node_counter}"
        
        canvas_width = self.canvas.canvas.winfo_width() or 800
        canvas_height = self.canvas.canvas.winfo_height() or 600
        
        x = (canvas_width / 2 - self.canvas.pan_x) / self.canvas.zoom
        y = (canvas_height / 2 - self.canvas.pan_y) / self.canvas.zoom
        
        offset = 0
        for existing_node in self.canvas.nodes.values():
            if abs(existing_node.x - x) < 160 and abs(existing_node.y - y) < 70:
                offset += 80
        
        x += offset
        
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
        self._notify_content_changed()
    
    def _on_node_select(self, node_id: str, node_type: str):
        """节点选中"""
        node = self.canvas.nodes.get(node_id)
        if node:
            node_data = {
                "id": node_id,
                "type": node_type,
                "name": node.name,
                "enabled": node.enabled,
                "config": node.config or {}
            }
        else:
            node_data = {
                "id": node_id,
                "type": node_type,
                "name": "",
                "enabled": True,
                "config": {}
            }
        self.property_panel.load_node(node_id, node_type, node_data)
    
    def _on_node_deselect(self):
        """节点取消选中"""
        self.property_panel.save_and_clear()
    
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
        if node_id and node_id in self.canvas.nodes:
            node = self.canvas.nodes[node_id]
            node.update_config(key, value)
        self._is_modified = True
        self._notify_content_changed()
    
    def _on_delete_selected(self):
        """删除选中节点或连线"""
        if self.canvas.selected_node:
            command = RemoveNodeCommand(
                canvas=self.canvas,
                node_id=self.canvas.selected_node
            )
            self.command_manager.execute(command)
            self._is_modified = True
            self._update_undo_redo_buttons()
        elif self.canvas.selected_connection:
            self.canvas.remove_selected_connection()
            self._is_modified = True
            self._notify_content_changed()
    
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
        data = self.canvas.get_tree_data()
        data = BehaviorTreeSerializer.update_metadata(data, save_type="auto")
        data = BehaviorTreeSerializer.update_editor_state(
            data,
            selected_node=self.canvas.selected_node,
            selected_connection=getattr(self.canvas, 'selected_connection', None)
        )
        return data
    
    def is_modified(self) -> bool:
        """是否已修改"""
        return self._is_modified
    
    def _notify_content_changed(self):
        """通知内容变更"""
        self.auto_save_manager.on_content_changed()
        
    def save_now(self):
        """立即执行自动保存"""
        self.auto_save_manager.save_now()
    
    def set_running(self, running: bool):
        """设置运行状态（供外部调用）"""
        self.toolbar.set_running(running)
        if not running:
            self.canvas.reset_all_status()
    
    def update_node_status(self, node_id: str, status: str):
        """更新节点状态（供外部调用）"""
        status_map = {
            "running": NodeExecutionStatus.RUNNING,
            "success": NodeExecutionStatus.SUCCESS,
            "failure": NodeExecutionStatus.FAILURE,
            "aborted": NodeExecutionStatus.ABORTED,
        }
        node_status = status_map.get(status, NodeExecutionStatus.IDLE)
        self.canvas.set_node_status(node_id, node_status)
        
    def destroy(self):
        """销毁前保存"""
        self.auto_save_manager.save_now()
        self.auto_save_manager.stop()
        self.crash_recovery_handler.uninstall()
        super().destroy()
