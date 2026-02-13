"""
路线搜索历史存储

保存和加载路线搜索历史记录
"""

import json
import os
from typing import List, Dict, Optional
from datetime import datetime


class RouteHistoryStorage:
    """路线搜索历史存储"""

    def __init__(self, storage_file: str = None):
        """
        初始化路线历史存储

        Args:
            storage_file: 存储文件路径（如果为None，使用默认路径）
        """
        if storage_file is None:
            # 使用新的数据路径管理
            from app.data_paths import get_route_history_file
            self.storage_path = get_route_history_file()
        else:
            self.storage_path = storage_file

        self.history_records = []

        # 加载历史记录
        self._load_history()

    def _load_history(self):
        """从文件加载历史记录"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.history_records = data.get('records', [])
                print(f"[路线历史存储] 加载了 {len(self.history_records)} 条历史记录")
            except Exception as e:
                print(f"[路线历史存储] 加载失败: {e}")
                self.history_records = []
        else:
            print("[路线历史存储] 未找到历史记录文件，将创建新文件")
            self.history_records = []

    def _save_history(self):
        """保存历史记录到文件"""
        try:
            data = {
                'records': self.history_records,
                'last_updated': datetime.now().isoformat()
            }

            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"[路线历史存储] 已保存 {len(self.history_records)} 条记录到 {self.storage_path}")
            return True
        except Exception as e:
            print(f"[路线历史存储] 保存失败: {e}")
            return False

    def add_record(self, start: str, end: str, mode: str, waypoints: List[str] = None,
                   start_coords: tuple = None, end_coords: tuple = None,
                   waypoint_coords: List[tuple] = None,
                   distance: float = None, duration: int = None,
                   route_points: List[tuple] = None,
                   start_coord_system: str = None, end_coord_system: str = None,
                   waypoint_coord_systems: List[str] = None) -> bool:
        """
        添加路线搜索记录

        Args:
            start: 起点名称
            end: 终点名称
            mode: 交通方式 (driving/cycling/walking)
            waypoints: 途径点名称列表
            start_coords: 起点坐标 (lat, lon)
            end_coords: 终点坐标 (lat, lon)
            waypoint_coords: 途径点坐标列表
            distance: 路线总距离（米）
            duration: 路线总时长（秒）
            route_points: 完整路线坐标点列表（包含海拔）[(lat, lon, elevation), ...]

        Returns:
            bool: 是否保存成功
        """
        # 检查是否已存在相同记录（起点、终点、交通方式相同）
        for record in self.history_records:
            if (record.get('start') == start and
                record.get('end') == end and
                record.get('mode') == mode):
                # 更新时间戳和搜索次数
                record['timestamp'] = datetime.now().isoformat()
                record['search_count'] = record.get('search_count', 1) + 1

                # 更新坐标信息（如果提供了新的坐标）
                # 确保坐标格式为列表（JSON兼容）
                if start_coords is not None:
                    record['start_coords'] = list(start_coords) if start_coords else None
                if end_coords is not None:
                    record['end_coords'] = list(end_coords) if end_coords else None
                if waypoint_coords is not None:
                    record['waypoint_coords'] = [list(coord) if coord else None for coord in waypoint_coords]
                if waypoints is not None:
                    record['waypoints'] = waypoints
                if distance is not None:
                    record['distance'] = distance
                if duration is not None:
                    record['duration'] = duration
                if route_points is not None:
                    # 保存路线点（过滤掉None分隔符，转换为列表格式）
                    record['route_points'] = [
                        list(point) if point and point is not None else None
                        for point in route_points
                    ]
                if start_coord_system is not None:
                    record['start_coord_system'] = start_coord_system
                if end_coord_system is not None:
                    record['end_coord_system'] = end_coord_system
                if waypoint_coord_systems is not None:
                    record['waypoint_coord_systems'] = waypoint_coord_systems

                # 移到列表开头（最近使用）
                self.history_records.remove(record)
                self.history_records.insert(0, record)

                print(f"[路线历史存储] 更新记录: {start} → {end}, 坐标: {record.get('start_coords')} → {record.get('end_coords')}, "
                      f"距离: {distance}米, 时长: {duration}秒, 路线点数: {len([p for p in (route_points or []) if p is not None])}")
                return self._save_history()

        # 创建新记录
        # 确保坐标格式为列表（JSON兼容）
        record = {
            'start': start,
            'end': end,
            'mode': mode,
            'waypoints': waypoints or [],
            'start_coords': list(start_coords) if start_coords else None,
            'end_coords': list(end_coords) if end_coords else None,
            'waypoint_coords': [list(coord) if coord else None for coord in (waypoint_coords or [])],
            'distance': distance,
            'duration': duration,
            'route_points': [
                list(point) if point and point is not None else None
                for point in (route_points or [])
            ] if route_points else None,
            'start_coord_system': start_coord_system,
            'end_coord_system': end_coord_system,
            'waypoint_coord_systems': waypoint_coord_systems,
            'timestamp': datetime.now().isoformat(),
            'search_count': 1
        }

        # 添加到列表开头
        self.history_records.insert(0, record)

        # 限制历史记录数量（最多保存50条）
        if len(self.history_records) > 50:
            self.history_records = self.history_records[:50]

        print(f"[路线历史存储] 新增记录: {start} → {end}, 坐标: {record.get('start_coords')} → {record.get('end_coords')}, "
              f"距离: {distance}米, 时长: {duration}秒, 路线点数: {len([p for p in (route_points or []) if p is not None])}")
        return self._save_history()

    def get_history(self, limit: int = 10) -> List[Dict]:
        """
        获取历史记录

        Args:
            limit: 返回的最大记录数

        Returns:
            历史记录列表
        """
        return self.history_records[:limit]

    def clear_history(self) -> bool:
        """
        清空历史记录

        Returns:
            bool: 是否清空成功
        """
        self.history_records = []
        return self._save_history()

    def remove_record(self, record: int or dict) -> bool:
        """
        删除指定记录

        Args:
            record: 记录索引或记录数据

        Returns:
            bool: 是否删除成功
        """
        index = None
        if isinstance(record, int):
            index = record
        elif isinstance(record, dict):
            # 根据记录数据查找索引
            for i, r in enumerate(self.history_records):
                if r == record:
                    index = i
                    break
        
        if index is not None and 0 <= index < len(self.history_records):
            removed = self.history_records.pop(index)
            print(f"[路线历史存储] 删除记录: {removed.get('start')} → {removed.get('end')}")
            return self._save_history()
        return False


# 添加sys导入
import sys
