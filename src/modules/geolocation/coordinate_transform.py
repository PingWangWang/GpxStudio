"""
坐标转换模块

实现GCJ-02（高德地图）和WGS-84（国际标准）坐标系之间的转换
"""

import math
from typing import Tuple, List

class CoordinateTransform:
    """坐标转换类"""
    
    # 常量定义
    PI = 3.14159265358979324
    AXIS = 6378245.0
    OFFSET = 0.00669342162296594323
    
    @staticmethod
    def transform_lat(x: float, y: float) -> float:
        """转换纬度"""
        ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
        ret += (20.0 * math.sin(6.0 * x * CoordinateTransform.PI) + 20.0 * math.sin(2.0 * x * CoordinateTransform.PI)) * 2.0 / 3.0
        ret += (20.0 * math.sin(y * CoordinateTransform.PI) + 40.0 * math.sin(y / 3.0 * CoordinateTransform.PI)) * 2.0 / 3.0
        ret += (160.0 * math.sin(y / 12.0 * CoordinateTransform.PI) + 320.0 * math.sin(y * CoordinateTransform.PI / 30.0)) * 2.0 / 3.0
        return ret
    
    @staticmethod
    def transform_lon(x: float, y: float) -> float:
        """转换经度"""
        ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
        ret += (20.0 * math.sin(6.0 * x * CoordinateTransform.PI) + 20.0 * math.sin(2.0 * x * CoordinateTransform.PI)) * 2.0 / 3.0
        ret += (20.0 * math.sin(x * CoordinateTransform.PI) + 40.0 * math.sin(x / 3.0 * CoordinateTransform.PI)) * 2.0 / 3.0
        ret += (150.0 * math.sin(x / 12.0 * CoordinateTransform.PI) + 300.0 * math.sin(x * CoordinateTransform.PI / 30.0)) * 2.0 / 3.0
        return ret
    
    @staticmethod
    def wgs84_to_gcj02(lat: float, lon: float) -> Tuple[float, float]:
        """
        WGS-84坐标转换为GCJ-02坐标
        
        Args:
            lat: WGS-84纬度
            lon: WGS-84经度
            
        Returns:
            (lat, lon): GCJ-02坐标
        """
        if CoordinateTransform._out_of_china(lat, lon):
            return lat, lon
        
        dLat = CoordinateTransform.transform_lat(lon - 105.0, lat - 35.0)
        dLon = CoordinateTransform.transform_lon(lon - 105.0, lat - 35.0)
        
        radLat = lat / 180.0 * CoordinateTransform.PI
        magic = math.sin(radLat)
        magic = 1 - CoordinateTransform.OFFSET * magic * magic
        sqrtMagic = math.sqrt(magic)
        
        dLat = (dLat * 180.0) / ((CoordinateTransform.AXIS * (1 - CoordinateTransform.OFFSET)) / (magic * sqrtMagic) * CoordinateTransform.PI)
        dLon = (dLon * 180.0) / (CoordinateTransform.AXIS / sqrtMagic * math.cos(radLat) * CoordinateTransform.PI)
        
        mgLat = lat + dLat
        mgLon = lon + dLon
        
        return mgLat, mgLon
    
    @staticmethod
    def gcj02_to_wgs84(lat: float, lon: float) -> Tuple[float, float]:
        """
        GCJ-02坐标转换为WGS-84坐标
        
        Args:
            lat: GCJ-02纬度
            lon: GCJ-02经度
            
        Returns:
            (lat, lon): WGS-84坐标
        """
        if CoordinateTransform._out_of_china(lat, lon):
            return lat, lon
        
        dLat = CoordinateTransform.transform_lat(lon - 105.0, lat - 35.0)
        dLon = CoordinateTransform.transform_lon(lon - 105.0, lat - 35.0)
        
        radLat = lat / 180.0 * CoordinateTransform.PI
        magic = math.sin(radLat)
        magic = 1 - CoordinateTransform.OFFSET * magic * magic
        sqrtMagic = math.sqrt(magic)
        
        dLat = (dLat * 180.0) / ((CoordinateTransform.AXIS * (1 - CoordinateTransform.OFFSET)) / (magic * sqrtMagic) * CoordinateTransform.PI)
        dLon = (dLon * 180.0) / (CoordinateTransform.AXIS / sqrtMagic * math.cos(radLat) * CoordinateTransform.PI)
        
        mgLat = lat + dLat
        mgLon = lon + dLon
        
        return lat * 2 - mgLat, lon * 2 - mgLon
    
    @staticmethod
    def _out_of_china(lat: float, lon: float) -> bool:
        """
        判断坐标是否在中国境外（GCJ-02坐标系适用区域之外）
        
        注意：GCJ-02坐标系仅适用于中国大陆地区
        台湾、香港、澳门等地区不使用GCJ-02坐标系，使用WGS-84坐标系
        
        Args:
            lat: 纬度
            lon: 经度
            
        Returns:
            bool: 是否在GCJ-02适用区域之外（True表示不需要进行坐标转换）
        """
        # 基本范围判断：不在中国经纬度范围内
        if not (73.66 < lon < 135.05 and 3.86 < lat < 53.55):
            return True
        
        # 台湾地区 (119.3°E-124.6°E, 21.9°N-25.3°N)
        if 119.3 < lon < 124.6 and 21.9 < lat < 25.3:
            return True
        
        # 香港地区 (113.8°E-114.5°E, 22.1°N-22.6°N)
        if 113.8 < lon < 114.5 and 22.1 < lat < 22.6:
            return True
        
        # 澳门地区 (113.5°E-113.6°E, 22.1°N-22.2°N)
        if 113.5 < lon < 113.6 and 22.1 < lat < 22.2:
            return True
        
        return False
    
    @staticmethod
    def transform_route_points(points: List[Tuple[float, float]], transform_func) -> List[Tuple[float, float]]:
        """
        转换路线点列表
        
        Args:
            points: 原始路线点列表 [(lat, lon), ...]
            transform_func: 转换函数，如 wgs84_to_gcj02 或 gcj02_to_wgs84
            
        Returns:
            List[Tuple[float, float]]: 转换后的路线点列表
        """
        transformed_points = []
        for point in points:
            if point is not None:
                lat, lon = point
                transformed_lat, transformed_lon = transform_func(lat, lon)
                transformed_points.append((transformed_lat, transformed_lon))
            else:
                transformed_points.append(None)
        return transformed_points