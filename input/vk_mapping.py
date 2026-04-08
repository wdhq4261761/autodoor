"""
Windows 虚拟键码映射表
用于将虚拟键码（VK）转换为字符
"""

# Windows 虚拟键码到字符的映射
VK_TO_CHAR = {
    0x41: 'a',  # A
    0x42: 'b',  # B
    0x43: 'c',  # C
    0x44: 'd',  # D
    0x45: 'e',  # E
    0x46: 'f',  # F
    0x47: 'g',  # G
    0x48: 'h',  # H
    0x49: 'i',  # I
    0x4A: 'j',  # J
    0x4B: 'k',  # K
    0x4C: 'l',  # L
    0x4D: 'm',  # M
    0x4E: 'n',  # N
    0x4F: 'o',  # O
    0x50: 'p',  # P
    0x51: 'q',  # Q
    0x52: 'r',  # R
    0x53: 's',  # S
    0x54: 't',  # T
    0x55: 'u',  # U
    0x56: 'v',  # V
    0x57: 'w',  # W
    0x58: 'x',  # X
    0x59: 'y',  # Y
    0x5A: 'z',  # Z
    0x30: '0',  # 0
    0x31: '1',  # 1
    0x32: '2',  # 2
    0x33: '3',  # 3
    0x34: '4',  # 4
    0x35: '5',  # 5
    0x36: '6',  # 6
    0x37: '7',  # 7
    0x38: '8',  # 8
    0x39: '9',  # 9
    0x20: 'space',  # Space
    0x0D: 'enter',  # Enter
    0x08: 'backspace',  # Backspace
    0x09: 'tab',  # Tab
    0x1B: 'escape',  # Escape
    0x70: 'f1',  # F1
    0x71: 'f2',  # F2
    0x72: 'f3',  # F3
    0x73: 'f4',  # F4
    0x74: 'f5',  # F5
    0x75: 'f6',  # F6
    0x76: 'f7',  # F7
    0x77: 'f8',  # F8
    0x78: 'f9',  # F9
    0x79: 'f10',  # F10
    0x7A: 'f11',  # F11
    0x7B: 'f12',  # F12
    0x21: 'pageup',  # Page Up
    0x22: 'pagedown',  # Page Down
    0x23: 'end',  # End
    0x24: 'home',  # Home
    0x25: 'left',  # Left Arrow
    0x26: 'up',  # Up Arrow
    0x27: 'right',  # Right Arrow
    0x28: 'down',  # Down Arrow
    0x2D: 'insert',  # Insert
    0x2E: 'delete',  # Delete
    0x14: 'capslock',  # Caps Lock
    0x90: 'numlock',  # Num Lock
    0x91: 'scrolllock',  # Scroll Lock
    0x2C: 'printscreen',  # Print Screen
    0xBD: '-',  # Minus
    0xBB: '=',  # Equal
    0xDB: '[',  # Left Bracket
    0xDD: ']',  # Right Bracket
    0xDC: '\\',  # Backslash
    0xBA: ';',  # Semicolon
    0xDE: "'",  # Quote
    0xC0: '`',  # Grave
    0xBC: ',',  # Comma
    0xBE: '.',  # Period
    0xBF: '/',  # Slash
}

def vk_to_char(vk_code):
    """
    将虚拟键码转换为字符
    
    Args:
        vk_code: 虚拟键码（整数）
    
    Returns:
        字符串，如果无法转换则返回 None
    """
    return VK_TO_CHAR.get(vk_code)
