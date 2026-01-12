# GPX Studio

GPX Studio 是一款基于 PyQt5 开发的开源路线规划工具，支持多种交通方式，可生成并导出 GPX 格式的路线文件。

## 主要功能

- **多交通方式路线规划**：支持步行、骑行、驾车
- **多地图源支持**：集成高德地图和 OSM 地图
- **途径点管理**：支持多个途径点，可调整顺序
- **路线信息展示**：显示距离、预计时间等详细信息
- **GPX 导出**：兼容主流 GPS 设备和导航软件
- **地理定位**：支持获取当前位置
- **地点搜索**：支持模糊搜索快速定位
- **实时日志**：便于调试和问题排查
- **跨平台支持**：兼容 Windows、macOS 和 Linux

## TODO LIST
- [ ] 将界面操作逻辑和后台逻辑分离，实现解耦，防止后台阻塞界面
- [ ] 增加程序启动进度条，提示用户等待

## 技术栈

- **Python 3.7+**
- **PyQt5** / **PyQtWebEngine**
- **folium** (地图可视化)
- **gpxpy** (GPX 处理)
- **requests** (HTTP 请求)
- **geopy** (地理计算)

## 安装

### 环境要求
- Python 3.7+
- Windows 10/11 (支持定位服务)

### 安装步骤

1. 克隆仓库
   ```bash
   git clone https://github.com/PingWangWang/gpx-studio.git
   cd gpx-studio
   ```

2. 创建虚拟环境 (可选)
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   ```

3. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

4. 配置地图 API 密钥
   - 高德地图：访问 [高德开放平台](https://lbs.amap.com/) 申请 API 密钥
   - 通过应用界面配置："工具" -> "地图配置"

## 使用方法

1. **启动应用**：`python main.py`
2. **搜索地点**：输入关键词，选择起点/终点/途径点
3. **规划路线**：设置起点、终点、途径点，选择交通方式，点击"规划路线"
4. **查看路线**：右侧地图显示路线，中间面板显示详细信息
5. **导出 GPX**：路线规划完成后，点击"导出 GPX"按钮

## 项目结构

### 项目根目录
```
GPX-Studio/
├── main.py                 # 应用程序入口
├── requirements.txt        # 项目依赖
├── setup.py                # 包构建配置
├── setup.cfg               # 安装配置
├── version.py              # 版本信息
├── README.md               # 项目说明
├── build/                  # 构建脚本
├── clean.py                # 清理脚本
├── .vscode/                # VS Code配置
├── .gitignore              # Git忽略规则
├── .venv/                  # 虚拟环境（可选）
```

### 源代码结构
```
GPX-Studio/
├── src/                    # 源代码根目录
│   ├── app/                # 主应用
│   ├── core/               # 核心逻辑
│   ├── modules/            # 功能模块
│   │   ├── geolocation/    # 定位功能
│   │   ├── gpx/            # GPX处理
│   │   ├── map/            # 地图渲染
│   │   ├── routing/        # 路线规划
│   │   └── search/         # 位置搜索
│   ├── services/           # 服务层
│   │   ├── config/         # 配置服务
│   │   ├── gaode/          # 高德地图服务
│   │   ├── osm/            # OSM地图服务
│   │   ├── http/           # HTTP服务
│   │   └── interfaces/     # 服务接口
│   ├── ui/                 # UI组件
│   │   ├── dialogs/        # 对话框
│   │   ├── layout/         # 布局管理
│   │   └── panels/         # 面板组件
│   ├── tests/              # 测试用例
│   ├── scripts/            # 工具脚本
│   ├── docs/               # 文档
│   └── version.py          # 版本信息
```

## 贡献

1. Fork 仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

MIT 许可证

## 联系方式

- 项目地址：https://github.com/PingWangWang/gpx-studio
- 邮箱：1341783770@qq.com

## 更新日志

### v1.2.0
- 优化 GPX 导出功能，使用下划线连接起点和终点名称
- 修复高德地图路线规划中海拔数据处理问题
- 优化地址显示栏，移除无功能的箭头按钮
- 修复长地址名称被滚动条遮挡的问题
- 版本信息同步更新

### v1.1.1
- 优化 PyInstaller 打包脚本
- 移除 Nuitka 打包支持
- 修复构建过程中的路径处理问题
- 增强错误处理和日志输出
- 版本信息同步更新

### v1.1.0
- 添加 OSM 地图支持
- 多地图源切换功能
- 路线规划算法优化
- 错误处理增强
- 测试覆盖改进

### v1.0.1
- 代码重构与模块化设计
- 依赖注入容器引入
- 服务接口规范化
- UI 组件分离

### v1.0.0
- 初始版本发布
- 基本路线规划功能
- 多种交通方式支持
- GPX 导出功能
- 地图集成与定位
