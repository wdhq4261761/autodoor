import threading
import time
import tkinter as tk

try:
    import screeninfo
except ImportError:
    screeninfo = None

from core.priority_lock import get_module_priority
from core.click_handler import ClickHandler


class TimedModule:
    """
    定时任务模块
    优先级: 5 (Number=6 > Timed=5 > Image=4 > OCR=3 > Color=2 > Script=1)
    """
    
    PRIORITY = get_module_priority('timed')
    
    def __init__(self, app):
        self.app = app
        self.click_handler = ClickHandler(app)
    
    def start_timed_tasks(self):
        def start_func():
            start_count = 0
            for i, group in enumerate(self.app.timed_groups):
                if group["enabled"].get():
                    try:
                        interval = int(group["interval"].get())
                    except (ValueError, TypeError):
                        interval = 10
                    key = group["key"].get()
                    stop_event = threading.Event()
                    self.app.timed_stop_events[i] = stop_event
                    thread = threading.Thread(target=self.timed_task_loop, args=(i, interval, key, stop_event), daemon=True)
                    self.app.timed_threads.append(thread)
                    thread.start()
                    start_count += 1
            return start_count

        self.app.start_module("timed", start_func)

    def stop_timed_tasks(self):
        for stop_event in self.app.timed_stop_events.values():
            stop_event.set()
        self.app.timed_stop_events.clear()
        if self.app.timed_threads:
            self.app.timed_threads.clear()

    def timed_task_loop(self, group_index, interval, key, stop_event):
        while not stop_event.is_set() and self.app.timed_groups[group_index]["enabled"].get():
            try:
                for _ in range(int(interval)):
                    if stop_event.is_set():
                        return
                    time.sleep(1)

                if stop_event.is_set():
                    return

                group = self.app.timed_groups[group_index]

                if stop_event.is_set():
                    return

                self.app.alarm_module.play_alarm_sound(group["alarm"])

                if stop_event.is_set():
                    return

                if group["click_enabled"].get():
                    if stop_event.is_set():
                        return

                    pos_x = group["position_x"].get()
                    pos_y = group["position_y"].get()

                    if pos_x != 0 or pos_y != 0:
                        self.click_handler.execute_click(
                            x=pos_x,
                            y=pos_y,
                            priority=self.PRIORITY,
                            module_name="定时任务",
                            index=group_index,
                            delay=0.5
                        )

                    if stop_event.is_set():
                        return

                if key:
                    if stop_event.is_set():
                        return

                    self.app.logging_manager.log_message(f"[{self.app.platform_adapter.platform}] 定时任务{group_index+1}触发按键: {key}")
                    
                    from modules.input import KeyEventExecutor
                    delay_min_var = group["delay_min"]
                    delay_max_var = group["delay_max"]
                    executor = KeyEventExecutor(self.app.input_controller, delay_min_var, delay_max_var, self.PRIORITY)
                    executor.execute_keypress(key)
                    
                    self.app.logging_manager.log_message(f"定时任务{group_index+1}按下了 {key} 键")
                else:
                    self.app.logging_manager.log_message(f"[{self.app.platform_adapter.platform}] 定时任务{group_index+1}按键配置为空")
            except Exception as e:
                self.app.logging_manager.log_message(f"[{self.app.platform_adapter.platform}] 定时任务{group_index+1}错误: {str(e)}")
                break

    def start_timed_position_selection(self, group_index):
        self.app.logging_manager.log_message(f"开始定时组{group_index+1}屏幕位置选择...")
        self.app.is_selecting = True
        self.app.current_timed_group = group_index

        if screeninfo is None:
            self.app.show_message("错误", "screeninfo库未安装，无法支持多显示器选择。请运行 'pip install screeninfo' 安装该库。")
            return

        monitors = screeninfo.get_monitors()

        self.app.min_x = min(monitor.x for monitor in monitors)
        self.app.min_y = min(monitor.y for monitor in monitors)
        max_x = max(monitor.x + monitor.width for monitor in monitors)
        max_y = max(monitor.y + monitor.height for monitor in monitors)

        self.app.select_window = tk.Toplevel(self.app.root)
        self.app.select_window.geometry(f"{max_x - self.app.min_x}x{max_y - self.app.min_y}+{self.app.min_x}+{self.app.min_y}")
        self.app.select_window.overrideredirect(True)
        self.app.select_window.attributes("-alpha", 0.3)
        self.app.select_window.attributes("-topmost", True)

        self.app.canvas = tk.Canvas(self.app.select_window, cursor="cross", 
                               width=max_x - self.app.min_x, height=max_y - self.app.min_y)
        self.app.canvas.pack(fill=tk.BOTH, expand=True)

        self.app.canvas.create_text((max_x - self.app.min_x) // 2, (max_y - self.app.min_y) // 2, 
                              text="请点击要记录的屏幕位置", font=("Arial", 16), fill="red")

        self.app.canvas.bind("<Button-1>", self.on_timed_position_click)
        self.app.select_window.protocol("WM_DELETE_WINDOW", self.app.cancel_selection)
        self.app.select_window.bind("<Escape>", lambda e: self.app.cancel_selection())
        
        self.app.select_window.focus_set()

    def on_timed_position_click(self, event):
        pos_x = event.x_root
        pos_y = event.y_root

        self.app.logging_manager.log_message(f"定时组{self.app.current_timed_group+1}已选择位置: {pos_x},{pos_y}")

        if 0 <= self.app.current_timed_group < len(self.app.timed_groups):
            group = self.app.timed_groups[self.app.current_timed_group]
            group["position_x"].set(pos_x)
            group["position_y"].set(pos_y)
            group["position_var"].set(f"{pos_x},{pos_y}")

            if hasattr(self.app, 'save_config') and callable(self.app.save_config):
                try:
                    self.app.save_config()
                except Exception:
                    pass

        self.app.cancel_selection()
