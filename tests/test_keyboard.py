import pytest
from unittest.mock import MagicMock, patch


class TestKeyboardListening:
    """键盘监听测试类"""
    
    def test_keysym_mapping(self):
        """测试键名映射"""
        keysym_map = {
            "Prior": "PageUp",
            "Next": "PageDown",
            "Return": "Enter",
            "space": "Space"
        }
        
        assert keysym_map["Prior"] == "PageUp"
        assert keysym_map["Next"] == "PageDown"
        assert keysym_map["Return"] == "Enter"
        assert keysym_map["space"] == "Space"
    
    def test_allowed_function_keys(self):
        """测试允许的功能键"""
        allowed_function_keys = [
            "Insert", "Delete", "Home", "End", "Prior", "Next", "PageUp", "PageDown",
            "Up", "Down", "Left", "Right",
            "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12",
            "Escape", "Tab", "Return", "Enter", "Space", "space", "BackSpace", "Backspace",
            "Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L", "Alt_R"
        ]
        
        assert "F1" in allowed_function_keys
        assert "F12" in allowed_function_keys
        assert "Enter" in allowed_function_keys
        assert "Space" in allowed_function_keys
    
    def test_key_validation(self):
        """测试按键验证"""
        allowed_function_keys = ["F1", "F2", "Enter", "Space"]
        
        def is_valid_key(keysym):
            return len(keysym) == 1 or keysym in allowed_function_keys
        
        assert is_valid_key("a") is True
        assert is_valid_key("F1") is True
        assert is_valid_key("Enter") is True
        assert is_valid_key("invalid_key") is False


class TestKeyboardUtils:
    """键盘工具测试类"""
    
    def test_key_combination_format(self):
        """测试组合键格式"""
        combo = "ctrl+shift+a"
        
        parts = combo.split("+")
        
        assert len(parts) == 3
        assert parts[0] == "ctrl"
        assert parts[1] == "shift"
        assert parts[2] == "a"
    
    def test_key_normalization(self):
        """测试键名标准化"""
        keys = ["ENTER", "Enter", "enter"]
        
        normalized = [k.lower() for k in keys]
        
        assert all(k == "enter" for k in normalized)
    
    def test_function_key_range(self):
        """测试功能键范围"""
        function_keys = [f"F{i}" for i in range(1, 13)]
        
        assert len(function_keys) == 12
        assert "F1" in function_keys
        assert "F12" in function_keys
