import threading
import time
import re
import tkinter as tk

class RecorderBase:
    """
    录制器基类，提供统一的资源管理接口
    """
    def __init__(self, app):
        self.app = app
        self.resources = []  # 跟踪所有需清理的资源
    
    def register_resource(self, resource, cleanup_func):
        """
        注册需要清理的资源
        Args:
            resource: 资源对象
            cleanup_func: 清理函数
        """
        self.resources.append((resource, cleanup_func))
    
    def cleanup_resources(self):
        """
        统一清理所有资源
        """
        for resource, cleanup_func in reversed(self.resources):
            try:
                cleanup_func(resource)
            except Exception as e:
                self.app.logging_manager.log_message(f"资源清理失败: {e}")
        self.resources.clear()