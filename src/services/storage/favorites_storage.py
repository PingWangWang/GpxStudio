"""
收藏点持久化存储模块

该模块负责将用户收藏点持久化存储到本地JSON文件（FavoritesList.json），
与 GeoInfoStorage 使用相同的存储模式。收藏点统一以 WGS-84 坐标存储，
渲染时由 MapRenderer 按地图源自动转换为对应坐标系。
"""

import json
import os
from typing import Optional, List, Dict
from datetime import datetime


class FavoritesStorage:
    """收藏点存储类"""

    def __init__(self, storage_file: str = None):
        """
        初始化收藏点存储

        Args:
            storage_file: 存储文件路径（如果为None，使用默认路径）
        """
        if storage_file is None:
            from app.data_paths import get_favorites_file
            self.storage_path = get_favorites_file()
        else:
            self.storage_path = storage_file

        self.favorites_list = []

        # 加载已有数据
        self._load()

    def _load(self):
        """从文件加载收藏点"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    self.favorites_list = json.load(f)
                print(f"[收藏点存储] 加载了 {len(self.favorites_list)} 个收藏点")
            except Exception as e:
                print(f"[收藏点存储] 加载失败: {e}")
                self.favorites_list = []
        else:
            print("[收藏点存储] 未找到收藏点文件，将创建新文件")
            self.favorites_list = []

    def _save(self):
        """保存收藏点到文件"""
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.favorites_list, f, ensure_ascii=False, indent=2)
            print(f"[收藏点存储] 已保存 {len(self.favorites_list)} 个收藏点到 {self.storage_path}")
        except Exception as e:
            print(f"[收藏点存储] 保存失败: {e}")

    def _next_id(self) -> int:
        """生成下一个收藏点ID（当前最大ID + 1）"""
        if not self.favorites_list:
            return 1
        return max(item.get('id', 0) for item in self.favorites_list) + 1

    def _find_duplicate(self, lat: float, lon: float) -> int:
        """
        查找坐标相同的已存在收藏点

        Args:
            lat: 纬度（WGS-84）
            lon: 经度（WGS-84）

        Returns:
            int: 已存在收藏点的索引，-1 表示不存在
        """
        for i, item in enumerate(self.favorites_list):
            item_lat = item.get('lat', 0)
            item_lon = item.get('lon', 0)
            if (abs(item_lat - lat) < 0.0001 and
                    abs(item_lon - lon) < 0.0001):
                return i
        return -1

    def add_favorite(self, name: str, address: str, lat: float, lon: float,
                     note: str = '') -> tuple:
        """
        添加收藏点

        Args:
            name: 收藏点名称
            address: 收藏点地址
            lat: 纬度（WGS-84）
            lon: 经度（WGS-84）
            note: 备注（预留字段，当前版本不收集）

        Returns:
            (success, message): 是否添加成功及结果消息
            坐标重复时返回 (False, "该位置已收藏")
        """
        try:
            # 检查坐标是否已存在
            duplicate_index = self._find_duplicate(lat, lon)
            if duplicate_index >= 0:
                existing = self.favorites_list[duplicate_index]
                return False, f"该位置已收藏：{existing.get('name', '')}"

            # 构建收藏记录
            record = {
                'id': self._next_id(),
                'name': name,
                'address': address,
                'lat': lat,
                'lon': lon,
                'coord_system': 'WGS-84',  # 统一以 WGS-84 存储
                'note': note,
                'created_at': datetime.now().isoformat()
            }

            self.favorites_list.insert(0, record)
            self._save()

            print(f"[收藏点存储] 成功收藏: {name} ({lat}, {lon})")
            return True, "收藏成功"

        except Exception as e:
            print(f"[收藏点存储] 收藏失败: {e}")
            return False, f"收藏失败: {e}"

    def delete_favorite(self, fav_id: int) -> bool:
        """
        删除收藏点

        Args:
            fav_id: 收藏点ID

        Returns:
            bool: 是否删除成功
        """
        try:
            for i, item in enumerate(self.favorites_list):
                if item.get('id') == fav_id:
                    removed = self.favorites_list.pop(i)
                    self._save()
                    print(f"[收藏点存储] 已删除收藏点: {removed.get('name', '')} (id={fav_id})")
                    return True
            print(f"[收藏点存储] 未找到要删除的收藏点: id={fav_id}")
            return False
        except Exception as e:
            print(f"[收藏点存储] 删除失败: {e}")
            return False

    def is_favorited(self, lat: float, lon: float) -> bool:
        """
        查询坐标（WGS-84）是否已收藏

        Args:
            lat: 纬度（WGS-84）
            lon: 经度（WGS-84）

        Returns:
            bool: True 已收藏
        """
        return self._find_duplicate(lat, lon) >= 0

    def delete_by_coords(self, lat: float, lon: float) -> bool:
        """
        按坐标（WGS-84）删除收藏点

        Args:
            lat: 纬度（WGS-84）
            lon: 经度（WGS-84）

        Returns:
            bool: 是否删除成功
        """
        index = self._find_duplicate(lat, lon)
        if index < 0:
            return False
        removed = self.favorites_list.pop(index)
        self._save()
        print(f"[收藏点存储] 已按坐标删除收藏点: {removed.get('name', '')}")
        return True

    def get_all(self) -> List[Dict]:
        """
        获取所有收藏点

        Returns:
            List[Dict]: 收藏点列表（新收藏的在前）
        """
        return self.favorites_list

    def clear_all(self):
        """清空所有收藏点"""
        self.favorites_list = []
        self._save()
        print("[收藏点存储] 已清空所有收藏点")
