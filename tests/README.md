# GPX Studio 测试模块

这个目录包含了GPX Studio项目的所有单元测试脚本，按照功能模块进行了组织。

## 测试目录结构

```
tests/
├── conftest.py                 # pytest配置文件
├── unit/                       # 单元测试
│   ├── app/                    # 应用层测试
│   │   └── test_app.py         # 主应用程序测试
│   ├── core/                   # 核心模块测试
│   │   └── test_core.py        # 依赖注入、信号管理等测试
│   ├── modules/                # 功能模块测试
│   │   ├── gpx/                # GPX处理模块测试
│   │   │   ├── test_gpx.py     # GPX相关功能测试
│   │   │   └── test_gpx_export.py # GPX导出服务测试
│   │   ├── geolocation/        # 地理位置模块测试
│   │   │   └── test_location_helper.py # 地理位置辅助功能测试
│   │   ├── map/                # 地图模块测试
│   │   │   └── test_map.py     # 地图渲染相关测试
│   │   ├── routing/            # 路由模块测试
│   │   │   └── test_routing.py # 路由服务接口测试
│   │   └── search/             # 搜索模块测试
│   │       ├── test_search.py  # 搜索功能测试
│   │       └── test_search_module.py # 搜索模块测试
│   └── services/               # 服务层测试
│       ├── config/             # 配置服务测试
│       │   └── test_config.py  # 地图配置管理测试
│       ├── http/               # HTTP服务测试
│       │   └── test_http_server.py # HTTP服务器服务测试
│       ├── test_geocoding.py   # 地理编码服务测试
│       └── test_routing.py     # 路由服务测试
└── __init__.py
```

## 运行测试

从项目根目录运行：

```bash
# 安装项目（开发模式）
pip install -e .

# 运行所有测试
python -m pytest tests/

# 运行特定模块的测试
python -m pytest tests/unit/services/
python -m pytest tests/unit/modules/gpx/
python -m pytest tests/unit/core/

# 运行单个测试文件
python -m pytest tests/unit/modules/gpx/test_gpx_export.py

# 查看详细输出
python -m pytest tests/ -v
```

## 测试说明

- 所有测试遵循单元测试最佳实践，使用mocking隔离外部依赖
- 测试覆盖了核心功能包括GPX处理、地理编码、路线规划、地图渲染等
- UI相关功能需要通过手动测试进行验证，不包含在自动化测试中
- 使用unittest框架和pytest运行器
- 配置文件位于tests/conftest.py和setup.cfg
- 所有测试均已通过验证，可在安装开发模式后正常运行