import customtkinter as ctk
import tkinter as tk
from ui.theme import Theme
from ui.widgets import CardFrame, AnimatedButton, create_section_title, create_divider


def create_home_tab(app):
    page = ctk.CTkFrame(app.content_area, fg_color='transparent')
    app.pages['home'] = page
    
    status_card = CardFrame(page)
    status_card.pack(fill='x', pady=(0, 12))
    
    status_header = ctk.CTkFrame(status_card, fg_color='transparent')
    status_header.pack(fill='x', padx=12, pady=(10, 6))
    create_section_title(status_header, '功能状态', level=1).pack(side='left')
    
    btn_row_header = ctk.CTkFrame(status_header, fg_color='transparent')
    btn_row_header.pack(side='right')
    
    app.global_start_btn = AnimatedButton(btn_row_header, text='▶ 开始运行', font=Theme.get_font('xs'), 
                                          width=80, height=28, corner_radius=6,
                                          fg_color=Theme.COLORS['success'], hover_color='#16A34A',
                                          command=app.start_all)
    app.global_start_btn.pack(side='left', padx=(0, 6))
    
    app.global_stop_btn = AnimatedButton(btn_row_header, text='⏹ 停止运行', font=Theme.get_font('xs'), 
                                         width=80, height=28, corner_radius=6,
                                         fg_color=Theme.COLORS['error'], hover_color='#DC2626',
                                         command=app.stop_all)
    app.global_stop_btn.pack(side='left')
    
    create_divider(status_card)
    
    app.status_labels = {
        "ocr": tk.StringVar(value="文字识别: 未运行"),
        "timed": tk.StringVar(value="定时功能: 未运行"),
        "number": tk.StringVar(value="数字识别: 未运行"),
        "image": tk.StringVar(value="图像检测: 未运行"),
        "script": tk.StringVar(value="脚本运行: 未运行")
    }
    
    app.module_check_vars = {
        "ocr": tk.BooleanVar(value=False),
        "timed": tk.BooleanVar(value=False),
        "number": tk.BooleanVar(value=False),
        "image": tk.BooleanVar(value=False),
        "script": tk.BooleanVar(value=False)
    }
    
    module_names = {
        "ocr": "文字识别",
        "timed": "定时功能",
        "number": "数字识别",
        "image": "图像检测",
        "script": "脚本运行"
    }
    
    for module, name in module_names.items():
        row = ctk.CTkFrame(status_card, fg_color='transparent')
        row.pack(fill='x', padx=12, pady=4)
        
        ctk.CTkLabel(row, text=name, font=Theme.get_font('sm')).pack(side='left')
        
        indicator = ctk.CTkLabel(row, text='●', font=('Arial', 24), text_color='#9CA3AF')
        indicator.pack(side='left', padx=(8, 0))
        app.module_indicators[module] = indicator
        
        switch = ctk.CTkSwitch(row, text='', width=36, variable=app.module_check_vars[module])
        switch.pack(side='right')
        app.module_switches[module] = switch
    
    ctk.CTkFrame(status_card, height=8, fg_color='transparent').pack()
    
    log_card = CardFrame(page)
    log_card.pack(fill='both', expand=True)
    
    log_header = ctk.CTkFrame(log_card, fg_color='transparent')
    log_header.pack(fill='x', padx=12, pady=(10, 6))
    create_section_title(log_header, '运行日志', level=1).pack(side='left')
    
    app.home_log_text = ctk.CTkTextbox(log_card, font=('Consolas', 10), height=150)
    app.home_log_text.pack(fill='both', expand=True, padx=12, pady=(0, 8))
    
    clear_btn = AnimatedButton(log_card, text='清除日志', font=Theme.get_font('xs'), width=70,
                               fg_color=Theme.COLORS['primary'], text_color='#ffffff',
                               hover_color=Theme.COLORS['primary_hover'], corner_radius=4,
                               command=app.clear_log)
    clear_btn.pack(side='right', padx=12, pady=(0, 10))
