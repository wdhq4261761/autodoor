"""
行为树代理类

封装行为树相关操作
"""

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from autodoor import AutoDoorOCR


class BehaviorTreeProxy:
    """行为树代理类"""
    
    def __init__(self, app: "AutoDoorOCR"):
        self.app = app
        self.engine = None
        self.editor = None
    
    def create_tab(self, parent):
        """创建行为树标签页"""
        from ui.bt_editor import BehaviorTreeEditor
        self.editor = BehaviorTreeEditor(parent, self.app)
        return self.editor
    
    def load_tree(self, file_path: str) -> bool:
        """加载行为树"""
        from modules.behavior_tree import BehaviorTreeEngine
        
        if not self.engine:
            self.engine = BehaviorTreeEngine(self.app)
        
        return self.engine.load_from_file(file_path)
    
    def save_tree(self, file_path: Optional[str] = None) -> bool:
        """保存行为树"""
        if not self.engine:
            return False
        return self.engine.save_to_file(file_path)
    
    def start_execution(self) -> bool:
        """开始执行"""
        if not self.engine:
            return False
        
        if not self.engine.root_node:
            return False
        
        self.engine.start()
        return True
    
    def stop_execution(self) -> None:
        """停止执行"""
        if self.engine:
            self.engine.stop()
    
    def pause_execution(self) -> None:
        """暂停执行"""
        if self.engine:
            self.engine.pause()
    
    def resume_execution(self) -> None:
        """恢复执行"""
        if self.engine:
            self.engine.resume()
    
    def get_status(self) -> dict:
        """获取执行状态"""
        if self.engine:
            return self.engine.get_status()
        return {
            "is_running": False,
            "is_paused": False,
            "tree_name": "",
            "tick_count": 0,
            "elapsed_time": 0,
            "file_path": None,
        }
