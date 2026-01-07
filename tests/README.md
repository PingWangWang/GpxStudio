# GPX Studio 测试模块

这个目录包含了GPX Studio项目的所有测试脚本。

## 测试文件说明

- `test_services.py` - 测试所有服务模块（地理编码、路由规划、GPX导出等）
- `test_layout.py` - 测试UI布局比例和模块导入
- `test_map_init.py` - 测试地图初始化逻辑
- `test_map_display.py` - 简化的地图显示测试程序

## 运行测试

从项目根目录运行：

```bash
# 测试所有服务
python tests/test_services.py

# 测试布局和模块导入
python tests/test_layout.py

# 测试地图初始化
python tests/test_map_init.py

# 运行地图显示测试程序
python tests/test_map_display.py
```

## 注意事项

所有测试脚本都会自动设置正确的Python路径，无需手动配置。