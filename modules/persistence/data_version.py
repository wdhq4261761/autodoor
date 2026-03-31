"""
数据版本管理器

提供数据格式版本迁移、数据校验功能
"""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, Optional


class DataVersionManager:
    """
    数据版本管理器
    
    功能：
    - 数据版本迁移
    - 数据完整性校验
    """
    
    CURRENT_VERSION = "2.0"
    
    VERSION_MIGRATIONS = {
        "1.0": "_migrate_v1_to_v2",
        "1.5": "_migrate_v1_5_to_v2",
    }
    
    @classmethod
    def migrate(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        迁移数据到当前版本
        
        Args:
            data: 原始数据
            
        Returns:
            迁移后的数据
        """
        if not data:
            return data
        
        version = data.get("version", "1.0")
        
        while version != cls.CURRENT_VERSION:
            if version not in cls.VERSION_MIGRATIONS:
                data["version"] = cls.CURRENT_VERSION
                break
            
            migration_func = getattr(cls, cls.VERSION_MIGRATIONS[version])
            data = migration_func(data)
            version = data.get("version", cls.CURRENT_VERSION)
        
        return data
        
    @classmethod
    def _migrate_v1_to_v2(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        从v1.0迁移到v2.0
        
        变更：
        - 添加format_type字段
        - 添加metadata字段
        - 迁移节点位置格式
        """
        data["version"] = "2.0"
        data["format_type"] = "behavior_tree_editor"
        
        if "metadata" not in data:
            data["metadata"] = {
                "created_at": data.get("created_at", ""),
                "modified_at": data.get("modified_at", datetime.now().isoformat()),
                "app_version": "1.0.0",
                "save_type": "migrated",
                "checksum": ""
            }
        
        if "nodes" in data:
            for node_id, node in data["nodes"].items():
                if "position" not in node:
                    node["position"] = {
                        "x": node.get("x", 0),
                        "y": node.get("y", 0)
                    }
                    if "x" in node:
                        del node["x"]
                    if "y" in node:
                        del node["y"]
        
        if "canvas" not in data:
            data["canvas"] = {
                "name": data.get("name", "未命名"),
                "description": "",
                "viewport": {
                    "zoom": 1.0,
                    "offset_x": 0,
                    "offset_y": 0
                },
                "grid": {
                    "enabled": True,
                    "size": 20
                }
            }
        
        return data
        
    @classmethod
    def _migrate_v1_5_to_v2(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        从v1.5迁移到v2.0
        
        变更：
        - 添加format_type字段
        - 完善metadata字段
        """
        data["version"] = "2.0"
        data["format_type"] = "behavior_tree_editor"
        
        if "metadata" not in data:
            data["metadata"] = {}
        
        data["metadata"]["app_version"] = data.get("app_version", "1.0.0")
        data["metadata"]["save_type"] = "migrated"
        
        return data
        
    @classmethod
    def calculate_checksum(cls, data: Dict[str, Any]) -> str:
        """
        计算数据校验和
        
        Args:
            data: 数据字典
            
        Returns:
            校验和字符串
        """
        data_copy = {}
        for k, v in data.items():
            if k == "metadata":
                metadata_copy = {mk: mv for mk, mv in v.items() if mk != "checksum"}
                data_copy[k] = metadata_copy
            else:
                data_copy[k] = v
        
        json_str = json.dumps(data_copy, sort_keys=True, ensure_ascii=False)
        checksum = hashlib.sha256(json_str.encode()).hexdigest()[:16]
        return f"sha256:{checksum}"
        
    @classmethod
    def verify_checksum(cls, data: Dict[str, Any]) -> bool:
        """
        验证数据校验和
        
        Args:
            data: 数据字典
            
        Returns:
            是否验证通过
        """
        if "metadata" not in data or "checksum" not in data["metadata"]:
            return True
        
        expected = data["metadata"]["checksum"]
        if not expected:
            return True
        
        actual = cls.calculate_checksum(data)
        return expected == actual
        
    @classmethod
    def validate_structure(cls, data: Dict[str, Any]) -> bool:
        """
        验证数据结构完整性
        
        Args:
            data: 数据字典
            
        Returns:
            是否验证通过
        """
        if not isinstance(data, dict):
            return False
        
        required_fields = ["version", "nodes"]
        
        for field in required_fields:
            if field not in data:
                return False
        
        if not isinstance(data["nodes"], dict):
            return False
        
        return True
        
    @classmethod
    def add_metadata(
        cls,
        data: Dict[str, Any],
        save_type: str = "auto",
        app_version: str = "1.0.0"
    ) -> Dict[str, Any]:
        """
        添加元数据
        
        Args:
            data: 数据字典
            save_type: 保存类型
            app_version: 应用版本
            
        Returns:
            添加元数据后的数据
        """
        if "metadata" not in data:
            data["metadata"] = {}
        
        now = datetime.now().isoformat()
        
        if not data["metadata"].get("created_at"):
            data["metadata"]["created_at"] = now
        
        data["metadata"]["modified_at"] = now
        data["metadata"]["app_version"] = app_version
        data["metadata"]["save_type"] = save_type
        data["metadata"]["checksum"] = cls.calculate_checksum(data)
        
        data["version"] = cls.CURRENT_VERSION
        data["format_type"] = "behavior_tree_editor"
        
        return data
        
    @classmethod
    def get_version_info(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取版本信息
        
        Args:
            data: 数据字典
            
        Returns:
            版本信息字典
        """
        return {
            "data_version": data.get("version", "unknown"),
            "current_version": cls.CURRENT_VERSION,
            "needs_migration": data.get("version", "1.0") != cls.CURRENT_VERSION,
            "format_type": data.get("format_type", "unknown"),
            "app_version": data.get("metadata", {}).get("app_version", "unknown"),
            "save_type": data.get("metadata", {}).get("save_type", "unknown"),
            "created_at": data.get("metadata", {}).get("created_at", ""),
            "modified_at": data.get("metadata", {}).get("modified_at", "")
        }
