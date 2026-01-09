"""应用程序常量定义"""

# 窗口配置
WINDOW_TITLE = "GPX Studio - 路线规划工具"
WINDOW_SIZE = (1400, 800)

# 搜索类型
SEARCH_TYPE_START = "start"
SEARCH_TYPE_END = "end"
SEARCH_TYPE_WAYPOINT = "waypoint"

# 地图相关
INITIAL_MAP_ZOOM = 10

# 颜色配置
COLOR_INFO = "blue"
COLOR_SUCCESS = "green"
COLOR_WARNING = "purple"
COLOR_ERROR = "red"
COLOR_ORANGE = "orange"

# 图标配置
ICON_INFO = "info-sign"
ICON_SUCCESS = "play"
ICON_WARNING = "star"
ICON_ERROR = "stop"

# 定位错误消息
GEOLOCATION_ERROR_MESSAGES = {
    -1: "浏览器不支持定位",
    1: "用户拒绝定位请求",
    2: "位置信息不可用",
    3: "定位请求超时",
    4: "未知错误"
}

# 面板尺寸配置
PANEL_SIZES = [300, 300, 700]
PANEL_STRETCH_FACTORS = [1, 1, 4]

# 地图加载延迟
MAP_LOAD_DELAY_MS = 500

# 搜索结果状态
SEARCH_RESULTS_TITLE = "搜索结果"
START_SEARCH_LIST_TITLE = "起点搜索列表"
END_SEARCH_LIST_TITLE = "终点搜索列表"
WAYPOINT_SEARCH_LIST_TITLE = "途径点搜索列表"

# 搜索结果标题映射
SEARCH_LIST_TITLES = {
    SEARCH_TYPE_START: START_SEARCH_LIST_TITLE,
    SEARCH_TYPE_END: END_SEARCH_LIST_TITLE,
    SEARCH_TYPE_WAYPOINT: WAYPOINT_SEARCH_LIST_TITLE
}
