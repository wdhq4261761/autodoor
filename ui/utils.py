import tkinter as tk
from ui.theme import Theme
from tkinter import messagebox
import os
import time

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False


def update_group_style(group_frame, enabled):
    """更新组的样式"""
    if enabled:
        group_frame.configure(fg_color=Theme.COLORS['info_light'], 
                            border_color=Theme.COLORS['primary'])
    else:
        group_frame.configure(fg_color='#ffffff', 
                            border_color=Theme.COLORS['border'])


def toggle_group_bg(frame, enabled):
    """切换组背景色（update_group_style 的别名）"""
    update_group_style(frame, enabled)


def add_group(app, groups, create_func, listener_setup_func=None, max_count=15):
    """通用新增组方法
    
    Args:
        app: 主应用实例
        groups: 组列表（如 app.ocr_groups）
        create_func: 创建组的函数（如 lambda idx: create_ocr_group(app, idx)）
        listener_setup_func: 设置监听器的函数（可选）
        max_count: 最大允许数量，默认 15
    
    Returns:
        bool: 是否成功创建
    """
    if len(groups) >= max_count:
        messagebox.showwarning("警告", f"最多只能创建{max_count}个组！")
        return False
    
    create_func(len(groups))
    
    if listener_setup_func and groups:
        listener_setup_func(groups[-1])
    
    if hasattr(app, 'config_manager'):
        app.config_manager.defer_save_config()
    
    return True


def delete_group(app, groups, group_frame, renumber_func, confirm=True, confirm_message="确定要删除该组吗？"):
    """通用删除组方法
    
    Args:
        app: 主应用实例
        groups: 组列表（如 app.ocr_groups）
        group_frame: 要删除的组框架
        renumber_func: 重新编号函数（如 lambda: renumber_ocr_groups(app)）
        confirm: 是否显示确认对话框
        confirm_message: 确认消息
    
    Returns:
        bool: 是否成功删除
    """
    if confirm:
        if not messagebox.askyesno("确认删除", confirm_message):
            return False
    
    for i, group in enumerate(groups):
        if group["frame"] == group_frame:
            group["frame"].destroy()
            groups.pop(i)
            renumber_func()
            
            if hasattr(app, 'config_manager'):
                app.config_manager.defer_save_config()
            
            return True
    
    return False


def create_color_picker(app, callback, log_func=None):
    """
    创建颜色选择器
    
    创建一个全屏透明的选择窗口，用户点击任意位置获取该位置的颜色值。
    
    Args:
        app: 应用实例（需要有 root 属性）
        callback: 回调函数，参数为 (r, g, b) 元组
        log_func: 日志函数（可选）
    
    Returns:
        None
    """
    try:
        import screeninfo
        monitors = screeninfo.get_monitors()
        min_x = min(monitor.x for monitor in monitors)
        min_y = min(monitor.y for monitor in monitors)
        max_x = max(monitor.x + monitor.width for monitor in monitors)
        max_y = max(monitor.y + monitor.height for monitor in monitors)
    except ImportError:
        messagebox.showerror("错误", "screeninfo库未安装，无法支持多显示器选择。\n请运行 'pip install screeninfo' 安装该库。")
        return
    except Exception:
        min_x, min_y, max_x, max_y = 0, 0, 1920, 1080
    
    selection_window = tk.Toplevel(app.root)
    selection_window.overrideredirect(True)
    selection_window.geometry(f"{max_x - min_x}x{max_y - min_y}+{min_x}+{min_y}")
    selection_window.attributes("-alpha", 0.3)
    selection_window.attributes("-topmost", True)
    selection_window.configure(cursor="crosshair")
    
    canvas = tk.Canvas(selection_window, bg="white", highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)
    
    def on_click(event):
        selection_window.withdraw()
        selection_window.update()
        
        abs_x, abs_y = event.x_root, event.y_root
        
        try:
            from utils.screenshot import ScreenshotManager
            screen = ScreenshotManager().get_full_screenshot()
        except Exception:
            from PIL import ImageGrab
            screen = ImageGrab.grab(all_screens=True)
        
        try:
            import screeninfo
            monitors = screeninfo.get_monitors()
            offset_x = min(monitor.x for monitor in monitors)
            offset_y = min(monitor.y for monitor in monitors)
        except:
            offset_x, offset_y = 0, 0
        
        rel_x = abs_x - offset_x
        rel_y = abs_y - offset_y
        
        pixel = screen.getpixel((rel_x, rel_y))
        r, g, b = pixel[:3]
        
        selection_window.destroy()
        
        if log_func:
            log_func(f"选择颜色: RGB({r}, {g}, {b})")
            log_func(f"选择位置: ({abs_x}, {abs_y})")
        
        callback((r, g, b))
    
    def on_escape(e):
        if log_func:
            log_func("已取消颜色选择")
        selection_window.destroy()
    
    canvas.bind("<Button-1>", on_click)
    selection_window.bind("<Escape>", on_escape)
    selection_window.focus_set()


def get_app_dir():
    """获取应用程序所在目录（兼容打包后路径）"""
    import sys
    
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def update_image_preview(image_preview, preview_container, image_path):
    """
    更新图像预览
    
    Args:
        image_preview: CTkLabel 预览控件
        preview_container: 预览容器控件
        image_path: 图像文件路径
    
    Returns:
        bool: 是否成功更新
    """
    if not image_preview or not image_path:
        return False
    
    try:
        if not os.path.exists(image_path):
            return False
        
        from PIL import Image as PILImage
        image = PILImage.open(image_path)
        orig_w, orig_h = image.size
        
        if preview_container:
            preview_container.update_idletasks()
            max_w = preview_container.winfo_width() - 4
            max_h = preview_container.winfo_height() - 4
            if max_w < 50:
                max_w = 140
            if max_h < 30:
                max_h = 70
        else:
            max_w, max_h = 140, 70
        
        ratio = min(max_w / orig_w, max_h / orig_h)
        new_w = int(orig_w * ratio)
        new_h = int(orig_h * ratio)
        
        if CTK_AVAILABLE:
            ctk_image = ctk.CTkImage(light_image=image, size=(new_w, new_h))
            image_preview.configure(image=ctk_image, text='')
            image_preview.image = ctk_image
        
        return True
        
    except Exception:
        return False


def select_template_image(app, groups, index, log_prefix="", log_func=None):
    """
    选择模板图像（通用）
    
    Args:
        app: 应用实例
        groups: 组列表
        index: 组索引
        log_prefix: 日志前缀（如 "检测组" 或 "监控组"）
        log_func: 日志函数
    
    Returns:
        tuple: (success, template, file_path) 或 None
    """
    if not CV2_AVAILABLE:
        messagebox.showerror("错误", "OpenCV未安装，无法使用图像检测功能\n请运行: pip install opencv-python")
        return None
    
    from tkinter import filedialog
    
    file_path = filedialog.askopenfilename(
        title="选择模板图像",
        filetypes=[
            ("图像文件", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"),
            ("所有文件", "*.*")
        ]
    )
    
    if not file_path:
        return None
    
    if index < 0 or index >= len(groups):
        return None
    
    group = groups[index]
    
    try:
        template = cv2.imread(file_path, cv2.IMREAD_COLOR)
        if template is None:
            messagebox.showerror("错误", f"无法读取图像文件: {file_path}")
            return None
        
        group["template_image"] = template
        group["reference_image"] = file_path
        if "image_path_var" in group:
            group["image_path_var"].set(os.path.basename(file_path))
        
        h, w = template.shape[:2]
        
        if log_func:
            log_func(f"{log_prefix}{index + 1}已加载模板: {file_path}")
            log_func(f"{log_prefix}{index + 1}模板尺寸: {w}x{h}")
        
        if "image_preview" in group:
            update_image_preview(group["image_preview"], group.get("preview_container"), file_path)
        
        if hasattr(app, 'config_manager') and app.config_manager:
            app.config_manager.defer_save_config()
        
        return (True, template, file_path)
        
    except Exception as e:
        if log_func:
            log_func(f"{log_prefix}{index + 1}加载图像失败: {str(e)}")
        messagebox.showerror("错误", f"加载图像失败: {str(e)}")
        return None


def save_cropped_template(app, region, groups, index, log_prefix="", log_func=None):
    """
    保存截图作为模板（通用）
    
    Args:
        app: 应用实例
        region: 截图区域
        groups: 组列表
        index: 组索引
        log_prefix: 日志前缀
        log_func: 日志函数
    
    Returns:
        tuple: (success, template, file_path) 或 None
    """
    if not CV2_AVAILABLE:
        messagebox.showerror("错误", "OpenCV未安装，无法使用图像裁剪功能\n请运行: pip install opencv-python")
        return None
    
    if index is None or index < 0 or index >= len(groups):
        return None
    
    try:
        app_dir = get_app_dir()
        image_dir = os.path.join(app_dir, "image")
        
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
        
        app.root.update()
        time.sleep(0.1)
        
        from utils.screenshot import ScreenshotManager
        screenshot = ScreenshotManager().get_region_screenshot(region)
        
        if not screenshot:
            messagebox.showerror("错误", "无法获取截图区域")
            return None
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        save_path = os.path.join(image_dir, filename)
        
        screenshot.save(save_path)
        
        template = cv2.imread(save_path, cv2.IMREAD_COLOR)
        if template is None:
            messagebox.showerror("错误", f"无法读取截图: {save_path}")
            return None
        
        group = groups[index]
        group["template_image"] = template
        group["reference_image"] = save_path
        if "image_path_var" in group:
            group["image_path_var"].set(os.path.basename(save_path))
        
        if "image_preview" in group:
            update_image_preview(group["image_preview"], group.get("preview_container"), save_path)
        
        if hasattr(app, 'config_manager'):
            app.config_manager.defer_save_config()
        
        if log_func:
            log_func(f"{log_prefix}{index + 1}截图已保存: {save_path}")
        
        messagebox.showinfo("成功", f"截图已保存到:\n{save_path}")
        
        return (True, template, save_path)
        
    except Exception as e:
        if log_func:
            log_func(f"{log_prefix}{index + 1}截图失败: {str(e)}")
        messagebox.showerror("错误", f"截图失败: {str(e)}")
        return None
