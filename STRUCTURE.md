# GPX Studio 项目结构说明

## 目录结构

```
GpxStudio/
├── main.py                     # 程序入口文件
├── requirements.txt            # Python依赖列表
├── README.md                   # 项目说明文档
├── STRUCTURE.md               # 本文档
│
├── core/                      # 核心模块
│   ├── __init__.py           # 导出 GpxStudio 主类
│   └── app.py                # 主应用窗口（700+ 行）
│
├── handlers/                  # 处理器模块
│   ├── __init__.py           # 导出处理器类
│   ├── geolocation.py        # 定位处理器（信号发送）
│   └── webengine.py          # 自定义WebEngine页面（JS消息拦截）
│
├── services/                  # 服务模块
│   ├── __init__.py           # 导出服务类
│   ├── geocoding.py          # 地理编码服务
│   ├── routing.py            # 路由规划服务
│   └── gpx_export.py         # GPX导出服务
│
├── ui/                        # UI模块
│   ├── __init__.py           # 导出UI工具类
│   ├── panels.py             # 面板工厂（创建UI组件）
│   └── styles.py             # 样式定义（集中管理样式）
│
└── utils/                     # 工具模块
    ├── __init__.py           # 导出工具类
    ├── map_renderer.py       # 地图渲染工具
    └── location_helper.py    # 定位辅助工具（IP定位等）
```

## 模块详细说明

### 1. main.py（入口文件）
- **功能**: 程序启动入口
- **内容**:
  - 导入 `GpxStudio` 类
  - 创建 QApplication
  - 启动主窗口
- **代码量**: 约20行

### 2. core/app.py（主应用）
- **功能**: 主应用窗口，整合所有功能
- **职责**:
  - 初始化所有服务（GeocodingService, RoutingService, GpxExportService）
  - 创建UI布局（左中右三面板）
  - 处理用户交互（搜索、选择、规划、导出）
  - 管理应用状态（坐标、路线、搜索结果等）
- **主要方法**:
  - `init_ui()`: 初始化界面
  - `create_left_panel()`: 创建控制面板
  - `create_middle_panel()`: 创建搜索结果面板
  - `create_right_panel()`: 创建地图面板
  - `search_location()`: 搜索地点
  - `plan_route()`: 规划路线
  - `export_gpx()`: 导出GPX
  - `get_current_location()`: 获取定位
- **代码量**: 约700行

### 3. handlers/（处理器模块）

#### 3.1 geolocation.py
- **类**: `GeolocationHandler`
- **功能**: 定位事件处理
- **信号**:
  - `geolocation_success(lat, lon, accuracy)`: 定位成功
  - `geolocation_error(msg)`: 定位失败
- **代码量**: 约20行

#### 3.2 webengine.py
- **类**: `ConsoleWebEnginePage`
- **功能**: 自定义WebEngine页面
- **职责**:
  - 继承 `QWebEnginePage`
  - 重写 `javaScriptConsoleMessage()` 方法
  - 解析JS控制台消息
  - 触发定位信号
- **代码量**: 约50行

### 4. services/（服务模块）

#### 4.1 geocoding.py
- **类**: `GeocodingService`
- **功能**: 地理编码服务
- **方法**:
  - `search_location(search_text)`: 搜索地点（多策略）
  - `reverse_geocode(lat, lon)`: 反向地理编码
- **依赖**: geopy.Nominatim
- **代码量**: 约80行

#### 4.2 routing.py
- **类**: `RoutingService`
- **功能**: 路由规划服务
- **方法**:
  - `plan_route(points, transport_mode)`: 规划路线
  - `calculate_distance(route_points)`: 计算距离
- **依赖**: OSRM API, requests
- **代码量**: 约80行

#### 4.3 gpx_export.py
- **类**: `GpxExportService`
- **功能**: GPX导出服务
- **方法**:
  - `export_to_gpx(route_points, start_time, file_path)`: 导出GPX
  - `get_gpx_info(route_points)`: 获取GPX信息
- **依赖**: gpxpy
- **代码量**: 约80行

### 5. ui/（UI模块）

#### 5.1 styles.py
- **类**: `UIStyles`
- **功能**: UI样式定义
- **内容**:
  - 按钮样式常量（定位、测试、规划、导出、清空）
  - 进度条样式
  - 标题样式
- **代码量**: 约60行

#### 5.2 panels.py
- **类**: `PanelFactory`
- **功能**: UI面板工厂
- **方法**:
  - `create_location_group()`: 创建地点搜索组
  - `create_waypoint_group()`: 创建途径点组
  - `create_transport_group()`: 创建交通方式组
  - `create_time_group()`: 创建时间设置组
  - `create_progress_bar()`: 创建进度条
- **代码量**: 约150行

### 6. utils/（工具模块）

#### 6.1 map_renderer.py
- **类**: `MapRenderer`
- **功能**: 地图渲染工具
- **方法**:
  - `create_base_map()`: 创建基础地图
  - `add_marker()`: 添加标记
  - `add_route()`: 添加路线
  - `save_and_get_url()`: 保存地图并返回URL
  - `calculate_zoom_level()`: 计算缩放级别
  - `add_geolocation_script()`: 添加定位脚本
- **依赖**: folium
- **代码量**: 约180行

#### 6.2 location_helper.py
- **类**: `LocationHelper`
- **功能**: 定位辅助工具
- **方法**:
  - `get_ip_location()`: IP定位
  - `format_coordinates()`: 格式化坐标
- **代码量**: 约40行

## 数据流

```
用户操作
    ↓
core/app.py (主窗口)
    ↓
├→ services/* (业务逻辑)
│   ├→ geocoding.py (地理编码)
│   ├→ routing.py (路由规划)
│   └→ gpx_export.py (GPX导出)
│
├→ utils/* (工具函数)
│   ├→ map_renderer.py (地图渲染)
│   └→ location_helper.py (定位辅助)
│
├→ ui/* (UI组件)
│   ├→ panels.py (创建面板)
│   └→ styles.py (应用样式)
│
└→ handlers/* (事件处理)
    ├→ geolocation.py (定位信号)
    └→ webengine.py (JS消息)
```

## 模块依赖关系

```
main.py
  └→ core/app.py
      ├→ handlers/*
      ├→ services/*
      ├→ utils/*
      └→ ui/*
```

**注意**:
- 各模块之间相互独立，只有 `core/app.py` 导入其他模块
- 模块内部通过 `__init__.py` 统一导出接口
- 便于单元测试和功能扩展

## 扩展指南

### 添加新服务
1. 在 `services/` 下创建新文件（如 `weather.py`）
2. 定义服务类（如 `WeatherService`）
3. 在 `services/__init__.py` 中导出
4. 在 `core/app.py` 中实例化并使用

### 添加新UI组件
1. 在 `ui/panels.py` 中添加工厂方法
2. 在 `ui/styles.py` 中定义样式
3. 在 `core/app.py` 的面板创建方法中使用

### 添加新工具函数
1. 在 `utils/` 下创建新文件或扩展现有文件
2. 定义工具类或函数
3. 在 `utils/__init__.py` 中导出
4. 在需要的地方导入使用

## 优势

1. **模块化**: 功能清晰分离，易于理解和维护
2. **可测试性**: 每个模块可独立测试
3. **可扩展性**: 添加新功能不影响现有代码
4. **可读性**: 文件小，职责单一，代码清晰
5. **可维护性**: 修改局部不影响整体

## 文件统计

- **总文件数**: 约20个（包括 `__init__.py`）
- **总代码量**: 约1400行（原main.py约1100行）
- **平均文件大小**: 约70行
- **最大文件**: `core/app.py` (约700行)

## 对比原始结构

**原始**:
- 1个文件 (main.py)
- 1100+ 行代码
- 所有功能混在一起

**重构后**:
- 5个模块目录
- 15+ 个功能文件
- 职责清晰分离
- 易于维护和扩展
