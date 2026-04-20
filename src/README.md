# GPX Studio 源代码结构说明

GPX Studio 是一个基于 Python 和 PyQt5 的 GPS 路线规划工具，支持高德地图和 OpenStreetMap (OSM) 双数据源，具备路线规划、定位、搜索及 GPX 导出等功能。

## 📁 目录结构概览

```text
src/
├── app/           # 应用核心层：主窗口与业务管理器
├── core/          # 核心基础设施：日志、信号、依赖注入、后台任务
├── modules/       # 功能模块：地理定位、地图渲染、路线规划、搜索、GPX处理
├── services/      # 服务层：高德/OSM API 封装、配置管理、数据存储
└── ui/            # 用户界面：布局、面板、弹窗、自定义控件、图标管理
```

---

## 🏗️ 核心架构设计

### 1. 应用核心 (`app/`)

采用**管理器模式 (Manager Pattern)**，将复杂的业务逻辑解耦为独立的管理器类，由主窗口 `GpxStudio` 统一调度。

- **`app.py`**: 主应用程序入口，负责初始化各个管理器并连接信号。
- **`managers/`**:
  - `WindowManager`: 窗口生命周期、系统托盘及关闭逻辑管理。
  - `ServiceManager`: 统一管理高德、OSM 等第三方服务的实例化。
  - `DataManager`: 集中存储应用状态（起点、终点、路线点、搜索结果等）。
  - `LocationManager`: 协调 Windows 原生定位、浏览器 Geolocation 及 IP 定位。
  - `MapManager`: 负责地图视图的生成、刷新、坐标转换及图层叠加。
  - `RouteManager`: 处理路线规划请求、多方案切换及 GPX 文件导出。
  - `TimeManager`: 管理行程起止时间及途经时间的自动计算。
  - `UpdateManager`: 软件版本检测、下载及自动安装更新。

### 2. 核心基础设施 (`core/`)

提供跨模块的基础支持能力。

- **`signals.py`**: 全局信号管理器，实现模块间的松耦合通信。
- **`background_task.py`**: 后台任务管理系统，支持优先级队列、进度回调及任务中断。
- **`di.py`**: 依赖注入容器，管理服务实例的生命周期。
- **`logging_setup.py`**: 日志系统配置，支持文件轮转及控制台输出重定向。
- **`resource_path.py`**: 资源路径辅助工具，兼容开发环境与 PyInstaller 打包环境。

### 3. 功能模块 (`modules/`)

按业务领域划分的独立功能单元。

- **`geolocation/`**:
  - 坐标转换工具 (`coordinate_transform.py`)：支持 WGS-84 与 GCJ-02 互转。
  - Windows 原生定位服务封装。
- **`map/`**:
  - `map_renderer.py`: 基于 Folium 生成 HTML 地图，集成 Leaflet.js。
  - `http_server.py`: 本地 HTTP 服务器，用于高效加载动态地图瓦片。
- **`routing/`**:
  - `ui/route_plan_panel.py`: 路线规划交互面板。
  - `storage/route_history_storage.py`: 路线历史记录持久化存储。
- **`search/`**:
  - 包含搜索历史、结果展示弹窗及地理信息存储逻辑。
- **`gpx/`**:
  - `gpx_export.py`: 将路线数据导出为标准 GPX 格式，支持时区自动检测。

### 4. 服务层 (`services/`)

封装外部 API 调用及底层数据操作。

- **`gaode/`**: 高德地图 Web 服务 API 封装（地理编码、逆地理编码、路径规划）。
- **`osm/`**: OpenStreetMap Nominatim API 封装。
- **`config/`**: 应用程序配置管理（地图源、API Key、用户偏好）。
- **`storage/`**: 基础数据存储服务接口。

### 5. 用户界面 (`ui/`)

基于 PyQt5 构建的现代化 UI 组件库。

- **`panels/`**: 侧边栏功能面板（日志、比例尺、时间日期、任务进度）。
- **`popups/`**: 浮动弹窗（设置、更新提示、GPX 导出向导、右键菜单）。
- **`widgets/`**: 自定义动画按钮、日期时间选择器等交互控件。
- **`icons/`**: SVG/PNG 图标资源管理及主题适配。
- **`styles.py`**: 统一的 QSS 样式定义。

---

## ⚙️ 关键技术特性

1. **双地图引擎支持**: 无缝切换高德地图（GCJ-02）与 OSM（WGS-84），内置自动坐标纠偏逻辑。
2. **异步任务处理**: 所有耗时操作（定位、规划、下载）均通过 `TaskManager` 在后台线程执行，确保 UI 流畅响应。
3. **智能缩放算法**: 根据 POI 类型（如小区、街道、城市）及实际半径自动计算最佳地图缩放级别。
4. **高性能渲染**: 使用 Canvas 渲染器优化大量轨迹点的显示性能，支持数万个坐标点的平滑拖动。
5. **模块化设计**: 严格的分层架构使得新增地图源或扩展功能变得简单且不影响现有逻辑。

## 🚀 运行与开发

1. **环境要求**: Python 3.8+, PyQt5, PyQtWebEngine, Folium, Requests.
2. **启动方式**: 运行根目录下的 `main.py`。
3. **配置**: 首次启动需在【地图设置】中配置高德地图 Web 服务 API Key 以启用完整功能。

---

_本文档由 AI 根据 `src` 目录代码结构自动生成_
