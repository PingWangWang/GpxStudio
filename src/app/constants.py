"""应用程序常量定义"""

# 窗口配置
WINDOW_TITLE = "GPX Studio - 路线规划工具"  # 应用程序窗口标题
WINDOW_SIZE = (1200, 700)  # 应用程序窗口默认大小 (宽度, 高度)

# 搜索类型
SEARCH_TYPE_START = "start"  # 起点搜索类型
SEARCH_TYPE_END = "end"  # 终点搜索类型
SEARCH_TYPE_WAYPOINT = "waypoint"  # 途径点搜索类型

# 地图相关
INITIAL_MAP_ZOOM = 10  # 地图初始缩放级别

# 颜色配置
COLOR_INFO = "blue"  # 信息类元素颜色
COLOR_SUCCESS = "green"  # 成功类元素颜色
COLOR_WARNING = "purple"  # 警告类元素颜色
COLOR_ERROR = "red"  # 错误类元素颜色
COLOR_ORANGE = "orange"  # 橙色，用于特殊标记

# 图标配置
ICON_INFO = "info-sign"  # 信息图标
ICON_SUCCESS = "play"  # 成功图标
ICON_WARNING = "star"  # 警告图标
ICON_ERROR = "stop"  # 错误图标
ICON_DOT = ""  # 纯色气泡（当前选中地址标识，无内部图形，与起点/终点图标区分）

# 定位错误消息
GEOLOCATION_ERROR_MESSAGES = {
    -1: "浏览器不支持定位",  # 浏览器不支持地理定位功能
    1: "用户拒绝定位请求",  # 用户拒绝了定位权限请求
    2: "位置信息不可用",  # 位置信息无法获取
    3: "定位请求超时",  # 定位请求超时
    4: "未知错误"  # 其他未知错误
}



# 地图加载延迟
MAP_LOAD_DELAY_MS = 500  # 地图加载延迟时间（毫秒），确保UI完全初始化后再显示地图

# 搜索结果状态
SEARCH_RESULTS_TITLE = "搜索结果"  # 默认搜索结果标题
START_SEARCH_LIST_TITLE = "起点搜索列表"  # 起点搜索结果标题
END_SEARCH_LIST_TITLE = "终点搜索列表"  # 终点搜索结果标题
WAYPOINT_SEARCH_LIST_TITLE = "途径点搜索列表"  # 途径点搜索结果标题

# 搜索结果标题映射
SEARCH_LIST_TITLES = {
    SEARCH_TYPE_START: START_SEARCH_LIST_TITLE,  # 起点搜索结果标题映射
    SEARCH_TYPE_END: END_SEARCH_LIST_TITLE,  # 终点搜索结果标题映射
    SEARCH_TYPE_WAYPOINT: WAYPOINT_SEARCH_LIST_TITLE  # 途径点搜索结果标题映射
}
