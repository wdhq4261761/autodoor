import os


class PlatformAdapter:
    """Windows平台适配器"""
    def __init__(self, app):
        self.app = app
        self.platform = "Windows"
        self.app_name = "AutoDoorOCR"
        self._init_adapters()

    def _init_adapters(self):
        self.input = WindowsInputAdapter(self.app)
        self.recorder = WindowsRecorderAdapter(self.app)
        self.permission = WindowsPermissionAdapter()

    def start_recording(self):
        return self.recorder.start()
    
    def check_permissions(self):
        return self.permission.check()
    
    def get_config_dir(self):
        """获取配置文件目录"""
        return os.path.join(os.environ.get("APPDATA"), self.app_name)
    
    def get_log_file_path(self):
        """获取日志文件路径"""
        project_root = os.path.abspath('.')
        return os.path.join(project_root, "autodoor.log")
    
    def get_tesseract_paths(self, app_root):
        """获取Tesseract可执行文件的可能路径"""
        return [
            os.path.join(app_root, "tesseract", "tesseract.exe"),
            os.path.join(app_root, "tesseract.exe"),
        ]
    
    def is_valid_tesseract_path(self, path):
        """验证Tesseract路径是否有效"""
        if not path:
            return False
        
        if not os.path.exists(path):
            return False
        
        if not os.path.isfile(path):
            return False
        
        return path.endswith("tesseract.exe")
    
    def get_test_file_path(self):
        """获取测试文件路径"""
        return 'test_tesseract.png'


class WindowsInputAdapter:
    """Windows输入适配器"""
    def __init__(self, app):
        self.app = app
    
    def press_key(self, key, delay):
        self.app.input_controller.press_key(key, delay)
    
    def key_down(self, key):
        self.app.input_controller.key_down(key)
    
    def key_up(self, key):
        self.app.input_controller.key_up(key)
    
    def click(self, x, y):
        self.app.input_controller.click(x, y)


class WindowsRecorderAdapter:
    """Windows录制器适配器"""
    def __init__(self, app):
        self.app = app
    
    def start(self):
        pass


class WindowsPermissionAdapter:
    """Windows权限适配器"""
    def check(self):
        return True
