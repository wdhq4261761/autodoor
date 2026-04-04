import customtkinter as ctk
import tkinter as tk
from ui.theme import Theme
from ui.widgets import CardFrame, AnimatedButton, NumericEntry, create_divider
from ui.utils import toggle_group_bg, add_group, delete_group, select_template_image, save_cropped_template


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
    header.pack(fill='x', padx=10, pady=(6, 2))
    
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
    
    select_region_btn = AnimatedButton(row1, text='选择区域', font=Theme.get_font('xs'), width=60, height=24,
                                        corner_radius=4, fg_color=Theme.COLORS['primary'],
                                        hover_color=Theme.COLORS['primary_hover'],
                                        command=lambda: start_image_region_selection(app, index))
    select_region_btn.pack(side='left', padx=(0, 4))
    
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
                                       command=lambda: on_select_image(app, index))
    select_image_btn.pack(side='left', padx=(0, 4))
    
    image_path_entry = ctk.CTkEntry(row2, textvariable=group_vars["image_path_var"], width=80, height=24, state='disabled')
    image_path_entry.pack(side='left', padx=(0, 4))
    
    crop_image_btn = AnimatedButton(row2, text='截图', font=Theme.get_font('xs'), width=36, height=24,
                                     corner_radius=4, fg_color=Theme.COLORS['info'],
                                     hover_color=Theme.COLORS['info_hover'],
                                     command=lambda: select_reference_image(app, index))
    crop_image_btn.pack(side='left', padx=(0, 8))
    
    ctk.CTkLabel(row2, text='阈值:', font=Theme.get_font('xs')).pack(side='left')
    threshold_entry = NumericEntry(row2, textvariable=group_vars["threshold_var"], width=30, height=24)
    threshold_entry.pack(side='left', padx=(2, 0))
    ctk.CTkLabel(row2, text='%', font=Theme.get_font('xs')).pack(side='left')
    
    click_frame = ctk.CTkFrame(row2, fg_color='transparent')
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
        "image_preview": image_preview,
        "preview_container": preview_container
    }
    app.image_groups.append(group_config)

def on_select_image(app, index):
    """选择图像回调"""
    select_template_image(app, app.image_groups, index, "检测组", app.logging_manager.log_message)


def add_image_group(app):
    """新增图像检测组"""
    return add_group(
        app=app,
        groups=app.image_groups,
        create_func=lambda idx: create_image_group(app, idx),
        listener_setup_func=getattr(app, '_setup_image_group_listeners', None)
    )

def delete_image_group(app, group_frame, confirm=True):
    """删除图像检测组"""
    return delete_group(
        app=app,
        groups=app.image_groups,
        group_frame=group_frame,
        renumber_func=lambda: renumber_image_groups(app),
        confirm=confirm,
        confirm_message="确定要删除该检测组吗？"
    )

def renumber_image_groups(app):
    """重新编号所有图像检测组"""
    for i, group in enumerate(app.image_groups):
        group["title_label"].configure(text=f'检测组 {i + 1}')

def start_image_region_selection(app, index):
    """开始选择图像检测区域"""
    from utils.region import _start_selection
    _start_selection(app, "image", index)

def select_reference_image(app, index):
    """截取屏幕区域作为参考图像"""
    if index >= len(app.image_groups):
        return
    
    app.logging_manager.log_message("[图像截图] 请在屏幕上选择要截取的区域...")
    
    app._crop_group_index = index
    
    from utils.region import _start_selection
    _start_selection(app, "crop", index)

def save_cropped_image(app, region):
    """保存截取的屏幕区域图像"""
    group_index = getattr(app, '_crop_group_index', None)
    
    if group_index is None:
        return
    
    save_cropped_template(app, region, app.image_groups, group_index, "检测组", app.logging_manager.log_message)
    
    app._crop_group_index = None
