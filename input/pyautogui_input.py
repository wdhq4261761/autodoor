"""
PyAutoGUI输入控制器实现
标准版默认方案
"""
import pyautogui
from .base import BaseInputController
from .key_mapping import get_pyautogui_key


class PyAutoGUIInput(BaseInputController):
    """PyAutoGUI输入控制器"""
    
    def __init__(self, app=None):
        self._available = True
        self.app = app
        pyautogui.FAILSAFE = False
    
    @property
    def method_name(self) -> str:
        return "PyAutoGUI"
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def _log(self, message: str):
        """日志输出"""
        if self.app:
            if hasattr(self.app, 'logging_manager'):
                self.app.logging_manager.log_message(message)
            else:
                print(message)
    
    def key_down(self, key: str, priority: int = 0) -> bool:
        try:
            mapped_key = get_pyautogui_key(key)
            pyautogui.keyDown(mapped_key)
            self._log(f"执行: 按下 {key} (映射: {mapped_key})")
            return True
        except pyautogui.FailSafeException:
            self._log("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
            return False
        except Exception as e:
            self._log(f"❌ 按键按下错误: {str(e)}")
            return False
    
    def key_up(self, key: str, priority: int = 0) -> bool:
        try:
            mapped_key = get_pyautogui_key(key)
            pyautogui.keyUp(mapped_key)
            self._log(f"执行: 抬起 {key} (映射: {mapped_key})")
            return True
        except pyautogui.FailSafeException:
            self._log("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
            return False
        except Exception as e:
            self._log(f"❌ 按键抬起错误: {str(e)}")
            return False
    
    def press_key(self, key: str, delay: float = 0, priority: int = 0) -> bool:
        try:
            mapped_key = get_pyautogui_key(key)
            pyautogui.press(mapped_key, interval=delay)
            self._log(f"执行按键: {key} (映射: {mapped_key})")
            return True
        except pyautogui.FailSafeException:
            self._log("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
            return False
        except Exception as e:
            self._log(f"❌ 按键执行错误: {str(e)}")
            return False
    
    def mouse_move(self, x: int, y: int) -> bool:
        try:
            pyautogui.moveTo(x, y)
            self._log(f"执行: 移动鼠标到 ({x}, {y})")
            return True
        except pyautogui.FailSafeException:
            self._log("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
            return False
        except Exception as e:
            self._log(f"❌ 鼠标移动错误: {str(e)}")
            return False
    
    def mouse_move_relative(self, dx: int, dy: int) -> bool:
        try:
            pyautogui.moveRel(dx, dy)
            self._log(f"执行: 相对移动鼠标 ({dx}, {dy})")
            return True
        except pyautogui.FailSafeException:
            self._log("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
            return False
        except Exception as e:
            self._log(f"❌ 鼠标相对移动错误: {str(e)}")
            return False
    
    def mouse_click(self, button: str = 'left') -> bool:
        try:
            pyautogui.click(button=button)
            self._log(f"执行: 鼠标{button}点击")
            return True
        except pyautogui.FailSafeException:
            self._log("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
            return False
        except Exception as e:
            self._log(f"❌ 鼠标点击错误: {str(e)}")
            return False
    
    def mouse_down(self, button: str = 'left') -> bool:
        try:
            pyautogui.mouseDown(button=button)
            self._log(f"执行: 按下鼠标{button}键")
            return True
        except pyautogui.FailSafeException:
            self._log("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
            return False
        except Exception as e:
            self._log(f"❌ 鼠标按下错误: {str(e)}")
            return False
    
    def mouse_up(self, button: str = 'left') -> bool:
        try:
            pyautogui.mouseUp(button=button)
            self._log(f"执行: 抬起鼠标{button}键")
            return True
        except pyautogui.FailSafeException:
            self._log("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
            return False
        except Exception as e:
            self._log(f"❌ 鼠标抬起错误: {str(e)}")
            return False
    
    def mouse_scroll(self, clicks: int) -> bool:
        try:
            pyautogui.scroll(clicks)
            self._log(f"执行: 鼠标滚轮 {clicks}")
            return True
        except pyautogui.FailSafeException:
            self._log("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
            return False
        except Exception as e:
            self._log(f"❌ 鼠标滚轮错误: {str(e)}")
            return False
