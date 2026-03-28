"""
行为树标签页

创建行为树可视化编辑器标签页
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING

from ui.theme import Theme
from ui.bt_editor import BehaviorTreeEditor

if TYPE_CHECKING:
    from autodoor import AutoDoorOCR


def create_bt_tab(app: "AutoDoorOCR"):
    """创建行为树标签页"""
    page = ctk.CTkFrame(app.content_area, fg_color="transparent")
    page.pack(fill="both", expand=True)
    app.pages["behavior_tree"] = page
    
    app.bt_editor = BehaviorTreeEditor(page, app)
    app.bt_editor.pack(fill="both", expand=True)
