import unittest
import sys
import os

# Add the project root to the path for the test
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from modules.map.map_renderer import MapRenderer


class TestMapRenderer(unittest.TestCase):
    """MapRenderer测试类"""

    def test_create_base_map(self):
        """测试创建基础地图"""
        center = [39.9042, 116.4074]  # 北京坐标
        zoom_start = 13
        
        # 创建基础地图
        map_obj = MapRenderer.create_base_map(center, zoom_start)
        
        # 验证返回对象存在（具体的folium.Map对象检查）
        self.assertIsNotNone(map_obj)

    def test_add_marker(self):
        """测试向地图添加标记"""
        center = [39.9042, 116.4074]
        map_obj = MapRenderer.create_base_map(center)
        
        # 添加标记
        location = [39.9052, 116.4084]
        popup_text = "测试标记"
        
        # add_marker 方法修改地图对象但不返回新对象
        result = MapRenderer.add_marker(map_obj, location, popup_text)
        
        # 验证方法执行后返回 None（因为是就地修改）
        self.assertIsNone(result)
        # 验证原地图对象仍然存在
        self.assertIsNotNone(map_obj)

    def test_add_route(self):
        """测试向地图添加路线"""
        center = [39.9042, 116.4074]
        map_obj = MapRenderer.create_base_map(center)
        
        # 添加路线
        route_points = [[39.9042, 116.4074], [39.9052, 116.4084], [39.9062, 116.4094]]
        
        # add_route 方法修改地图对象但不返回新对象
        result = MapRenderer.add_route(map_obj, route_points)
        
        # 验证方法执行后返回 None（因为是就地修改）
        self.assertIsNone(result)
        # 验证原地图对象仍然存在
        self.assertIsNotNone(map_obj)

    def test_calculate_zoom_level(self):
        """测试计算缩放级别"""
        points = [[39.9042, 116.4074], [39.9052, 116.4084]]
        
        zoom_level = MapRenderer.calculate_zoom_level(points)
        
        # 验证返回的是整数类型的缩放级别
        self.assertIsInstance(zoom_level, int)
        self.assertGreaterEqual(zoom_level, 0)

    def test_fit_bounds(self):
        """测试适配边界"""
        center = [39.9042, 116.4074]
        map_obj = MapRenderer.create_base_map(center)
        
        points = [[39.9042, 116.4074], [39.9052, 116.4084]]
        
        # fit_bounds 方法修改地图对象但不返回新对象
        result = MapRenderer.fit_bounds(map_obj, points)
        
        # 验证方法执行后返回 None（因为是就地修改）
        self.assertIsNone(result)
        # 验证原地图对象仍然存在
        self.assertIsNotNone(map_obj)

    def test_get_zoom_by_level(self):
        """测试根据级别获取缩放"""
        zoom = MapRenderer.get_zoom_by_level()
        
        # 验证返回的是整数类型的缩放级别
        self.assertIsInstance(zoom, int)
        self.assertGreaterEqual(zoom, 0)


if __name__ == '__main__':
    unittest.main()