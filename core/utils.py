import tkinter as tk
from tkinter import messagebox


def handle_error(func, logging_manager=None, *args, **kwargs):
    """
    处理函数执行错误的通用方法
    Args:
        func: 要执行的函数
        logging_manager: 日志管理器实例
        *args: 函数参数
        **kwargs: 关键字参数
    Returns:
        函数执行结果，出错时返回None
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        # 获取调用信息
        import traceback
        caller_frame = traceback.extract_stack()[-3]
        caller_func = caller_frame.name
        
        # 构造错误信息
        error_msg = f"{caller_func}错误: {str(e)}"
        if logging_manager:
            logging_manager.log_message(error_msg)
            logging_manager.log_message(f"错误详情: {traceback.format_exc()}")
        return None


def delete_group_by_button(app, button, groups, group_type, delete_func):
    """通用的通过按钮删除组的方法
    Args:
        app: 主应用实例
        button: 触发删除的按钮
        groups: 组列表
        group_type: 组类型名称（用于日志）
        delete_func: 删除函数
    """
    for i, group in enumerate(groups):
        group_frame = group["frame"]
        if button.winfo_parent() == str(group_frame):
            delete_func(i)
            return
        
        for child in group_frame.winfo_children():
            if button.winfo_parent() == str(child):
                delete_func(i)
                return
    
    messagebox.showerror("错误", f"无法找到对应的{group_type}，请重试！")


def exit_program(app):
    """退出程序
    Args:
        app: 主应用实例
    """
    app.save_config()
    
    if app.is_running:
        app.ocr.stop_monitoring()
    app.timed_module.stop_timed_tasks()
    app.number_module.stop_number_recognition()

    if hasattr(app, 'script_executor') and app.script_executor.is_running:
        app.script_executor.stop_script()

    if hasattr(app, 'color_recognition_manager') and hasattr(app.color_recognition_manager, 'color_recognition'):
        cr = app.color_recognition_manager.color_recognition
        if cr and hasattr(cr, 'is_running') and cr.is_running:
            cr.stop_recognition()

    if hasattr(app, 'global_listener') and app.global_listener:
        app.global_listener.stop()

    app.event_manager.is_event_running = False
    
    app.logging_manager.log_message("程序正在退出...")
    app.root.quit()
    app.root.destroy()
