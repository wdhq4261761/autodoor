import customtkinter as ctk
import tkinter as tk
from ui.theme import Theme
from ui.widgets import CardFrame, AnimatedButton, NumericEntry, create_divider
from ui.utils import toggle_group_bg, add_group, delete_group


def create_timed_tab(app):
    page = ctk.CTkFrame(app.content_area, fg_color='transparent')
    app.pages['timed'] = page
    
    top_frame = ctk.CTkFrame(page, fg_color='transparent')
    top_frame.pack(fill='x', pady=(0, 10))
    
    app.add_timed_group_btn = AnimatedButton(top_frame, text='+ 新增定时组', font=Theme.get_font('sm'),
                                             height=28, corner_radius=6,
                                             fg_color=Theme.COLORS['primary'],
                                             hover_color=Theme.COLORS['primary_hover'],
                                             command=lambda: add_timed_group(app))
    app.add_timed_group_btn.pack(side='left')
    
    scroll_frame = ctk.CTkScrollableFrame(page)
    scroll_frame.pack(fill='both', expand=True)
    
    app.timed_groups_frame = scroll_frame
    app.timed_groups = []
    
    for i in range(3):
        create_timed_group(app, i)


def create_timed_group(app, index):
    enabled_var = tk.BooleanVar(value=False)
    
    default_keys = ["space", "enter", "tab", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12"]
    
    group_vars = {
        "interval_var": tk.StringVar(value=str(10 * (index + 1))),
        "key_var": tk.StringVar(value=default_keys[index % len(default_keys)]),
        "delay_min_var": tk.StringVar(value="300"),
        "delay_max_var": tk.StringVar(value="500"),
        "alarm_var": tk.BooleanVar(value=False),
        "click_enabled_var": tk.BooleanVar(value=False),
        "position_var": tk.StringVar(value="未选择位置")
    }
    
    group_frame = CardFrame(app.timed_groups_frame, fg_color='#ffffff', border_width=1, border_color=Theme.COLORS['border'])
    group_frame.pack(fill='x', pady=(0, 10))
    
    header = ctk.CTkFrame(group_frame, fg_color='transparent')
    header.pack(fill='x', padx=10, pady=(8, 4))
    
    title_label = ctk.CTkLabel(header, text=f'定时组 {index + 1}', font=Theme.get_font('base'))
    title_label.pack(side='left')
    
    switch = ctk.CTkSwitch(header, text='', width=36, variable=enabled_var,
                          command=lambda: toggle_group_bg(group_frame, enabled_var.get()))
    switch.pack(side='left', padx=(8, 0))
    
    delete_btn = AnimatedButton(header, text='删除', font=Theme.get_font('xs'), width=50, height=22,
                               fg_color=Theme.COLORS['error'], hover_color='#DC2626', corner_radius=4,
                               command=lambda: delete_timed_group(app, group_frame))
    delete_btn.pack(side='right')
    
    create_divider(group_frame, height=1, pady=(4, 2))
    
    row1 = ctk.CTkFrame(group_frame, fg_color='transparent')
    row1.pack(fill='x', padx=10, pady=(4, 8))
    
    ctk.CTkLabel(row1, text='间隔:', font=Theme.get_font('xs')).pack(side='left')
    interval_entry = NumericEntry(row1, textvariable=group_vars["interval_var"], width=45, height=24)
    interval_entry.pack(side='left', padx=(2, 2))
    ctk.CTkLabel(row1, text='秒', font=Theme.get_font('xs')).pack(side='left', padx=(0, 8))
    
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
    
    click_frame = ctk.CTkFrame(row1, fg_color='transparent')
    click_frame.pack(side='left')
    ctk.CTkLabel(click_frame, text='点击', font=Theme.get_font('xs')).pack(side='left', padx=(0, 2))
    ctk.CTkSwitch(click_frame, text='', width=36, variable=group_vars["click_enabled_var"]).pack(side='left', padx=(0, 6))
    
    pos_btn = AnimatedButton(row1, text='位置', font=Theme.get_font('xs'), width=40, height=24, corner_radius=4,
                            fg_color=Theme.COLORS['primary'], hover_color=Theme.COLORS['primary_hover'],
                            command=lambda: start_timed_position_selection(app, index))
    pos_btn.pack(side='left', padx=(0, 4))
    pos_entry = ctk.CTkEntry(row1, textvariable=group_vars["position_var"], width=80, height=24, state='disabled')
    pos_entry.pack(side='left', padx=(0, 8))
    
    alarm_frame = ctk.CTkFrame(row1, fg_color='transparent')
    alarm_frame.pack(side='left')
    ctk.CTkLabel(alarm_frame, text='报警', font=Theme.get_font('xs')).pack(side='left', padx=(0, 2))
    ctk.CTkSwitch(alarm_frame, text='', width=36, variable=group_vars["alarm_var"]).pack(side='left')
    
    group_config = {
        "frame": group_frame,
        "enabled": enabled_var,
        "interval": group_vars["interval_var"],
        "key": group_vars["key_var"],
        "delay_min": group_vars["delay_min_var"],
        "delay_max": group_vars["delay_max_var"],
        "alarm": group_vars["alarm_var"],
        "click_enabled": group_vars["click_enabled_var"],
        "position_x": tk.IntVar(value=0),
        "position_y": tk.IntVar(value=0),
        "position_var": group_vars["position_var"],
        "title_label": title_label
    }
    app.timed_groups.append(group_config)


def add_timed_group(app):
    return add_group(
        app=app,
        groups=app.timed_groups,
        create_func=lambda idx: create_timed_group(app, idx),
        listener_setup_func=getattr(app, '_setup_group_listeners', None)
    )


def delete_timed_group(app, group_frame, confirm=True):
    return delete_group(
        app=app,
        groups=app.timed_groups,
        group_frame=group_frame,
        renumber_func=lambda: renumber_timed_groups(app),
        confirm=confirm,
        confirm_message="确定要删除该定时组吗？"
    )


def renumber_timed_groups(app):
    for i, group in enumerate(app.timed_groups):
        group["title_label"].configure(text=f'定时组 {i + 1}')


def start_timed_position_selection(app, index):
    if hasattr(app, 'timed_module') and hasattr(app.timed_module, 'start_timed_position_selection'):
        app.timed_module.start_timed_position_selection(index)
