import queue
import time
import threading
from core.priority_lock import get_module_priority


class EventManager:
    """
    事件管理器类，负责事件队列的管理和处理
    支持优先级调度：Number(6) > Timed(5) > Image(4) > OCR(3) > Color(2) > Script(1)
    """
    
    DEFAULT_IDLE_DELAY = 0.05
    DEFAULT_BUSY_DELAY = 0.02
    
    def __init__(self, app):
        self.app = app
        self.is_event_running = False
        self.event_thread = None
        self.event_queue = queue.PriorityQueue()
        self._event_count = 0
        self._last_event_time = 0
        
    def start_event_thread(self):
        """启动事件处理线程"""
        self.is_event_running = True
        self.event_thread = threading.Thread(target=self.process_events, daemon=True)
        self.event_thread.start()
        if hasattr(self.app, 'logging_manager'):
            self.app.logging_manager.log_message("事件处理线程已启动")
        else:
            print("事件处理线程已启动")

    def process_events(self):
        """
        处理事件队列中的事件
        使用动态延迟策略：空闲时较长延迟，繁忙时较短延迟
        """
        while self.is_event_running:
            try:
                event_data = self.event_queue.get(block=True, timeout=1)
                
                self._event_count += 1
                self._last_event_time = time.time()
                
                self.execute_event(event_data)
                self.event_queue.task_done()
                
                queue_size = self.event_queue.qsize()
                if queue_size > 0:
                    time.sleep(self.DEFAULT_BUSY_DELAY)
                else:
                    time.sleep(self.DEFAULT_IDLE_DELAY)
                    
            except queue.Empty:
                continue
            except Exception as e:
                if hasattr(self.app, 'logging_manager'):
                    self.app.logging_manager.log_message(f"事件处理错误: {str(e)}")
                else:
                    print(f"事件处理错误: {str(e)}")
                time.sleep(0.5)

    def add_event(self, event, module_info=None, priority=None):
        """
        添加事件到队列，支持优先级
        Args:
            event: 事件元组
            module_info: 模块信息，可选
            priority: 优先级，可选
        """
        if priority is None and module_info:
            module_type = module_info[0]
            priority = get_module_priority(module_type)
        elif priority is None:
            priority = 0
        
        priority = -priority
        self.event_queue.put((priority, event, module_info))

    def clear_events(self):
        """清空事件队列"""
        try:
            while True:
                self.event_queue.get(block=False)
                self.event_queue.task_done()
        except queue.Empty:
            pass

    def execute_event(self, event_data):
        """执行具体事件"""
        if len(event_data) == 3:
            neg_priority, event, module_info = event_data
            priority = -neg_priority if neg_priority else 0
        else:
            event, module_info = event_data
            priority = 0
        event_type, data = event

        if event_type == 'keypress':
            key = data
            try:
                if module_info:
                    module_type, module_index = module_info
                    if module_type == 'ocr':
                        delay_min_var = self.app.ocr_groups[module_index]['delay_min']
                        delay_max_var = self.app.ocr_groups[module_index]['delay_max']
                    elif module_type == 'timed':
                        delay_min_var = self.app.timed_groups[module_index]['delay_min']
                        delay_max_var = self.app.timed_groups[module_index]['delay_max']
                    elif module_type == 'number':
                        delay_min_var = self.app.number_regions[module_index]['delay_min']
                        delay_max_var = self.app.number_regions[module_index]['delay_max']
                    else:
                        class DefaultVar:
                            def get(self):
                                return "300"
                        delay_min_var = DefaultVar()
                        delay_max_var = DefaultVar()
                else:
                    class DefaultVar:
                        def get(self):
                            return "300"
                    delay_min_var = DefaultVar()
                    delay_max_var = DefaultVar()

                from modules.input import KeyEventExecutor
                executor = KeyEventExecutor(
                    self.app.input_controller, 
                    delay_min_var, 
                    delay_max_var,
                    priority=priority
                )
                executor.execute_keypress(key)

                delay_min = max(1, int(delay_min_var.get()))
                delay_max = max(delay_min, int(delay_max_var.get()))
                self.app.logging_manager.log_message(f"按下了 {key} 键，延迟范围 {delay_min}-{delay_max} 毫秒")
            except Exception as e:
                self.app.logging_manager.log_message(f"按键执行错误: {str(e)}")
        elif event_type == 'exit':
            pass
