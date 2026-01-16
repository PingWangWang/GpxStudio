"""
地理信息持久化存储模块

该模块负责将地理编码搜索结果持久化存储到本地JSON文件，
以便后续快速访问，避免重复的API调用。
"""

import json
import os
from typing import Optional, List, Dict
from datetime import datetime


class GeoInfoStorage:
    """地理信息存储类"""

    def __init__(self, storage_file: str = None):
        """
        初始化地理信息存储

        Args:
            storage_file: 存储文件路径（如果为None，使用默认路径）
        """
        if storage_file is None:
            # 使用新的数据路径管理
            from app.data_paths import get_geo_info_file
            self.storage_path = get_geo_info_file()
        else:
            self.storage_path = storage_file

        self.geo_info_list = []
        self.max_history = 100  # 最多保存100条历史记录

        # 加载已有数据
        self._load()

    def _load(self):
        """从文件加载地理信息"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    self.geo_info_list = json.load(f)
                print(f"[地理信息存储] 加载了 {len(self.geo_info_list)} 条历史记录")
            except Exception as e:
                print(f"[地理信息存储] 加载失败: {e}")
                self.geo_info_list = []
        else:
            print("[地理信息存储] 未找到历史记录文件，将创建新文件")
            self.geo_info_list = []

    def _save(self):
        """保存地理信息到文件"""
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.geo_info_list, f, ensure_ascii=False, indent=2)
            print(f"[地理信息存储] 已保存 {len(self.geo_info_list)} 条记录到 {self.storage_path}")
        except Exception as e:
            print(f"[地理信息存储] 保存失败: {e}")

    def add_search_result(self, search_text: str, result: Dict):
        """
        添加搜索结果到历史记录

        Args:
            search_text: 搜索关键词
            result: 搜索结果字典，包含 name, address, lat, lon, type, level, radius 等字段
        """
        try:
            # 确保坐标是数字类型
            lat = result.get('lat', 0)
            lon = result.get('lon', 0)

            # 转换为float（如果是字符串）
            if isinstance(lat, str):
                lat = float(lat) if lat else 0.0
            if isinstance(lon, str):
                lon = float(lon) if lon else 0.0

            # 构建存储记录
            record = {
                'search_text': search_text,
                'name': result.get('name', ''),
                'address': result.get('address', ''),
                'lat': lat,
                'lon': lon,
                'type': result.get('type', ''),
                'level': result.get('level', ''),
                'radius': result.get('radius', None),
                'timestamp': datetime.now().isoformat()
            }

            # 检查是否已存在相同的记录（基于名称和坐标）
            existing_index = -1
            for i, item in enumerate(self.geo_info_list):
                item_lat = item.get('lat', 0)
                item_lon = item.get('lon', 0)

                # 确保比较的是数字
                if isinstance(item_lat, str):
                    item_lat = float(item_lat) if item_lat else 0.0
                if isinstance(item_lon, str):
                    item_lon = float(item_lon) if item_lon else 0.0

                if (item.get('name') == record['name'] and
                    abs(item_lat - record['lat']) < 0.0001 and
                    abs(item_lon - record['lon']) < 0.0001):
                    existing_index = i
                    break

            # 如果已存在，移除旧记录
            if existing_index >= 0:
                self.geo_info_list.pop(existing_index)

            # 将新记录添加到列表开头（最新的在前面）
            self.geo_info_list.insert(0, record)

            # 限制历史记录数量
            if len(self.geo_info_list) > self.max_history:
                self.geo_info_list = self.geo_info_list[:self.max_history]

            # 保存到文件
            self._save()

            print(f"[地理信息存储] 成功保存: {record['name']}")

        except Exception as e:
            print(f"[地理信息存储] 保存失败: {e}")
            import traceback
            traceback.print_exc()

    def get_recent_history(self, limit: int = 10) -> List[Dict]:
        """
        获取最近的搜索历史记录

        Args:
            limit: 返回的最大记录数（默认10条）

        Returns:
            List[Dict]: 历史记录列表
        """
        return self.geo_info_list[:limit]

    def search_history(self, keyword: str, limit: int = 10) -> List[Dict]:
        """
        在历史记录中搜索匹配的记录

        Args:
            keyword: 搜索关键词
            limit: 返回的最大记录数

        Returns:
            List[Dict]: 匹配的历史记录列表
        """
        if not keyword:
            return self.get_recent_history(limit)

        keyword_lower = keyword.lower()
        matched = []

        for record in self.geo_info_list:
            # 在名称、地址、搜索文本中搜索
            if (keyword_lower in record.get('name', '').lower() or
                keyword_lower in record.get('address', '').lower() or
                keyword_lower in record.get('search_text', '').lower()):
                matched.append(record)
                if len(matched) >= limit:
                    break

        return matched

    def clear_history(self):
        """清空所有历史记录"""
        self.geo_info_list = []
        self._save()
        print("[地理信息存储] 已清空所有历史记录")


# 导入sys模块
import sys
