class PermissionManager:
    """统一权限管理器类（Windows版本）"""
    
    def __init__(self, app):
        """初始化权限管理器
        Args:
            app: AutoDoorOCR实例
        """
        self.app = app
    
    def check_accessibility(self):
        """检查辅助功能权限（Windows默认返回True）"""
        return True
    
    def check_screen_recording(self):
        """检查屏幕录制权限（Windows默认返回True）"""
        return True
    
    def check_all(self):
        """检查所有权限"""
        return self.check_accessibility() and self.check_screen_recording()
