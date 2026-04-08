"""
模块控制器，负责统一管理各功能模块的启动和停止
"""
import tkinter as tk
from ui.theme import Theme


class ModuleController:
    """模块控制器类"""
    
    def __init__(self, app):
        """
        初始化模块控制器
        Args:
            app: 主应用实例
        """
        self.app = app
    
    def start_module(self, module_name, start_func):
        """统一启动模块
        Args:
            module_name: 模块名称
            start_func: 启动函数
        """
        if module_name in self.app.MODULES:
            config = self.app.MODULES[module_name]
            stop_func_path = config["stop_func"]
            parts = stop_func_path.split(".")
            obj = self.app
            for part in parts:
                obj = getattr(obj, part)
            stop_func = obj
            label = config["label"]
            self.app.thread_manager.start(module_name, start_func, stop_func, label)
        else:
            self.app.logging_manager.log_message(f"未知模块: {module_name}")

    def _update_indicator(self, module_key, is_running):
        """更新模块指示灯状态"""
        if hasattr(self.app, 'module_indicators') and module_key in self.app.module_indicators:
            color = Theme.COLORS['success'] if is_running else '#9CA3AF'
            self.app.module_indicators[module_key].configure(text_color=color)

    def _execute_module_action(self, action):
        """统一执行模块操作（启动或停止）
        
        Args:
            action: 操作类型，"start" 或 "stop"
        """
        for module_key, config in self.app.MODULES.items():
            if config.get("optional", False):
                object_path = config["object_path"]
                parts = object_path.split(".")
                obj = self.app
                try:
                    for part in parts:
                        obj = getattr(obj, part)
                except AttributeError:
                    continue
            
            object_path = config["object_path"]
            parts = object_path.split(".")
            obj = self.app
            for part in parts:
                obj = getattr(obj, part)
            
            if action == "start":
                check_var = self.app.module_check_vars.get(
                    module_key, 
                    tk.BooleanVar(value=False)
                )
                if not check_var.get():
                    continue
                
                start_func_path = config["start_func"]
                parts = start_func_path.split(".")
                start_obj = self.app
                for part in parts[:-1]:
                    start_obj = getattr(start_obj, part)
                start_func = getattr(start_obj, parts[-1])
                start_func()
                
                self._update_indicator(module_key, True)
            
            elif action == "stop":
                stop_func_path = config["stop_func"]
                parts = stop_func_path.split(".")
                stop_obj = self.app
                for part in parts[:-1]:
                    stop_obj = getattr(stop_obj, part)
                stop_func = getattr(stop_obj, parts[-1])
                
                stop_kwargs = config.get("stop_kwargs", {})
                stop_func(**stop_kwargs)
                
                self._update_indicator(module_key, False)

    def start_all(self):
        """开始运行"""
        self.app.logging_manager.log_message("开始运行")

        self.app.system_stopped = False

        if hasattr(self.app, 'module_switches'):
            for switch in self.app.module_switches.values():
                switch.configure(state="disabled")

        self.app.global_start_btn.configure(state="disabled")

        self.app.global_stop_btn.configure(state="normal")
        
        self._toggle_all_ui_state("disabled")

        self._execute_module_action("start")

        self.app.alarm_module.play_start_sound()
        
        self.app.is_running = True

    def stop_all(self):
        """停止运行"""
        self.app.logging_manager.log_message("停止运行")

        self.app.system_stopped = True

        self._execute_module_action("stop")

        if hasattr(self.app, 'color_recognition_manager') and hasattr(self.app.color_recognition_manager, 'color_recognition'):
            cr = self.app.color_recognition_manager.color_recognition
            if cr and hasattr(cr, 'is_running') and cr.is_running:
                cr.stop_recognition()
            elif cr and hasattr(cr, 'recognition_thread') and cr.recognition_thread is not None and cr.recognition_thread.is_alive():
                cr.is_running = False
                cr.recognition_thread.join(timeout=2)

        self.app.event_manager.clear_events()

        self.app.alarm_module.play_stop_sound()

        if hasattr(self.app, 'module_switches'):
            for switch in self.app.module_switches.values():
                switch.configure(state="normal")

        self.app.global_start_btn.configure(state="normal")

        self.app.global_stop_btn.configure(state="disabled")
        
        self._toggle_all_ui_state("normal")
        
        self.app.is_running = False
    
    def _toggle_all_ui_state(self, state):
        """递归地禁用或启用所有UI控件
        
        Args:
            state: 控件状态，"disabled" 或 "normal"
        """
        for child in self.app.root.winfo_children():
            self._toggle_widget_state(child, state)
    
    def _toggle_widget_state(self, widget, state):
        """递归地禁用或启用控件及其所有子控件
        
        Args:
            widget: 控件
            state: 控件状态，"disabled" 或 "normal"
        """
        if widget == self.app.global_stop_btn:
            return
        
        if widget == self.app.global_start_btn:
            return
        
        for indicator in self.app.module_indicators.values():
            if widget == indicator:
                return
        
        if hasattr(self.app, 'script_tabview') and widget == self.app.script_tabview:
            return
        
        try:
            widget.configure(state=state)
        except Exception:
            pass
        
        try:
            for child in widget.winfo_children():
                self._toggle_widget_state(child, state)
        except Exception:
            pass
