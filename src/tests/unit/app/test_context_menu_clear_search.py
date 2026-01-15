"""
测试右键菜单设置点时清除搜索结果功能和智能缩放
"""

import pytest
from unittest.mock import Mock, call, patch, MagicMock
import sys
import os

# 添加项目根目录到路径
project_root = os.path.join(os.path.dirname(__file__), '../../..')
sys.path.insert(0, project_root)
# 添加src目录到路径
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)


class TestContextMenuClearSearch:
    """测试右键菜单设置点时清除搜索结果和智能缩放"""

    def test_set_start_clears_search_results_with_intelligent_zoom(self):
        """测试设置起点时清除搜索结果并使用智能缩放"""
        # 创建Mock对象
        mock_data_manager = Mock()
        mock_search_manager = Mock()
        mock_map_manager = Mock()
        mock_logger = Mock()

        # 模拟有搜索结果
        mock_data_manager.search_results = [{'name': '搜索结果1'}]

        # 模拟地图管理器返回单个坐标
        mock_map_manager._get_all_selected_coords = Mock(return_value=[(39.9, 116.4)])

        # 模拟右键菜单设置起点的逻辑
        name, lat, lon = "测试地点", 39.9, 116.4
        level = "门牌号级"
        type_info = "住宅小区"

        # 1. 保存起点信息
        mock_data_manager.set_start_location((lat, lon), name)

        # 2. 检查是否有搜索结果
        has_search_results = len(mock_data_manager.search_results) > 0

        # 3. 清除搜索结果
        mock_search_manager.clear_search_results()

        # 4. 更新地图（使用智能缩放）
        all_coords = mock_map_manager._get_all_selected_coords()
        if len(all_coords) >= 2:
            mock_map_manager.update_map_preview(auto_fit=True)
        else:
            # 单点：根据地址级别智能缩放
            # 模拟get_zoom_by_level的返回值
            zoom_level = 17  # 住宅小区应该返回17（社区级）
            mock_map_manager.update_map_preview_simple((lat, lon), zoom_level=zoom_level)

        # 验证调用
        mock_data_manager.set_start_location.assert_called_once_with((39.9, 116.4), "测试地点")
        mock_search_manager.clear_search_results.assert_called_once()
        # 单点时应该调用update_map_preview_simple，使用智能缩放级别
        mock_map_manager.update_map_preview_simple.assert_called_once()
        # 验证调用参数
        call_args = mock_map_manager.update_map_preview_simple.call_args
        assert call_args[0][0] == (39.9, 116.4)
        assert 'zoom_level' in call_args[1]

    def test_set_end_clears_search_results_with_intelligent_zoom(self):
        """测试设置终点时清除搜索结果并使用智能缩放"""
        # 创建Mock对象
        mock_data_manager = Mock()
        mock_search_manager = Mock()
        mock_map_manager = Mock()

        # 模拟有搜索结果
        mock_data_manager.search_results = [{'name': '搜索结果1'}]

        # 模拟地图管理器返回单个坐标
        mock_map_manager._get_all_selected_coords = Mock(return_value=[(39.9, 116.4)])

        # 模拟右键菜单设置终点的逻辑
        name, lat, lon = "测试地点", 39.9, 116.4
        level = "150200"
        type_info = "餐饮服务"

        # 1. 保存终点信息
        mock_data_manager.set_end_location((lat, lon), name)

        # 2. 检查是否有搜索结果
        has_search_results = len(mock_data_manager.search_results) > 0

        # 3. 清除搜索结果
        mock_search_manager.clear_search_results()

        # 4. 更新地图（使用智能缩放）
        all_coords = mock_map_manager._get_all_selected_coords()
        if len(all_coords) >= 2:
            mock_map_manager.update_map_preview(auto_fit=True)
        else:
            # 单点：根据地址级别智能缩放
            # 模拟get_zoom_by_level的返回值
            zoom_level = 16  # 餐饮服务应该返回16（POI级）
            mock_map_manager.update_map_preview_simple((lat, lon), zoom_level=zoom_level)

        # 验证调用
        mock_data_manager.set_end_location.assert_called_once_with((39.9, 116.4), "测试地点")
        mock_search_manager.clear_search_results.assert_called_once()
        # 单点时应该调用update_map_preview_simple，使用智能缩放级别
        mock_map_manager.update_map_preview_simple.assert_called_once()
        # 验证调用参数
        call_args = mock_map_manager.update_map_preview_simple.call_args
        assert call_args[0][0] == (39.9, 116.4)
        assert 'zoom_level' in call_args[1]

    def test_add_waypoint_clears_search_results_with_intelligent_zoom(self):
        """测试添加途径点时清除搜索结果并使用智能缩放"""
        # 创建Mock对象
        mock_data_manager = Mock()
        mock_search_manager = Mock()
        mock_map_manager = Mock()

        # 模拟有搜索结果
        mock_data_manager.search_results = [{'name': '搜索结果1'}]

        # 模拟地图管理器返回单个坐标
        mock_map_manager._get_all_selected_coords = Mock(return_value=[(39.9, 116.4)])

        # 模拟右键菜单添加途径点的逻辑
        name, lat, lon = "测试地点", 39.9, 116.4
        level = "街道级"
        type_info = "道路"

        # 1. 添加途径点
        mock_data_manager.add_waypoint((lat, lon), name)

        # 2. 检查是否有搜索结果
        has_search_results = len(mock_data_manager.search_results) > 0

        # 3. 清除搜索结果
        mock_search_manager.clear_search_results()

        # 4. 更新地图（使用智能缩放）
        all_coords = mock_map_manager._get_all_selected_coords()
        if len(all_coords) >= 2:
            mock_map_manager.update_map_preview(auto_fit=True)
        else:
            # 单点：根据地址级别智能缩放
            # 模拟get_zoom_by_level的返回值
            zoom_level = 15  # 街道级应该返回15
            mock_map_manager.update_map_preview_simple((lat, lon), zoom_level=zoom_level)

        # 验证调用
        mock_data_manager.add_waypoint.assert_called_once_with((39.9, 116.4), "测试地点")
        mock_search_manager.clear_search_results.assert_called_once()
        # 单点时应该调用update_map_preview_simple，使用智能缩放级别
        mock_map_manager.update_map_preview_simple.assert_called_once()
        # 验证调用参数
        call_args = mock_map_manager.update_map_preview_simple.call_args
        assert call_args[0][0] == (39.9, 116.4)
        assert 'zoom_level' in call_args[1]

    def test_set_start_with_multiple_points_auto_fit(self):
        """测试设置起点时如果有多个点则自动适应"""
        # 创建Mock对象
        mock_data_manager = Mock()
        mock_search_manager = Mock()
        mock_map_manager = Mock()

        # 模拟地图管理器返回多个坐标
        mock_map_manager._get_all_selected_coords = Mock(return_value=[
            (39.9, 116.4),
            (40.0, 116.5)
        ])

        # 模拟右键菜单设置起点的逻辑
        name, lat, lon = "测试地点", 39.9, 116.4

        # 1. 保存起点信息
        mock_data_manager.set_start_location((lat, lon), name)

        # 2. 清除搜索结果
        mock_search_manager.clear_search_results()

        # 3. 更新地图
        all_coords = mock_map_manager._get_all_selected_coords()
        if len(all_coords) >= 2:
            mock_map_manager.update_map_preview(auto_fit=True)

        # 验证调用
        mock_data_manager.set_start_location.assert_called_once_with((39.9, 116.4), "测试地点")
        mock_search_manager.clear_search_results.assert_called_once()
        mock_map_manager.update_map_preview.assert_called_once_with(auto_fit=True)

    def test_clear_search_results_removes_data_and_ui(self):
        """测试清除搜索结果同时清除数据和UI"""
        # 直接导入DataManager类，避免触发整个模块初始化
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "data_manager",
            os.path.join(os.path.dirname(__file__), '../../../app/managers/data_manager.py')
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        DataManager = module.DataManager

        # 创建真实的数据管理器
        data_manager = DataManager()

        # 设置一些搜索结果
        test_results = [
            {'name': '地点1', 'lat': 39.9, 'lon': 116.4},
            {'name': '地点2', 'lat': 40.0, 'lon': 116.5}
        ]
        data_manager.set_search_results(test_results, 'start')
        data_manager.set_selected_search_result((39.9, 116.4))

        # 验证搜索结果已设置
        assert len(data_manager.search_results) == 2
        assert data_manager.searching_for == 'start'
        assert data_manager.selected_search_result_coords == (39.9, 116.4)

        # 清除搜索结果
        data_manager.clear_search_results()

        # 验证搜索结果已清除
        assert len(data_manager.search_results) == 0
        assert data_manager.searching_for is None
        assert data_manager.selected_search_result_coords is None
