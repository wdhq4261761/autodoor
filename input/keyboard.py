import sys
import os

PYINPUT_AVAILABLE = False
try:
    from pynput import keyboard as pynput_keyboard
    PYINPUT_AVAILABLE = True
except ImportError:
    pass


def get_available_keys():
    """获取可用按键列表"""
    return [
        "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
        "space", "enter", "tab", "escape", "backspace", "delete", "insert",
        "equal", "plus", "minus", "asterisk", "slash", "backslash",
        "comma", "period", "semicolon", "apostrophe", "quote", "left", "right", "up", "down", "home", "end", "pageup", "pagedown",
        "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12"
    ]


def stop_old_listener(app):
    """停止旧的全局键盘监听器（如果存在）"""
    # 停止pynput监听器
    if hasattr(app, 'global_listener') and app.global_listener:
        try:
            app.global_listener.stop()
            app.logging_manager.log_message("旧的全局键盘监听器已停止")
        except Exception as e:
            app.logging_manager.log_message(f"停止旧的全局键盘监听器时出错: {str(e)}")

def get_key_name(key):
    """获取按键名称
    Args:
        key: 按键对象
    
    Returns:
        str: 按键名称
    """
    if hasattr(key, 'name'):
        # 普通按键
        return key.name.upper()
    elif hasattr(key, 'char') and key.char:
        # 字符按键
        return key.char.upper()
    elif hasattr(key, 'vk'):
        # 特殊按键（F键等）
        if 112 <= key.vk <= 123:  # VK_F1=112, VK_F12=123
            return f"F{key.vk - 111}"  # F1=112-111=1, 依此类推
        else:
            return str(key)
    else:
        return str(key)

def handle_global_key_press(app, key):
    """处理全局按键事件
    Args:
        app: 应用实例
        key: 按键对象
    """
    try:
        key_name = get_key_name(key)

        # 检查是否是开始快捷键
        if key_name == app.start_shortcut_var.get().upper() and not app.is_running:
            app.root.after(0, app.start_all)
        # 检查是否是结束快捷键
        if key_name == app.stop_shortcut_var.get().upper() and app.is_running:
            app.root.after(0, app.stop_all)
        if key_name == app.record_hotkey_var.get().upper():
            app.root.after(0, lambda: (
                app.script.start_recording() if not hasattr(app, 'script_executor') or not getattr(app.script_executor, 'is_recording', False) else app.script.stop_recording()
            ))
    except Exception as e:
        app.logging_manager.log_message(f"全局快捷键处理错误: {str(e)}")

def setup_global_shortcuts(app):
    """设置全局快捷键
    Args:
        app: 应用实例
    Returns:
        bool: 是否设置成功
    """
    # 其他平台使用pynput
    if PYINPUT_AVAILABLE:
        try:
            from pynput import keyboard as pynput_keyboard
            # 创建并启动全局键盘监听器
            app.global_listener = pynput_keyboard.Listener(on_press=lambda key: handle_global_key_press(app, key))
            app.global_listener.start()
            app.logging_manager.log_message("全局快捷键监听已启动 (使用pynput)")
            return True
        except Exception as e:
            app.logging_manager.log_message(f"pynput全局快捷键设置失败: {str(e)}")
    return False

def setup_shortcuts(app):
    """设置快捷键绑定
    Args:
        app: 应用实例
    """
    # 停止旧的全局键盘监听器（如果存在）
    stop_old_listener(app)

    # 只使用全局快捷键
    if setup_global_shortcuts(app):
        app.logging_manager.log_message("全局快捷键设置成功")
    else:
        app.logging_manager.log_message("全局快捷键设置失败，快捷键功能将不可用")
