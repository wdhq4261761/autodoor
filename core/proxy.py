"""
代理类模块，按功能分组管理代理方法
"""
import tkinter as tk

from ui.ocr_tab import (
    create_ocr_tab, create_ocr_group, add_ocr_group,
    delete_ocr_group, renumber_ocr_groups,
    start_ocr_region_selection
)
from ui.timed_tab import (
    create_timed_tab, create_timed_group, add_timed_group,
    delete_timed_group, renumber_timed_groups
)
from ui.number_tab import (
    create_number_tab, create_number_region, add_number_region,
    delete_number_region, renumber_number_regions,
    start_number_region_selection
)
from ui.script_tab import create_script_tab
from ui.home import create_home_tab
from ui.basic_tab import create_basic_tab
from ui.image_tab import (
    create_image_tab, create_image_group, add_image_group,
    delete_image_group, renumber_image_groups,
    start_image_region_selection, select_reference_image
)


class OCRProxy:
    """OCR功能代理类"""
    
    def __init__(self, app):
        self.app = app
    
    def create_tab(self, parent):
        """创建文字识别标签页"""
        create_ocr_tab(self.app)
    
    def create_group(self, index):
        """创建单个文字识别组"""
        create_ocr_group(self.app, index)
    
    def add_group(self):
        """新增文字识别组"""
        add_ocr_group(self.app)
    
    def delete_group_by_button(self, button):
        """通过按钮删除对应的文字识别组"""
        pass
    
    def delete_group(self, index, confirm=True):
        """删除文字识别组"""
        delete_ocr_group(self.app, index, confirm)
    
    def renumber_groups(self):
        """重新编号所有文字识别组"""
        renumber_ocr_groups(self.app)
    
    def start_region_selection(self, index):
        """开始选择OCR识别区域"""
        start_ocr_region_selection(self.app, index)
    
    def start_monitoring(self):
        """开始监控"""
        self.app.ocr_module.start_monitoring()
    
    def stop_monitoring(self):
        """停止监控"""
        self.app.ocr_module.stop_monitoring()


class TimedProxy:
    """定时功能代理类"""
    
    def __init__(self, app):
        self.app = app
    
    def create_tab(self, parent):
        """创建定时功能标签页"""
        create_timed_tab(self.app)
    
    def create_group(self, index):
        """创建单个定时组"""
        create_timed_group(self.app, index)
    
    def add_group(self):
        """新增定时组"""
        add_timed_group(self.app)
    
    def delete_group_by_button(self, button):
        """通过按钮删除对应的定时组"""
        pass
    
    def delete_group(self, index, confirm=True):
        """删除定时组"""
        delete_timed_group(self.app, index, confirm)
    
    def renumber_groups(self):
        """重新编号所有定时组"""
        renumber_timed_groups(self.app)
    
    def start_tasks(self):
        """启动定时任务"""
        self.app.timed_module.start_timed_tasks()
    
    def stop_tasks(self):
        """停止定时功能"""
        self.app.timed_module.stop_timed_tasks()


class NumberProxy:
    """数字识别代理类"""
    
    def __init__(self, app):
        self.app = app
    
    def create_tab(self, parent):
        """创建数字识别标签页"""
        create_number_tab(self.app)
    
    def create_region(self, index):
        """创建单个数字识别区域"""
        create_number_region(self.app, index)
    
    def add_region(self):
        """新增数字识别区域"""
        add_number_region(self.app)
    
    def delete_region_by_button(self, button):
        """通过按钮删除对应的数字识别区域"""
        pass
    
    def delete_region(self, index, confirm=True):
        """删除数字识别区域"""
        delete_number_region(self.app, index, confirm)
    
    def renumber_regions(self):
        """重新编号所有数字识别区域"""
        renumber_number_regions(self.app)
    
    def start_region_selection(self, region_index):
        """开始数字识别区域选择"""
        start_number_region_selection(self.app, region_index)
    
    def start_recognition(self):
        """开始数字识别"""
        self.app.number_module.start_number_recognition()
    
    def stop_recognition(self):
        """停止数字识别"""
        self.app.number_module.stop_number_recognition()


class ScriptProxy:
    """脚本功能代理类"""
    
    def __init__(self, app):
        self.app = app
    
    def create_tab(self, parent):
        """创建脚本运行标签页"""
        create_script_tab(self.app)
    
    def start(self, start_color_recognition=True):
        """启动脚本"""
        self.app.script_module.start_script(start_color_recognition)
    
    def stop(self, stop_color_recognition=True):
        """停止脚本执行"""
        self.app.script_module.stop_script(stop_color_recognition)
    
    def start_recording(self):
        """开始录制脚本"""
        self.app.script_module.start_recording()
    
    def stop_recording(self):
        """停止录制脚本"""
        self.app.script_module.stop_recording()


class ColorProxy:
    """颜色识别代理类"""
    
    def __init__(self, app):
        self.app = app
    
    def select_region(self):
        """选择颜色识别区域"""
        self.app.color_recognition_manager.select_color_region()
    
    def select_color(self):
        """选择颜色"""
        self.app.color_recognition_manager.select_color()
    
    def start_recognition(self):
        """开始颜色识别"""
        self.app.color_recognition_manager.start_color_recognition()
    
    def stop_recognition(self):
        """停止颜色识别"""
        self.app.color_recognition_manager.stop_color_recognition()


class ImageDetectionProxy:
    """图像检测代理类"""
    
    def __init__(self, app):
        self.app = app
    
    def create_tab(self, parent):
        """创建图像检测标签页"""
        create_image_tab(self.app)
    
    def create_group(self, index):
        """创建单个图像检测组"""
        create_image_group(self.app, index)
    
    def add_group(self):
        """新增图像检测组"""
        add_image_group(self.app)
    
    def delete_group(self, index, confirm=True):
        """删除图像检测组"""
        delete_image_group(self.app, index, confirm)
    
    def renumber_groups(self):
        """重新编号所有图像检测组"""
        renumber_image_groups(self.app)
    
    def start_region_selection(self, index):
        """开始选择检测区域"""
        start_image_region_selection(self.app, index)
    
    def select_reference_image(self, index):
        """选择参考图像"""
        select_reference_image(self.app, index)
    
    def start_detection(self):
        """开始图像检测"""
        self.app.image_detection_manager.start_all_detection()
    
    def stop_detection(self):
        """停止图像检测"""
        self.app.image_detection_manager.stop_all_detection()


class UIProxy:
    """UI工具代理类"""
    
    def __init__(self, app):
        self.app = app
    
    def create_home_tab(self, parent):
        """创建首页标签页"""
        create_home_tab(self.app)
    
    def create_basic_tab(self, parent):
        """创建基本设置标签页"""
        create_basic_tab(self.app)
    
    def show_message(self, title, message):
        """显示消息对话框"""
        from tkinter import messagebox
        messagebox.showinfo(title, message)
    
    def show_progress(self, message):
        """显示进度提示"""
        if hasattr(self.app, 'status_var'):
            self.app.status_var.set(message)
        self.app.root.update_idletasks()
    
    def hide_progress(self):
        """隐藏进度提示"""
        if hasattr(self.app, 'status_var'):
            self.app.status_var.set("")
        self.app.root.update_idletasks()
