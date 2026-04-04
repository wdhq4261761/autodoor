import threading
import time
import re
import tkinter as tk

from modules.recorder import RecorderBase
from core.priority_lock import get_module_priority


pynput_to_pyautogui_map = {
    'page_up': 'pageup',
    'page_down': 'pagedown',
    'ctrl_l': 'ctrlleft',
    'ctrl_r': 'ctrlright',
    'shift_l': 'shiftleft',
    'shift_r': 'shiftright',
    'alt_l': 'altleft',
    'alt_r': 'altright',
    'cmd': 'command',
    'cmd_l': 'command',
    'cmd_r': 'command',
    'win_l': 'winleft',
    'win_r': 'winright',
}


class ScriptModule:
    """
    脚本模块
    优先级: 1 (Number=6 > Timed=5 > Image=4 > OCR=3 > Color=2 > Script=1)
    """
    
    PRIORITY = get_module_priority('script')
    
    def __init__(self, app):
        """
        初始化脚本模块
        Args:
            app: 主应用实例
        """
        self.app = app
    
    def start_script(self, start_color_recognition=True):
        """从首页启动脚本
        
        Args:
            start_color_recognition: 是否同时启动颜色识别线程，默认值为True
        """
        if self.app.system_stopped:
            self.app.logging_manager.log_message("系统已完全停止，拒绝执行StartScript命令")
            return
        
        if not hasattr(self.app, 'script_executor'):
            self.app.script_executor = ScriptExecutor(self.app)
        
        if hasattr(self.app, 'script_text'):
            script_content = self.app.script_text.get(1.0, tk.END)
            if not script_content.strip():
                tk.messagebox.showwarning("警告", "脚本内容为空，请先编写脚本！")
                return
            
            self.app.script_executor.run_script(script_content)
            self.app.status_var.set("脚本执行中...")
            self.app.logging_manager.log_message("脚本已启动")
            
            if start_color_recognition and hasattr(self.app, 'color_enabled') and self.app.color_enabled.get():
                self.app.color.start_recognition()
                self.app.logging_manager.log_message("颜色识别已自动启动")

    def stop_script(self, stop_color_recognition=True):
        """停止脚本执行
        Args:
            stop_color_recognition: 是否同时停止颜色识别线程，默认值为True
        """
        if hasattr(self.app, 'script_executor') and hasattr(self.app.script_executor, 'is_running') and self.app.script_executor.is_running:
            self.app.script_executor.stop_script()
            self.app.status_var.set("脚本已停止")
        
        if stop_color_recognition:
            self.app.color.stop_recognition()

    def start_recording(self):
        """开始录制脚本"""
        if not hasattr(self.app, 'script_executor'):
            self.app.script_executor = ScriptExecutor(self.app)
        
        self.app.script_executor.start_recording()
        if hasattr(self.app, 'record_btn'):
            self.app.record_btn.configure(text="录制中...", state="disabled")
        if hasattr(self.app, 'stop_record_btn'):
            self.app.stop_record_btn.configure(state="normal")
        self.app.status_var.set("录制中...")
        self.app.alarm_module.play_start_sound()

    def stop_recording(self):
        """停止录制脚本"""
        if hasattr(self.app, 'script_executor'):
            self.app.script_executor.stop_recording()
            if hasattr(self.app, 'record_btn'):
                self.app.record_btn.configure(text="开始录制", state="normal")
            if hasattr(self.app, 'stop_record_btn'):
                self.app.stop_record_btn.configure(state="disabled")
            self.app.status_var.set("录制已停止")
            self.app.alarm_module.play_stop_sound()

class ScriptExecutor(RecorderBase):
    """
    脚本执行器类
    优先级: 1 (最低)
    """
    PRIORITY = get_module_priority('script')
    
    def __init__(self, app):
        super().__init__(app)
        self.is_running = False
        self.is_paused = False
        self.execution_thread = None
        self.recording_thread = None
        self.recording_events = []
        self.recording_start_time = None
        self.last_event_time = None
        self.recording_grace_period = False
        
        self.core_graphics_available = False

    def _optimize_delay(self, command, next_command=None):
        """统一延迟优化逻辑"""
        if command["type"] != "delay" or not next_command:
            return command
        
        # 按键操作前的延迟可减少 100ms（人类感知阈值）
        if next_command["type"] in ["keydown", "keyup", "click"]:
            optimized = command.copy()
            optimized["time"] = max(0, command["time"] - 100)
            return optimized
        
        return command
    
    def _execute_with_optimization(self, command, next_command=None):
        """统一执行入口，自动应用优化"""
        optimized = self._optimize_delay(command, next_command)
        self.execute_command(optimized)

    def run_script(self, script_content):
        def execute():
            self.is_running = True
            self.is_paused = False
            pressed_keys = set()
            
            try:
                lines = script_content.splitlines()
                commands = []
                for line in lines:
                    command = self.parse_line(line)
                    if command:
                        commands.append(command)
                
                if not commands:
                    self.app.logging_manager.log_message("脚本中没有有效命令！")
                    self.is_running = False
                    return
                
                while self.is_running:
                    for i, command in enumerate(commands):
                        if not self.is_running:
                            break
                        
                        while self.is_paused:
                            time.sleep(0.1)
                            if not self.is_running:
                                break
                        
                        if not self.is_running:
                            break
                        
                        if command["type"] in ["keydown", "keyup"]:
                            key = command["key"]
                            count = int(command["count"])
                            for _ in range(count):
                                if not self.is_running:
                                    break
                                while self.is_paused:
                                    time.sleep(0.1)
                                    if not self.is_running:
                                        break
                                if not self.is_running:
                                    break
                                
                                try:
                                    if command["type"] == "keydown":
                                        if key not in pressed_keys:
                                            self.app.input_controller.key_down(key, priority=self.PRIORITY)
                                            pressed_keys.add(key)
                                    elif command["type"] == "keyup":
                                        if key in pressed_keys:
                                            self.app.input_controller.key_up(key, priority=self.PRIORITY)
                                            pressed_keys.remove(key)
                                except Exception as e:
                                    self.app.logging_manager.log_message(f"执行按键 {key} 时出错: {str(e)}")
                        else:
                            next_cmd = commands[i + 1] if i + 1 < len(commands) else None
                            self._execute_with_optimization(command, next_cmd)
            except Exception as e:
                error_msg = f"脚本执行出错: {str(e)}"
                self.app.logging_manager.log_message(error_msg)
                try:
                    if hasattr(self.app, 'root') and hasattr(self.app, 'status_var'):
                        self.app.root.after(0, lambda: self.app.status_var.set(f"执行错误: {str(e)}"))
                except Exception:
                    pass
            finally:
                for key in pressed_keys:
                    try:
                        self.app.input_controller.key_up(key, priority=self.PRIORITY)
                        self.app.logging_manager.log_message(f"确保抬起: {key}")
                    except Exception as e:
                        self.app.logging_manager.log_message(f"抬起按键 {key} 时出错: {str(e)}")
                
                self.is_running = False
        
        # 启动执行线程
        self.execution_thread = threading.Thread(target=execute, daemon=True)
        self.execution_thread.start()

    def run_script_once(self, script_content):
        def execute():
            self.is_running = True
            self.is_paused = False
            pressed_keys = set()
            
            try:
                lines = script_content.splitlines()
                commands = []
                for line in lines:
                    command = self.parse_line(line)
                    if command:
                        commands.append(command)
                
                if not commands:
                    self.app.logging_manager.log_message("脚本中没有有效命令！")
                    self.is_running = False
                    return
                
                for i, command in enumerate(commands):
                    if not self.is_running:
                        break
                    
                    while self.is_paused:
                        time.sleep(0.1)
                        if not self.is_running:
                            break
                    
                    if not self.is_running:
                        break
                    
                    if command["type"] in ["keydown", "keyup"]:
                        key = command["key"]
                        count = int(command["count"])
                        for _ in range(count):
                            if not self.is_running:
                                break
                            while self.is_paused:
                                time.sleep(0.1)
                                if not self.is_running:
                                    break
                            if not self.is_running:
                                break
                            
                            if command["type"] == "keydown":
                                if key not in pressed_keys:
                                    self.app.input_controller.key_down(key, priority=self.PRIORITY)
                                    pressed_keys.add(key)
                            elif command["type"] == "keyup":
                                if key in pressed_keys:
                                    self.app.input_controller.key_up(key, priority=self.PRIORITY)
                                    pressed_keys.remove(key)
                    else:
                            next_cmd = commands[i + 1] if i + 1 < len(commands) else None
                            self._execute_with_optimization(command, next_cmd)
            except Exception as e:
                error_msg = f"脚本执行出错: {str(e)}"
                self.app.logging_manager.log_message(error_msg)
                try:
                    if hasattr(self.app, 'root') and hasattr(self.app, 'status_var'):
                        self.app.root.after(0, lambda: self.app.status_var.set(f"执行错误: {str(e)}"))
                except Exception:
                    pass
            finally:
                for key in pressed_keys:
                    try:
                        self.app.input_controller.key_up(key, priority=self.PRIORITY)
                        self.app.logging_manager.log_message(f"确保抬起: {key}")
                    except Exception as e:
                        self.app.logging_manager.log_message(f"抬起按键 {key} 时出错: {str(e)}")
                
                self.is_running = False
                self.app.logging_manager.log_message("脚本执行完成")
        
        self.execution_thread = threading.Thread(target=execute, daemon=True)
        self.execution_thread.start()

    def parse_line(self, line):
        line = line.strip()
        if not line:
            return None
        
        key_pattern = re.compile(r'^(KeyDown|KeyUp)\s+["\'](.*?)["\']\s*\,\s*(\d+)$', re.IGNORECASE)
        match = key_pattern.match(line)
        if match:
            command_type = match.group(1).lower()
            key = match.group(2).lower()
            count = int(match.group(3))
            return {
                "type": command_type,
                "key": key,
                "count": count
            }
        
        mouse_pattern = re.compile(r'^(Left|Right|Middle)(Down|Up)\s+(\d+)$', re.IGNORECASE)
        match = mouse_pattern.match(line)
        if match:
            button = match.group(1).lower()
            action = match.group(2).lower()
            count = int(match.group(3))
            return {
                "type": f"mouse_{action}",
                "button": button,
                "count": count
            }
        
        move_pattern = re.compile(r"^MoveTo\s+(\d+)\s*\,\s*(\d+)$", re.IGNORECASE)
        match = move_pattern.match(line)
        if match:
            x = int(match.group(1))
            y = int(match.group(2))
            return {
                "type": "moveto",
                "x": x,
                "y": y
            }
        
        delay_pattern = re.compile(r"^Delay\s+(\d+)$", re.IGNORECASE)
        match = delay_pattern.match(line)
        if match:
            delay_time = int(match.group(1))
            return {
                "type": "delay",
                "time": delay_time
            }
        
        if line.strip().lower() == "stopscript":
            return {
                "type": "stopscript"
            }
        elif line.strip().lower() == "startscript":
            return {
                "type": "startscript"
            }
        
        return None

    def execute_command(self, command):
        try:
            if command["type"] in ["keydown", "keyup"]:
                key = command["key"]
                count = int(command["count"])
                for _ in range(count):
                    if not self.is_running:
                        break
                    while self.is_paused:
                        time.sleep(0.1)
                        if not self.is_running:
                            break
                    if not self.is_running:
                        break
                    
                    if command["type"] == "keydown":
                        self.app.input_controller.key_down(key, priority=self.PRIORITY)
                    else:
                        self.app.input_controller.key_up(key, priority=self.PRIORITY)
            elif command["type"] in ["mouse_down", "mouse_up"]:
                button = command["button"]
                count = int(command["count"])
                for _ in range(count):
                    if not self.is_running:
                        break
                    while self.is_paused:
                        time.sleep(0.1)
                        if not self.is_running:
                            break
                    if not self.is_running:
                        break
                    
                    if command["type"] == "mouse_down":
                        self.app.input_controller.mouse_down(button=button, priority=self.PRIORITY)
                    else:
                        self.app.input_controller.mouse_up(button=button, priority=self.PRIORITY)
            elif command["type"] == "moveto":
                x = int(command["x"])
                y = int(command["y"])
                if self.is_running and not self.is_paused:
                    self.app.input_controller.move_to(x, y, priority=self.PRIORITY)
            elif command["type"] == "delay":
                delay_time = command["time"] / 1000
                self.app.logging_manager.log_message(f"执行: 延迟 {delay_time}秒")
                
                # 分段延迟，以便能够响应暂停/停止命令
                start_time = time.time()
                elapsed_time = 0
                while elapsed_time < delay_time:
                    if not self.is_running:
                        break
                    while self.is_paused:
                        time.sleep(0.1)
                        if not self.is_running:
                            break
                    if not self.is_running:
                        break
                    
                    sleep_time = min(0.1, delay_time - elapsed_time)
                    time.sleep(sleep_time)
                    elapsed_time = time.time() - start_time
            elif command["type"] == "stopscript":
                # 停止脚本执行，确保在主线程中执行
                if not self.is_running:
                    return
                while self.is_paused:
                    time.sleep(0.1)
                    if not self.is_running:
                        return
                if not self.is_running:
                    return
                self.app.logging_manager.log_message("执行: 停止脚本")
                self.app.root.after(0, lambda: self.app.script.stop(stop_color_recognition=False))
            elif command["type"] == "startscript":
                if not self.is_running:
                    return
                while self.is_paused:
                    time.sleep(0.1)
                    if not self.is_running:
                        return
                if not self.is_running:
                    return
                self.app.logging_manager.log_message("执行: 启动脚本")
                self.app.root.after(0, lambda: self.app.script.start(start_color_recognition=False))
        except Exception as e:
            # 添加错误处理，确保即使执行命令失败也不会导致应用程序崩溃
            error_msg = f"执行命令出错: {str(e)}"
            self.app.logging_manager.log_message(error_msg)
            # 记录详细的错误信息
            import traceback
            self.app.logging_manager.log_message(f"错误详情: {traceback.format_exc()}")
            # 继续执行其他命令，而不是终止整个脚本
            return

    def pause_script(self):
        """暂停脚本执行"""
        self.is_paused = True

    def resume_script(self):
        """恢复脚本执行"""
        self.is_paused = False

    def stop_script(self):
        """停止脚本执行"""
        self.is_running = False
        self.is_paused = False

    def start_recording(self):
        """开始录制按键"""
        # 设置录制缓冲期，避免记录开始录制时的操作
        self.recording_grace_period = True
        
        def record():
            import time
            self.is_recording = True
            self.recording_events = []
            self.recording_start_time = time.time()
            self.last_event_time = self.recording_start_time
            
            # 记录当前按下的按键，用于避免重复记录
            pressed_keys = set()
            # 记录鼠标移动的最后位置
            last_mouse_position = None
            
            # 导入pynput模块
            keyboard = None
            mouse = None
            keyboard_listener = None
            mouse_listener = None
            
            try:
                from pynput import keyboard, mouse
            except Exception as e:
                self.app.root.after(0, lambda: self.app.ui.show_message("提示", "无法启动录制功能，请确保pynput模块已正确安装。"))
                self.is_recording = False
                self.recording_events = []
                self.generate_recorded_script()
                return
            
            # 键盘事件处理
            def on_key_press(key):
                if not self.is_recording:
                    return False
                if getattr(self, 'recording_grace_period', False):
                    self.recording_grace_period = False
                    return
                
                try:
                    key_name = key.char
                except AttributeError:
                    key_name = key.name
                except Exception:
                    return
                
                key_name = pynput_to_pyautogui_map.get(key_name, key_name)
                
                record_hotkey = self.app.record_hotkey_var.get().lower()
                if key_name == record_hotkey:
                    return
                
                if key_name not in pressed_keys:
                    current_time = time.time()
                    delay = int((current_time - self.last_event_time) * 1000)
                    self.last_event_time = current_time
                    
                    try:
                        self.recording_events.append({
                            "type": "keydown",
                            "key": key_name,
                            "delay": delay
                        })
                        pressed_keys.add(key_name)
                    except Exception as e:
                        pass
            
            def on_key_release(key):
                if not self.is_recording:
                    return False
                if getattr(self, 'recording_grace_period', False):
                    return
                
                try:
                    key_name = key.char
                except AttributeError:
                    key_name = key.name
                except Exception:
                    return
                
                key_name = pynput_to_pyautogui_map.get(key_name, key_name)
                
                record_hotkey = self.app.record_hotkey_var.get().lower()
                if key_name == record_hotkey:
                    return
                
                if key_name in pressed_keys:
                    current_time = time.time()
                    delay = int((current_time - self.last_event_time) * 1000)
                    self.last_event_time = current_time
                    
                    try:
                        self.recording_events.append({
                            "type": "keyup",
                            "key": key_name,
                            "delay": delay
                        })
                        pressed_keys.remove(key_name)
                    except Exception as e:
                        pass
            
            # 鼠标移动事件处理
            def on_mouse_move(x, y):
                if not self.is_recording:
                    return False
                if getattr(self, 'recording_grace_period', False):
                    return
                
                nonlocal last_mouse_position
                last_mouse_position = (x, y)
            
            # 鼠标点击事件处理
            def on_mouse_click(x, y, button, pressed):
                if not self.is_recording:
                    return False
                if getattr(self, 'recording_grace_period', False):
                    return
                
                current_time = time.time()
                delay = int((current_time - self.last_event_time) * 1000)
                self.last_event_time = current_time
                
                try:
                    button_name = button.name
                except Exception:
                    return
                
                if last_mouse_position:
                    mouse_x, mouse_y = last_mouse_position
                else:
                    mouse_x, mouse_y = x, y
                
                try:
                    self.recording_events.append({
                        "type": "moveto",
                        "x": int(mouse_x),
                        "y": int(mouse_y),
                        "delay": delay
                    })
                    
                    self.recording_events.append({
                        "type": f"mouse_{'down' if pressed else 'up'}",
                        "button": button_name,
                        "x": int(mouse_x),
                        "y": int(mouse_y),
                        "delay": 0
                    })
                except Exception as e:
                    pass

            time.sleep(0.5)
            self.recording_grace_period = False
            
            self.app.logging_manager.log_message("🔴 开始录制操作...")

            try:
                keyboard_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
                mouse_listener = mouse.Listener(on_move=on_mouse_move, on_click=on_mouse_click)
                
                self.register_resource(keyboard_listener, lambda listener: listener.stop())
                self.register_resource(mouse_listener, lambda listener: listener.stop())
                
                keyboard_listener.start()
                mouse_listener.start()
                
                while self.is_recording:
                    time.sleep(0.1)
                    
            except Exception as e:
                self.app.root.after(0, lambda: self.app.show_message("提示", f"录制启动失败: {str(e)}"))
                self.is_recording = False
            finally:
                self.cleanup_resources()
                self.generate_recorded_script()
                self.app.logging_manager.log_message("🟢 录制完成")
        
        # 启动录制线程
        self.recording_thread = threading.Thread(target=record, daemon=True)
        self.recording_thread.start()

    def stop_recording(self):
        """停止录制按键"""
        import time
        
        # 设置录制缓冲期，避免记录停止录制时的操作
        self.recording_grace_period = True
        self.is_recording = False
        self.is_listening = False  # 确保监听循环退出
        # 等待0.5秒后再生成脚本，确保缓冲期生效
        time.sleep(0.1)
        
        # 显式停止所有监听器
        if hasattr(self, 'keyboard_listener') and self.keyboard_listener:
            try:
                self.keyboard_listener.stop()
                self.keyboard_listener = None
            except:
                pass
        
        if hasattr(self, 'mouse_listener') and self.mouse_listener:
            try:
                self.mouse_listener.stop()
                self.mouse_listener = None
            except:
                pass
        
        if hasattr(self, 'key_listener') and self.key_listener:
            try:
                self.key_listener.stop_listening()  # 确保 CGEventTap 正确清理
                self.key_listener = None
            except:
                pass
        
        # 调用基类统一清理
        self.cleanup_resources()
        
        # 等待监听线程完全退出（最多 500ms）
        start = time.time()
        while any([hasattr(self, 'keyboard_listener') and self.keyboard_listener,
                   hasattr(self, 'mouse_listener') and self.mouse_listener,
                   hasattr(self, 'key_listener') and self.key_listener]) \
              and time.time() - start < 0.5:
            time.sleep(0.01)
        
        # 脚本生成已在录制线程的 finally 块中处理
        # 此处不再重复生成脚本
        
        # 播放停止运行音效
        try:
            self.app.play_stop_sound()
        except Exception as e:
            pass

    def generate_recorded_script(self):
        """生成录制脚本"""
        current_platform = self.app.platform_adapter.platform
        
        script_content = ""
        event_types = {"keydown": 0, "keyup": 0, "moveto": 0, "mouse_down": 0, "mouse_up": 0}
        
        try:
            if hasattr(self, 'recording_events'):
                for event in self.recording_events:
                    if event["delay"] > 0:
                        script_content += f"Delay {event['delay']}\n"
                    
                    if event["type"] in ["keydown", "keyup"]:
                        script_content += f"{event['type'].capitalize()} \"{event['key']}\", 1\n"
                        event_types[event["type"]] += 1
                    elif event["type"] == "moveto":
                        # 生成鼠标移动命令
                        script_content += f"MoveTo {event['x']}, {event['y']}\n"
                        event_types["moveto"] += 1
                    elif event["type"] in ["mouse_down", "mouse_up"]:
                        button = event["button"].capitalize()
                        action = event["type"].split('_')[1].capitalize()
                        script_content += f"{button}{action} 1\n"
                        event_types[event["type"]] += 1
            
            # 将生成的脚本插入到文本框末尾
            self.app.root.after(0, lambda:
                (self.app.script_text.insert(self.app.script_text.index(tk.END), script_content),
                 self.app.script_text.see(tk.END))
            )
        except Exception as e:
            pass
