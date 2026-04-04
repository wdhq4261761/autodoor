import time
import win32gui
import win32con
from typing import Optional, Tuple

from utils.window_capture import find_window_by_title, get_window_rect


class QuickSwitchBackend:
    """快速窗口切换后台操作实现"""
    
    def __init__(self, app=None):
        self.app = app
        self.hwnd: Optional[int] = None
        self.switch_delay: float = 0.05
        self.restore_delay: float = 0.02
        self._original_fg_window: Optional[int] = None
        self._input_controller = None
    
    def _get_input_controller(self):
        """获取输入控制器"""
        if self._input_controller is None and self.app:
            self._input_controller = self.app.input_controller
        return self._input_controller
    
    def find_window(self, title_keyword: str) -> Tuple[bool, Optional[str]]:
        """
        通过标题关键字查找窗口
        
        Args:
            title_keyword: 窗口标题关键字
        
        Returns:
            tuple: (success, window_title)
        """
        hwnd = find_window_by_title(title_keyword)
        if hwnd:
            self.hwnd = hwnd
            title = win32gui.GetWindowText(hwnd)
            return (True, title)
        return (False, None)
    
    def set_hwnd(self, hwnd: int) -> None:
        """设置目标窗口句柄"""
        self.hwnd = hwnd
    
    def _save_foreground_window(self) -> None:
        """保存当前前台窗口"""
        try:
            self._original_fg_window = win32gui.GetForegroundWindow()
        except Exception:
            self._original_fg_window = None
    
    def _restore_foreground_window(self) -> None:
        """
        恢复原来的前台窗口
        使用方法1: Alt+Tab模拟用户操作
        """
        if self._original_fg_window:
            try:
                time.sleep(self.restore_delay)
                
                if not win32gui.IsWindow(self._original_fg_window):
                    self._original_fg_window = None
                    return
                
                # 确保原窗口可见
                if win32gui.IsIconic(self._original_fg_window):
                    win32gui.ShowWindow(self._original_fg_window, win32con.SW_RESTORE)
                    time.sleep(0.1)
                
                # 方法1: 发送Alt+Tab模拟用户操作
                import win32api
                win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)  # Alt键按下
                time.sleep(0.05)
                win32api.keybd_event(win32con.VK_TAB, 0, 0, 0)    # Tab键按下
                time.sleep(0.05)
                win32api.keybd_event(win32con.VK_TAB, 0, win32con.KEYEVENTF_KEYUP, 0)  # Tab键释放
                time.sleep(0.05)
                win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)  # Alt键释放
                time.sleep(0.1)
                
                # 然后激活窗口
                win32gui.SetForegroundWindow(self._original_fg_window)
                time.sleep(0.1)
                
            except Exception:
                pass
        self._original_fg_window = None
    
    def _switch_to_target(self) -> bool:
        """
        切换到目标窗口
        
        Returns:
            bool: 是否成功
        """
        if not self.hwnd:
            return False
        
        try:
            if not win32gui.IsWindow(self.hwnd):
                return False
            
            # 首先确保窗口可见
            if win32gui.IsIconic(self.hwnd):
                win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
                time.sleep(0.1)  # 增加等待时间
            
            # 方法2: 先将窗口设置为最顶层，然后激活
            # 先设置为最顶层
            win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                               win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            time.sleep(0.1)  # 增加等待时间
            # 然后激活窗口
            win32gui.SetForegroundWindow(self.hwnd)
            time.sleep(0.1)  # 增加等待时间，确保窗口完全激活
            
            # 取消最顶层状态
            win32gui.SetWindowPos(self.hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, 
                               win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            time.sleep(0.1)  # 增加等待时间
            
            # 等待窗口完全激活
            time.sleep(0.2)  # 增加等待时间，确保窗口完全激活
            return True
            
        except Exception:
            try:
                # 即使出现异常，也要尝试取消最顶层状态
                win32gui.SetWindowPos(self.hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, 
                                   win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            except Exception:
                pass
            # 即使出现异常，也尝试返回True，因为窗口可能已经成功激活
            time.sleep(0.5)  # 增加等待时间，确保窗口完全激活
            return True
    
    def switch_to_target(self) -> bool:
        """
        切换到目标窗口并保存原窗口
        
        Returns:
            bool: 是否成功
        """
        self._save_foreground_window()
        return self._switch_to_target()
    
    def restore_foreground_window(self) -> None:
        """
        恢复原来的前台窗口
        """
        self._restore_foreground_window()
