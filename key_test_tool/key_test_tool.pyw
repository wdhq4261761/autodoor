# -*- coding: utf-8 -*-
import os
import sys
import time
import threading
import ctypes
import win32api
import win32con
import win32gui
from datetime import datetime

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except ImportError:
    print("tkinter not available")
    sys.exit(1)

import pyautogui
pyautogui.FAILSAFE = False

try:
    from pynput import keyboard as pynput_keyboard
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

VK_CODES = {
    'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45, 'f': 0x46,
    'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A, 'k': 0x4B, 'l': 0x4C,
    'm': 0x4D, 'n': 0x4E, 'o': 0x4F, 'p': 0x50, 'q': 0x51, 'r': 0x52,
    's': 0x53, 't': 0x54, 'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58,
    'y': 0x59, 'z': 0x5A,
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
    '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
    'enter': 0x0D, 'space': 0x20, 'tab': 0x09, 'escape': 0x1B,
    'backspace': 0x08, 'delete': 0x2E, 'insert': 0x2D,
    'up': 0x26, 'down': 0x28, 'left': 0x25, 'right': 0x27,
    'home': 0x24, 'end': 0x23, 'pageup': 0x21, 'pagedown': 0x22,
    'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
    'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77,
    'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B,
    'shift': 0x10, 'ctrl': 0x11, 'alt': 0x12,
    'equal': 0xBD, 'minus': 0xBB, 'plus': 0xBD,
    'comma': 0xBC, 'period': 0xBE, 'slash': 0xBF,
    'semicolon': 0xBA, 'quote': 0xDE, 'backslash': 0xDC,
    'bracketleft': 0xDB, 'bracketright': 0xDD,
}

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "key_test.log")

if getattr(sys, 'frozen', False):
    LOG_FILE = os.path.join(os.path.dirname(sys.executable), "key_test.log")


def log_to_file(message):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
    except:
        pass


class PyAutoGUIMethod:
    NAME = "PyAutoGUI"

    def press(self, key, delay=0.05):
        try:
            pyautogui.press(key.lower(), interval=delay)
            log_to_file(f"[PyAutoGUI] 按键 {key} 成功")
            return True, "成功"
        except Exception as e:
            log_to_file(f"[PyAutoGUI] 按键 {key} 失败: {str(e)}")
            return False, str(e)


class PynputMethod:
    NAME = "pynput"

    def press(self, key, delay=0.05):
        if not PYNPUT_AVAILABLE:
            return False, "pynput不可用"

        try:
            key_lower = key.lower()

            if len(key_lower) == 1:
                key_code = pynput_keyboard.KeyCode.from_char(key_lower)
            else:
                key_map = {
                    'space': pynput_keyboard.Key.space,
                    'enter': pynput_keyboard.Key.enter,
                    'tab': pynput_keyboard.Key.tab,
                    'escape': pynput_keyboard.Key.esc,
                    'backspace': pynput_keyboard.Key.backspace,
                    'delete': pynput_keyboard.Key.delete,
                    'up': pynput_keyboard.Key.up,
                    'down': pynput_keyboard.Key.down,
                    'left': pynput_keyboard.Key.left,
                    'right': pynput_keyboard.Key.right,
                    'home': pynput_keyboard.Key.home,
                    'end': pynput_keyboard.Key.end,
                    'pageup': pynput_keyboard.Key.page_up,
                    'pagedown': pynput_keyboard.Key.page_down,
                }
                for k, v in key_map.items():
                    if key_lower == k:
                        key_code = v
                        break
                else:
                    if key_lower.startswith('f') and key_lower[1:].isdigit():
                        f_num = int(key_lower[1:])
                        if 1 <= f_num <= 12:
                            key_code = getattr(pynput_keyboard.Key, f'f{f_num}')
                        else:
                            return False, f"不支持的按键: {key}"
                    else:
                        return False, f"不支持的按键: {key}"

            controller = pynput_keyboard.Controller()
            controller.press(key_code)
            time.sleep(delay)
            controller.release(key_code)
            log_to_file(f"[pynput] 按键 {key} 成功")
            return True, "成功"
        except Exception as e:
            log_to_file(f"[pynput] 按键 {key} 失败: {str(e)}")
            return False, str(e)


class SendInputMethod:
    NAME = "SendInput"

    def press(self, key, delay=0.05):
        try:
            from ctypes import wintypes, windll, byref, pointer, c_ulong, create_string_buffer

            vk_code = VK_CODES.get(key.lower())
            if not vk_code:
                return False, f"不支持的按键: {key}"

            scan_code = win32api.MapVirtualKey(vk_code, 0)

            class KEYBDINPUT(ctypes.Structure):
                _fields_ = [
                    ("wVk", wintypes.WORD),
                    ("wScan", wintypes.WORD),
                    ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD),
                    ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
                ]

            class INPUT(ctypes.Structure):
                _fields_ = [
                    ("type", wintypes.DWORD),
                    ("ki", KEYBDINPUT),
                    ("padding", ctypes.c_ubyte * 8)
                ]

            KEYEVENTF_KEYUP = 0x0002
            INPUT_KEYBOARD = 1

            extra = ctypes.c_ulong(0)

            inputs = (INPUT * 2)()

            inputs[0].type = INPUT_KEYBOARD
            inputs[0].ki.wVk = vk_code
            inputs[0].ki.wScan = scan_code
            inputs[0].ki.dwFlags = 0
            inputs[0].ki.time = 0
            inputs[0].ki.dwExtraInfo = ctypes.pointer(extra)

            inputs[1].type = INPUT_KEYBOARD
            inputs[1].ki.wVk = vk_code
            inputs[1].ki.wScan = scan_code
            inputs[1].ki.dwFlags = KEYEVENTF_KEYUP
            inputs[1].ki.time = 0
            inputs[1].ki.dwExtraInfo = ctypes.pointer(extra)

            ctypes.windll.user32.SendInput(2, ctypes.byref(inputs), ctypes.sizeof(INPUT))
            log_to_file(f"[SendInput] 按键 {key} 成功")
            return True, "成功"
        except Exception as e:
            log_to_file(f"[SendInput] 按键 {key} 失败: {str(e)}")
            return False, str(e)


class KeybdEventMethod:
    NAME = "keybd_event"

    def press(self, key, delay=0.05):
        try:
            vk_code = VK_CODES.get(key.lower())
            if not vk_code:
                return False, f"不支持的按键: {key}"

            win32api.keybd_event(vk_code, 0, 0, 0)
            time.sleep(delay)
            win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            log_to_file(f"[keybd_event] 按键 {key} 成功")
            return True, "成功"
        except Exception as e:
            log_to_file(f"[keybd_event] 按键 {key} 失败: {str(e)}")
            return False, str(e)


class PostMessageMethod:
    NAME = "PostMessage"

    def press(self, key, delay=0.05):
        try:
            vk_code = VK_CODES.get(key.lower())
            if not vk_code:
                return False, f"不支持的按键: {key}"

            scan_code = win32api.MapVirtualKey(vk_code, 0)

            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return False, "无法获取前台窗口"

            win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, vk_code, (scan_code << 16) | 0x0001)
            time.sleep(delay)
            win32gui.PostMessage(hwnd, win32con.WM_KEYUP, vk_code, (scan_code << 16) | 0xC0000001)
            log_to_file(f"[PostMessage] 按键 {key} 成功")
            return True, "成功"
        except Exception as e:
            log_to_file(f"[PostMessage] 按键 {key} 失败: {str(e)}")
            return False, str(e)


class SendMessageMethod:
    NAME = "SendMessage"

    def press(self, key, delay=0.05):
        try:
            vk_code = VK_CODES.get(key.lower())
            if not vk_code:
                return False, f"不支持的按键: {key}"

            scan_code = win32api.MapVirtualKey(vk_code, 0)

            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return False, "无法获取前台窗口"

            win32gui.SendMessage(hwnd, win32con.WM_KEYDOWN, vk_code, (scan_code << 16) | 0x0001)
            time.sleep(delay)
            win32gui.SendMessage(hwnd, win32con.WM_KEYUP, vk_code, (scan_code << 16) | 0xC0000001)
            log_to_file(f"[SendMessage] 按键 {key} 成功")
            return True, "成功"
        except Exception as e:
            log_to_file(f"[SendMessage] 按键 {key} 失败: {str(e)}")
            return False, str(e)


def get_all_methods():
    methods = [PyAutoGUIMethod()]

    if PYNPUT_AVAILABLE:
        methods.append(PynputMethod())

    methods.append(KeybdEventMethod())
    methods.append(SendInputMethod())
    methods.append(PostMessageMethod())
    methods.append(SendMessageMethod())

    return methods


class KeyTestTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Windows按键方法测试工具")
        self.root.geometry("780x700")
        self.root.resizable(False, False)

        self.methods = get_all_methods()
        self.test_key = tk.StringVar(value="a")
        self.delay_var = tk.IntVar(value=300)
        self.test_count = tk.IntVar(value=5)
        self.hotkey_listener = None

        self._init_ui()
        self._setup_hotkey()
        log_to_file("程序启动")

    def _init_ui(self):
        title_label = tk.Label(self.root, text="Windows 多方法按键测试工具",
                              font=("微软雅黑", 16, "bold"))
        title_label.pack(pady=10)

        info_text = (
            "使用说明：\n"
            "1. 选择要测试的按键和方法(下方勾选)\n"
            "2. 点击[执行测试/F10]按钮或按F10快捷键\n"
            "3. 快速切换到目标应用窗口\n"
            "4. 观察目标应用是否有反应\n"
            "5. 记录哪些方法有效"
        )
        info_label = tk.Label(self.root, text=info_text,
                            font=("微软雅黑", 9), fg="blue", justify="left")
        info_label.pack(anchor="w", padx=20, pady=5)

        input_frame = tk.LabelFrame(self.root, text="测试设置", font=("微软雅黑", 10))
        input_frame.pack(fill="x", padx=20, pady=10)

        tk.Label(input_frame, text="测试按键:").grid(row=0, column=0, padx=10, pady=8, sticky="w")
        key_entry = tk.Entry(input_frame, textvariable=self.test_key, width=10, font=("Arial", 10))
        key_entry.grid(row=0, column=1, padx=5, pady=8, sticky="w")

        key_buttons = [
            ("A", "a"), ("B", "b"), ("1", "1"), ("2", "2"),
            ("Enter", "enter"), ("Space", "space")
        ]
        for i, (text, key) in enumerate(key_buttons):
            btn = tk.Button(input_frame, text=text, width=6, command=lambda k=key: self.test_key.set(k))
            btn.grid(row=0, column=2+i, padx=2, pady=8)

        arrow_buttons = [
            ("↑上", "up"), ("↓下", "down"), ("←左", "left"), ("→右", "right")
        ]
        for i, (text, key) in enumerate(arrow_buttons):
            btn = tk.Button(input_frame, text=text, width=6, fg="red",
                          command=lambda k=key: self.test_key.set(k))
            btn.grid(row=1, column=2+i, padx=2, pady=8)

        tk.Label(input_frame, text="按键延迟:").grid(row=2, column=0, padx=10, pady=8, sticky="w")
        delay_scale = tk.Scale(input_frame, from_=10, to=1000, orient="horizontal",
                              variable=self.delay_var, length=150, showvalue=True)
        delay_scale.grid(row=2, column=1, columnspan=2, padx=5, pady=8, sticky="w")
        tk.Label(input_frame, text="ms").grid(row=2, column=3, padx=5, pady=8, sticky="w")

        tk.Label(input_frame, text="测试次数:").grid(row=2, column=4, padx=10, pady=8, sticky="w")
        count_spin = tk.Spinbox(input_frame, from_=1, to=20, textvariable=self.test_count, width=8)
        count_spin.grid(row=2, column=5, padx=5, pady=8, sticky="w")

        btn_frame = tk.Frame(input_frame)
        btn_frame.grid(row=3, column=0, columnspan=6, pady=10)

        test_btn = tk.Button(btn_frame, text="执行测试 /F10", command=self.run_test,
                            bg="#4CAF50", fg="white", font=("微软雅黑", 11, "bold"),
                            width=18, height=2, cursor="hand2")
        test_btn.pack(side="left", padx=10)

        clear_btn = tk.Button(btn_frame, text="清空结果", command=self.clear_results,
                             bg="#FF9800", fg="white", font=("微软雅黑", 10),
                             width=12, height=2, cursor="hand2")
        clear_btn.pack(side="left", padx=10)

        select_all_btn = tk.Button(btn_frame, text="全选", command=self.select_all,
                                   bg="#2196F3", fg="white", font=("微软雅黑", 10),
                                   width=8, height=2, cursor="hand2")
        select_all_btn.pack(side="left", padx=10)

        deselect_all_btn = tk.Button(btn_frame, text="取消全选", command=self.deselect_all,
                                    bg="#9C27B0", fg="white", font=("微软雅黑", 10),
                                    width=8, height=2, cursor="hand2")
        deselect_all_btn.pack(side="left", padx=10)

        methods_frame = tk.LabelFrame(self.root, text="按键方法 (勾选要测试的方法，灰色为未选中)", font=("微软雅黑", 10))
        methods_frame.pack(fill="both", expand=True, padx=20, pady=5)

        self.methods_canvas = tk.Canvas(methods_frame)
        scrollbar = ttk.Scrollbar(methods_frame, orient="vertical",
                                   command=self.methods_canvas.yview)
        self.methods_scrollable = ttk.Frame(self.methods_canvas)

        self.methods_scrollable.bind(
            "<Configure>",
            lambda e: self.methods_canvas.configure(
                scrollregion=self.methods_canvas.bbox("all")
            )
        )

        self.methods_canvas.create_window((0, 0), window=self.methods_scrollable,
                                          anchor="nw")
        self.methods_canvas.configure(yscrollcommand=scrollbar.set)

        self.methods_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.method_vars = {}

        for method in self.methods:
            var = tk.BooleanVar(value=False)
            self.method_vars[method.NAME] = var

            cb = tk.Checkbutton(self.methods_scrollable, text=method.NAME,
                               variable=var, font=("微软雅黑", 10), cursor="hand2")
            cb.pack(anchor="w", padx=20, pady=5)

        results_frame = tk.LabelFrame(self.root, text="测试结果日志", font=("微软雅黑", 10))
        results_frame.pack(fill="both", expand=True, padx=20, pady=5)

        self.results_text = tk.Text(results_frame, height=10, font=("Consolas", 9),
                                   bg="#1e1e1e", fg="#00ff00")
        self.results_text.pack(fill="both", expand=True, padx=5, pady=5)

        self.results_text.insert("end", "程序就绪，请选择测试方法和按键后点击执行测试或按F10快捷键\n")

    def _setup_hotkey(self):
        if PYNPUT_AVAILABLE:
            def on_press(key):
                try:
                    if hasattr(key, 'vk') and key.vk == 121:
                        self.root.after(0, self.run_test)
                    elif hasattr(key, 'name') and key.name == 'f10':
                        self.root.after(0, self.run_test)
                except:
                    pass

            try:
                self.hotkey_listener = keyboard.Listener(on_press=on_press)
                self.hotkey_listener.start()
                log_to_file("F10全局快捷键监听已启动")
                self.results_text.insert("end", "[系统] F10快捷键监听已启动\n")
                self.results_text.see("end")
            except Exception as e:
                log_to_file(f"F10快捷键启动失败: {str(e)}")
                self.results_text.insert("end", f"[系统] F10快捷键启动失败: {str(e)}\n")
                self.results_text.see("end")

    def select_all(self):
        for var in self.method_vars.values():
            var.set(True)

    def deselect_all(self):
        for var in self.method_vars.values():
            var.set(False)

    def run_test(self):
        key = self.test_key.get().strip().lower()
        if not key:
            messagebox.showwarning("警告", "请输入要测试的按键")
            return

        if key not in VK_CODES and len(key) != 1:
            messagebox.showwarning("警告", f"不支持的按键: {key}")
            return

        selected_methods = [m for m in self.methods
                           if self.method_vars.get(m.NAME, tk.BooleanVar()).get()]

        if not selected_methods:
            messagebox.showwarning("警告", "请至少选择一个测试方法")
            return

        delay = self.delay_var.get() / 1000.0
        count = self.test_count.get()

        log_to_file(f"开始测试: 按键={key}, 延迟={self.delay_var.get()}ms, 次数={count}")

        self.results_text.insert("end", f"\n{'='*60}\n")
        self.results_text.insert("end", f"[开始测试] 按键: [{key}] 延迟: {self.delay_var.get()}ms 次数: {count}\n")
        self.results_text.insert("end", f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.results_text.insert("end", f"{'='*60}\n")
        self.results_text.see("end")

        for method in selected_methods:
            success_count = 0
            fail_count = 0

            for i in range(count):
                try:
                    success, msg = method.press(key, delay)
                    if success:
                        success_count += 1
                    else:
                        fail_count += 1

                    self.results_text.insert("end", f"  [{method.NAME}] 第{i+1}次: {msg}\n")
                    self.results_text.see("end")

                except Exception as e:
                    fail_count += 1
                    self.results_text.insert("end", f"  [{method.NAME}] 第{i+1}次: 异常 - {str(e)}\n")
                    self.results_text.see("end")

                time.sleep(0.1)

            status = "✓有效" if success_count > 0 else "✗无效"
            self.results_text.insert("end", f"\n>>> {method.NAME}: {status} ({success_count}/{count}成功)\n")
            self.results_text.insert("end", "-"*50 + "\n")
            self.results_text.see("end")

            log_to_file(f"方法 {method.NAME}: {status} ({success_count}/{count}成功)")

        self.results_text.insert("end", "\n>>> 测试完成！请检查目标窗口是否有按键效果！\n\n")
        self.results_text.see("end")

        log_to_file("测试完成")

        messagebox.showinfo("提示", f"测试完成！\n请查看目标应用窗口是否有响应。\n\n有效方法请查看上方绿色日志。")

    def clear_results(self):
        self.results_text.delete("1.0", "end")
        self.results_text.insert("end", "结果已清空\n")
        log_to_file("结果已清空")

    def run(self):
        self.root.mainloop()


def main():
    log_to_file("=" * 50)
    log_to_file("程序启动")
    app = KeyTestTool()
    app.run()


if __name__ == "__main__":
    main()
