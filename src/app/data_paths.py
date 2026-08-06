"""
数据路径管理模块

管理应用程序的所有数据文件路径，包括：
- 配置文件
- 日志文件
- 地理信息列表
- 路线历史
- 地图缓存
"""

import os
import sys


def is_frozen():
    """判断是否为打包后的exe"""
    return getattr(sys, 'frozen', False)


def get_app_root():
    """获取应用程序根目录"""
    if is_frozen():
        # 打包后的exe，返回exe所在目录
        return os.path.dirname(sys.executable)
    else:
        # 开发环境，返回项目根目录
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_data_root():
    """获取数据根目录"""
    app_root = get_app_root()

    if is_frozen():
        # 打包后：在exe同目录创建GPXStudioData
        data_root = os.path.join(app_root, 'GPXStudioData')
    else:
        # 开发环境：在Dist目录下创建GPXStudioData
        data_root = os.path.join(app_root, 'Dist', 'GPXStudioData')

    # 确保目录存在
    os.makedirs(data_root, exist_ok=True)

    return data_root


def get_config_dir():
    """获取配置文件目录"""
    config_dir = os.path.join(get_data_root(), 'config')
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


def get_log_dir():
    """获取日志文件目录"""
    log_dir = os.path.join(get_data_root(), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def get_cache_dir():
    """获取缓存根目录"""
    cache_dir = os.path.join(get_data_root(), 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def get_gaode_cache_dir():
    """获取高德地图缓存目录"""
    gaode_dir = os.path.join(get_cache_dir(), 'GaoDeMapData')
    os.makedirs(gaode_dir, exist_ok=True)
    return gaode_dir


def get_osm_cache_dir():
    """获取OSM地图缓存目录"""
    osm_dir = os.path.join(get_cache_dir(), 'OSMMapData')
    os.makedirs(osm_dir, exist_ok=True)
    return osm_dir


def get_geo_info_file():
    """获取地理信息列表文件路径"""
    return os.path.join(get_data_root(), 'GeoInfoList.json')


def get_route_history_file():
    """获取路线历史文件路径"""
    return os.path.join(get_data_root(), 'RouteHistoryList.json')


def get_favorites_file():
    """获取收藏点列表文件路径"""
    return os.path.join(get_data_root(), 'FavoritesList.json')


def get_map_config_file():
    """获取地图配置文件路径"""
    return os.path.join(get_config_dir(), 'map_config.json')


def init_data_directories():
    """初始化所有数据目录"""
    print("=" * 80)
    print("初始化数据目录")
    print("=" * 80)

    data_root = get_data_root()
    print(f"数据根目录: {data_root}")

    # 创建所有必要的目录
    dirs = {
        '配置目录': get_config_dir(),
        '日志目录': get_log_dir(),
        '缓存目录': get_cache_dir(),
        '高德地图缓存': get_gaode_cache_dir(),
        'OSM地图缓存': get_osm_cache_dir(),
    }

    for name, path in dirs.items():
        print(f"{name}: {path}")

    print("=" * 80)
    print("数据目录初始化完成")
    print("=" * 80)

    return data_root


if __name__ == '__main__':
    # 测试
    init_data_directories()
    print(f"\n地理信息文件: {get_geo_info_file()}")
    print(f"路线历史文件: {get_route_history_file()}")
    print(f"地图配置文件: {get_map_config_file()}")
