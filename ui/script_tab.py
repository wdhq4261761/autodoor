import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog

from ui.theme import Theme
from ui.widgets import CardFrame, AnimatedButton, NumericEntry, create_divider

def center_window_on_parent(window, parent):
    """将窗口居中显示在父窗口上"""
    window.update_idletasks()
    parent_x = parent.winfo_rootx()
    parent_y = parent.winfo_rooty()
    parent_width = parent.winfo_width()
    parent_height = parent.winfo_height()
    window_width = window.winfo_width()
    window_height = window.winfo_height()
    x = parent_x + (parent_width - window_width) // 2
    y = parent_y + (parent_height - window_height) // 2
    window.geometry(f"+{x}+{y}")

def askyesnocancel_centered(parent, title, message):
    """显示居中的是/否/取消对话框"""
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.transient(parent)
    dialog.grab_set()
    dialog.resizable(False, False)
    
    result = [None]
    
    frame = ctk.CTkFrame(dialog, fg_color='transparent')
    frame.pack(fill='both', expand=True, padx=20, pady=15)
    
    label = ctk.CTkLabel(frame, text=message, font=Theme.get_font('base'), wraplength=300)
    label.pack(pady=(0, 15))
    
    btn_frame = ctk.CTkFrame(frame, fg_color='transparent')
    btn_frame.pack(fill='x')
    
    def on_yes():
        result[0] = True
        dialog.destroy()
    
    def on_no():
        result[0] = False
        dialog.destroy()
    
    def on_cancel():
        result[0] = None
        dialog.destroy()
    
    yes_btn = ctk.CTkButton(btn_frame, text='是', width=80, command=on_yes,
                            fg_color=Theme.COLORS['success'], hover_color='#16A34A')
    yes_btn.pack(side='left', padx=5, expand=True)
    
    no_btn = ctk.CTkButton(btn_frame, text='否', width=80, command=on_no,
                           fg_color=Theme.COLORS['error'], hover_color='#DC2626')
    no_btn.pack(side='left', padx=5, expand=True)
    
    cancel_btn = ctk.CTkButton(btn_frame, text='取消', width=80, command=on_cancel,
                               fg_color='#6B7280', hover_color='#4B5563',
                               text_color='white')
    cancel_btn.pack(side='left', padx=5, expand=True)
    
    dialog.protocol("WM_DELETE_WINDOW", on_cancel)
    
    dialog.update_idletasks()
    dialog_width = dialog.winfo_width()
    dialog_height = dialog.winfo_height()
    parent_x = parent.winfo_rootx()
    parent_y = parent.winfo_rooty()
    parent_width = parent.winfo_width()
    parent_height = parent.winfo_height()
    x = parent_x + (parent_width - dialog_width) // 2
    y = parent_y + (parent_height - dialog_height) // 2
    dialog.geometry(f"+{x}+{y}")
    
    dialog.wait_window()
    return result[0]

def askyesno_centered(parent, title, message):
    """显示居中的是/否对话框"""
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.transient(parent)
    dialog.grab_set()
    dialog.resizable(False, False)
    
    result = [False]
    
    frame = ctk.CTkFrame(dialog, fg_color='transparent')
    frame.pack(fill='both', expand=True, padx=20, pady=15)
    
    label = ctk.CTkLabel(frame, text=message, font=Theme.get_font('base'), wraplength=300)
    label.pack(pady=(0, 15))
    
    btn_frame = ctk.CTkFrame(frame, fg_color='transparent')
    btn_frame.pack(fill='x')
    
    def on_yes():
        result[0] = True
        dialog.destroy()
    
    def on_no():
        result[0] = False
        dialog.destroy()
    
    yes_btn = ctk.CTkButton(btn_frame, text='是', width=80, command=on_yes,
                            fg_color=Theme.COLORS['success'], hover_color='#16A34A')
    yes_btn.pack(side='left', padx=10, expand=True)
    
    no_btn = ctk.CTkButton(btn_frame, text='否', width=80, command=on_no,
                           fg_color=Theme.COLORS['error'], hover_color='#DC2626')
    no_btn.pack(side='left', padx=10, expand=True)
    
    dialog.protocol("WM_DELETE_WINDOW", on_no)
    
    dialog.update_idletasks()
    dialog_width = dialog.winfo_width()
    dialog_height = dialog.winfo_height()
    parent_x = parent.winfo_rootx()
    parent_y = parent.winfo_rooty()
    parent_width = parent.winfo_width()
    parent_height = parent.winfo_height()
    x = parent_x + (parent_width - dialog_width) // 2
    y = parent_y + (parent_height - dialog_height) // 2
    dialog.geometry(f"+{x}+{y}")
    
    dialog.wait_window()
    return result[0]

def create_script_tab(app):
    page = ctk.CTkFrame(app.content_area, fg_color='transparent')
    app.pages['script'] = page
    
    main_container = ctk.CTkFrame(page, fg_color='transparent')
    main_container.pack(fill='both', expand=True)
    
    left_frame = ctk.CTkFrame(main_container, fg_color='transparent')
    left_frame.pack(side='left', fill='both', expand=True, padx=(0, 8))
    
    key_card = CardFrame(left_frame, fg_color='#ffffff', border_width=1, border_color=Theme.COLORS['border'])
    key_card.pack(fill='x', pady=(0, 8))
    
    key_header = ctk.CTkFrame(key_card, fg_color='transparent')
    key_header.pack(fill='x', padx=10, pady=(8, 4))
    ctk.CTkLabel(key_header, text='按键命令', font=Theme.get_font('base')).pack(side='left')
    
    create_divider(key_card)
    
    key_row = ctk.CTkFrame(key_card, fg_color='transparent')
    key_row.pack(fill='x', padx=10, pady=(4, 8))
    
    ctk.CTkLabel(key_row, text='按键:', font=Theme.get_font('xs')).pack(side='left')
    app.key_var = ctk.CTkEntry(key_row, width=50, height=24, state='disabled')
    app.key_var.insert(0, '1')
    app.key_var.pack(side='left', padx=(2, 2))
    
    from utils.keyboard import start_key_listening
    app.set_key_btn = AnimatedButton(key_row, text='修改', font=Theme.get_font('xs'), width=24, height=24, corner_radius=4,
                                     fg_color=Theme.COLORS['primary'], hover_color=Theme.COLORS['primary_hover'])
    app.set_key_btn.configure(command=lambda: start_key_listening(app, app.key_var, app.set_key_btn))
    app.set_key_btn.pack(side='left', padx=(0, 8))
    
    ctk.CTkLabel(key_row, text='类型:', font=Theme.get_font('xs')).pack(side='left', padx=(0, 2))
    app.key_type = tk.StringVar(value="KeyDown")
    from ui.widgets import create_bordered_option_menu
    create_bordered_option_menu(key_row, values=["KeyDown", "KeyUp"], variable=app.key_type, width=80, height=24)
    
    app.key_count = tk.IntVar(value=1)
    
    app.insert_key_btn = AnimatedButton(key_row, text='插入', font=Theme.get_font('xs'), width=50, height=24,
                                        corner_radius=4, fg_color=Theme.COLORS['success'],
                                        hover_color='#16A34A',
                                        command=lambda: insert_key_command(app))
    app.insert_key_btn.pack(side='left')
    
    delay_card = CardFrame(left_frame, fg_color='#ffffff', border_width=1, border_color=Theme.COLORS['border'])
    delay_card.pack(fill='x', pady=(0, 8))
    
    delay_header = ctk.CTkFrame(delay_card, fg_color='transparent')
    delay_header.pack(fill='x', padx=10, pady=(8, 4))
    ctk.CTkLabel(delay_header, text='延迟命令', font=Theme.get_font('base')).pack(side='left')
    
    create_divider(delay_card)
    
    delay_row = ctk.CTkFrame(delay_card, fg_color='transparent')
    delay_row.pack(fill='x', padx=10, pady=(4, 8))
    
    ctk.CTkLabel(delay_row, text='延迟(ms):', font=Theme.get_font('xs')).pack(side='left')
    app.delay_var = tk.StringVar(value="250")
    app.delay_entry = NumericEntry(delay_row, textvariable=app.delay_var, width=60, height=24)
    app.delay_entry.pack(side='left', padx=(2, 6))
    
    app.insert_delay_btn = AnimatedButton(delay_row, text='插入', font=Theme.get_font('xs'), width=50, height=24,
                                          corner_radius=4, fg_color=Theme.COLORS['success'],
                                          hover_color='#16A34A',
                                          command=lambda: insert_delay_command(app))
    app.insert_delay_btn.pack(side='left')
    
    mouse_card = CardFrame(left_frame, fg_color='#ffffff', border_width=1, border_color=Theme.COLORS['border'])
    mouse_card.pack(fill='x', pady=(0, 8))
    
    mouse_header = ctk.CTkFrame(mouse_card, fg_color='transparent')
    mouse_header.pack(fill='x', padx=10, pady=(8, 4))
    ctk.CTkLabel(mouse_header, text='鼠标命令', font=Theme.get_font('base')).pack(side='left')
    
    create_divider(mouse_card)
    
    mouse_row = ctk.CTkFrame(mouse_card, fg_color='transparent')
    mouse_row.pack(fill='x', padx=10, pady=(4, 8))
    
    ctk.CTkLabel(mouse_row, text='按键:', font=Theme.get_font('xs')).pack(side='left', padx=(0, 2))
    app.mouse_button_var = tk.StringVar(value="Left")
    from ui.widgets import create_bordered_option_menu
    create_bordered_option_menu(mouse_row, values=["Left", "Right", "Middle"],
                                variable=app.mouse_button_var, width=60, height=24)
    
    ctk.CTkLabel(mouse_row, text='操作:', font=Theme.get_font('xs')).pack(side='left', padx=(8, 2))
    app.mouse_action_var = tk.StringVar(value="Down")
    create_bordered_option_menu(mouse_row, values=["Down", "Up"],
                                variable=app.mouse_action_var, width=60, height=24)
    
    app.mouse_count_var = tk.IntVar(value=1)
    
    app.insert_mouse_click_btn = AnimatedButton(mouse_row, text='插入', font=Theme.get_font('xs'), width=50, height=24,
                                                corner_radius=4, fg_color=Theme.COLORS['success'],
                                                hover_color='#16A34A',
                                                command=lambda: insert_mouse_click_command(app))
    app.insert_mouse_click_btn.pack(side='left')
    
    mouse_row2 = ctk.CTkFrame(mouse_card, fg_color='transparent')
    mouse_row2.pack(fill='x', padx=10, pady=(0, 8))
    
    app.select_coordinate_btn = AnimatedButton(mouse_row2, text='选择坐标点', font=Theme.get_font('xs'),
                                               height=24, corner_radius=4,
                                               fg_color=Theme.COLORS['primary'],
                                               hover_color=Theme.COLORS['primary_hover'],
                                               command=lambda: select_coordinate(app))
    app.select_coordinate_btn.pack(fill='x')
    
    combo_card = CardFrame(left_frame, fg_color='#ffffff', border_width=1, border_color=Theme.COLORS['border'])
    combo_card.pack(fill='x', pady=(0, 8))
    
    combo_header = ctk.CTkFrame(combo_card, fg_color='transparent')
    combo_header.pack(fill='x', padx=10, pady=(8, 4))
    ctk.CTkLabel(combo_header, text='组合按键', font=Theme.get_font('base')).pack(side='left')
    
    create_divider(combo_card)
    
    combo_row = ctk.CTkFrame(combo_card, fg_color='transparent')
    combo_row.pack(fill='x', padx=10, pady=(4, 8))
    
    ctk.CTkLabel(combo_row, text='按键:', font=Theme.get_font('xs')).pack(side='left')
    app.combo_key_var = ctk.CTkEntry(combo_row, width=50, height=24, state='disabled')
    app.combo_key_var.insert(0, '1')
    app.combo_key_var.pack(side='left', padx=(2, 2))
    
    app.set_combo_key_btn = AnimatedButton(combo_row, text='修改', font=Theme.get_font('xs'), width=24, height=24, corner_radius=4,
                                           fg_color=Theme.COLORS['primary'], hover_color=Theme.COLORS['primary_hover'])
    app.set_combo_key_btn.configure(command=lambda: start_key_listening(app, app.combo_key_var, app.set_combo_key_btn))
    app.set_combo_key_btn.pack(side='left', padx=(0, 8))
    
    ctk.CTkLabel(combo_row, text='按键延迟(ms):', font=Theme.get_font('xs')).pack(side='left')
    app.combo_key_delay = tk.StringVar(value="2500")
    combo_delay_entry = NumericEntry(combo_row, textvariable=app.combo_key_delay, width=50, height=24)
    combo_delay_entry.pack(side='left', padx=(2, 6))
    
    ctk.CTkLabel(combo_row, text='抬起延迟(ms):', font=Theme.get_font('xs')).pack(side='left')
    app.combo_after_delay = tk.StringVar(value="300")
    combo_after_entry = NumericEntry(combo_row, textvariable=app.combo_after_delay, width=50, height=24)
    combo_after_entry.pack(side='left', padx=(2, 6))
    
    app.insert_combo_btn = AnimatedButton(combo_row, text='插入', font=Theme.get_font('xs'), width=50, height=24,
                                          corner_radius=4, fg_color=Theme.COLORS['success'],
                                          hover_color='#16A34A',
                                          command=lambda: insert_combo_command(app))
    app.insert_combo_btn.pack(side='left')
    
    control_card = CardFrame(left_frame, fg_color='#ffffff', border_width=1, border_color=Theme.COLORS['border'])
    control_card.pack(fill='x', pady=(0, 8))
    
    control_header = ctk.CTkFrame(control_card, fg_color='transparent')
    control_header.pack(fill='x', padx=10, pady=(8, 4))
    ctk.CTkLabel(control_header, text='脚本控制', font=Theme.get_font('base')).pack(side='left')
    
    create_divider(control_card)
    
    file_path_row = ctk.CTkFrame(control_card, fg_color='transparent')
    file_path_row.pack(fill='x', padx=10, pady=(4, 4))
    
    ctk.CTkLabel(file_path_row, text='当前文件:', font=Theme.get_font('xs')).pack(side='left')
    app.script_file_path_var = tk.StringVar(value="未保存")
    app.script_file_path_label = ctk.CTkLabel(file_path_row, textvariable=app.script_file_path_var, 
                                               font=Theme.get_font('xs'), text_color=Theme.COLORS['text_muted'],
                                               anchor='w')
    app.script_file_path_label.pack(side='left', padx=(4, 0), fill='x', expand=True)
    
    control_row1 = ctk.CTkFrame(control_card, fg_color='transparent')
    control_row1.pack(fill='x', padx=10, pady=(4, 8))
    
    app.record_btn = AnimatedButton(control_row1, text='开始录制', font=Theme.get_font('xs'),
                                    height=24, corner_radius=4, fg_color=Theme.COLORS['success'],
                                    hover_color='#16A34A',
                                    command=lambda: app.script_module.start_recording() if hasattr(app, 'script_module') else None)
    app.record_btn.pack(side='left', fill='x', expand=True, padx=(0, 4))
    
    app.stop_record_btn = AnimatedButton(control_row1, text='停止录制', font=Theme.get_font('xs'),
                                         height=24, corner_radius=4, fg_color=Theme.COLORS['error'],
                                         hover_color='#DC2626',
                                         command=lambda: app.script_module.stop_recording() if hasattr(app, 'script_module') else None)
    app.stop_record_btn.configure(state='disabled')
    app.stop_record_btn.pack(side='left', fill='x', expand=True)
    
    control_row2 = ctk.CTkFrame(control_card, fg_color='transparent')
    control_row2.pack(fill='x', padx=10, pady=(0, 8))
    
    new_btn = AnimatedButton(control_row2, text='新建', font=Theme.get_font('xs'),
                             height=24, corner_radius=4, 
                             fg_color='transparent', text_color=Theme.COLORS['primary'],
                             border_width=1, hover_color=Theme.COLORS['info_light'],
                             command=lambda: new_script(app))
    new_btn.pack(side='left', fill='x', expand=True, padx=(0, 4))
    
    open_btn = AnimatedButton(control_row2, text='打开', font=Theme.get_font('xs'), height=24, corner_radius=4,
                              fg_color=Theme.COLORS['primary'], hover_color=Theme.COLORS['primary_hover'],
                              command=lambda: load_script(app))
    open_btn.pack(side='left', fill='x', expand=True, padx=(0, 4))
    
    save_btn = AnimatedButton(control_row2, text='保存', font=Theme.get_font('xs'), height=24, corner_radius=4,
                              fg_color=Theme.COLORS['success'], hover_color='#16A34A',
                              command=lambda: save_script(app))
    save_btn.pack(side='left', fill='x', expand=True)
    
    right_frame = ctk.CTkFrame(main_container, width=400)
    right_frame.pack(side='left', fill='both', expand=True)
    right_frame.pack_propagate(False)
    
    app.script_tabview = ctk.CTkTabview(right_frame)
    app.script_tabview.pack(fill='both', expand=True, padx=4, pady=4)
    
    editor_tab = app.script_tabview.add('脚本编辑')
    color_tab = app.script_tabview.add('颜色识别')
    
    editor_content = ctk.CTkFrame(editor_tab, fg_color='transparent')
    editor_content.pack(fill='both', expand=True, padx=4, pady=4)
    
    app.script_text = ctk.CTkTextbox(editor_content, font=('Consolas', 10))
    app.script_text.pack(fill='both', expand=True)
    
    clear_btn = AnimatedButton(editor_content, text='清空', font=Theme.get_font('xs'), width=80, height=22,
                               fg_color='#ffffff', text_color=Theme.COLORS['text_secondary'],
                               border_width=1, border_color=Theme.COLORS['border'],
                               corner_radius=4,
                               hover_color=Theme.COLORS['info_light'],
                               command=lambda: clear_script(app))
    clear_btn.pack(side='right', pady=(4, 0))
    
    app.script_modified = False
    app.script_original_content = ""
    
    def on_script_modified(event):
        if app.script_text.edit_modified():
            app.script_modified = True
            app.script_text.edit_modified(False)
    
    app.script_text.bind("<<Modified>>", on_script_modified)
    
    create_color_recognition_tab(app, color_tab)


def create_color_recognition_tab(app, parent):
    color_content = ctk.CTkFrame(parent, fg_color='transparent')
    color_content.pack(fill='both', expand=True, padx=8, pady=8)
    
    color_row1 = ctk.CTkFrame(color_content, fg_color='transparent')
    color_row1.pack(fill='x', pady=4)
    app.color_enabled = tk.BooleanVar(value=False)
    color_enable_frame = ctk.CTkFrame(color_row1, fg_color='transparent')
    color_enable_frame.pack(side='left')
    ctk.CTkLabel(color_enable_frame, text='启用', font=Theme.get_font('sm')).pack(side='left', padx=(0, 4))
    ctk.CTkSwitch(color_enable_frame, text='', width=36, variable=app.color_enabled).pack(side='left')
    
    color_row2 = ctk.CTkFrame(color_content, fg_color='transparent')
    color_row2.pack(fill='x', pady=4)
    AnimatedButton(color_row2, text='选择区域', font=Theme.get_font('xs'), width=60, height=24, corner_radius=4,
                  fg_color=Theme.COLORS['primary'], hover_color=Theme.COLORS['primary_hover'],
                  command=lambda: app.color.select_region() if hasattr(app, 'color') else None).pack(side='left', padx=(0, 4))
    app.color_region = ctk.CTkEntry(color_row2, textvariable=app.region_var, width=120, height=24, state='disabled')
    app.color_region.pack(side='left')
    
    color_row3 = ctk.CTkFrame(color_content, fg_color='transparent')
    color_row3.pack(fill='x', pady=4)
    AnimatedButton(color_row3, text='选择颜色', font=Theme.get_font('xs'), width=60, height=24, corner_radius=4,
                  fg_color=Theme.COLORS['primary'], hover_color=Theme.COLORS['primary_hover'],
                  command=lambda: app.color.select_color() if hasattr(app, 'color') else None).pack(side='left', padx=(0, 4))
    app.color_display = ctk.CTkFrame(color_row3, width=40, height=24, fg_color='gray', corner_radius=4, border_width=1, border_color='#000000')
    app.color_display.pack(side='left', padx=(0, 8))
    ctk.CTkLabel(color_row3, text='容差:', font=Theme.get_font('xs')).pack(side='left')
    app.color_tolerance = NumericEntry(color_row3, textvariable=app.tolerance_var, width=40, height=24)
    app.color_tolerance.pack(side='left', padx=(2, 8))
    ctk.CTkLabel(color_row3, text='间隔:', font=Theme.get_font('xs')).pack(side='left')
    app.color_interval = NumericEntry(color_row3, textvariable=app.interval_var, width=40, height=24)
    app.color_interval.pack(side='left', padx=(2, 0))
    ctk.CTkLabel(color_row3, text='秒', font=Theme.get_font('xs')).pack(side='left')
    
    ctk.CTkLabel(color_content, text='执行命令:', font=Theme.get_font('sm')).pack(anchor='w', pady=(8, 2))
    app.color_commands = ctk.CTkTextbox(color_content, font=('Consolas', 10), height=100)
    app.color_commands.pack(fill='both', expand=True)
    
    info_label = ctk.CTkLabel(color_content, text="额外命令: StartScript/StopScript；用于开始/停止脚本运行", 
                              font=Theme.get_font('xs'), text_color=Theme.COLORS['text_muted'])
    info_label.pack(anchor='w', pady=(4, 0))

def insert_key_command(app):
    key = app.key_var.get().strip()
    key_type = app.key_type.get()
    count = app.key_count.get()
    
    if not key:
        messagebox.showwarning("警告", "请输入按键名称！")
        return
    
    if count < 1:
        messagebox.showwarning("警告", "请输入有效的执行次数！")
        return
    
    command = f'{key_type} "{key}", {count}\n'
    
    current_tab = app.script_tabview.get()
    if "颜色" in current_tab and hasattr(app, 'color_commands'):
        app.color_commands.insert(tk.INSERT, command)
        app.color_commands.see(tk.END)
    elif hasattr(app, 'script_text'):
        app.script_text.insert(tk.INSERT, command)
        app.script_text.see(tk.END)

def insert_delay_command(app):
    delay = app.delay_var.get().strip()
    
    if not delay.isdigit() or int(delay) < 0:
        messagebox.showwarning("警告", "请输入有效的延迟时间！")
        return
    
    command = f"Delay {delay}\n"
    
    current_tab = app.script_tabview.get()
    if "颜色" in current_tab and hasattr(app, 'color_commands'):
        app.color_commands.insert(tk.INSERT, command)
        app.color_commands.see(tk.END)
    elif hasattr(app, 'script_text'):
        app.script_text.insert(tk.INSERT, command)
        app.script_text.see(tk.END)

def insert_mouse_click_command(app):
    button = app.mouse_button_var.get()
    action = app.mouse_action_var.get()
    count = app.mouse_count_var.get()
    
    if count < 1:
        messagebox.showwarning("警告", "请输入有效的执行次数！")
        return
    
    mouse_command = f"{button}{action} {count}\n"
    
    current_tab = app.script_tabview.get()
    if "颜色" in current_tab and hasattr(app, 'color_commands'):
        app.color_commands.insert(tk.INSERT, mouse_command)
        app.color_commands.see(tk.END)
    elif hasattr(app, 'script_text'):
        app.script_text.insert(tk.INSERT, mouse_command)
        app.script_text.see(tk.END)

def select_coordinate(app):
    app.log_message("开始选择坐标点...")
    create_coordinate_selection_window(app)

def create_coordinate_selection_window(app):
    try:
        import screeninfo
        monitors = screeninfo.get_monitors()
        
        min_x = min(monitor.x for monitor in monitors)
        min_y = min(monitor.y for monitor in monitors)
        max_x = max(monitor.x + monitor.width for monitor in monitors)
        max_y = max(monitor.y + monitor.height for monitor in monitors)
    except ImportError:
        messagebox.showerror("错误", "screeninfo库未安装，无法支持多显示器选择。")
        return
    except Exception:
        min_x, min_y, max_x, max_y = 0, 0, 1920, 1080
    
    app.coordinate_window = tk.Toplevel(app.root)
    app.coordinate_window.overrideredirect(True)
    app.coordinate_window.geometry(f"{max_x - min_x}x{max_y - min_y}+{min_x}+{min_y}")
    app.coordinate_window.attributes("-alpha", 0.3)
    app.coordinate_window.attributes("-topmost", True)
    app.coordinate_window.configure(cursor="crosshair")
    
    app.coordinate_canvas = tk.Canvas(app.coordinate_window, bg="white", highlightthickness=0)
    app.coordinate_canvas.pack(fill=tk.BOTH, expand=True)
    
    app.coordinate_canvas.bind("<Button-1>", lambda e: on_coordinate_select(app, e))
    app.coordinate_window.bind("<Escape>", lambda e: app.coordinate_window.destroy())
    
    app.coordinate_window.focus_set()

def on_coordinate_select(app, event):
    abs_x = event.x_root
    abs_y = event.y_root
    
    app.coordinate_window.destroy()
    
    coordinate_command = f"MoveTo {abs_x}, {abs_y}\n"
    
    current_tab = app.script_tabview.get()
    if "颜色" in current_tab and hasattr(app, 'color_commands'):
        app.color_commands.insert(tk.INSERT, coordinate_command)
        app.color_commands.see(tk.END)
    elif hasattr(app, 'script_text'):
        app.script_text.insert(tk.INSERT, coordinate_command)
        app.script_text.see(tk.END)
    
    app.log_message(f"已选择坐标点: ({abs_x}, {abs_y})")

def insert_combo_command(app):
    key = app.combo_key_var.get().strip()
    key_delay = app.combo_key_delay.get().strip()
    after_delay = app.combo_after_delay.get().strip()
    
    if not key:
        messagebox.showwarning("警告", "请输入按键名称！")
        return
    
    if not key_delay.isdigit() or int(key_delay) < 0:
        messagebox.showwarning("警告", "请输入有效的按键延迟时间！")
        return
    
    if not after_delay.isdigit() or int(after_delay) < 0:
        messagebox.showwarning("警告", "请输入有效的抬起后延迟时间！")
        return
    
    combo_command = f'Delay {key_delay}\nKeyDown "{key}", 1\nDelay {after_delay}\nKeyUp "{key}", 1\n'
    
    current_tab = app.script_tabview.get()
    if "颜色" in current_tab and hasattr(app, 'color_commands'):
        app.color_commands.insert(tk.INSERT, combo_command)
        app.color_commands.see(tk.END)
    elif hasattr(app, 'script_text'):
        app.script_text.insert(tk.INSERT, combo_command)
        app.script_text.see(tk.END)

def check_script_modified(app):
    """检查脚本是否已修改，返回True表示可以继续操作"""
    if hasattr(app, 'script_modified') and app.script_modified:
        result = askyesnocancel_centered(app.root, "保存确认", "当前脚本已修改，是否保存？")
        if result is None:
            return False
        elif result:
            save_script(app)
    return True

def new_script(app):
    """新建脚本"""
    if not check_script_modified(app):
        return
    
    app.script_text.delete(1.0, tk.END)
    app.script_file_path_var.set("未保存")
    app.script_file_path = None
    app.script_modified = False
    app.script_original_content = ""

def clear_script(app):
    if askyesno_centered(app.root, "确认", "确定要清空当前脚本吗？"):
        app.script_text.delete(1.0, tk.END)
        app.script_file_path_var.set("未保存")
        app.script_modified = False

def save_script(app):
    current_path = app.script_file_path_var.get()
    if current_path and current_path != "未保存":
        file_path = current_path
    else:
        import os
        initial_dir = None
        if hasattr(app, 'script_file_path') and app.script_file_path:
            initial_dir = os.path.dirname(app.script_file_path)
        
        file_path = filedialog.asksaveasfilename(
            initialdir=initial_dir,
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            title="保存脚本"
        )
    
    if file_path:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(app.script_text.get(1.0, tk.END))
            app.script_file_path_var.set(file_path)
            app.script_file_path = file_path
            import os
            app.script_file_path_label.configure(text=os.path.basename(file_path))
            app.script_modified = False
            app.script_original_content = app.script_text.get(1.0, tk.END)
            messagebox.showinfo("成功", f"脚本已保存到: {file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"保存脚本失败: {str(e)}")

def save_script_as(app):
    import os
    initial_dir = None
    if hasattr(app, 'script_file_path') and app.script_file_path:
        initial_dir = os.path.dirname(app.script_file_path)
    
    file_path = filedialog.asksaveasfilename(
        initialdir=initial_dir,
        defaultextension=".txt",
        filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
        title="另存为"
    )
    if file_path:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(app.script_text.get(1.0, tk.END))
            app.script_file_path_var.set(file_path)
            app.script_file_path = file_path
            import os
            app.script_file_path_label.configure(text=os.path.basename(file_path))
            app.script_modified = False
            app.script_original_content = app.script_text.get(1.0, tk.END)
            messagebox.showinfo("成功", f"脚本已保存到: {file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"保存脚本失败: {str(e)}")

def load_script(app):
    if not check_script_modified(app):
        return
    
    initial_dir = None
    if hasattr(app, 'script_file_path') and app.script_file_path:
        import os
        initial_dir = os.path.dirname(app.script_file_path)
    
    file_path = filedialog.askopenfilename(
        initialdir=initial_dir,
        filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
        title="打开脚本"
    )
    if file_path:
        try:
            encodings = ['utf-8', 'gbk', 'gb2312', 'ansi']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                messagebox.showerror("错误", "无法读取文件，编码不支持！")
                return
            
            app.script_text.delete(1.0, tk.END)
            app.script_text.insert(1.0, content)
            app.script_file_path_var.set(file_path)
            app.script_file_path = file_path
            import os
            app.script_file_path_label.configure(text=os.path.basename(file_path))
            app.script_modified = False
            app.script_original_content = content
            messagebox.showinfo("成功", f"脚本已从: {file_path} 加载")
        except Exception as e:
            messagebox.showerror("错误", f"加载脚本失败: {str(e)}")