# GPX Studio

GPX Studio是一款基于PyQt5开发的开源路线规划工具，支持多种交通方式，可生成并导出GPX格式的路线文件。

## 主要功能

- **路线规划**：支持起点、终点及多个途径点的路线规划
- **多种交通方式**：支持步行、骑行、驾车等多种交通方式
- **地图显示**：集成高德地图，提供直观的地图界面
- **路线信息展示**：显示详细的路线信息，包括起点、途径点、终点、时间、距离等
- **GPX导出**：将规划的路线导出为GPX格式文件
- **地理定位**：支持当前位置获取

## 技术栈

- **Python 3.x**
- **PyQt5**：GUI框架
- **PyQtWebEngine**：Web视图组件
- **folium**：地图可视化
- **gpxpy**：GPX文件处理
- **requests**：HTTP请求
- **geopy**：地理计算
- **高德地图API**：地理编码、路线规划服务

## 安装

### 环境要求

- Python 3.7+
- Windows 10/11 (支持Windows定位服务)

### 安装步骤

1. 克隆仓库

   ```bash
   git clone https://github.com/your-username/gpx-studio.git
   cd gpx-studio
   ```
2. 创建虚拟环境 (可选但推荐)

   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   ```
3. 安装依赖

   ```bash
   pip install -r requirements.txt
   ```
4. 配置高德地图API密钥

   - 访问 [高德开放平台](https://lbs.amap.com/) 申请API密钥
   - 将API密钥填写到 `config/gaode_config.json` 文件中

## 使用方法

1. 启动应用

   ```bash
   python main.py
   ```
2. 规划路线

   - 输入起点和终点
   - 可添加多个途径点
   - 选择交通方式
   - 设置起始时间
   - 点击"规划路线"按钮
3. 查看路线信息

   - 地图上显示规划的路线
   - 中间面板显示详细的路线信息
4. 导出GPX文件

   - 路线规划完成后，点击"导出GPX"按钮
   - 选择保存位置

## 项目结构

```
GPX-Studio/
├── core/             # 核心应用逻辑
├── handlers/         # 事件处理器
├── services/         # 服务层
├── ui/               # UI组件
├── utils/            # 工具函数
├── config/           # 配置文件
├── tests/            # 测试用例
├── main.py           # 主程序入口
├── requirements.txt  # 依赖列表
└── README.md         # 项目说明
```

## 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork 仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系方式

如有问题或建议，请通过以下方式联系：

- 项目地址：https://github.com/PingWangWang/gpx-studio
- 邮箱：1341783770@qq.com

## 更新日志

### v1.0.0

- 初始版本
- 基本路线规划功能
- GPX导出支持
- 多种交通方式
