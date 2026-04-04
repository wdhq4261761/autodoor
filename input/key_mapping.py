"""
按键码映射表
包含PyAutoGUI和DD虚拟键盘的按键映射
"""

# PyAutoGUI按键名称映射
# 将标准按键名称映射到PyAutoGUI支持的名称
KEY_NAME_MAPPING = {
    'alt_l': 'altleft',
    'alt_r': 'altright',
    'control_l': 'ctrlleft',
    'control_r': 'ctrlright',
    'shift_l': 'shiftleft',
    'shift_r': 'shiftright',
    'win_l': 'winleft',
    'win_r': 'winright',
    'super_l': 'winleft',
    'super_r': 'winright',
    'meta_l': 'winleft',
    'meta_r': 'winright',
    'escape': 'escape',
    'return': 'enter',
    'backspace': 'backspace',
    'tab': 'tab',
    'space': 'space',
    'prior': 'pageup',
    'next': 'pagedown',
    'caps_lock': 'capslock',
    'num_lock': 'numlock',
    'scroll_lock': 'scrolllock',
    'print_screen': 'printscreen',
    'up': 'up',
    'down': 'down',
    'left': 'left',
    'right': 'right',
    'insert': 'insert',
    'delete': 'delete',
    'home': 'home',
    'end': 'end',
    'page_up': 'pageup',
    'page_down': 'pagedown',
}

# DD虚拟键盘键码映射
# 将标准按键名称映射到DD虚拟键盘的键码
DD_KEY_CODES = {}

DD_CODE_TO_KEY = {}


def get_pyautogui_key(key: str) -> str:
    """
    获取PyAutoGUI格式的按键名称
    
    Args:
        key: 标准按键名称
    
    Returns:
        PyAutoGUI支持的按键名称
    """
    return KEY_NAME_MAPPING.get(key.lower(), key.lower())


def get_dd_code(key: str) -> int:
    """
    获取DD虚拟键盘的键码
    
    Args:
        key: 标准按键名称
    
    Returns:
        DD键码，如果不存在返回0
    """
    return DD_KEY_CODES.get(key.lower(), 0)
