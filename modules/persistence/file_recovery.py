"""
文件恢复处理器

提供文件损坏检测、恢复、启动时恢复检测功能
"""

import gzip
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class FileRecoveryHandler:
    """
    文件恢复处理器
    
    功能：
    - 文件完整性验证
    - 文件损坏恢复
    - 启动时恢复检测
    """
    
    def __init__(
        self,
        autosave_dir: str = "data/autosave",
        recovery_dir: str = "data/recovery",
        log_func: Optional[callable] = None
    ):
        """
        初始化文件恢复处理器
        
        Args:
            autosave_dir: 自动保存目录
            recovery_dir: 崩溃恢复目录
            log_func: 日志记录函数
        """
        self._autosave_dir = Path(autosave_dir)
        self._recovery_dir = Path(recovery_dir)
        self._log_func = log_func
        
    def verify_file(self, filepath: Path) -> bool:
        """
        验证文件完整性
        
        Args:
            filepath: 文件路径
            
        Returns:
            是否验证通过
        """
        if not filepath.exists():
            return False
        
        try:
            if filepath.suffix == '.gz':
                with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            return self._validate_data_structure(data)
        except Exception:
            return False
            
    def _validate_data_structure(self, data: Dict[str, Any]) -> bool:
        """
        验证数据结构
        
        Args:
            data: 数据字典
            
        Returns:
            是否验证通过
        """
        if not isinstance(data, dict):
            return False
        
        if "nodes" not in data:
            return False
        
        if not isinstance(data["nodes"], dict):
            return False
        
        return True
        
    def find_recoverable_files(self) -> List[Dict[str, Any]]:
        """
        查找所有可恢复的文件
        
        Returns:
            可恢复文件列表（按时间倒序）
        """
        recoverable = []
        
        for i in range(1, 4):
            filepath = self._autosave_dir / f"autosave_{i}.json.gz"
            if filepath.exists():
                valid = self.verify_file(filepath)
                stat = filepath.stat()
                recoverable.append({
                    "path": str(filepath),
                    "type": "autosave",
                    "index": i,
                    "mtime": stat.st_mtime,
                    "size": stat.st_size,
                    "valid": valid
                })
        
        if self._recovery_dir.exists():
            for filepath in self._recovery_dir.glob("crash_*.json"):
                valid = self.verify_file(filepath)
                stat = filepath.stat()
                recoverable.append({
                    "path": str(filepath),
                    "type": "crash",
                    "index": 0,
                    "mtime": stat.st_mtime,
                    "size": stat.st_size,
                    "valid": valid
                })
        
        return sorted(recoverable, key=lambda x: x["mtime"], reverse=True)
        
    def load_file(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """
        加载文件数据
        
        Args:
            filepath: 文件路径
            
        Returns:
            文件数据，加载失败返回None
        """
        try:
            if filepath.suffix == '.gz':
                with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                    return json.load(f)
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            if self._log_func:
                self._log_func(f"[文件恢复] 加载文件失败: {filepath} - {e}")
            return None
            
    def get_best_recovery_file(self) -> Optional[Dict[str, Any]]:
        """
        获取最佳恢复文件
        
        Returns:
            最佳恢复文件信息，不存在则返回None
        """
        files = self.find_recoverable_files()
        
        for file_info in files:
            if file_info["valid"]:
                return file_info
        
        return None
        
    def has_recovery_data(self) -> bool:
        """
        检查是否存在恢复数据
        
        Returns:
            是否存在恢复数据
        """
        files = self.find_recoverable_files()
        return any(f["valid"] for f in files)
        
    def check_and_get_recovery(self) -> Optional[Dict[str, Any]]:
        """
        检查并获取恢复数据
        
        Returns:
            恢复数据，不存在则返回None
        """
        best_file = self.get_best_recovery_file()
        
        if not best_file:
            return None
        
        data = self.load_file(Path(best_file["path"]))
        
        if data:
            return {
                "data": data,
                "source": best_file["type"],
                "path": best_file["path"],
                "mtime": datetime.fromtimestamp(best_file["mtime"]).isoformat()
            }
        
        return None
        
    def cleanup_recovery_files(self, keep_crash_days: int = 7) -> Dict[str, int]:
        """
        清理恢复文件
        
        Args:
            keep_crash_days: 保留崩溃文件的天数
            
        Returns:
            清理统计
        """
        stats = {
            "autosave_deleted": 0,
            "crash_deleted": 0
        }
        
        cutoff_time = datetime.now().timestamp() - (keep_crash_days * 24 * 60 * 60)
        
        if self._recovery_dir.exists():
            for filepath in self._recovery_dir.glob("crash_*.json"):
                try:
                    if filepath.stat().st_mtime < cutoff_time:
                        filepath.unlink()
                        stats["crash_deleted"] += 1
                except Exception:
                    continue
        
        return stats
        
    def get_recovery_summary(self) -> Dict[str, Any]:
        """
        获取恢复数据摘要
        
        Returns:
            恢复数据摘要
        """
        files = self.find_recoverable_files()
        
        autosave_count = sum(1 for f in files if f["type"] == "autosave" and f["valid"])
        crash_count = sum(1 for f in files if f["type"] == "crash" and f["valid"])
        
        latest_autosave = None
        latest_crash = None
        
        for f in files:
            if f["type"] == "autosave" and f["valid"] and not latest_autosave:
                latest_autosave = {
                    "path": f["path"],
                    "mtime": datetime.fromtimestamp(f["mtime"]).isoformat(),
                    "size": f["size"]
                }
            elif f["type"] == "crash" and f["valid"] and not latest_crash:
                latest_crash = {
                    "path": f["path"],
                    "mtime": datetime.fromtimestamp(f["mtime"]).isoformat(),
                    "size": f["size"]
                }
        
        return {
            "has_recovery_data": autosave_count > 0 or crash_count > 0,
            "autosave_count": autosave_count,
            "crash_count": crash_count,
            "latest_autosave": latest_autosave,
            "latest_crash": latest_crash,
            "total_files": len(files),
            "valid_files": sum(1 for f in files if f["valid"])
        }
