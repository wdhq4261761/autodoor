import tkinter as tk
from tkinter import messagebox
import screeninfo


def _start_selection(app, selection_type, region_index):
    """
    通用的区域选择方法
    Args:
        app: 应用实例
        selection_type: 选择类型，"normal"、"number"、"ocr"、"image"或"crop"
        region_index: 识别区域索引，仅当selection_type为"number"、"ocr"、"image"或"crop"时有效
    """
    type_names = {
        "number": "数字识别区域",
        "ocr": "文字识别区域",
        "image": "图像检测区域",
        "crop": "图像裁剪区域"
    }
    app.logging_manager.log_message(f"开始{type_names.get(selection_type, '')}区域选择...")
    app.is_selecting = True
    app.selection_type = selection_type

    if selection_type == "number":
        app.current_number_region_index = region_index
    elif selection_type == "ocr":
        app.current_ocr_region_index = region_index
    elif selection_type == "image":
        app.current_image_region_index = region_index
    elif selection_type == "crop":
        app.current_image_region_index = region_index

    # 检查screeninfo库是否可用
    if screeninfo is None:
        messagebox.showerror("错误", "screeninfo库未安装，无法支持多显示器选择。请运行 'pip install screeninfo' 安装该库。")
        return

    # 获取虚拟屏幕的尺寸（包含所有显示器）
    monitors = screeninfo.get_monitors()

    # 计算整个虚拟屏幕的边界
    app.min_x = min(monitor.x for monitor in monitors)
    app.min_y = min(monitor.y for monitor in monitors)
    max_x = max(monitor.x + monitor.width for monitor in monitors)
    max_y = max(monitor.y + monitor.height for monitor in monitors)

    # 创建透明的区域选择窗口，覆盖整个虚拟屏幕
    app.select_window = tk.Toplevel(app.root)
    app.select_window.geometry(f"{max_x - app.min_x}x{max_y - app.min_y}+{app.min_x}+{app.min_y}")
    app.select_window.overrideredirect(True)  # 移除窗口装饰
    app.select_window.attributes("-alpha", 0.3)
    app.select_window.attributes("-topmost", True)

    # 创建画布用于绘制选择框
    app.canvas = tk.Canvas(app.select_window, cursor="cross", 
                           width=max_x - app.min_x, height=max_y - app.min_y)
    app.canvas.pack(fill=tk.BOTH, expand=True)

    # 绑定鼠标事件
    app.canvas.bind("<Button-1>", lambda event: on_mouse_down(app, event))
    app.canvas.bind("<B1-Motion>", lambda event: on_mouse_drag(app, event))

    # 根据选择类型绑定不同的鼠标释放事件
    if selection_type == "number":
        app.canvas.bind("<ButtonRelease-1>", lambda event: on_number_region_mouse_up(app, event))
    else:
        app.canvas.bind("<ButtonRelease-1>", lambda event: on_mouse_up(app, event))

    app.select_window.protocol("WM_DELETE_WINDOW", lambda: cancel_selection(app))

    app.select_window.bind("<Escape>", lambda e: cancel_selection(app))
    
    app.select_window.focus_set()

def on_mouse_down(app, event):
    """鼠标按下事件"""
    # 保存绝对坐标用于最终区域保存
    app.start_x_abs = event.x_root
    app.start_y_abs = event.y_root
    # 计算相对Canvas的坐标用于绘制
    app.start_x_rel = event.x_root - app.min_x
    app.start_y_rel = event.y_root - app.min_y
    app.rect = None


def on_mouse_drag(app, event):
    """鼠标拖动事件"""
    # 获取当前绝对坐标
    current_x_abs = event.x_root
    current_y_abs = event.y_root
    # 计算相对Canvas的坐标用于绘制
    current_x_rel = current_x_abs - app.min_x
    current_y_rel = current_y_abs - app.min_y

    if app.rect:
        app.canvas.delete(app.rect)

    # 使用相对坐标绘制选择框，确保视觉上与鼠标位置一致
    app.rect = app.canvas.create_rectangle(
        app.start_x_rel, app.start_y_rel, current_x_rel, current_y_rel,
        outline="red", width=2, fill="red"
    )


def _save_selection(app, start_x, start_y, end_x, end_y):
    """保存选择区域的公共方法"""
    # 确保选择区域有效
    if abs(end_x - start_x) < 10 or abs(end_y - start_y) < 10:
        messagebox.showwarning("警告", "选择的区域太小，请重新选择")
        cancel_selection(app)
        return None

    # 保存选择区域（使用绝对坐标）
    region = (
        min(start_x, end_x),
        min(start_y, end_y),
        max(start_x, end_x),
        max(start_y, end_y)
    )

    return region


def on_mouse_up(app, event):
    """
    鼠标释放事件
    """
    # 获取结束绝对坐标
    end_x_abs = event.x_root
    end_y_abs = event.y_root

    # 保存选择区域
    region = _save_selection(app, app.start_x_abs, app.start_y_abs, end_x_abs, end_y_abs)
    if region is None:
        return

    # 根据选择类型保存区域
    if hasattr(app, 'selection_type'):
        if app.selection_type == 'ocr':
            # OCR组区域选择
            if app.current_ocr_region_index is not None and 0 <= app.current_ocr_region_index < len(app.ocr_groups):
                app.ocr_groups[app.current_ocr_region_index]['region'] = region
                app.ocr_groups[app.current_ocr_region_index]['region_var'].set(f"{region[0]},{region[1]},{region[2]},{region[3]}")
                app.logging_manager.log_message(f"已为识别组{app.current_ocr_region_index+1}选择区域: {region}")
        elif app.selection_type == 'image':
            # 图像检测组区域选择
            if app.current_image_region_index is not None and 0 <= app.current_image_region_index < len(app.image_groups):
                app.image_groups[app.current_image_region_index]['region'] = region
                app.image_groups[app.current_image_region_index]['region_var'].set(f"{region[0]},{region[1]} - {region[2]},{region[3]}")
                app.logging_manager.log_message(f"已为检测组{app.current_image_region_index+1}选择区域: {region}")
        elif app.selection_type == 'crop':
            cancel_selection(app)
            from ui.image_tab import save_cropped_image
            save_cropped_image(app, region)
            return
        elif app.selection_type == 'color':
            if not hasattr(app, 'color_recognition_manager'):
                from modules.color import ColorRecognitionManager
                app.color_recognition_manager = ColorRecognitionManager(app)
            if not app.color_recognition_manager.color_recognition:
                from modules.color import ColorRecognition
                app.color_recognition_manager.color_recognition = ColorRecognition(app)
            app.color_recognition_manager.color_recognition.set_region(region)
            app.color_recognition_region = region
            if hasattr(app, 'region_var'):
                app.region_var.set(f"{region[0]},{region[1]},{region[2]},{region[3]}")
            app.logging_manager.log_message(f"已选择颜色识别区域: {region}")
        else:
            if hasattr(app, 'region_var'):
                app.region_var.set(f"{region[0]},{region[1]},{region[2]},{region[3]}")
            app.logging_manager.log_message(f"已选择区域: {region}")
    else:
        if hasattr(app, 'region_var'):
            app.region_var.set(f"{region[0]},{region[1]},{region[2]},{region[3]}")
        app.logging_manager.log_message(f"已选择区域: {region}")

    cancel_selection(app)

    if hasattr(app, 'config_manager') and app.config_manager:
        app.config_manager.defer_save_config()


def cancel_selection(app):
    """取消区域选择"""
    if app.is_selecting:
        app.logging_manager.log_message("已取消区域选择")
    app.is_selecting = False
    if hasattr(app, 'select_window') and app.select_window.winfo_exists():
        app.select_window.destroy()


def on_number_region_mouse_up(app, event):
    """数字识别区域鼠标释放事件"""
    # 获取结束绝对坐标
    end_x_abs = event.x_root
    end_y_abs = event.y_root

    # 保存选择区域
    region = _save_selection(app, app.start_x_abs, app.start_y_abs, end_x_abs, end_y_abs)
    if region is None:
        return

    # 更新界面
    region_index = app.current_number_region_index
    app.number_regions[region_index]["region"] = region
    app.number_regions[region_index]["region_var"].set(f"{region[0]},{region[1]},{region[2]},{region[3]}")
    app.logging_manager.log_message(f"已选择数字识别区域{region_index+1}: {region}")
    cancel_selection(app)

    if hasattr(app, 'save_config') and callable(app.save_config):
        try:
            app.save_config()
        except Exception:
            pass
