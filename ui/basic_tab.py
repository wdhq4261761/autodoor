import customtkinter as ctk
import tkinter as tk
from modules.alarm import select_alarm_sound
from ui.theme import Theme
from ui.widgets import CardFrame, AnimatedButton, create_section_title, create_divider

def create_basic_tab(app):
    page = ctk.CTkFrame(app.content_area, fg_color='transparent')
    app.pages['settings'] = page
    
    scroll_frame = ctk.CTkScrollableFrame(page)
    scroll_frame.pack(fill='both', expand=True)
    
    tess_frame = CardFrame(scroll_frame, fg_color='#ffffff', border_width=1, border_color=Theme.COLORS['border'])
    tess_frame.pack(fill='x', pady=(0, 10))
    
    tess_header = ctk.CTkFrame(tess_frame, fg_color='transparent')
    tess_header.pack(fill='x', padx=12, pady=(10, 6))
    create_section_title(tess_header, 'Tesseract OCR 设置', level=1).pack(side='left')
    
    create_divider(tess_frame)
    
    tess_row = ctk.CTkFrame(tess_frame, fg_color='transparent')
    tess_row.pack(fill='x', padx=12, pady=(4, 10))
    
    ctk.CTkLabel(tess_row, text='路径:', font=Theme.get_font('sm')).pack(side='left')
    
    app.tesseract_path_var = tk.StringVar(value=app.tesseract_path)
    app.tesseract_path_entry = ctk.CTkEntry(tess_row, textvariable=app.tesseract_path_var, height=28, state='disabled')
    app.tesseract_path_entry.pack(side='left', fill='x', expand=True, padx=(6, 6))
    
    app.set_path_btn = AnimatedButton(tess_row, text='浏览', font=Theme.get_font('xs'), width=50, height=28,
                                      corner_radius=4, fg_color=Theme.COLORS['primary'],
                                      hover_color=Theme.COLORS['primary_hover'],
                                      command=app.set_tesseract_path)
    app.set_path_btn.pack(side='left')
    
    alarm_frame = CardFrame(scroll_frame, fg_color='#ffffff', border_width=1, border_color=Theme.COLORS['border'])
    alarm_frame.pack(fill='x', pady=(0, 10))
    
    alarm_header = ctk.CTkFrame(alarm_frame, fg_color='transparent')
    alarm_header.pack(fill='x', padx=12, pady=(10, 6))
    create_section_title(alarm_header, '报警设置', level=1).pack(side='left')
    
    create_divider(alarm_frame)
    
    alarm_row1 = ctk.CTkFrame(alarm_frame, fg_color='transparent')
    alarm_row1.pack(fill='x', padx=12, pady=4)
    
    ctk.CTkLabel(alarm_row1, text='声音:', font=Theme.get_font('sm')).pack(side='left')
    
    alarm_sound_entry = ctk.CTkEntry(alarm_row1, textvariable=app.alarm_sound_path, height=28, state='disabled')
    alarm_sound_entry.pack(side='left', fill='x', expand=True, padx=(6, 6))
    
    alarm_sound_btn = AnimatedButton(alarm_row1, text='浏览', font=Theme.get_font('xs'), width=50, height=28,
                                     corner_radius=4, fg_color=Theme.COLORS['primary'],
                                     hover_color=Theme.COLORS['primary_hover'],
                                     command=lambda: select_alarm_sound(app))
    alarm_sound_btn.pack(side='left')
    
    alarm_row2 = ctk.CTkFrame(alarm_frame, fg_color='transparent')
    alarm_row2.pack(fill='x', padx=12, pady=(4, 10))
    
    ctk.CTkLabel(alarm_row2, text='音量:', font=Theme.get_font('sm')).pack(side='left')
    
    def update_volume_display(*args):
        app.alarm_volume_str.set(str(app.alarm_volume.get()))
    
    app.alarm_volume.trace_add("write", update_volume_display)
    
    volume_slider = ctk.CTkSlider(alarm_row2, from_=0, to=100, variable=app.alarm_volume, width=200)
    volume_slider.pack(side='left', padx=(6, 6))
    
    volume_label = ctk.CTkLabel(alarm_row2, textvariable=app.alarm_volume_str, font=Theme.get_font('sm'), width=40)
    volume_label.pack(side='left')
    
    shortcut_frame = CardFrame(scroll_frame, fg_color='#ffffff', border_width=1, border_color=Theme.COLORS['border'])
    shortcut_frame.pack(fill='x', pady=(0, 10))
    
    shortcut_header = ctk.CTkFrame(shortcut_frame, fg_color='transparent')
    shortcut_header.pack(fill='x', padx=12, pady=(10, 6))
    create_section_title(shortcut_header, '快捷键设置', level=1).pack(side='left')
    
    create_divider(shortcut_frame)
    
    shortcuts = [('开始运行:', 'F10', 'start_shortcut_var'), ('停止运行:', 'F12', 'stop_shortcut_var'), ('录制按钮:', 'F11', 'record_hotkey_var')]
    
    from utils.keyboard import start_key_listening
    
    for label, default, var_name in shortcuts:
        row = ctk.CTkFrame(shortcut_frame, fg_color='transparent')
        row.pack(fill='x', padx=12, pady=4)
        
        ctk.CTkLabel(row, text=label, font=Theme.get_font('sm')).pack(side='left')
        
        var = tk.StringVar(value=default)
        setattr(app, var_name, var)
        
        entry = ctk.CTkEntry(row, textvariable=var, width=80, height=24, state='disabled')
        entry.pack(side='left', padx=(6, 2))
        
        btn = AnimatedButton(row, text='修改', font=Theme.get_font('xs'), width=24, height=24, corner_radius=4,
                            fg_color=Theme.COLORS['primary'], hover_color=Theme.COLORS['primary_hover'])
        btn.configure(command=lambda e=entry, b=btn: start_key_listening(app, e, b))
        btn.pack(side='left')
    
    ctk.CTkFrame(shortcut_frame, height=6, fg_color='transparent').pack()