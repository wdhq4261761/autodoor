"""
自动保存管理器

提供定时自动保存、变更触发保存、备份文件轮转功能
"""

import gzip
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional


class AutoSaveManager:
    """
    自动保存管理器
    
    功能：
    - 定时自动保存（默认60秒间隔）
    - 变更后延迟保存（默认5秒延迟）
    - 备份文件轮转（保留最近3个备份）
    """
    
    AUTO_SAVE_INTERVAL = 60
    SAVE_DELAY_AFTER_CHANGE = 5
    MAX_BACKUP_COUNT = 3
    
    def __init__(
        self,
        get_data_func: Callable[[], Dict[str, Any]],
        on_save_callback: Optional[Callable[[bool], None]] = None,
        autosave_dir: str = "data/autosave",
        get_file_path_func: Optional[Callable[[], Optional[str]]] = None
    ):
        """
        初始化自动保存管理器
        
        Args:
            get_data_func: 获取当前画板数据的函数
            on_save_callback: 保存完成后的回调函数，参数为是否成功
            autosave_dir: 自动保存目录
            get_file_path_func: 获取当前文件路径的函数，如果有则保存到该路径
        """
        self._get_data_func = get_data_func
        self._on_save_callback = on_save_callback
        self._autosave_dir = Path(autosave_dir)
        self._get_file_path_func = get_file_path_func
        self._save_timer: Optional[threading.Timer] = None
        self._is_running = False
        self._last_save_time: float = 0
        self._save_lock = threading.Lock()
        
    def start(self) -> None:
        """启动自动保存"""
        if self._is_running:
            return
        
        self._is_running = True
        self._autosave_dir.mkdir(parents=True, exist_ok=True)
        self._schedule_auto_save()
        
    def stop(self) -> None:
        """停止自动保存"""
        self._is_running = False
        if self._save_timer:
            self._save_timer.cancel()
            self._save_timer = None
            
    def save_now(self) -> bool:
        """
        立即执行保存
        
        Returns:
            是否保存成功
        """
        return self._do_save()
        
    def on_content_changed(self) -> None:
        """
        内容变更时触发延迟保存
        """
        if not self._is_running:
            return
        
        if self._save_timer:
            self._save_timer.cancel()
        
        self._save_timer = threading.Timer(
            self.SAVE_DELAY_AFTER_CHANGE,
            self._delayed_save
        )
        self._save_timer.daemon = True
        self._save_timer.start()
        
    def _schedule_auto_save(self) -> None:
        """调度下一次自动保存"""
        if not self._is_running:
            return
        
        self._save_timer = threading.Timer(
            self.AUTO_SAVE_INTERVAL,
            self._auto_save
        )
        self._save_timer.daemon = True
        self._save_timer.start()
        
    def _auto_save(self) -> None:
        """执行定时自动保存"""
        self._do_save()
        self._schedule_auto_save()
        
    def _delayed_save(self) -> None:
        """执行延迟保存"""
        self._do_save()
        self._schedule_auto_save()
        
    def _do_save(self) -> bool:
        """
        执行保存操作
        
        Returns:
            是否保存成功
        """
        with self._save_lock:
            try:
                data = self._get_data_func()
                
                if not data or not data.get("nodes"):
                    return False
                
                self._add_metadata(data)
                
                if self._get_file_path_func:
                    file_path = self._get_file_path_func()
                    if file_path:
                        self._save_to_file(data, file_path)
                    else:
                        self._rotate_and_save(data)
                else:
                    self._rotate_and_save(data)
                
                self._last_save_time = time.time()
                
                if self._on_save_callback:
                    self._on_save_callback(True)
                
                return True
                
            except Exception as e:
                if self._on_save_callback:
                    self._on_save_callback(False)
                return False
    
    def _save_to_file(self, data: Dict[str, Any], file_path: str) -> None:
        """保存到指定文件"""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
                
    def _add_metadata(self, data: Dict[str, Any]) -> None:
        """添加元数据"""
        if "metadata" not in data:
            data["metadata"] = {}
        
        data["metadata"]["modified_at"] = datetime.now().isoformat()
        data["metadata"]["save_type"] = "auto"
        
    def _rotate_and_save(self, data: Dict[str, Any]) -> None:
        """
        轮转备份文件并保存新数据
        
        备份文件命名规则：
        - autosave_1.json.gz (最新)
        - autosave_2.json.gz (次新)
        - autosave_3.json.gz (最旧)
        """
        autosave_3 = self._autosave_dir / "autosave_3.json.gz"
        autosave_2 = self._autosave_dir / "autosave_2.json.gz"
        autosave_1 = self._autosave_dir / "autosave_1.json.gz"
        
        if autosave_3.exists():
            autosave_3.unlink()
        
        if autosave_2.exists():
            autosave_2.rename(autosave_3)
        
        if autosave_1.exists():
            autosave_1.rename(autosave_2)
        
        with gzip.open(autosave_1, 'wt', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def get_latest_autosave(self) -> Optional[Dict[str, Any]]:
        """
        获取最新的自动保存数据
        
        Returns:
            自动保存数据，不存在则返回None
        """
        autosave_1 = self._autosave_dir / "autosave_1.json.gz"
        
        if not autosave_1.exists():
            return None
        
        try:
            with gzip.open(autosave_1, 'rt', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
            
    def get_all_autosaves(self) -> list:
        """
        获取所有自动保存文件信息
        
        Returns:
            按时间排序的自动保存文件列表（最新在前）
        """
        autosaves = []
        
        for i in range(1, self.MAX_BACKUP_COUNT + 1):
            filepath = self._autosave_dir / f"autosave_{i}.json.gz"
            if filepath.exists():
                stat = filepath.stat()
                autosaves.append({
                    "path": str(filepath),
                    "index": i,
                    "mtime": stat.st_mtime,
                    "size": stat.st_size
                })
        
        return sorted(autosaves, key=lambda x: x["index"])
        
    def clear_autosaves(self) -> None:
        """清除所有自动保存文件"""
        for i in range(1, self.MAX_BACKUP_COUNT + 1):
            filepath = self._autosave_dir / f"autosave_{i}.json.gz"
            if filepath.exists():
                filepath.unlink()
                
    @property
    def last_save_time(self) -> float:
        """获取上次保存时间戳"""
        return self._last_save_time
        
    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._is_running
