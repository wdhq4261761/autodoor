"""
输入控制模块
"""
from .controller import InputController, create_input_controller, USE_DD_INPUT
from .base import BaseInputController
from .key_mapping import KEY_NAME_MAPPING, DD_KEY_CODES, get_pyautogui_key, get_dd_code

__all__ = [
    'InputController',
    'create_input_controller',
    'BaseInputController',
    'KEY_NAME_MAPPING',
    'DD_KEY_CODES',
    'get_pyautogui_key',
    'get_dd_code',
    'USE_DD_INPUT',
]
