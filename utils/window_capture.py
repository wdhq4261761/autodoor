import ctypes
import win32gui
import win32ui
import win32con
from PIL import Image
from typing import Optional, List, Tuple


def find_window_by_title(keyword: str) -> Optional[int]:
    """
    通过标题关键字查找窗口
    
    Args:
        keyword: 窗口标题关键字（不区分大小写）
    
    Returns:
        int: 窗口句柄，未找到返回None
    """
    if not keyword:
        return None
    
    keyword_lower = keyword.lower()
    found_hwnd = None
    
    def enum_windows_callback(hwnd, _):
        nonlocal found_hwnd
        if found_hwnd is not None:
            return False
        
        if not win32gui.IsWindowVisible(hwnd):
            return True
        
        title = win32gui.GetWindowText(hwnd)
        if keyword_lower in title.lower():
            found_hwnd = hwnd
            return False
        
        return True
    
    try:
        win32gui.EnumWindows(enum_windows_callback, None)
        return found_hwnd
    except Exception:
        return None


def find_all_windows_by_title(keyword: str) -> List[Tuple[int, str]]:
    """
    通过标题关键字查找所有匹配的窗口
    
    Args:
        keyword: 窗口标题关键字（不区分大小写）
    
    Returns:
        list: [(hwnd, title), ...] 窗口句柄和标题列表
    """
    if not keyword:
        return []
    
    keyword_lower = keyword.lower()
    results = []
    
    def enum_windows_callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return True
        
        title = win32gui.GetWindowText(hwnd)
        if keyword_lower in title.lower():
            results.append((hwnd, title))
        
        return True
    
    try:
        win32gui.EnumWindows(enum_windows_callback, None)
        return results
    except Exception:
        return []


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


def get_window_title(hwnd: int) -> Optional[str]:
    """
    获取窗口标题
    
    Args:
        hwnd: 窗口句柄
    
    Returns:
        str: 窗口标题，失败返回None
    """
    try:
        return win32gui.GetWindowText(hwnd)
    except Exception:
        return None


def is_window_minimized(hwnd: int) -> bool:
    """
    检查窗口是否最小化
    
    Args:
        hwnd: 窗口句柄
    
    Returns:
        bool: 是否最小化
    """
    try:
        return win32gui.IsIconic(hwnd)
    except Exception:
        return True


def restore_window(hwnd: int) -> bool:
    """
    恢复最小化的窗口
    
    Args:
        hwnd: 窗口句柄
    
    Returns:
        bool: 是否成功
    """
    try:
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        return True
    except Exception:
        return False


def capture_window(hwnd: int) -> Optional[Image.Image]:
    """
    后台截图 - 使用PrintWindow API
    
    Args:
        hwnd: 窗口句柄
    
    Returns:
        PIL.Image: 截图图像，失败返回None
    """
    if not hwnd:
        return None
    
    hwndDC = None
    mfcDC = None
    saveDC = None
    saveBitMap = None
    
    try:
        rect = win32gui.GetWindowRect(hwnd)
        left, top, right, bottom = rect
        width = right - left
        height = bottom - top
        
        if width <= 0 or height <= 0:
            return None
        
        hwndDC = win32gui.GetWindowDC(hwnd)
        if not hwndDC:
            return None
        
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        if not mfcDC:
            return None
        
        saveDC = mfcDC.CreateCompatibleDC()
        if not saveDC:
            return None
        
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)
        
        result = ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)
        if not result:
            return None
        
        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
        
        img = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1
        )
        
        return img
        
    except Exception:
        return None
    
    finally:
        try:
            if saveBitMap:
                win32gui.DeleteObject(saveBitMap.GetHandle())
        except Exception:
            pass
        
        try:
            if saveDC:
                saveDC.DeleteDC()
        except Exception:
            pass
        
        try:
            if mfcDC:
                mfcDC.DeleteDC()
        except Exception:
            pass
        
        try:
            if hwndDC:
                win32gui.ReleaseDC(hwnd, hwndDC)
        except Exception:
            pass


def capture_window_region(hwnd: int, region: tuple) -> Optional[Image.Image]:
    """
    后台截图指定区域
    
    Args:
        hwnd: 窗口句柄
        region: 区域坐标 (x1, y1, x2, y2)，窗口相对坐标
    
    Returns:
        PIL.Image: 区域截图，失败返回None
    """
    if not hwnd or not region:
        return None
    
    full_image = capture_window(hwnd)
    if full_image is None:
        return None
    
    try:
        x1, y1, x2, y2 = region
        
        x1 = max(0, int(x1))
        y1 = max(0, int(y1))
        x2 = min(full_image.width, int(x2))
        y2 = min(full_image.height, int(y2))
        
        if x2 <= x1 or y2 <= y1:
            return None
        
        return full_image.crop((x1, y1, x2, y2))
        
    except Exception:
        return None


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
