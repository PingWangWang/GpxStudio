# GPX Studio

基于 PyQt5 的开源 GPX 路线规划工具，支持多交通方式、智能缩放、实时预览。

## 核心功能

- **路线规划**：步行/骑行/驾车多交通方式，途径点管理，实时距离/时间/海拔显示
- **地图定位**：高德地图/OSM双地图源，智能缩放，地点搜索，Windows原生定位
- **GPX导出**：兼容主流GPS设备，支持时区检测
- **技术特性**：异步处理，启动优化，模块化设计

## 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/PingWangWang/gpx-studio.git
cd gpx-studio

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行程序
python main.py
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
└── src/                    # 源代码
    ├── app/                # 主应用
    ├── core/               # 核心功能（异步、信号、DI）
    ├── modules/            # 功能模块（定位、GPX、地图、路线）
    ├── services/           # 服务层（高德、OSM、配置）
    ├── ui/                 # 界面组件
    └── tests/              # 测试代码
```

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

### 打包程序
```bash
python build/build_release_pyinstaller.py    # PyInstaller打包
python build/build_release_nuitka.py         # Nuitka打包
```

## 技术栈

- **Python** 3.7+ | **GUI**: PyQt5 + PyQtWebEngine
- **地图**: folium + xyzservices | **路线**: 高德API / OSM Nominatim
- **GPX**: gpxpy | **定位**: winrt (Windows原生)

## 核心特性

### 智能缩放
基于POI实际范围（中心到入口距离）自动计算最佳缩放级别，支持20级精度。

### 搜索可视化
选中地址绿色标记，其他结果灰色标记，点击即时切换。

### 异步架构
后台任务管理器 + 信号槽机制，UI线程与业务逻辑完全分离。

## 版本历史

**v1.3.3** (当前) - 版本号更新，打包文件名格式优化（使用下划线）
**v1.3.2** - 项目结构优化，numpy/pandas兼容性修复
**v1.3.0** - 智能缩放，图标差异化，启动优化，异步重构
**v1.2.0** - GPX导出优化，海拔数据修复
**v1.1.0** - 多地图源支持，路线算法优化
**v1.0.0** - 初始版本

## 项目重组说明

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
