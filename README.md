# GPX Studio

基于 PyQt5 的开源 GPX 路线规划工具，支持多交通方式、智能缩放、实时预览。

## 核心功能

### 路线规划
- **多交通方式**：步行、骑行、驾车
- **途径点管理**：添加/删除/调整多个途径点
- **路线信息**：实时显示距离、时间、海拔
- **GPX 导出**：兼容主流 GPS 设备

### 地图与定位
- **双地图源**：高德地图、OpenStreetMap
- **智能缩放**：基于 POI 实际范围自动调整缩放级别
- **地点搜索**：模糊搜索，结果差异化显示（绿色选中，灰色未选）
- **实时定位**：Windows 原生定位服务支持

### 技术特性
- **异步处理**：后台任务不阻塞 UI
- **启动优化**：带进度的启动画面
- **模块化设计**：清晰的分层架构

## 技术栈

- **Python** 3.7+
- **GUI**：PyQt5 + PyQtWebEngine
- **地图**：folium (可视化) + xyzservices (瓦片服务)
- **路线**：高德地图 API / OSM Nominatim
- **GPX**：gpxpy (文件处理)
- **定位**：winrt (Windows 原生)

## 快速开始

### 环境要求
- Python 3.7+
- Windows 10/11（定位功能需要）

### 安装运行

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

## 使用流程

1. **搜索地点**：输入关键词 → 选择起点/终点/途径点
2. **规划路线**：选择交通方式 → 点击"规划路线"
3. **查看结果**：地图显示路线 + 详细信息面板
4. **导出文件**：点击"导出 GPX"保存路线

## 项目结构

```
GPX-Studio/
├── main.py                 # 程序入口
├── requirements.txt        # 依赖清单
├── version.py              # 版本号
├── build/                  # 打包脚本
├── res/                    # 资源文件
└── src/                    # 源代码
    ├── app/                # 主应用
    │   └── managers/       # 业务管理器
    ├── core/               # 核心功能
    │   ├── background_task.py   # 异步任务
    │   ├── signals.py           # 信号管理
    │   └── di.py                # 依赖注入
    ├── modules/            # 功能模块
    │   ├── geolocation/    # 定位服务
    │   ├── gpx/            # GPX 处理
    │   ├── map/            # 地图渲染
    │   └── routing/        # 路线规划
    ├── services/           # 服务层
    │   ├── gaode/          # 高德地图
    │   ├── osm/            # OSM 服务
    │   └── config/         # 配置管理
    └── ui/                 # 界面组件
        ├── dialogs/        # 对话框
        ├── layout/         # 布局
        └── panels/         # 面板
```

## 核心特性

### 智能缩放
- 基于 POI 实际范围（中心到入口距离）计算最佳缩放级别
- 三级优先级：实际半径 > POI 类型 > 行政区划
- 支持 20 级缩放精度（国家级到超精细级）

### 搜索结果可视化
- 选中地址：绿色图标 + "ok-sign"
- 其他结果：灰色图标 + "info-sign"
- 点击即时切换高亮显示

### 异步架构
- 后台任务管理器（TaskManager）
- 信号槽机制（SignalManager）
- UI 线程与业务逻辑完全分离

## 版本历史

### v1.3.0 (当前版本)
- ✅ 智能缩放：基于 POI 实际范围自动调整地图缩放
- ✅ 图标差异化：选中地址绿色标记，其他灰色标记
- ✅ 启动优化：添加进度条启动画面
- ✅ 异步重构：后台任务不阻塞 UI
- ✅ 类型识别：优化建筑、景点、生活服务场所识别

### v1.2.0
- GPX 导出优化：下划线连接起点终点
- 海拔数据处理修复
- 长地址显示优化

### v1.1.0
- 多地图源支持（高德 + OSM）
- 路线算法优化
- 错误处理增强

### v1.0.0
- 初始版本发布

## 贡献与许可

**许可证**：MIT License

**贡献流程**：
1. Fork 仓库
2. 创建分支 (`git checkout -b feature/YourFeature`)
3. 提交代码 (`git commit -m 'Add feature'`)
4. 推送分支 (`git push origin feature/YourFeature`)
5. 提交 Pull Request

**联系方式**：
- GitHub：https://github.com/PingWangWang/gpx-studio
- Email：1341783770@qq.com

---

⭐ 如果这个项目对您有帮助，欢迎 Star！