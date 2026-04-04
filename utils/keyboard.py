def start_key_listening(app, target_var, button, is_shortcut=False):
    """开始监听用户按下的按键"""
    current_focus = app.root.focus_get()
    
    original_status = app.status_var.get()
    
    original_text = button.cget("text")
    if hasattr(button, 'configure'):
        button.configure(state="disabled")
    else:
        button.configure(state="disabled")
    
    app.status_var.set("请按任意按键进行设置，按ESC键清空当前记录")
    
    def on_key_press(event):
        """处理按键按下事件
        屏蔽中文输入法，只处理物理按键事件
        """
        app.status_var.set(original_status)
        
        keysym = event.keysym
        
        if not keysym:
            return "break"
        
        allowed_function_keys = [
            "Insert", "Delete", "Home", "End", "Prior", "Next", "PageUp", "PageDown",
            "Up", "Down", "Left", "Right",
            "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12",
            "Escape", "Tab", "Return", "Enter", "Space", "space", "BackSpace", "Backspace",
            "Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L", "Alt_R"
        ]
        
        if not (
            len(keysym) == 1 or 
            keysym in allowed_function_keys or 
            keysym.startswith("Key")
        ):
            return "break"
        
        keysym_map = {
            "Prior": "PageUp",
            "Next": "PageDown",
            "Return": "Enter",
            "space": "Space"
        }
        
        keysym = keysym_map.get(keysym, keysym)
        
        if keysym == "Escape":
            _set_target_value(target_var, "")
            _restore_button_state(button)
            app.root.unbind("<KeyPress>", funcid=key_listener_id)
            if current_focus:
                current_focus.focus_set()
            return "break"
        
        _set_target_value(target_var, keysym)
        
        if is_shortcut:
            app.update_hotkey()
        
        _restore_button_state(button)
        app.root.unbind("<KeyPress>", funcid=key_listener_id)
        if current_focus:
            current_focus.focus_set()
        
        return "break"
    
    key_listener_id = app.root.bind("<KeyPress>", on_key_press)
    app.root.focus_set()


def _set_target_value(target_var, value):
    """设置目标变量的值，支持StringVar和CTkEntry"""
    if hasattr(target_var, 'set'):
        target_var.set(value)
    elif hasattr(target_var, 'configure'):
        target_var.configure(state='normal')
        target_var.delete(0, 'end')
        if value:
            target_var.insert(0, value)
        target_var.configure(state='disabled')


def _restore_button_state(button):
    """恢复按钮状态，支持CustomTkinter和Tkinter"""
    if hasattr(button, 'configure'):
        button.configure(state="normal")
    else:
        button.configure(state="normal")