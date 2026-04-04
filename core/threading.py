from collections import defaultdict

class ThreadManager:
    """统一线程管理器"""
    def __init__(self, app):
        self.app = app
        self.threads = defaultdict(list)  # {module: [thread1, thread2...]}
    
    def start(self, module, start_func, stop_func, log_prefix):
        """启动模块线程"""
        # 停止现有线程
        self.stop(module, stop_func, log_prefix)
        
        self.app.logging_manager.log_message(f"开始{log_prefix}")
        
        # 启动新线程
        start_count = start_func()
        
        if start_count == 0:
            module_display_name = {
                "定时功能": "定时功能",
                "数字识别": "数字识别",
                "文字识别": "文字识别",
                "图像检测": "图像检测",
                "脚本运行": "脚本运行"
            }.get(log_prefix, log_prefix)
            self.app.logging_manager.log_message(f"没有启用任何{module_display_name}")
        
        return start_count
    
    def stop(self, module, stop_func, log_prefix):
        """停止模块线程"""
        stop_func()
        
        # 清空线程列表
        if module in self.threads:
            self.threads[module].clear()