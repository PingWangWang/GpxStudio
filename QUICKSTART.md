# GPX Studio 快速开始指南

## 目录结构概览

```
GpxStudio/
├── main.py              # 启动程序
├── test_services.py     # 服务模块测试脚本
├── .vscode/            # VS Code配置
│   ├── launch.json     # 调试配置
│   ├── settings.json   # 编辑器设置
│   └── tasks.json      # 任务配置
├── core/               # 主应用窗口
├── handlers/           # 定位和WebEngine处理器
├── services/           # 地理编码、路由、GPX导出服务
├── ui/                # UI面板和样式
└── utils/             # 地图渲染和定位工具
```

## 快速启动

```bash
# 1. 进入项目目录
cd d:\Code\GpxStudio

# 2. 安装依赖（如果还没安装）
pip install -r requirements.txt

# 3. 运行程序
python main.py
```

## 调试和开发

### VS Code 调试配置

项目已配置好VS Code调试环境，支持以下调试模式：

#### 1. 主程序调试
- **配置名称**: "Python: GPX Studio"
- **用途**: 从main.py启动完整程序
- **快捷键**: F5 (选择此配置)

#### 2. 外部终端调试
- **配置名称**: "Python: GPX Studio (External Terminal)"
- **用途**: 在外部终端窗口运行，便于查看GUI

#### 3. 核心模块调试
- **配置名称**: "Python: Debug Core Module"
- **用途**: 直接调试core.app模块

#### 4. 服务模块测试
- **配置名称**: "Python: Debug Services"
- **用途**: 运行test_services.py测试各个服务模块

### 使用调试器

1. **设置断点**: 在代码中点击行号左侧设置断点
2. **启动调试**: 按F5，选择调试配置
3. **调试控制**: 使用调试面板的控制按钮（继续、单步等）
4. **变量查看**: 在调试时查看变量值和调用栈

### 运行任务

VS Code任务栏提供以下快捷任务：

- **Run GPX Studio**: 运行主程序
- **Install Dependencies**: 安装Python依赖
- **Test Services**: 运行服务模块测试
- **Update Requirements**: 更新requirements.txt
- **Clean Cache**: 清理__pycache__文件夹

### 测试服务模块

运行 `test_services.py` 来单独测试各个服务：

```bash
python test_services.py
```

测试包括：
- 地理编码服务（地点搜索）
- 路由规划服务（OSRM API）
- GPX导出服务
- 定位辅助工具（IP定位）

## 核心功能使用

### 1. 搜索地点
- 在"起点"或"终点"输入框输入地名
- 点击"搜索"或按回车
- 从中间面板的搜索结果中选择

### 2. 添加途径点
- 在"途径点"输入框搜索
- 点击搜索结果添加
- 可以添加多个途径点
- 点击"删除选中的途径点"移除

### 3. 定位当前位置
- 点击"📍 定位我的位置"按钮
- 系统会尝试浏览器定位
- 如果失败会自动使用IP定位

### 4. 规划路线
- 设置起点和终点
- 选择交通方式（步行/骑行/驾车）
- 点击"规划路线"按钮
- 地图上会显示规划好的路线

### 5. 导出GPX
- 规划路线后点击"导出GPX"
- 选择保存位置
- GPX文件包含完整的路线和时间信息

## 界面布局优化

程序采用优化的三列布局设计：

- **左侧面板（参数配置）**: 约12.5%宽度 - 包含所有控制选项
- **中间面板（信息展示）**: 约12.5%宽度 - 显示搜索结果和状态
- **右侧面板（地图展示）**: 约75%宽度 - 主要地图显示区域

这样的布局让地图获得更多展示空间，提供更好的用户体验。

## 模块说明

### core/app.py
主应用窗口，整合所有功能。如需修改界面布局或添加新功能，主要在这里编辑。

### handlers/
- `geolocation.py`: 定位信号处理
- `webengine.py`: JS控制台消息拦截

### services/
- `geocoding.py`: 地点搜索和反向地理编码
- `routing.py`: 路由规划（OSRM API）
- `gpx_export.py`: GPX文件生成

### ui/
- `panels.py`: UI面板工厂方法
- `styles.py`: 集中管理UI样式

### utils/
- `map_renderer.py`: Folium地图渲染
- `location_helper.py`: IP定位等辅助功能

## 修改示例

### 修改按钮样式
编辑 `ui/styles.py`:
```python
LOCATE_BUTTON = """
    QPushButton {
        background-color: #YOUR_COLOR;
        ...
    }
"""
```

### 添加新的地图标记
编辑 `utils/map_renderer.py`，使用 `add_marker()` 方法。

### 更换路由服务
编辑 `services/routing.py`，修改 `OSRM_BASE_URL` 或实现新的路由方法。

## 测试功能

程序内置了测试功能：
- 点击"🧪 测试定位功能"检查定位系统状态
- 查看控制台输出的调试信息

## 常见问题

**Q: 搜索不到地点？**
A:
1. 检查网络连接
2. 尝试更具体的地址（如：陕西省西安市）
3. 尝试英文搜索

**Q: 定位失败？**
A:
1. 系统会自动回退到IP定位
2. IP定位精度较低，但可用

**Q: 路线规划失败？**
A:
1. 检查起点和终点是否都已设置
2. 确保网络连接正常
3. OSRM服务可能暂时不可用

## 开发建议

1. **添加新服务**: 在 `services/` 创建新文件
2. **修改UI**: 编辑 `ui/panels.py` 和 `ui/styles.py`
3. **扩展地图功能**: 编辑 `utils/map_renderer.py`
4. **调试**: 查看控制台输出，程序有详细的日志

## 更多文档

- `README.md`: 完整的项目说明
- `STRUCTURE.md`: 详细的项目结构文档
- 各模块文件中的文档字符串

## 获取帮助

查看源代码中的注释和文档字符串，每个类和方法都有详细说明。
