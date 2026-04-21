# GPX Studio 源代码结构说明

GPX Studio 是一个基于 Python 和 PyQt5 的 GPS 路线规划工具，支持高德地图和 OpenStreetMap (OSM) 双数据源，具备路线规划、定位、搜索及 GPX 导出等功能。

## 📁 目录结构概览

```text
src/
├── app/            # 应用核心层：主窗口、管理器、Mixin
├── core/           # 核心基础设施：日志、信号、依赖注入、后台任务
├── domain/         # 领域层：业务模型、接口、协调器（无 PyQt5 依赖）
├── infrastructure/ # 基础设施层：外部 API 实现、持久化存储
├── modules/        # UI 功能模块：地理定位、地图渲染、路线规划、搜索、GPX 处理
├── services/       # 服务层：高德/OSM API 封装、配置管理（向后兼容保留）
└── ui/             # 用户界面：布局、面板、弹窗、自定义控件、ViewModel、图标
```

---

## 🏗️ 核心架构设计

### 1. 应用核心 (`app/`)

采用**管理器 + Mixin 模式**，将主窗口 `GpxStudio` 的职责拆分为独立的管理器类和 Mixin，由主窗口统一组合调度。

- **`app.py`**: 主窗口入口，通过多重继承组合所有 Mixin，负责初始化各管理器并连接信号。
- **`managers/`**:
  - `WindowManager`: 窗口生命周期、系统托盘及关闭逻辑管理。
  - `ServiceManager`: 统一管理高德、OSM 等第三方服务的实例化。
  - `DataManager`: 集中存储应用状态（起点、终点、路线点、搜索结果等）。
  - `LocationManager`: 协调 Windows 原生定位、浏览器 Geolocation 及 IP 定位。
  - `MapManager`: 负责地图视图的生成、刷新及图层叠加。
  - `RouteManager`: 处理路线规划请求、多方案切换及 GPX 文件导出。
  - `TimeManager`: 管理行程起止时间及途经时间的自动计算。
  - `UpdateManager`: 软件版本检测、下载及自动安装更新。
  - `MapViewStateManager`: 维护并恢复地图视图状态（中心坐标、缩放级别）。
- **`mixins/`**: 将主窗口行为按功能域拆分为独立 Mixin：
  - `InitMixin`: 启动流程、管理器初始化、信号连接。
  - `MapMixin`: 地图交互回调（定位、切换、重载）。
  - `SearchMixin`: 搜索输入、结果展示、历史记录。
  - `RouteMixin`: 路线规划流程、途经点管理。
  - `GpxExportMixin`: GPX 文件导出向导。
  - `TaskMixin`: 后台任务进度与状态回调。
  - `UICallbacksMixin`: 通用 UI 事件响应（面板显示、按钮状态等）。
  - `ContextMenuMixin`: 地图右键菜单事件处理。
  - `UpdateMixin`: 更新检测与提示。
  - `HiddenUIMixin`: 隐藏辅助面板（时间、日期）管理。

### 2. 核心基础设施 (`core/`)

提供跨模块的基础支持能力，不依赖任何业务逻辑。

- **`signals.py`**: 全局信号管理器，实现模块间的松耦合通信。
- **`background_task.py`**: 后台任务管理系统，支持优先级队列、进度回调及任务中断。
- **`di.py`**: 依赖注入容器，管理服务实例的生命周期。
- **`logging_setup.py`**: 日志系统配置，支持文件轮转及控制台输出重定向。
- **`resource_path.py`**: 资源路径辅助工具，兼容开发环境与 PyInstaller 打包环境。

### 3. 领域层 (`domain/`)

纯业务逻辑层，**零 PyQt5 依赖**，可独立测试。

- **`models/`**: 核心数据模型（`Route`、`Location`、`SearchResult`）。
- **`services/`**: 业务服务接口（抽象基类）：
  - `IGeocodingService`: 地理编码/逆编码接口。
  - `IRoutingService`: 路线规划接口。
  - `ILocationService`: 设备定位接口。
  - `IConfigService`: 配置读写接口。
- **`coordinators/`**: 业务协调器，编排多个服务完成跨域用例：
  - `SearchCoordinator`: 搜索流程（编码 → 存储 → 通知）。
  - `RouteCoordinator`: 路线规划流程（请求 → 坐标转换 → 结果封装）。
  - `LocationCoordinator`: 定位流程（多源融合）。
  - `ExportCoordinator`: GPX 导出流程。
  - `MapContextCoordinator`: 地图右键菜单业务逻辑。

### 4. 基础设施层 (`infrastructure/`)

实现领域接口，封装外部依赖，**不含业务逻辑**。

- **`api/gaode/`**: 高德地图 Web 服务 API 实现（地理编码、逆地理编码、路径规划）。
- **`api/osm/`**: OpenStreetMap Nominatim/OSRM API 实现。
- **`config/`**: 应用程序配置读写实现（地图源、API Key、用户偏好）。
- **`http/`**: 本地 HTTP 服务器，用于高效加载动态地图瓦片。
- **`storage/`**: 数据持久化实现（地理信息缓存）。

### 5. UI 功能模块 (`modules/`)

按业务领域划分的独立 UI 功能单元，依赖 PyQt5 但不含核心业务逻辑。

- **`geolocation/`**:
  - `coordinate_transform.py`: 坐标转换工具，所有转换统一通过 `CoordinateTransform.convert()` 调用，支持 WGS-84 ↔ GCJ-02。
  - `windows_location.py`: Windows 原生定位服务封装（实现 `ILocationService`）。
- **`map/`**:
  - `map_renderer.py`: 基于 Folium 生成 HTML 地图，集成 Leaflet.js。
  - `js_bridge.py`: `MapJsBridge` — 统一封装所有地图 JS 调用，消除内联 JS 字符串。
  - `js/`: 独立 JS 文件（`map_zoom.js`、`map_center.js`、`map_road_overlay.js`、`map_geolocation.js`、`map_get_view_state.js`、`map_update_route.js`）。
  - `webengine.py`: 自定义 `QWebEnginePage`，拦截控制台消息处理定位回调。
- **`routing/`**:
  - `ui/route_plan_panel.py`: 路线规划交互面板。
  - `storage/route_history_storage.py`: 路线历史记录持久化存储。
- **`search/`**: 搜索历史、结果展示弹窗及地理信息存储逻辑。
- **`gpx/`**: `gpx_export.py` — 将路线数据导出为标准 GPX 格式，支持时区自动检测。

### 6. 服务层 (`services/`)

保留用于向后兼容；新代码优先使用 `infrastructure/` 或 `domain/` 中的实现。

- **`gaode/`**: 高德地图 API 封装（地理编码、路径规划）。
- **`osm/`**: OpenStreetMap API 封装。
- **`config/`**: 地图配置管理。
- **`interfaces/`**: 旧接口路径 shim（重定向至 `domain/services/`）。

### 7. 用户界面 (`ui/`)

基于 PyQt5 构建的现代化 UI 组件库。

- **`panels/`**: 侧边栏功能面板（日志、比例尺、时间日期、任务进度）。
- **`popups/`**: 浮动弹窗（设置、更新提示、GPX 导出向导、右键菜单）。
- **`widgets/`**: 自定义动画按钮、日期时间选择器等交互控件。
- **`viewmodels/`**: MVVM ViewModel 层（`AppViewModel`、`MapViewModel`、`RouteViewModel`、`SearchViewModel`），解耦 UI 与业务状态。
- **`icons/`**: SVG/PNG 图标资源管理及主题适配。
- **`styles.py`**: 统一的 QSS 样式定义。

---

## ⚙️ 关键技术特性

1. **严格分层架构**: `domain/` 零框架依赖，可独立单元测试；`infrastructure/` 实现接口，可替换；UI 层通过 ViewModel 与业务解耦。
2. **JS 调用统一管理**: 所有地图 JavaScript 调用通过 `MapJsBridge` 统一分发，JS 逻辑存放于 `modules/map/js/` 独立文件，消除内联 JS 字符串。
3. **坐标转换统一入口**: 所有 WGS-84 ↔ GCJ-02 转换通过 `CoordinateTransform.convert()` 调用，不直接调用底层函数。
4. **双地图引擎支持**: 无缝切换高德地图（GCJ-02）与 OSM（WGS-84），坐标系自动适配。
5. **异步任务处理**: 所有耗时操作（定位、规划、下载）均通过 `TaskManager` 在后台线程执行，确保 UI 流畅响应。
6. **智能缩放算法**: 根据 POI 类型（如小区、街道、城市）及实际半径自动计算最佳地图缩放级别。
7. **高性能渲染**: 使用 Canvas 渲染器优化大量轨迹点的显示性能，支持数万个坐标点的平滑拖动。

## 🧪 测试

单元测试位于根目录 `tests/`，覆盖领域层核心逻辑：

- `test_coordinate_transform.py`: 坐标转换精度验证
- `test_domain_models.py`: 领域模型行为测试
- `test_route_coordinator.py`: 路线规划协调器测试
- `test_search_coordinator.py`: 搜索协调器测试
- `test_export_coordinator.py`: GPX 导出协调器测试

运行：`python -m pytest tests/ -q`（当前 **86 tests passed**）

## 🚀 运行与开发

1. **环境要求**: Python 3.8+, PyQt5, PyQtWebEngine, Folium, Requests.
2. **启动方式**: 运行根目录下的 `main.py`。
3. **配置**: 首次启动需在【地图设置】中配置高德地图 Web 服务 API Key 以启用完整功能。

---

_本文档根据 `src` 目录代码结构手动维护，最后更新：2026-04-21_
