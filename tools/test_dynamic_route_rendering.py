"""
测试动态路线渲染功能
用于诊断地图缩放时路线点重绘问题
"""

import sys
import os

# 添加src目录和根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, 'src')
sys.path.insert(0, parent_dir)  # 添加根目录用于导入version
sys.path.insert(0, src_dir)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
import logging

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_signal_connection():
    """测试信号连接"""
    print("\n========== 测试1: 信号连接 ==========")

    from core.signals import SignalManager

    signal_manager = SignalManager()

    # 测试信号是否存在
    print(f"map_zoom_changed信号存在: {hasattr(signal_manager, 'map_zoom_changed')}")

    # 连接测试槽函数
    def test_slot(zoom_level):
        print(f"✅ 接收到缩放信号: {zoom_level}")

    signal_manager.map_zoom_changed.connect(test_slot)

    # 发射信号测试
    print("发射测试信号...")
    signal_manager.map_zoom_changed.emit(15)

    print("信号连接测试完成\n")

def test_data_manager():
    """测试DataManager的属性"""
    print("\n========== 测试2: DataManager属性 ==========")

    from app.managers.data_manager import DataManager

    dm = DataManager()

    print(f"original_route_points存在: {hasattr(dm, 'original_route_points')}")
    print(f"original_route_points值: {dm.original_route_points}")
    print(f"current_zoom_level存在: {hasattr(dm, 'current_zoom_level')}")
    print(f"current_zoom_level值: {dm.current_zoom_level}")
    print(f"route_points存在: {hasattr(dm, 'route_points')}")
    print(f"route_points值: {dm.route_points}")

    # 设置一些测试数据
    print("\n设置测试路线数据...")
    test_points = [(39.9, 116.4), (39.91, 116.41), (39.92, 116.42)]
    dm.set_route(test_points, 3600)

    print(f"设置后 original_route_points长度: {len(dm.original_route_points)}")
    print(f"设置后 route_points长度: {len(dm.route_points)}")
    print(f"original_route_points内容: {dm.original_route_points}")

    print("DataManager属性测试完成\n")

def test_route_optimizer():
    """测试RouteOptimizer"""
    print("\n========== 测试3: RouteOptimizer ==========")

    from modules.map.route_optimizer import RouteOptimizer

    # 创建测试路线数据
    original_points = [(39.9 + i*0.001, 116.4 + i*0.001) for i in range(100)]

    print(f"原始点数: {len(original_points)}")

    # 测试动态优化
    print("\n测试缩放级别10的优化...")
    optimized_10 = RouteOptimizer.optimize_route_dynamically(original_points, 10, None, 1000)
    print(f"缩放10优化后点数: {len([p for p in optimized_10 if p is not None])}")

    print("\n测试缩放级别14的优化...")
    optimized_14 = RouteOptimizer.optimize_route_dynamically(original_points, 14, 10, 1000)
    print(f"缩放14优化后点数: {len([p for p in optimized_14 if p is not None])}")

    print("RouteOptimizer测试完成\n")

def test_map_manager():
    """测试MapManager的缩放处理"""
    print("\n========== 测试4: MapManager缩放处理 ==========")

    from app.managers.data_manager import DataManager
    from app.managers.map_manager import MapManager
    import logging

    # 创建模拟的logger
    logger = logging.getLogger("test_map_manager")

    # 创建DataManager并设置测试数据
    dm = DataManager()
    test_points = [(39.9 + i*0.001, 116.4 + i*0.001) for i in range(100)]
    dm.set_route(test_points, 3600)

    print(f"DataManager设置完成:")
    print(f"  original_route_points: {len(dm.original_route_points)}点")
    print(f"  current_zoom_level: {dm.current_zoom_level}")

    # 创建MapManager（不创建实际的map_view）
    map_manager = MapManager(dm, None, logger, None)

    print(f"\nMapManager创建完成")
    print(f"  data_manager有original_route_points: {hasattr(map_manager.data_manager, 'original_route_points')}")
    print(f"  original_route_points点数: {len(map_manager.data_manager.original_route_points)}")

    # 模拟缩放变化
    print("\n模拟缩放从12变化到14...")
    try:
        # 注意：这会尝试渲染地图，可能会失败，但优化逻辑应该能执行
        map_manager.on_map_zoom_changed(14)
        print("✅ on_map_zoom_changed执行完成")
    except Exception as e:
        print(f"⚠️ on_map_zoom_changed执行出错（可能是渲染部分）: {e}")

    print(f"\n缩放后 route_points点数: {len([p for p in dm.route_points if p is not None])}")

    print("MapManager测试完成\n")

def test_full_integration():
    """完整集成测试"""
    print("\n========== 测试5: 完整集成测试 ==========")

    from core.signals import SignalManager
    from app.managers.data_manager import DataManager
    from app.managers.map_manager import MapManager
    import logging

    logger = logging.getLogger("integration_test")

    # 1. 创建信号管理器
    signal_manager = SignalManager()
    print("✅ 信号管理器创建完成")

    # 2. 创建数据管理器并设置路线
    dm = DataManager()
    test_points = [(39.9 + i*0.0001, 116.4 + i*0.0001) for i in range(500)]
    dm.set_route(test_points, 3600)
    print(f"✅ 数据管理器创建完成，路线点数: {len(dm.original_route_points)}")

    # 3. 创建地图管理器
    map_manager = MapManager(dm, None, logger, None)
    print("✅ 地图管理器创建完成")

    # 4. 连接信号到MapManager
    def on_zoom_changed(zoom_level):
        print(f"\n📡 信号触发: 缩放级别 = {zoom_level}")
        try:
            map_manager.on_map_zoom_changed(zoom_level)
            print(f"✅ 缩放处理完成，当前route_points点数: {len([p for p in dm.route_points if p is not None])}")
        except Exception as e:
            print(f"❌ 缩放处理失败: {e}")
            import traceback
            traceback.print_exc()

    signal_manager.map_zoom_changed.connect(on_zoom_changed)
    print("✅ 信号连接完成")

    # 5. 模拟缩放信号
    print("\n开始模拟缩放变化...")
    signal_manager.map_zoom_changed.emit(14)
    signal_manager.map_zoom_changed.emit(16)
    signal_manager.map_zoom_changed.emit(10)

    print("\n完整集成测试完成\n")

if __name__ == "__main__":
    print("=" * 60)
    print("动态路线渲染功能诊断工具")
    print("=" * 60)

    app = QApplication(sys.argv)

    # 运行所有测试
    test_signal_connection()
    test_data_manager()
    test_route_optimizer()
    test_map_manager()
    test_full_integration()

    print("=" * 60)
    print("所有测试完成！")
    print("=" * 60)
    print("\n请检查上述输出，查找可能的问题。")
    print("如果所有测试都通过，问题可能在于：")
    print("1. JavaScript端没有正确触发缩放事件")
    print("2. WebEngine没有正确捕获console消息")
    print("3. 信号连接在主应用中没有建立")

    sys.exit(0)
