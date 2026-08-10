# -*- coding: utf-8 -*-
"""
路线管理库存储

保存路线管理列表中的路线（GPX 导入 / 历史条目收藏），与搜索历史存储
（RouteHistoryStorage）相互独立，清空/收藏/海拔回写互不干扰。
"""

import json
import os
import uuid
from typing import List, Dict, Optional
from datetime import datetime


class RouteLibraryStorage:
    """路线管理库存储（独立 JSON 文件）"""

    def __init__(self, storage_file: str = None):
        """
        初始化路线管理库存储

        Args:
            storage_file: 存储文件路径（默认使用数据目录 RouteLibrary.json）
        """
        if storage_file is None:
            from app.data_paths import get_route_library_file
            self.storage_path = get_route_library_file()
        else:
            self.storage_path = storage_file

        self.records = []
        self._load()

    def _load(self):
        """从文件加载路线库"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.records = data.get('records', [])
                print(f"[路线库存储] 加载了 {len(self.records)} 条路线")
            except Exception as e:
                print(f"[路线库存储] 加载失败: {e}")
                self.records = []
        else:
            self.records = []

    def _save(self) -> bool:
        """保存路线库到文件"""
        try:
            data = {
                'records': self.records,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[路线库存储] 保存失败: {e}")
            return False

    def add_record(self, start: str, end: str, mode: str = 'driving',
                   waypoints: List[str] = None,
                   start_coords: tuple = None, end_coords: tuple = None,
                   waypoint_coords: List[tuple] = None,
                   route_points: List[tuple] = None,
                   distance: float = None, duration: int = None,
                   color_index: int = 0) -> Optional[str]:
        """添加路线到路线库

        按 (start, end) 去重：同一路线再次添加时更新原记录（保留原 id）。

        Args:
            start: 起点名称
            end: 终点名称
            mode: 交通方式
            waypoints: 途径点名称列表
            start_coords: 起点坐标 (lat, lon)（WGS-84 国际标准）
            end_coords: 终点坐标 (lat, lon)
            waypoint_coords: 途径点坐标列表
            route_points: 路线点列表 [(lat, lon, elevation?), ...]
            distance: 总距离（米）
            duration: 总时长（秒）
            color_index: 渲染颜色索引（多路线渲染配色）

        Returns:
            记录 id（新增或更新的记录）；失败返回 None
        """
        # 按 (start, end) 去重更新
        for rec in self.records:
            if rec.get('start') == start and rec.get('end') == end:
                rec['mode'] = mode
                rec['waypoints'] = waypoints or []
                if start_coords is not None:
                    rec['start_coords'] = list(start_coords)
                if end_coords is not None:
                    rec['end_coords'] = list(end_coords)
                if waypoint_coords is not None:
                    rec['waypoint_coords'] = [list(c) if c else None for c in waypoint_coords]
                if route_points is not None:
                    rec['route_points'] = [
                        list(p) if p is not None else None for p in route_points]
                if distance is not None:
                    rec['distance'] = distance
                if duration is not None:
                    rec['duration'] = duration
                rec['color_index'] = color_index
                rec['timestamp'] = datetime.now().isoformat()
                if self._save():
                    print(f"[路线库存储] 更新路线: {start} → {end}")
                    return rec.get('id')
                return None

        # 新增记录（经纬度一律按 WGS-84 国际标准存储）
        record = {
            'id': uuid.uuid4().hex,
            'start': start,
            'end': end,
            'mode': mode,
            'waypoints': waypoints or [],
            'start_coords': list(start_coords) if start_coords else None,
            'end_coords': list(end_coords) if end_coords else None,
            'waypoint_coords': [list(c) if c else None for c in (waypoint_coords or [])],
            'route_points': [
                list(p) if p is not None else None for p in (route_points or [])
            ] if route_points else None,
            'distance': distance,
            'duration': duration,
            'coord_system': 'WGS-84',
            'color_index': color_index,
            'timestamp': datetime.now().isoformat()
        }
        self.records.insert(0, record)
        if self._save():
            print(f"[路线库存储] 新增路线: {start} → {end}, id={record['id']}")
            return record['id']
        return None

    def update_route_points(self, record_id: str, route_points: List[tuple]) -> Optional[dict]:
        """更新指定路线的海拔路线点（仅替换 route_points，不动其他字段）

        Args:
            record_id: 路线记录 id
            route_points: 带海拔的路线点列表

        Returns:
            更新后的记录；未匹配返回 None
        """
        for rec in self.records:
            if rec.get('id') == record_id:
                rec['route_points'] = [
                    list(p) if p is not None else None for p in route_points]
                if self._save():
                    return rec
                return None
        return None

    def get_all(self) -> List[Dict]:
        """获取全部路线"""
        return list(self.records)

    def get_by_id(self, record_id: str) -> Optional[Dict]:
        """按 id 获取路线"""
        for rec in self.records:
            if rec.get('id') == record_id:
                return rec
        return None

    def find_by_key(self, start: str, end: str) -> Optional[Dict]:
        """按 (start, end) 查找路线（历史条目收藏状态判断用）"""
        for rec in self.records:
            if rec.get('start') == start and rec.get('end') == end:
                return rec
        return None

    def remove(self, record_id: str) -> bool:
        """删除指定路线"""
        for i, rec in enumerate(self.records):
            if rec.get('id') == record_id:
                self.records.pop(i)
                print(f"[路线库存储] 删除路线: {rec.get('start')} → {rec.get('end')}")
                return self._save()
        return False

    def clear(self) -> bool:
        """清空全部路线"""
        self.records = []
        return self._save()
