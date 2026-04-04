import win32gui
from typing import Optional, Tuple


class RelativeCoordinate:
    """相对比例坐标系统"""
    
    @staticmethod
    def pixel_to_ratio(region: tuple, window_size: tuple) -> Optional[tuple]:
        """
        像素坐标转比例坐标
        
        Args:
            region: (x1, y1, x2, y2) 像素坐标
            window_size: (width, height) 窗口尺寸
        
        Returns:
            tuple: (rx1, ry1, rx2, ry2) 比例坐标 (0.0-1.0)，失败返回None
        """
        if not region or not window_size:
            return None
        
        x1, y1, x2, y2 = region
        win_w, win_h = window_size
        
        if win_w <= 0 or win_h <= 0:
            return None
        
        return (
            x1 / win_w,
            y1 / win_h,
            x2 / win_w,
            y2 / win_h
        )
    
    @staticmethod
    def ratio_to_pixel(ratio_region: tuple, window_size: tuple) -> Optional[tuple]:
        """
        比例坐标转像素坐标
        
        Args:
            ratio_region: (rx1, ry1, rx2, ry2) 比例坐标
            window_size: (width, height) 窗口尺寸
        
        Returns:
            tuple: (x1, y1, x2, y2) 像素坐标，失败返回None
        """
        if not ratio_region or not window_size:
            return None
        
        rx1, ry1, rx2, ry2 = ratio_region
        win_w, win_h = window_size
        
        return (
            int(rx1 * win_w),
            int(ry1 * win_h),
            int(rx2 * win_w),
            int(ry2 * win_h)
        )


class WindowCoordinate:
    """窗口坐标系统工具类"""
    
    @staticmethod
    def screen_to_window(screen_x: int, screen_y: int, 
                         hwnd: int) -> Optional[Tuple[int, int]]:
        """
        屏幕绝对坐标转窗口相对坐标
        
        Args:
            screen_x, screen_y: 屏幕绝对坐标
            hwnd: 窗口句柄
        
        Returns:
            tuple: (rel_x, rel_y) 窗口相对坐标，失败返回None
        """
        try:
            rect = win32gui.GetWindowRect(hwnd)
            win_left, win_top = rect[0], rect[1]
            return (screen_x - win_left, screen_y - win_top)
        except Exception:
            return None
    
    @staticmethod
    def window_to_screen(rel_x: int, rel_y: int,
                         hwnd: int) -> Optional[Tuple[int, int]]:
        """
        窗口相对坐标转屏幕绝对坐标
        
        Args:
            rel_x, rel_y: 窗口相对坐标
            hwnd: 窗口句柄
        
        Returns:
            tuple: (screen_x, screen_y) 屏幕绝对坐标，失败返回None
        """
        try:
            rect = win32gui.GetWindowRect(hwnd)
            win_left, win_top = rect[0], rect[1]
            return (rel_x + win_left, rel_y + win_top)
        except Exception:
            return None
    
    @staticmethod
    def screen_region_to_window(screen_region: tuple,
                                 hwnd: int) -> Optional[tuple]:
        """
        屏幕绝对区域转窗口相对区域
        
        Args:
            screen_region: (x1, y1, x2, y2) 屏幕绝对坐标
            hwnd: 窗口句柄
        
        Returns:
            tuple: (x1, y1, x2, y2) 窗口相对坐标，失败返回None
        """
        try:
            rect = win32gui.GetWindowRect(hwnd)
            win_left, win_top = rect[0], rect[1]
            
            return (
                screen_region[0] - win_left,
                screen_region[1] - win_top,
                screen_region[2] - win_left,
                screen_region[3] - win_top
            )
        except Exception:
            return None
    
    @staticmethod
    def window_region_to_screen(window_region: tuple,
                                 hwnd: int) -> Optional[tuple]:
        """
        窗口相对区域转屏幕绝对区域
        
        Args:
            window_region: (x1, y1, x2, y2) 窗口相对坐标
            hwnd: 窗口句柄
        
        Returns:
            tuple: (x1, y1, x2, y2) 屏幕绝对坐标，失败返回None
        """
        try:
            rect = win32gui.GetWindowRect(hwnd)
            win_left, win_top = rect[0], rect[1]
            
            return (
                window_region[0] + win_left,
                window_region[1] + win_top,
                window_region[2] + win_left,
                window_region[3] + win_top
            )
        except Exception:
            return None
    
    @staticmethod
    def get_window_size(hwnd: int) -> Optional[Tuple[int, int]]:
        """
        获取窗口尺寸
        
        Args:
            hwnd: 窗口句柄
        
        Returns:
            tuple: (width, height)，失败返回None
        """
        try:
            rect = win32gui.GetWindowRect(hwnd)
            return (rect[2] - rect[0], rect[3] - rect[1])
        except Exception:
            return None
    
    @staticmethod
    def get_window_rect(hwnd: int) -> Optional[tuple]:
        """
        获取窗口矩形区域
        
        Args:
            hwnd: 窗口句柄
        
        Returns:
            tuple: (left, top, right, bottom)，失败返回None
        """
        try:
            return win32gui.GetWindowRect(hwnd)
        except Exception:
            return None
    
    @staticmethod
    def validate_region_in_window(region: tuple, hwnd: int) -> bool:
        """
        验证区域是否在窗口范围内
        
        Args:
            region: (x1, y1, x2, y2) 窗口相对坐标
            hwnd: 窗口句柄
        
        Returns:
            bool: 是否有效
        """
        if not region:
            return False
        
        x1, y1, x2, y2 = region
        win_size = WindowCoordinate.get_window_size(hwnd)
        
        if not win_size:
            return False
        
        win_w, win_h = win_size
        
        if x1 < 0 or y1 < 0:
            return False
        
        if x2 > win_w or y2 > win_h:
            return False
        
        if x2 - x1 < 10 or y2 - y1 < 10:
            return False
        
        return True
    
    @staticmethod
    def clamp_region_to_window(region: tuple, hwnd: int) -> Optional[tuple]:
        """
        将区域限制在窗口范围内
        
        Args:
            region: (x1, y1, x2, y2) 窗口相对坐标
            hwnd: 窗口句柄
        
        Returns:
            tuple: 调整后的区域坐标，失败返回None
        """
        if not region:
            return None
        
        win_size = WindowCoordinate.get_window_size(hwnd)
        if not win_size:
            return None
        
        win_w, win_h = win_size
        x1, y1, x2, y2 = region
        
        x1 = max(0, min(x1, win_w - 1))
        y1 = max(0, min(y1, win_h - 1))
        x2 = max(x1 + 10, min(x2, win_w))
        y2 = max(y1 + 10, min(y2, win_h))
        
        return (x1, y1, x2, y2)
