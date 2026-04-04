import datetime
import tkinter as tk
import threading
from collections import deque


class LoggingManager:
    """
    日志管理类，负责记录和显示日志信息
    
    性能优化:
    - 限制GUI日志条目数量，防止内存无限增长
    - GUI更新节流，批量刷新减少渲染次数
    """
    
    MAX_LOG_LINES = 500
    GUI_UPDATE_INTERVAL = 50  # ms
    
    def __init__(self, app):
        """
        初始化日志管理器
        Args:
            app: 应用程序实例
        """
        self.app = app
        self._log_buffer = deque(maxlen=self.MAX_LOG_LINES)
        self._gui_update_pending = False
        self._pending_logs = []
        self._update_lock = threading.Lock()
    
    def log_message(self, message):
        """
        记录日志信息（线程安全）
        Args:
            message: 要记录的日志消息
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        try:
            with open(self.app.log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"写入日志文件失败: {str(e)}")

        need_flush = False
        with self._update_lock:
            self._log_buffer.append(log_entry)
            self._pending_logs.append(log_entry)
            
            if not self._gui_update_pending:
                self._gui_update_pending = True
                need_flush = True
        
        if need_flush:
            if threading.current_thread() is not threading.main_thread():
                if hasattr(self.app, 'root') and self.app.root:
                    try:
                        self.app.root.after(self.GUI_UPDATE_INTERVAL, self._flush_gui_updates)
                    except Exception:
                        with self._update_lock:
                            self._gui_update_pending = False
            else:
                self._flush_gui_updates()
    
    def _flush_gui_updates(self):
        """
        批量刷新GUI日志（合并多次更新为一次）
        """
        with self._update_lock:
            logs_to_write = self._pending_logs.copy()
            self._pending_logs.clear()
            self._gui_update_pending = False
        
        if not logs_to_write:
            return
        
        if hasattr(self.app, 'home_log_text') and self.app.home_log_text:
            try:
                self.app.home_log_text.configure(state='normal')
                
                for log_entry in logs_to_write:
                    self.app.home_log_text.insert(tk.END, log_entry)
                
                line_count = int(self.app.home_log_text.index("end-1c").split(".")[0])
                if line_count > self.MAX_LOG_LINES:
                    lines_to_delete = line_count - self.MAX_LOG_LINES
                    self.app.home_log_text.delete("1.0", f"{lines_to_delete + 1}.0")
                
                self.app.home_log_text.see(tk.END)
                self.app.home_log_text.configure(state='disabled')
            except Exception as e:
                print(f"写入日志文本框失败: {str(e)}")

        if logs_to_write and hasattr(self.app, 'status_var'):
            try:
                last_log = logs_to_write[-1]
                if "] " in last_log:
                    message = last_log.split("] ")[-1].strip()
                else:
                    message = last_log.strip()
                self.app.status_var.set(message.split(":")[0] if ":" in message else message)
            except Exception:
                pass
    
    def clear_log(self):
        """清除日志"""
        with self._update_lock:
            self._log_buffer.clear()
            self._pending_logs.clear()
        
        if hasattr(self.app, 'home_log_text') and self.app.home_log_text:
            try:
                self.app.home_log_text.configure(state='normal')
                self.app.home_log_text.delete("1.0", tk.END)
                self.app.home_log_text.configure(state='disabled')
            except Exception as e:
                print(f"清除日志失败: {str(e)}")
