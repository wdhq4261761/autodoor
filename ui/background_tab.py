import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading

from ui.theme import Theme
from ui.widgets import CardFrame, AnimatedButton, NumericEntry, create_divider
from ui.utils import toggle_group_bg
from PIL import Image as PILImage


def create_background_tab(app):
    page = ctk.CTkFrame(app.content_area, fg_color='transparent')
    app.pages['background'] = page
    
    window_frame = CardFrame(page, fg_color='#ffffff', border_width=1, border_color=Theme.COLORS['border'])
    window_frame.pack(fill='x', pady=(0, 10), padx=5)
    
    window_header = ctk.CTkFrame(window_frame, fg_color='transparent')
    window_header.pack(fill='x', padx=10, pady=(8, 4))
    
    ctk.CTkLabel(window_header, text='目标窗口', font=Theme.get_font('base')).pack(side='left')
    
    window_content = ctk.CTkFrame(window_frame, fg_color='transparent')
    window_content.pack(fill='x', padx=10, pady=(4, 8))
    
    window_left = ctk.CTkFrame(window_content, fg_color='transparent')
    window_left.pack(side='left', fill='x', expand=True)
    
    window_row = ctk.CTkFrame(window_left, fg_color='transparent')
    window_row.pack(fill='x')
    
    ctk.CTkLabel(window_row, text='标题关键字:', font=Theme.get_font('xs')).pack(side='left')
    
    app.bg_window_title_var = tk.StringVar(value="")
    title_entry = ctk.CTkEntry(window_row, textvariable=app.bg_window_title_var, width=150, height=24)
    title_entry.pack(side='left', padx=(4, 8))
    
    find_btn = AnimatedButton(window_row, text='查找窗口', font=Theme.get_font('xs'), width=60, height=24,
                              corner_radius=4, fg_color=Theme.COLORS['primary'],
                              hover_color=Theme.COLORS['primary_hover'],
                              command=lambda: find_target_window(app))
    find_btn.pack(side='left', padx=(0, 8))
    
    app.bg_window_status_var = tk.StringVar(value="未绑定")
    status_label = ctk.CTkLabel(window_row, textvariable=app.bg_window_status_var, font=Theme.get_font('xs'),
                                text_color=Theme.COLORS['text_secondary'], width=150, anchor='w')
    status_label.pack(side='left')
    
    window_preview_frame = ctk.CTkFrame(window_content, fg_color=Theme.COLORS['border'], corner_radius=6, width=200, height=120)
    window_preview_frame.pack(side='left', padx=(10, 0))
    window_preview_frame.pack_propagate(False)
    
    app.bg_window_preview = ctk.CTkLabel(window_preview_frame, text='窗口预览', font=Theme.get_font('xs'),
                                          text_color=Theme.COLORS['text_muted'], width=196, height=116)
    app.bg_window_preview.pack(padx=2, pady=2)
    app.bg_window_preview_image = None
    
    top_frame = ctk.CTkFrame(page, fg_color='transparent')
    top_frame.pack(fill='x', pady=(0, 10))
    
    app.add_bg_ocr_btn = AnimatedButton(top_frame, text='+ 新增文字监控组', font=Theme.get_font('sm'),
                                        height=28, corner_radius=6,
                                        fg_color=Theme.COLORS['primary'],
                                        hover_color=Theme.COLORS['primary_hover'],
                                        command=lambda: add_background_group(app, "ocr"))
    app.add_bg_ocr_btn.pack(side='left', padx=(0, 4))
    
    app.add_bg_image_btn = AnimatedButton(top_frame, text='+ 新增图像监控组', font=Theme.get_font('sm'),
                                          height=28, corner_radius=6,
                                          fg_color=Theme.COLORS['primary'],
                                          hover_color=Theme.COLORS['primary_hover'],
                                          command=lambda: add_background_group(app, "image"))
    app.add_bg_image_btn.pack(side='left', padx=(0, 4))
    
    app.add_bg_color_btn = AnimatedButton(top_frame, text='+ 新增颜色监控组', font=Theme.get_font('sm'),
                                          height=28, corner_radius=6,
                                          fg_color=Theme.COLORS['primary'],
                                          hover_color=Theme.COLORS['primary_hover'],
                                          command=lambda: add_background_group(app, "color"))
    app.add_bg_color_btn.pack(side='left')
    
    scroll_frame = ctk.CTkScrollableFrame(page)
    scroll_frame.pack(fill='both', expand=True)
    
    app.bg_groups_frame = scroll_frame
    
    if not hasattr(app, 'background_groups'):
        app.background_groups = []
    
    if not hasattr(app, 'bg_group_counter'):
        app.bg_group_counter = 0


def create_background_group(app, index, monitor_type="ocr"):
    """
    创建后台监控组
    
    Args:
        app: 应用实例
        index: 显示编号（1-based）
        monitor_type: 监控类型
    """
    array_index = index - 1  # 转换为数组索引
    
    enabled_var = tk.BooleanVar(value=False)
    
    type_names = {
        "ocr": "文字",
        "image": "图像",
        "color": "颜色"
    }
    type_name = type_names.get(monitor_type, "文字")
    
    group_vars = {
        "region_var": tk.StringVar(value="未选择区域"),
        "interval_var": tk.StringVar(value="5"),
        "pause_var": tk.StringVar(value="180"),
        "key_var": tk.StringVar(value=""),
        "delay_min_var": tk.StringVar(value="100"),
        "delay_max_var": tk.StringVar(value="200"),
        "click_enabled_var": tk.BooleanVar(value=False),
        "alarm_var": tk.BooleanVar(value=False),
        "image_path_var": tk.StringVar(value="未选择"),
        "threshold_var": tk.StringVar(value="80"),
        "keywords_var": tk.StringVar(value=""),
        "language_var": tk.StringVar(value="eng"),
        "tolerance_var": tk.StringVar(value="10"),
        "color_var": tk.StringVar(value="未选择")
    }
    
    group_frame = CardFrame(app.bg_groups_frame, fg_color='#ffffff', border_width=1, border_color=Theme.COLORS['border'])
    group_frame.pack(fill='x', pady=(0, 10))
    
    header = ctk.CTkFrame(group_frame, fg_color='transparent')
    header.pack(fill='x', padx=10, pady=(6, 2))
    
    title_label = ctk.CTkLabel(header, text=f'监控组{index} - {type_name}', font=Theme.get_font('base'))
    title_label.pack(side='left')
    
    switch = ctk.CTkSwitch(header, text='', width=36, variable=enabled_var,
                          command=lambda: toggle_group_bg(group_frame, enabled_var.get()))
    switch.pack(side='left', padx=(8, 0))
    
    delete_btn = AnimatedButton(header, text='删除', font=Theme.get_font('xs'), width=50, height=22,
                               fg_color=Theme.COLORS['error'], hover_color='#DC2626', corner_radius=4,
                               command=lambda: delete_background_group(app, group_frame))
    delete_btn.pack(side='right')
    
    create_divider(group_frame)
    
    if monitor_type == "image":
        content_frame = ctk.CTkFrame(group_frame, fg_color='transparent')
        content_frame.pack(fill='x', padx=10, pady=0)
        
        left_frame = ctk.CTkFrame(content_frame, fg_color='transparent')
        left_frame.pack(side='left', fill='x', expand=True)
        
        right_frame = ctk.CTkFrame(content_frame, fg_color='transparent')
        right_frame.pack(side='left', fill='both', expand=True)
        
        preview_container = ctk.CTkFrame(right_frame, fg_color=Theme.COLORS['border'], corner_radius=6)
        preview_container.pack(padx=5, pady=(2, 5), fill='both', expand=True)
        
        image_preview = ctk.CTkLabel(preview_container, text='预览', font=Theme.get_font('xs'),
                                      text_color=Theme.COLORS['text_muted'])
        image_preview.pack(padx=2, pady=2, fill='both', expand=True)
        
        row1 = ctk.CTkFrame(left_frame, fg_color='transparent')
        row1.pack(fill='x', pady=2)
        
        row2 = ctk.CTkFrame(left_frame, fg_color='transparent')
        row2.pack(fill='x', pady=2)
        
        select_btn = AnimatedButton(row1, text='选择区域', font=Theme.get_font('xs'), width=60, height=24,
                                   corner_radius=4, fg_color=Theme.COLORS['primary'],
                                   hover_color=Theme.COLORS['primary_hover'],
                                   command=lambda: start_bg_region_selection(app, array_index))
        select_btn.pack(side='left', padx=(0, 4))
        
        region_entry = ctk.CTkEntry(row1, textvariable=group_vars["region_var"], width=130, height=24, state='disabled')
        region_entry.pack(side='left', padx=(0, 8))
        
        ctk.CTkLabel(row1, text='按键:', font=Theme.get_font('xs')).pack(side='left')
        key_entry = ctk.CTkEntry(row1, textvariable=group_vars["key_var"], width=50, height=24, state='disabled')
        key_entry.pack(side='left', padx=(2, 2))
        
        from utils.keyboard import start_key_listening
        key_btn = AnimatedButton(row1, text='修改', font=Theme.get_font('xs'), width=24, height=24, corner_radius=4,
                                fg_color=Theme.COLORS['primary'], hover_color=Theme.COLORS['primary_hover'])
        key_btn.configure(command=lambda: start_key_listening(app, key_entry, key_btn))
        key_btn.pack(side='left', padx=(0, 8))
        
        ctk.CTkLabel(row1, text='按键时长:', font=Theme.get_font('xs')).pack(side='left')
        delay_min_entry = NumericEntry(row1, textvariable=group_vars["delay_min_var"], width=45, height=24)
        delay_min_entry.pack(side='left', padx=(2, 2))
        ctk.CTkLabel(row1, text='-', font=Theme.get_font('xs')).pack(side='left')
        delay_max_entry = NumericEntry(row1, textvariable=group_vars["delay_max_var"], width=45, height=24)
        delay_max_entry.pack(side='left', padx=(2, 2))
        ctk.CTkLabel(row1, text='ms', font=Theme.get_font('xs')).pack(side='left', padx=(0, 8))
        
        alarm_frame = ctk.CTkFrame(row1, fg_color='transparent')
        alarm_frame.pack(side='left')
        ctk.CTkLabel(alarm_frame, text='报警', font=Theme.get_font('xs')).pack(side='left', padx=(0, 2))
        ctk.CTkSwitch(alarm_frame, text='', width=36, variable=group_vars["alarm_var"]).pack(side='left')
        
        ctk.CTkLabel(row2, text='间隔:', font=Theme.get_font('xs')).pack(side='left')
        interval_entry = NumericEntry(row2, textvariable=group_vars["interval_var"], width=45, height=24)
        interval_entry.pack(side='left', padx=(2, 2))
        ctk.CTkLabel(row2, text='秒', font=Theme.get_font('xs')).pack(side='left', padx=(0, 8))
        
        ctk.CTkLabel(row2, text='暂停:', font=Theme.get_font('xs')).pack(side='left')
        pause_entry = NumericEntry(row2, textvariable=group_vars["pause_var"], width=45, height=24)
        pause_entry.pack(side='left', padx=(2, 2))
        ctk.CTkLabel(row2, text='秒', font=Theme.get_font('xs')).pack(side='left', padx=(0, 8))
        
        select_image_btn = AnimatedButton(row2, text='选择图像', font=Theme.get_font('xs'), width=60, height=24,
                                          corner_radius=4, fg_color=Theme.COLORS['primary'],
                                          hover_color=Theme.COLORS['primary_hover'],
                                          command=lambda: select_bg_template_image(app, array_index))
        select_image_btn.pack(side='left', padx=(0, 4))
        
        image_path_entry = ctk.CTkEntry(row2, textvariable=group_vars["image_path_var"], width=80, height=24, state='disabled')
        image_path_entry.pack(side='left', padx=(0, 4))
        
        crop_image_btn = AnimatedButton(row2, text='截图', font=Theme.get_font('xs'), width=36, height=24,
                                        corner_radius=4, fg_color=Theme.COLORS['info'],
                                        hover_color=Theme.COLORS['info_hover'],
                                        command=lambda: crop_bg_template_image(app, array_index))
        crop_image_btn.pack(side='left', padx=(0, 8))
        
        ctk.CTkLabel(row2, text='阈值:', font=Theme.get_font('xs')).pack(side='left')
        threshold_entry = NumericEntry(row2, textvariable=group_vars["threshold_var"], width=40, height=24)
        threshold_entry.pack(side='left', padx=(2, 2))
        ctk.CTkLabel(row2, text='%', font=Theme.get_font('xs')).pack(side='left')
        
        click_frame = ctk.CTkFrame(row2, fg_color='transparent')
        click_frame.pack(side='left')
        ctk.CTkLabel(click_frame, text='点击', font=Theme.get_font('xs')).pack(side='left', padx=(0, 2))
        ctk.CTkSwitch(click_frame, text='', width=36, variable=group_vars["click_enabled_var"]).pack(side='left')
        
        group_config = {
            "frame": group_frame,
            "index": index,
            "type": monitor_type,
            "enabled": enabled_var,
            "region_var": group_vars["region_var"],
            "region": None,
            "region_ratio": None,
            "interval": group_vars["interval_var"],
            "pause": group_vars["pause_var"],
            "key": group_vars["key_var"],
            "delay_min": group_vars["delay_min_var"],
            "delay_max": group_vars["delay_max_var"],
            "click_enabled": group_vars["click_enabled_var"],
            "alarm": group_vars["alarm_var"],
            "title_label": title_label,
            "template_image": None,
            "reference_image": "",
            "image_path_var": group_vars["image_path_var"],
            "threshold": group_vars["threshold_var"],
            "image_preview": image_preview,
            "preview_container": preview_container
        }
        
    else:
        row1 = ctk.CTkFrame(group_frame, fg_color='transparent')
        row1.pack(fill='x', padx=10, pady=4)
        
        select_btn = AnimatedButton(row1, text='选择区域', font=Theme.get_font('xs'), width=60, height=24,
                                   corner_radius=4, fg_color=Theme.COLORS['primary'],
                                   hover_color=Theme.COLORS['primary_hover'],
                                   command=lambda: start_bg_region_selection(app, array_index))
        select_btn.pack(side='left', padx=(0, 4))
        
        region_entry = ctk.CTkEntry(row1, textvariable=group_vars["region_var"], width=130, height=24, state='disabled')
        region_entry.pack(side='left', padx=(0, 8))
        
        ctk.CTkLabel(row1, text='按键:', font=Theme.get_font('xs')).pack(side='left')
        key_entry = ctk.CTkEntry(row1, textvariable=group_vars["key_var"], width=50, height=24, state='disabled')
        key_entry.pack(side='left', padx=(2, 2))
        
        from utils.keyboard import start_key_listening
        key_btn = AnimatedButton(row1, text='修改', font=Theme.get_font('xs'), width=24, height=24, corner_radius=4,
                                fg_color=Theme.COLORS['primary'], hover_color=Theme.COLORS['primary_hover'])
        key_btn.configure(command=lambda: start_key_listening(app, key_entry, key_btn))
        key_btn.pack(side='left', padx=(0, 8))
        
        ctk.CTkLabel(row1, text='按键时长:', font=Theme.get_font('xs')).pack(side='left')
        delay_min_entry = NumericEntry(row1, textvariable=group_vars["delay_min_var"], width=45, height=24)
        delay_min_entry.pack(side='left', padx=(2, 2))
        ctk.CTkLabel(row1, text='-', font=Theme.get_font('xs')).pack(side='left')
        delay_max_entry = NumericEntry(row1, textvariable=group_vars["delay_max_var"], width=45, height=24)
        delay_max_entry.pack(side='left', padx=(2, 2))
        ctk.CTkLabel(row1, text='ms', font=Theme.get_font('xs')).pack(side='left', padx=(0, 8))
        
        alarm_frame = ctk.CTkFrame(row1, fg_color='transparent')
        alarm_frame.pack(side='left')
        ctk.CTkLabel(alarm_frame, text='报警', font=Theme.get_font('xs')).pack(side='left', padx=(0, 2))
        ctk.CTkSwitch(alarm_frame, text='', width=36, variable=group_vars["alarm_var"]).pack(side='left')
        
        row2 = ctk.CTkFrame(group_frame, fg_color='transparent')
        row2.pack(fill='x', padx=10, pady=(2, 6))
        
        ctk.CTkLabel(row2, text='间隔:', font=Theme.get_font('xs')).pack(side='left')
        interval_entry = NumericEntry(row2, textvariable=group_vars["interval_var"], width=45, height=24)
        interval_entry.pack(side='left', padx=(2, 2))
        ctk.CTkLabel(row2, text='秒', font=Theme.get_font('xs')).pack(side='left', padx=(0, 8))
        
        ctk.CTkLabel(row2, text='暂停:', font=Theme.get_font('xs')).pack(side='left')
        pause_entry = NumericEntry(row2, textvariable=group_vars["pause_var"], width=45, height=24)
        pause_entry.pack(side='left', padx=(2, 2))
        ctk.CTkLabel(row2, text='秒', font=Theme.get_font('xs')).pack(side='left', padx=(0, 8))
        
        if monitor_type == "ocr":
            ctk.CTkLabel(row2, text='关键词:', font=Theme.get_font('xs')).pack(side='left')
            keywords_entry = ctk.CTkEntry(row2, textvariable=group_vars["keywords_var"], width=80, height=24)
            keywords_entry.pack(side='left', padx=(2, 8))
            
            ctk.CTkLabel(row2, text='语言:', font=Theme.get_font('xs')).pack(side='left', padx=(0, 2))
            from ui.widgets import create_bordered_option_menu
            create_bordered_option_menu(row2, values=['eng', 'chi_sim', 'chi_tra'],
                                        variable=group_vars["language_var"], width=70, height=24)
        
        elif monitor_type == "color":
            color_btn = AnimatedButton(row2, text='选取颜色', font=Theme.get_font('xs'), width=60, height=24,
                                       corner_radius=4, fg_color=Theme.COLORS['primary'],
                                       hover_color=Theme.COLORS['primary_hover'],
                                       command=lambda: start_bg_color_selection(app, array_index))
            color_btn.pack(side='left', padx=(0, 4))
            
            color_display = ctk.CTkLabel(row2, textvariable=group_vars["color_var"], width=80, height=24,
                                         fg_color='gray', corner_radius=4)
            color_display.pack(side='left', padx=(0, 8))
            
            ctk.CTkLabel(row2, text='容差:', font=Theme.get_font('xs')).pack(side='left')
            tolerance_entry = NumericEntry(row2, textvariable=group_vars["tolerance_var"], width=40, height=24)
            tolerance_entry.pack(side='left', padx=(2, 8))
        
        click_frame = ctk.CTkFrame(row2, fg_color='transparent')
        click_frame.pack(side='left')
        ctk.CTkLabel(click_frame, text='点击', font=Theme.get_font('xs')).pack(side='left', padx=(0, 2))
        ctk.CTkSwitch(click_frame, text='', width=36, variable=group_vars["click_enabled_var"]).pack(side='left')
        
        group_config = {
            "frame": group_frame,
            "index": index,
            "type": monitor_type,
            "enabled": enabled_var,
            "region_var": group_vars["region_var"],
            "region": None,
            "region_ratio": None,
            "interval": group_vars["interval_var"],
            "pause": group_vars["pause_var"],
            "key": group_vars["key_var"],
            "delay_min": group_vars["delay_min_var"],
            "delay_max": group_vars["delay_max_var"],
            "click_enabled": group_vars["click_enabled_var"],
            "alarm": group_vars["alarm_var"],
            "title_label": title_label
        }
        
        if monitor_type == "ocr":
            group_config.update({
                "keywords": group_vars["keywords_var"],
                "language": group_vars["language_var"]
            })
        elif monitor_type == "color":
            group_config.update({
                "target_color": None,
                "color_var": group_vars["color_var"],
                "color_display": color_display,
                "tolerance": group_vars["tolerance_var"]
            })
    
    app.background_groups.append(group_config)


def add_background_group(app, monitor_type="ocr"):
    if not hasattr(app, 'bg_group_counter'):
        app.bg_group_counter = 0
    
    if app.bg_group_counter >= 15:
        messagebox.showwarning("警告", "监控组数量已达上限（15个）")
        return
    
    app.bg_group_counter += 1
    index = app.bg_group_counter
    
    create_background_group(app, index, monitor_type)
    
    if app.background_groups:
        listener_setup_func = getattr(app, '_setup_background_group_listeners', None)
        if listener_setup_func:
            listener_setup_func(app.background_groups[-1])
    
    if hasattr(app, 'config_manager') and app.config_manager:
        app.config_manager.defer_save_config()


def delete_background_group(app, group_frame, confirm=True):
    if confirm:
        if not messagebox.askyesno("确认", "确定要删除该监控组吗？"):
            return
    
    for i, group in enumerate(app.background_groups):
        if group["frame"] == group_frame:
            group_frame.destroy()
            app.background_groups.pop(i)
            renumber_background_groups(app)
            break
    
    if hasattr(app, 'config_manager') and app.config_manager:
        app.config_manager.defer_save_config()


def renumber_background_groups(app):
    for i, group in enumerate(app.background_groups):
        new_index = i + 1
        group["index"] = new_index
        type_names = {
            "ocr": "文字",
            "image": "图像",
            "color": "颜色"
        }
        type_name = type_names.get(group.get("type", "ocr"), "文字")
        group["title_label"].configure(text=f'监控组{new_index} - {type_name}')


def find_target_window(app):
    keyword = app.bg_window_title_var.get().strip()
    if not keyword:
        messagebox.showwarning("警告", "请输入窗口标题关键字")
        return
    
    from utils.window_capture import find_all_windows_by_title
    
    windows = find_all_windows_by_title(keyword)
    
    if not windows:
        app.bg_window_status_var.set("未找到窗口")
        messagebox.showwarning("警告", f"未找到标题包含 '{keyword}' 的窗口")
        return
    
    if len(windows) == 1:
        hwnd, title = windows[0]
        select_window(app, hwnd, title)
    else:
        select_window_from_list(app, windows)


def select_window_from_list(app, windows):
    dialog = tk.Toplevel(app.root)
    dialog.title("选择目标窗口")
    dialog.transient(app.root)
    dialog.grab_set()
    
    window_width = 400
    window_height = 300
    
    app.root.update_idletasks()
    app.root.update()
    
    root_x = app.root.winfo_rootx()
    root_y = app.root.winfo_rooty()
    root_width = app.root.winfo_width()
    root_height = app.root.winfo_height()
    
    if root_width < 100 or root_height < 100:
        root_width = 1050
        root_height = 700
        root_x = (dialog.winfo_screenwidth() - root_width) // 2
        root_y = (dialog.winfo_screenheight() - root_height) // 2
    
    pos_x = root_x + (root_width // 2) - (window_width // 2)
    pos_y = root_y + (root_height // 2) - (window_height // 2)
    
    dialog.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")
    
    ctk.CTkLabel(dialog, text="找到多个匹配窗口，请选择:", font=Theme.get_font('sm')).pack(pady=10)
    
    listbox = tk.Listbox(dialog, font=('Arial', 10), selectmode=tk.SINGLE)
    listbox.pack(fill='both', expand=True, padx=10, pady=5)
    
    for hwnd, title in windows:
        listbox.insert(tk.END, f"[{hwnd}] {title}")
    
    def on_select():
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请选择一个窗口")
            return
        
        idx = selection[0]
        hwnd, title = windows[idx]
        dialog.destroy()
        select_window(app, hwnd, title)
    
    def on_cancel():
        dialog.destroy()
    
    btn_frame = ctk.CTkFrame(dialog, fg_color='transparent')
    btn_frame.pack(fill='x', pady=10)
    
    ctk.CTkButton(btn_frame, text="确定", command=on_select, width=80).pack(side='left', padx=(100, 10))
    ctk.CTkButton(btn_frame, text="取消", command=on_cancel, width=80).pack(side='left')
    
    listbox.bind('<Double-Button-1>', lambda e: on_select())
    dialog.wait_window()


def select_window(app, hwnd, title):
    from modules.background import BackgroundManager
    if not hasattr(app, 'background_manager'):
        app.background_manager = BackgroundManager(app)
    
    app.background_manager.set_target_window(hwnd)
    
    max_title_len = 20
    display_title = title
    if len(title) > max_title_len:
        display_title = title[:max_title_len] + "..."
    
    app.bg_window_status_var.set(f"已绑定: {display_title}")
    app.logging_manager.log_message(f"已绑定目标窗口: [{hwnd}] {title}")
    
    update_window_preview(app, hwnd)


def update_window_preview(app, hwnd):
    def capture_and_update():
        try:
            from utils.window_capture import capture_window
            image = capture_window(hwnd)
            if image:
                image_resized = image.resize((196, 116), PILImage.LANCZOS)
                ctk_image = ctk.CTkImage(light_image=image_resized, size=(196, 116))
                app.root.after(0, lambda: update_preview_label(app, ctk_image))
            else:
                app.logging_manager.log_message("窗口截图失败: 无法获取窗口图像")
        except Exception as e:
            app.logging_manager.log_message(f"窗口截图失败: {str(e)}")
    
    threading.Thread(target=capture_and_update, daemon=True).start()


def update_preview_label(app, ctk_image):
    if hasattr(app, 'bg_window_preview'):
        app.bg_window_preview.configure(image=ctk_image, text='')
        app.bg_window_preview_image = ctk_image


def start_bg_region_selection(app, group_index):
    if not hasattr(app, 'background_manager') or not app.background_manager.target_hwnd:
        messagebox.showwarning("警告", "请先绑定目标窗口")
        return
    
    app._bg_region_group_index = group_index
    app.logging_manager.log_message("请在目标窗口上选择监控区域...")
    
    from utils.region import _start_selection
    _start_selection(app, "bg_region", group_index)


def save_bg_region(app, region):
    group_index = getattr(app, '_bg_region_group_index', None)
    if group_index is None:
        return
    
    if group_index < 0 or group_index >= len(app.background_groups):
        return
    
    from utils.coordinate import RelativeCoordinate
    from utils.window_capture import get_window_size
    
    hwnd = app.background_manager.target_hwnd
    window_size = get_window_size(hwnd)
    
    win_rect = None
    try:
        import win32gui
        win_rect = win32gui.GetWindowRect(hwnd)
    except:
        pass
    
    if win_rect:
        win_left, win_top = win_rect[0], win_rect[1]
        rel_x1 = region[0] - win_left
        rel_y1 = region[1] - win_top
        rel_x2 = region[2] - win_left
        rel_y2 = region[3] - win_top
        
        rel_region = (rel_x1, rel_y1, rel_x2, rel_y2)
    else:
        rel_region = region
    
    group = app.background_groups[group_index]
    group["region"] = rel_region
    group["region_var"].set(f"({rel_region[0]}, {rel_region[1]}) - ({rel_region[2]}, {rel_region[3]})")
    
    if window_size:
        group["region_ratio"] = RelativeCoordinate.pixel_to_ratio(rel_region, window_size)
    
    app.logging_manager.log_message(
        f"监控组{group_index + 1}已选择区域: 相对坐标({rel_region[0]}, {rel_region[1]}) - ({rel_region[2]}, {rel_region[3]})"
    )
    
    if hasattr(app, 'config_manager') and app.config_manager:
        app.config_manager.defer_save_config()
    
    app._bg_region_group_index = None


def select_bg_template_image(app, group_index):
    from ui.utils import select_template_image
    select_template_image(app, app.background_groups, group_index, "监控组", app.logging_manager.log_message)


def update_bg_image_preview(app, group_index, image_path):
    from ui.utils import update_image_preview
    if group_index < 0 or group_index >= len(app.background_groups):
        return
    group = app.background_groups[group_index]
    update_image_preview(group.get("image_preview"), group.get("preview_container"), image_path)


def crop_bg_template_image(app, group_index):
    if not hasattr(app, 'background_manager') or not app.background_manager.target_hwnd:
        messagebox.showwarning("警告", "请先绑定目标窗口")
        return
    
    app._bg_crop_group_index = group_index
    app.logging_manager.log_message("请在屏幕上选择要截取的区域...")
    
    from utils.region import _start_selection
    _start_selection(app, "bg_crop", group_index)


def save_bg_cropped_image(app, region):
    from ui.utils import save_cropped_template
    
    group_index = getattr(app, '_bg_crop_group_index', None)
    
    if group_index is None:
        return
    
    save_cropped_template(app, region, app.background_groups, group_index, "监控组", app.logging_manager.log_message)
    app._bg_crop_group_index = None


def start_bg_color_selection(app, group_index):
    app._bg_color_group_index = group_index
    app.logging_manager.log_message("开始选择目标颜色...")
    
    def on_color_selected(color):
        r, g, b = color
        group_index = getattr(app, '_bg_color_group_index', None)
        if group_index is not None and group_index >= 0 and group_index < len(app.background_groups):
            group = app.background_groups[group_index]
            group["target_color"] = (r, g, b)
            group["color_var"].set(f"RGB({r}, {g}, {b})")
            
            if "color_display" in group:
                group["color_display"].configure(fg_color=f"#{r:02x}{g:02x}{b:02x}")
            
            if hasattr(app, 'config_manager') and app.config_manager:
                app.config_manager.defer_save_config()
        
        app._bg_color_group_index = None
    
    from ui.utils import create_color_picker
    create_color_picker(app, on_color_selected, app.logging_manager.log_message)
