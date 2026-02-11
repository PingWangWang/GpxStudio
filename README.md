# GPX Studio

基于 PyQt5 的开源 GPX 路线规划工具，支持多交通方式、智能缩放、实时预览。

## 核心功能

- **路线规划**：步行/骑行/驾车多交通方式，多条路线方案对比，途径点管理，实时距离/时间/海拔显示
- **地图定位**：高德地图/OSM双地图源，智能缩放，地点搜索，Windows原生定位
- **地图右键菜单**：右键点击地图任意位置，快速设置起点/途径点/终点，显示位置详细信息
- **GPX导出**：兼容主流GPS设备，智能时间计算，时区检测
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

## 版本历史

**v2.0.6** (2026-02-11) - GPX导出时间计算优化
- ⏱️ **智能时间计算**：GPX导出时，途径点时间根据路线规划的预估总时长自动计算，而非简单的固定间隔
- 🎯 **精准时间分配**：起始时间使用用户设置的时间，后续每个点的时间按总路程/点数均匀分布
- 🔧 **向后兼容**：如果未提供预估总时长，保持默认10秒间隔行为

**v2.0.5** (2026-02-10) - GPX导出功能优化
- 📁 **导出路径记忆**：导出GPX文件时，默认使用上次导出的路径，提高用户体验
- 📅 **文件名时间后缀**：GPX文件名自动添加起始时间后缀，格式为 起点_终点_20260210_0930.gpx
- 💾 **配置管理**：添加导出路径的配置文件存储，确保设置持久化
- 🔧 **代码优化**：重构导出路径管理逻辑，使代码更加清晰易维护

**v2.0.4** (2026-02-10) - 地图模式切换功能
- 🗺️ **地图模式切换**：新增地图模式切换按钮，支持卫星/街道地图切换，点击时保持地图预览区域不变
- 💾 **地图模式保存**：地图模式设置保存到配置中，下次启动时保持相同模式
- 🏷️ **卫星地图标注**：为卫星地图添加标注图层，显示地名和街道名等地理信息
- 🔧 **代码优化**：修复地图模式切换时的参数名称错误，确保功能正常运行

**v2.0.3** (2026-02-10) - 界面优化与功能完善
- 🎨 **加载按钮优化**：替换加载按钮图标为圆形样式，修复旋转动画偏心问题，确保与其他按钮对齐
- 🔧 **地图设置面板**：高德地图切换时强制连接测试，保存按钮状态管理优化
- 🛠️ **路线规划面板**：移除冗余加载按钮，使用占位控件保持布局对齐
- 🔧 **代码优化**：修复搜索地址时的错误处理，提高系统稳定性

**v2.0.2** (2026-02-10) - GPX导出功能优化
- 📅 **时间记忆功能**：导出GPX数据时，起始时间默认值会记忆上次设置的时间，提高用户体验
- 🛠️ **配置管理**：添加时间设置的配置文件存储，确保设置持久化
- 🔧 **代码优化**：重构时间管理逻辑，使代码更加清晰易维护

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
