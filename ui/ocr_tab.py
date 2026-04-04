import customtkinter as ctk
import tkinter as tk
from ui.theme import Theme
from ui.widgets import CardFrame, AnimatedButton, NumericEntry, create_divider
from ui.utils import toggle_group_bg, add_group, delete_group


def create_ocr_tab(app):
    page = ctk.CTkFrame(app.content_area, fg_color='transparent')
    app.pages['ocr'] = page
    
    top_frame = ctk.CTkFrame(page, fg_color='transparent')
    top_frame.pack(fill='x', pady=(0, 10))
    
    app.add_ocr_group_btn = AnimatedButton(top_frame, text='+ 新增识别组', font=Theme.get_font('sm'),
                                           height=28, corner_radius=6,
                                           fg_color=Theme.COLORS['primary'],
                                           hover_color=Theme.COLORS['primary_hover'],
                                           command=lambda: add_ocr_group(app))
    app.add_ocr_group_btn.pack(side='left')
    
    scroll_frame = ctk.CTkScrollableFrame(page)
    scroll_frame.pack(fill='both', expand=True)
    
    app.ocr_groups_frame = scroll_frame
    app.ocr_groups = []
    
    for i in range(2):
        create_ocr_group(app, i)


def create_ocr_group(app, index):
    enabled_var = tk.BooleanVar(value=False)
    
    group_vars = {
        "region_var": tk.StringVar(value="未选择区域"),
        "interval_var": tk.StringVar(value="5"),
        "pause_var": tk.StringVar(value="180"),
        "key_var": tk.StringVar(value="equal"),
        "delay_min_var": tk.StringVar(value="300"),
        "delay_max_var": tk.StringVar(value="500"),
        "alarm_var": tk.BooleanVar(value=False),
        "keywords_var": tk.StringVar(value="men,door"),
        "language_var": tk.StringVar(value="eng"),
        "click_var": tk.BooleanVar(value=True)
    }
    
    group_frame = CardFrame(app.ocr_groups_frame, fg_color='#ffffff', border_width=1, border_color=Theme.COLORS['border'])
    group_frame.pack(fill='x', pady=(0, 10))
    
    header = ctk.CTkFrame(group_frame, fg_color='transparent')
    header.pack(fill='x', padx=10, pady=(8, 4))
    
    title_label = ctk.CTkLabel(header, text=f'识别组 {index + 1}', font=Theme.get_font('base'))
    title_label.pack(side='left')
    
    switch = ctk.CTkSwitch(header, text='', width=36, variable=enabled_var,
                          command=lambda: toggle_group_bg(group_frame, enabled_var.get()))
    switch.pack(side='left', padx=(8, 0))
    
    delete_btn = AnimatedButton(header, text='删除', font=Theme.get_font('xs'), width=50, height=22,
                               fg_color=Theme.COLORS['error'], hover_color='#DC2626', corner_radius=4,
                               command=lambda: delete_ocr_group(app, group_frame))
    delete_btn.pack(side='right')
    
    create_divider(group_frame, height=1, pady=(4, 2))
    
    row1 = ctk.CTkFrame(group_frame, fg_color='transparent')
    row1.pack(fill='x', padx=10, pady=4)
    
    select_btn = AnimatedButton(row1, text='选择区域', font=Theme.get_font('xs'), width=60, height=24,
                               corner_radius=4, fg_color=Theme.COLORS['primary'],
                               hover_color=Theme.COLORS['primary_hover'],
                               command=lambda: start_ocr_region_selection(app, index))
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
    row2.pack(fill='x', padx=10, pady=(4, 8))
    
    ctk.CTkLabel(row2, text='间隔:', font=Theme.get_font('xs')).pack(side='left')
    interval_entry = NumericEntry(row2, textvariable=group_vars["interval_var"], width=45, height=24)
    interval_entry.pack(side='left', padx=(2, 2))
    ctk.CTkLabel(row2, text='秒', font=Theme.get_font('xs')).pack(side='left', padx=(0, 8))
    
    ctk.CTkLabel(row2, text='暂停:', font=Theme.get_font('xs')).pack(side='left')
    pause_entry = NumericEntry(row2, textvariable=group_vars["pause_var"], width=45, height=24)
    pause_entry.pack(side='left', padx=(2, 2))
    ctk.CTkLabel(row2, text='秒', font=Theme.get_font('xs')).pack(side='left', padx=(0, 8))
    
    ctk.CTkLabel(row2, text='关键词:', font=Theme.get_font('xs')).pack(side='left')
    keywords_entry = ctk.CTkEntry(row2, textvariable=group_vars["keywords_var"], width=100, height=24)
    keywords_entry.pack(side='left', padx=(2, 8))
    
    ctk.CTkLabel(row2, text='语言:', font=Theme.get_font('xs')).pack(side='left', padx=(0, 2))
    from ui.widgets import create_bordered_option_menu
    create_bordered_option_menu(row2, values=['eng', 'chi_sim', 'chi_tra'],
                                variable=group_vars["language_var"], width=70, height=24)
    
    click_frame = ctk.CTkFrame(row2, fg_color='transparent')
    click_frame.pack(side='left')
    ctk.CTkLabel(click_frame, text='点击', font=Theme.get_font('xs')).pack(side='left', padx=(0, 2))
    ctk.CTkSwitch(click_frame, text='', width=36, variable=group_vars["click_var"]).pack(side='left')
    
    group_config = {
        "frame": group_frame,
        "enabled": enabled_var,
        "region_var": group_vars["region_var"],
        "region": None,
        "interval": group_vars["interval_var"],
        "pause": group_vars["pause_var"],
        "key": group_vars["key_var"],
        "delay_min": group_vars["delay_min_var"],
        "delay_max": group_vars["delay_max_var"],
        "alarm": group_vars["alarm_var"],
        "keywords": group_vars["keywords_var"],
        "language": group_vars["language_var"],
        "click": group_vars["click_var"],
        "title_label": title_label
    }
    app.ocr_groups.append(group_config)


def add_ocr_group(app):
    return add_group(
        app=app,
        groups=app.ocr_groups,
        create_func=lambda idx: create_ocr_group(app, idx),
        listener_setup_func=getattr(app, '_setup_ocr_group_listeners', None)
    )


def delete_ocr_group(app, group_frame, confirm=True):
    return delete_group(
        app=app,
        groups=app.ocr_groups,
        group_frame=group_frame,
        renumber_func=lambda: renumber_ocr_groups(app),
        confirm=confirm,
        confirm_message="确定要删除该识别组吗？"
    )


def renumber_ocr_groups(app):
    for i, group in enumerate(app.ocr_groups):
        group["title_label"].configure(text=f'识别组 {i + 1}')


def start_ocr_region_selection(app, index):
    from utils.region import _start_selection
    _start_selection(app, "ocr", index)
