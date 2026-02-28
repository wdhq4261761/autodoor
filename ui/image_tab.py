import customtkinter as ctk
import tkinter as tk
from ui.theme import Theme
from ui.widgets import CardFrame, AnimatedButton, NumericEntry, create_divider
from PIL import Image as PILImage


def create_image_tab(app):
    """创建图像检测标签页"""
    page = ctk.CTkFrame(app.content_area, fg_color='transparent')
    app.pages['image'] = page
    
    top_frame = ctk.CTkFrame(page, fg_color='transparent')
    top_frame.pack(fill='x', pady=(0, 10))
    
    app.add_image_group_btn = AnimatedButton(top_frame, text='+ 新增检测组', font=Theme.get_font('sm'),
                                              height=28, corner_radius=6,
                                              fg_color=Theme.COLORS['primary'],
                                              hover_color=Theme.COLORS['primary_hover'],
                                              command=lambda: add_image_group(app))
    app.add_image_group_btn.pack(side='left')
    
    scroll_frame = ctk.CTkScrollableFrame(page)
    scroll_frame.pack(fill='both', expand=True)
    
    app.image_groups_frame = scroll_frame
    app.image_groups = []
    
    for i in range(2):
        create_image_group(app, i)


def create_image_group(app, index):
    """创建图像检测组"""
    enabled_var = tk.BooleanVar(value=False)
    
    group_vars = {
        "region_var": tk.StringVar(value="未选择区域"),
        "image_path_var": tk.StringVar(value="未选择图像"),
        "threshold_var": tk.StringVar(value="5"),
        "interval_var": tk.StringVar(value="5"),
        "pause_var": tk.StringVar(value="180"),
        "key_var": tk.StringVar(value="equal"),
        "delay_min_var": tk.StringVar(value="300"),
        "delay_max_var": tk.StringVar(value="500"),
        "alarm_var": tk.BooleanVar(value=False),
        "click_var": tk.BooleanVar(value=True)
    }
    
    group_frame = CardFrame(app.image_groups_frame, fg_color='#ffffff', border_width=1, border_color=Theme.COLORS['border'])
    group_frame.pack(fill='x', pady=(0, 10))
    
    header = ctk.CTkFrame(group_frame, fg_color='transparent')
    header.pack(fill='x', padx=10, pady=(4, 0))
    
    title_label = ctk.CTkLabel(header, text=f'检测组 {index + 1}', font=Theme.get_font('base'))
    title_label.pack(side='left')
    
    switch = ctk.CTkSwitch(header, text='', width=36, variable=enabled_var,
                           command=lambda: toggle_group_bg(group_frame, enabled_var.get()))
    switch.pack(side='left', padx=(8, 0))
    
    delete_btn = AnimatedButton(header, text='删除', font=Theme.get_font('xs'), width=50, height=22,
                                 fg_color=Theme.COLORS['error'], hover_color='#DC2626', corner_radius=4,
                                 command=lambda: delete_image_group(app, group_frame))
    delete_btn.pack(side='right')
    
    create_divider(group_frame)
    
    content_frame = ctk.CTkFrame(group_frame, fg_color='transparent')
    content_frame.pack(fill='x', padx=10, pady=0)
    
    # 左侧配置区域
    left_frame = ctk.CTkFrame(content_frame, fg_color='transparent')
    left_frame.pack(side='left', fill='x', expand=True)
    
    # 右侧预览区域（在空白区域中心）
    right_frame = ctk.CTkFrame(content_frame, fg_color='transparent')
    right_frame.pack(side='left', fill='both', expand=True)
    
    # 预览容器 - 居中显示
    preview_container = ctk.CTkFrame(right_frame, fg_color=Theme.COLORS['border'], corner_radius=6, width=140, height=70)
    preview_container.pack(padx=5, pady=5, expand=True)
    preview_container.pack_propagate(False)
    
    # 预览标签
    image_preview = ctk.CTkLabel(preview_container, text='预览', font=Theme.get_font('xs'),
                                  text_color=Theme.COLORS['text_muted'], width=136, height=66)
    image_preview.pack(padx=2, pady=2)
    
    row1 = ctk.CTkFrame(left_frame, fg_color='transparent')
    row1.pack(fill='x', pady=2)
    
    select_region_btn = AnimatedButton(row1, text='选择区域', font=Theme.get_font('xs'), width=60, height=24,
                                        corner_radius=4, fg_color=Theme.COLORS['primary'],
                                        hover_color=Theme.COLORS['primary_hover'],
                                        command=lambda: start_image_region_selection(app, index))
    select_region_btn.pack(side='left', padx=(0, 4))
    
    region_entry = ctk.CTkEntry(row1, textvariable=group_vars["region_var"], width=130, height=24, state='disabled')
    region_entry.pack(side='left', padx=(0, 8))
    
    select_image_btn = AnimatedButton(row1, text='选择图像', font=Theme.get_font('xs'), width=60, height=24,
                                       corner_radius=4, fg_color=Theme.COLORS['primary'],
                                       hover_color=Theme.COLORS['primary_hover'],
                                       command=lambda: select_reference_image(app, index))
    select_image_btn.pack(side='left', padx=(0, 4))
    
    image_path_entry = ctk.CTkEntry(row1, textvariable=group_vars["image_path_var"], width=100, height=24, state='disabled')
    image_path_entry.pack(side='left', padx=(0, 4))
    
    crop_image_btn = AnimatedButton(row1, text='截图', font=Theme.get_font('xs'), width=36, height=24,
                                     corner_radius=4, fg_color=Theme.COLORS['info'],
                                     hover_color=Theme.COLORS['info_hover'],
                                     command=lambda: crop_reference_image(app, index))
    crop_image_btn.pack(side='left', padx=(0, 8))
    
    ctk.CTkLabel(row1, text='匹配度:', font=Theme.get_font('xs')).pack(side='left')
    threshold_entry = NumericEntry(row1, textvariable=group_vars["threshold_var"], width=30, height=24)
    threshold_entry.pack(side='left', padx=(2, 0))
    
    row2 = ctk.CTkFrame(left_frame, fg_color='transparent')
    row2.pack(fill='x', pady=2)
    
    ctk.CTkLabel(row2, text='按键:', font=Theme.get_font('xs')).pack(side='left')
    key_entry = ctk.CTkEntry(row2, textvariable=group_vars["key_var"], width=50, height=24, state='disabled')
    key_entry.pack(side='left', padx=(2, 2))
    
    from utils.keyboard import start_key_listening
    key_btn = AnimatedButton(row2, text='修改', font=Theme.get_font('xs'), width=24, height=24, corner_radius=4,
                             fg_color=Theme.COLORS['primary'], hover_color=Theme.COLORS['primary_hover'])
    key_btn.configure(command=lambda: start_key_listening(app, key_entry, key_btn))
    key_btn.pack(side='left', padx=(0, 8))
    
    ctk.CTkLabel(row2, text='按键时长:', font=Theme.get_font('xs')).pack(side='left')
    delay_min_entry = NumericEntry(row2, textvariable=group_vars["delay_min_var"], width=45, height=24)
    delay_min_entry.pack(side='left', padx=(2, 2))
    ctk.CTkLabel(row2, text='-', font=Theme.get_font('xs')).pack(side='left')
    delay_max_entry = NumericEntry(row2, textvariable=group_vars["delay_max_var"], width=45, height=24)
    delay_max_entry.pack(side='left', padx=(2, 2))
    ctk.CTkLabel(row2, text='ms', font=Theme.get_font('xs')).pack(side='left', padx=(0, 8))
    
    alarm_frame = ctk.CTkFrame(row2, fg_color='transparent')
    alarm_frame.pack(side='left')
    ctk.CTkLabel(alarm_frame, text='报警', font=Theme.get_font('xs')).pack(side='left', padx=(0, 2))
    ctk.CTkSwitch(alarm_frame, text='', width=36, variable=group_vars["alarm_var"]).pack(side='left')
    
    row3 = ctk.CTkFrame(left_frame, fg_color='transparent')
    row3.pack(fill='x', pady=(2, 4))
    
    ctk.CTkLabel(row3, text='间隔:', font=Theme.get_font('xs')).pack(side='left')
    interval_entry = NumericEntry(row3, textvariable=group_vars["interval_var"], width=45, height=24)
    interval_entry.pack(side='left', padx=(2, 2))
    ctk.CTkLabel(row3, text='秒', font=Theme.get_font('xs')).pack(side='left', padx=(0, 8))
    
    ctk.CTkLabel(row3, text='暂停:', font=Theme.get_font('xs')).pack(side='left')
    pause_entry = NumericEntry(row3, textvariable=group_vars["pause_var"], width=45, height=24)
    pause_entry.pack(side='left', padx=(2, 2))
    ctk.CTkLabel(row3, text='秒', font=Theme.get_font('xs')).pack(side='left', padx=(0, 8))
    
    click_frame = ctk.CTkFrame(row3, fg_color='transparent')
    click_frame.pack(side='left')
    ctk.CTkLabel(click_frame, text='点击', font=Theme.get_font('xs')).pack(side='left', padx=(0, 2))
    ctk.CTkSwitch(click_frame, text='', width=36, variable=group_vars["click_var"]).pack(side='left')
    
    group_config = {
        "frame": group_frame,
        "enabled": enabled_var,
        "region_var": group_vars["region_var"],
        "region": None,
        "reference_image": None,
        "template_image": None,
        "image_path_var": group_vars["image_path_var"],
        "threshold": group_vars["threshold_var"],
        "interval": group_vars["interval_var"],
        "pause": group_vars["pause_var"],
        "key": group_vars["key_var"],
        "delay_min": group_vars["delay_min_var"],
        "delay_max": group_vars["delay_max_var"],
        "alarm": group_vars["alarm_var"],
        "click": group_vars["click_var"],
        "title_label": title_label,
        "image_preview": image_preview
    }
    app.image_groups.append(group_config)


def toggle_group_bg(frame, enabled):
    """切换组背景色"""
    if enabled:
        frame.configure(fg_color=Theme.COLORS['info_light'], border_color=Theme.COLORS['primary'])
    else:
        frame.configure(fg_color='#ffffff', border_color=Theme.COLORS['border'])


def add_image_group(app):
    """新增图像检测组"""
    if len(app.image_groups) >= 15:
        return
    create_image_group(app, len(app.image_groups))
    if hasattr(app, '_setup_image_group_listeners') and app.image_groups:
        app._setup_image_group_listeners(app.image_groups[-1])
    if hasattr(app, 'config_manager'):
        app.config_manager.defer_save_config()


def delete_image_group(app, group_frame, confirm=True):
    """删除图像检测组"""
    if confirm:
        from tkinter import messagebox
        if not messagebox.askyesno("确认删除", "确定要删除该检测组吗？"):
            return
    
    for i, group in enumerate(app.image_groups):
        if group["frame"] == group_frame:
            group["frame"].destroy()
            app.image_groups.pop(i)
            renumber_image_groups(app)
            break
    
    if hasattr(app, 'config_manager'):
        app.config_manager.defer_save_config()


def renumber_image_groups(app):
    """重新编号所有图像检测组"""
    for i, group in enumerate(app.image_groups):
        group["title_label"].configure(text=f'检测组 {i + 1}')


def start_image_region_selection(app, index):
    """开始选择图像检测区域"""
    from utils.region import _start_selection
    _start_selection(app, "image", index)


def update_image_preview(app, index, image_path):
    """更新图像预览"""
    if index >= len(app.image_groups):
        return
    
    group = app.image_groups[index]
    image_preview = group.get("image_preview")
    
    if not image_preview or not image_path:
        return
    
    try:
        import os
        if not os.path.exists(image_path):
            return
        
        image = PILImage.open(image_path)
        orig_w, orig_h = image.size
        
        max_w, max_h = 136, 66
        
        ratio = min(max_w / orig_w, max_h / orig_h)
        new_w = int(orig_w * ratio)
        new_h = int(orig_h * ratio)
        
        ctk_image = ctk.CTkImage(light_image=image, size=(new_w, new_h))
        image_preview.configure(image=ctk_image, text='')
        image_preview.image = ctk_image
    except Exception as e:
        app.logging_manager.log_message(f"更新图像预览失败: {str(e)}")


def select_reference_image(app, index):
    """选择参考图像"""
    from tkinter import filedialog, messagebox
    import os
    
    try:
        import cv2
        CV2_AVAILABLE = True
    except ImportError:
        CV2_AVAILABLE = False
    
    if not CV2_AVAILABLE:
        messagebox.showerror("错误", "OpenCV未安装，无法使用图像检测功能\n请运行: pip install opencv-python")
        return
    
    file_path = filedialog.askopenfilename(
        title="选择参考图像（模板）",
        filetypes=[
            ("图像文件", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"),
            ("所有文件", "*.*")
        ]
    )
    
    if file_path:
        if index < len(app.image_groups):
            group = app.image_groups[index]
            
            try:
                template = cv2.imread(file_path, cv2.IMREAD_COLOR)
                if template is None:
                    messagebox.showerror("错误", f"无法读取图像文件: {file_path}")
                    return
                
                group["template_image"] = template
                group["reference_image"] = file_path
                group["image_path_var"].set(os.path.basename(file_path))
                
                h, w = template.shape[:2]
                app.logging_manager.log_message(f"[图像检测] 检测组{index + 1}已加载模板: {file_path}")
                app.logging_manager.log_message(f"[图像检测] 模板尺寸: {w}x{h}")
                
                update_image_preview(app, index, file_path)
                
                if hasattr(app, 'config_manager'):
                    app.config_manager.defer_save_config()
            except Exception as e:
                app.logging_manager.log_message(f"[图像检测] 加载图像失败: {str(e)}")
                messagebox.showerror("错误", f"加载图像失败: {str(e)}")


def get_app_dir():
    """获取应用程序所在目录（兼容打包后路径）"""
    import sys
    import os
    
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def crop_reference_image(app, index):
    """截取屏幕区域作为参考图像"""
    from tkinter import messagebox
    
    try:
        import cv2
        CV2_AVAILABLE = True
    except ImportError:
        CV2_AVAILABLE = False
    
    if not CV2_AVAILABLE:
        messagebox.showerror("错误", "OpenCV未安装，无法使用图像裁剪功能\n请运行: pip install opencv-python")
        return
    
    if index >= len(app.image_groups):
        return
    
    app.logging_manager.log_message("[图像截图] 请在屏幕上选择要截取的区域...")
    
    app._crop_source_image = None
    app._crop_group_index = index
    
    from utils.region import _start_selection
    _start_selection(app, "crop", index)


def save_cropped_image(app, region):
    """保存截取的屏幕区域图像"""
    from tkinter import messagebox
    import os
    import time
    
    group_index = getattr(app, '_crop_group_index', None)
    
    if group_index is None:
        return
    
    try:
        import cv2
        import numpy as np
        from PIL import Image
        
        app_dir = get_app_dir()
        image_dir = os.path.join(app_dir, "image")
        
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
        
        app.root.update()
        import time as t
        t.sleep(0.1)
        
        from utils.screenshot import ScreenshotManager
        screenshot_manager = ScreenshotManager()
        screenshot = screenshot_manager.get_region_screenshot(region)
        
        if not screenshot:
            messagebox.showerror("错误", "无法获取截图区域")
            return
        
        crop_w, crop_h = screenshot.size
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        save_path = os.path.join(image_dir, filename)
        
        screenshot.save(save_path)
        
        template = cv2.imread(save_path, cv2.IMREAD_COLOR)
        if template is None:
            messagebox.showerror("错误", f"无法读取截图: {save_path}")
            return
        
        group = app.image_groups[group_index]
        group["template_image"] = template
        group["reference_image"] = save_path
        group["image_path_var"].set(os.path.basename(save_path))
        
        h, w = template.shape[:2]
        
        update_image_preview(app, group_index, save_path)
        
        if hasattr(app, 'config_manager'):
            app.config_manager.defer_save_config()
        
        messagebox.showinfo("成功", f"截图已保存到:\n{save_path}")
        
    except Exception as e:
        messagebox.showerror("错误", f"截图失败: {str(e)}")
    finally:
        app._crop_source_image = None
        app._crop_group_index = None
