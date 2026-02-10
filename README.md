# GPX Studio

基于 PyQt5 的开源 GPX 路线规划工具，支持多交通方式、智能缩放、实时预览。

## 核心功能

- **路线规划**：步行/骑行/驾车多交通方式，多条路线方案对比，途径点管理，实时距离/时间/海拔显示
- **地图定位**：高德地图/OSM双地图源，智能缩放，地点搜索，Windows原生定位
- **地图右键菜单**：右键点击地图任意位置，快速设置起点/途径点/终点，显示位置详细信息
- **GPX导出**：兼容主流GPS设备，支持时区检测
- **数据管理**：统一数据目录，配置/日志/缓存分类存储，支持开发和打包环境
- **技术特性**：异步处理，启动优化，模块化设计，ESC快捷键支持

## 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/PingWangWang/gpx-studio.git
cd gpx-studio

# 2. 创建并激活虚拟环境（推荐）
python -m venv .venv

# Windows CMD 激活虚拟环境
.venv\Scripts\activate

# Windows PowerShell 激活虚拟环境
# .venv\Scripts\Activate.ps1

# Linux/macOS 激活虚拟环境
# source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt
# 清华镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
# 阿里镜像
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 4. 运行程序
python main.py

# 退出虚拟环境
deactivate

# 删除虚拟环境（如需重新创建）
# Windows CMD
rmdir /s /q .venv
# Windows PowerShell
# Remove-Item -Recurse -Force .venv
# Linux/macOS
# rm -rf .venv
```

### 配置地图
首次使用需配置高德地图 API Key：
1. 访问 [高德开放平台](https://lbs.amap.com/) 申请密钥
2. 应用内：工具 → 地图配置 → 输入 API Key

## 项目结构

```
GPXStudio/
├── main.py                 # 程序入口
├── version.py              # 版本号
├── requirements.txt        # 依赖清单
├── setup.py/setup.cfg      # 安装和测试配置
├── scripts/                # 维护脚本
│   ├── clean.py            # 项目清理
│   └── run_gpx_tests.py    # 运行测试
├── build/                  # 打包脚本
├── res/                    # 资源文件（图标）
├── Dist/                   # 打包输出目录
│   └── GPXStudioData/      # 数据目录（开发环境）
│       ├── config/         # 配置文件
│       ├── logs/           # 日志文件
│       ├── cache/          # 缓存目录
│       │   ├── GaoDeMapData/  # 高德地图缓存
│       │   └── OSMMapData/    # OSM地图缓存
│       ├── GeoInfoList.json   # 地理信息列表
│       └── RouteHistoryList.json  # 路线历史
└── src/                    # 源代码
    ├── app/                # 主应用
    │   ├── data_paths.py   # 数据路径管理
    │   └── managers/       # 管理器模块
    ├── core/               # 核心功能（异步、信号、DI）
    ├── modules/            # 功能模块（定位、GPX、地图、路线）
    ├── services/           # 服务层（高德、OSM、配置）
    ├── ui/                 # 界面组件
    │   └── popups/         # 弹出面板（设置、日志、关于）
    └── tests/              # 测试代码
```

**注意**：打包后的程序会在安装目录旁创建 `GPXStudioData` 文件夹存储所有数据。

## 开发指南

### 运行测试
```bash
# 运行所有GPX测试
python scripts/run_gpx_tests.py

# 运行特定测试
python -m unittest src.tests.unit.modules.gpx.test_gpx_export.TestGpxExportService.test_export_to_gpx
```

### 清理项目
```bash
python scripts/clean.py --all      # 清理所有
python scripts/clean.py --build    # 只清理构建文件
python scripts/clean.py --cache    # 只清理缓存
```

### 打包与安装包
```bash
# 生成 onedir 目录（启动更快，适合制作安装包）
python build/build_release_pyinstaller.py

# 生成安装包（Inno Setup）
# 1) 先运行上面的打包脚本
# 2) 使用 Inno Setup 编译 build/create_installer_script.iss
```

**安装目录规则**
- 默认安装目录：`C:\Program Files\GPX Studio\v{版本号}`
- 每次升级会创建新的版本目录（例如：`v1.0.0` → `v2.0.0`）
- 如果目标目录已存在，安装器会提示用户选择处理方式

## 技术栈

- **Python** 3.7+ | **GUI**: PyQt5 + PyQtWebEngine
- **地图**: folium + xyzservices | **路线**: 高德API / OSM Nominatim
- **GPX**: gpxpy | **定位**: winrt (Windows原生)

## 核心特性

### 多路线方案对比（v2.0新增）
参考高德地图，驾车路线规划提供3条备选方案：
- **推荐方案**：综合时间和路况的最优路线
- **距离最短**：路程最短的路线
- **躲避拥堵**：避开拥堵路段的路线

每条路线显示详细信息（距离、时间、红绿灯数、收费），支持一键切换预览。

### 统一数据管理（v2.0新增）
所有数据文件统一存储在 `GPXStudioData` 目录：
- **开发环境**：`项目根目录/Dist/GPXStudioData`
- **打包环境**：`安装目录旁/GPXStudioData`
- **自动分类**：配置、日志、缓存分别存储
- **地图缓存**：高德和OSM地图数据独立缓存，加快加载速度

### 智能缩放
基于POI实际范围（中心到入口距离）自动计算最佳缩放级别，支持20级精度。

### 搜索可视化
选中地址绿色标记，其他结果灰色标记，点击即时切换。搜索历史自动保存，支持快速回填。

### 地图右键菜单
在地图上右键点击任意位置，弹出自定义菜单显示位置信息（名称、坐标、类型），提供快速操作：设为起点、添加途径点、设为终点。详见 [地图右键菜单文档](docs/MAP_CONTEXT_MENU.md)。

### 异步架构
后台任务管理器 + 信号槽机制，UI线程与业务逻辑完全分离。

### 快捷键支持（v2.0新增）
- **ESC键**：快速关闭所有弹出面板（设置、日志、关于、路线规划）
- **Enter键**：搜索框内按回车快速搜索

## 版本历史

**v2.0.1** (2026-02-10) - 安装程序优化
- 📦 **安装程序修复**：修复默认安装路径显示错误的问题，确保升级时显示正确的新版本路径
- 🎨 **界面优化**：调整安装和卸载引导界面高度，使界面更加紧凑美观
- 🔧 **打包修复**：修复打包过程中的语法错误，确保安装程序能够正常编译
- 📝 **日志增强**：添加详细的安装过程日志，便于问题诊断

**v2.0.0** (2026-01-16) - 重大更新
- ✨ **多路线方案**：驾车路线提供3条备选方案（推荐/最短/躲避拥堵），支持对比和切换
- 📁 **统一数据管理**：所有数据文件集中存储在GPXStudioData目录，支持开发和打包环境
- 🗺️ **地图缓存**：高德和OSM地图数据独立缓存，显著提升加载速度
- ⌨️ **快捷键支持**：ESC键快速关闭弹出面板，Enter键快速搜索
- 🎨 **UI优化**：右侧按钮垂直居中，窗口大小调整为1000x600，全局字体统一为微软雅黑
- 🔧 **配置优化**：地图配置保存后自动重新加载，API Key配置问题修复
- 🐛 **Bug修复**：放大缩小按钮功能修复，历史记录自动恢复坐标

**v1.4.0** - 右键菜单智能缩放优化，基于高德地图API地址级别实现精确缩放

**v1.3.3** - 版本号更新，打包文件名格式优化（使用下划线）

**v1.3.2** - 项目结构优化，numpy/pandas兼容性修复

**v1.3.0** - 智能缩放，图标差异化，启动优化，异步重构

**v1.2.0** - GPX导出优化，海拔数据修复

**v1.1.0** - 多地图源支持，路线算法优化

**v1.0.0** - 初始版本

## 项目重组说明

**2026-01-16 v2.0.0 重大更新：**
- 实现多路线方案对比功能（参考高德地图）
- 统一数据目录管理（GPXStudioData）
- 地图缓存系统（高德/OSM独立缓存）
- UI/UX优化（ESC快捷键、垂直居中、字体统一）
- 配置管理优化（自动重载、路径修复）

**2026-01-15 项目结构优化：**
- 脚本文件移至 `/scripts` 目录
- PyInstaller配置移至 `/build` 目录
- 修复所有 `interfaces` 包的 `__init__.py` 文件
- 测试框架从pytest改为unittest（解决导入问题）
- 修复numpy 2.x与pandas 1.x兼容性问题

## 贡献与许可

**许可证**: MIT License

**贡献流程**:
1. Fork 仓库
2. 创建分支 (`git checkout -b feature/YourFeature`)
3. 提交代码 (`git commit -m 'Add feature'`)
4. 推送分支 (`git push origin feature/YourFeature`)
5. 提交 Pull Request

**联系方式**:
- GitHub: https://github.com/PingWangWang/gpx-studio
- Email: 1341783770@qq.com

---

⭐ 如果这个项目对您有帮助，欢迎 Star！
