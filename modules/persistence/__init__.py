"""
持久化模块

提供画板元素的自动保存、崩溃恢复、版本管理等功能
"""

from .auto_save import AutoSaveManager
from .crash_recovery import CrashRecoveryHandler
from .data_version import DataVersionManager
from .file_recovery import FileRecoveryHandler

__all__ = [
    "AutoSaveManager",
    "CrashRecoveryHandler",
    "DataVersionManager",
    "FileRecoveryHandler",
]
