# GPX Studio 配置系统说明

## 📋 配置文件概述

GPX Studio 使用两种类型的配置文件：

### 🏠 **运行时配置文件** (实际使用)
**路径**: `dist/GPXStudioData/config/map_config.json`

```json
{
  "log_level": "DEBUG",
  "is_first_run": false,
  "map_source": "gaode",
  "api_key": "b095225610e2763fae50488099c4aa81",
  "security_key": ""
}
```

- ✅ **程序实际使用的配置文件**
- 🏠 **用户数据目录** - 存储用户的个人配置
- 💾 **动态更新** - 程序运行时会读取和写入此文件
- 🔑 **包含敏感信息** - API密钥等用户配置
- 📍 **位置**: 用户数据目录，不会被程序更新覆盖

### 📝 **模板配置文件** (仅供参考)
**路径**: `src/services/config/config/map_config.json`

```json
{
  "_comment": "这是配置模板文件，仅供参考。程序运行时使用 dist/GPXStudioData/config/map_config.json",
  "_template_version": "1.0",
  "_description": "默认配置模板，包含所有可用的配置选项和默认值",
  
  "map_source": "osm",
  "api_key": "",
  "security_key": "",
  "route_optimization": {
    "enabled": true,
    "max_points_per_segment": 500,
    "auto_zoom_calculation": true
  }
}
```

- 📝 **仅作为参考模板** - 展示配置结构和默认值
- 🏗️ **源代码一部分** - 随代码分发
- 🔒 **程序不读取** - 程序运行时不会加载此文件
- 📚 **文档作用** - 帮助开发者了解配置选项

## 🔄 配置系统工作原理

### 1. **程序启动时**
```python
# 只加载运行时配置文件
config_file = "dist/GPXStudioData/config/map_config.json"
if os.path.exists(config_file):
    # 加载用户配置
    with open(config_file, 'r') as f:
        config_data = json.load(f)
    
    # 自动补全缺失的配置项
    _ensure_complete_config()
else:
    # 使用空配置，等待用户设置
    config_data = {}
```

### 2. **配置自动补全机制**

当程序启动时，MapConfig 类会自动检查运行时配置文件是否包含所有必要的配置项。如果发现缺失的配置项，会自动从模板配置中添加默认值到运行时配置文件中。

#### **自动补全的配置项**
- `route_optimization`: 路线渲染优化设置
  - `enabled`: 是否启用路线优化 (默认: true)
  - `max_points_per_segment`: 每段路线的最大点数 (默认: 500)
  - `auto_zoom_calculation`: 是否启用自动缩放级别计算 (默认: true)

#### **工作流程**
1. 程序启动时，MapConfig 读取运行时配置文件
2. 调用 `_ensure_complete_config()` 方法检查配置完整性
3. 如果发现缺失配置项，自动添加默认值
4. 将更新后的配置保存回运行时配置文件
5. 后续程序运行使用完整的配置

这确保了即使用户的运行时配置文件缺少某些配置项，程序也能正常工作，并且配置会被持久化保存。

### 3. **配置保存时**
```python
# 只保存到运行时配置文件
def save_config(self, config_data):
    config_file = "dist/GPXStudioData/config/map_config.json"
    with open(config_file, 'w') as f:
        json.dump(config_data, f, indent=2)
```

### 4. **配置读取优先级**
1. **运行时配置** - 程序唯一使用的配置源
2. **空配置** - 如果运行时配置不存在或损坏

## 📁 配置文件位置说明

### 🎯 **为什么这样设计？**

#### **运行时配置在用户数据目录**
- ✅ **用户数据持久化** - 程序更新不会丢失用户配置
- ✅ **权限安全** - 用户有完全控制权
- ✅ **多用户支持** - 每个用户有独立配置
- ✅ **备份友好** - 用户可以轻松备份配置

#### **模板配置在源代码目录**
- ✅ **版本控制** - 随代码版本管理
- ✅ **文档作用** - 展示完整配置结构
- ✅ **开发参考** - 开发者了解配置选项
- ✅ **不被程序使用** - 避免混淆

## 🔧 配置项说明

### **基础配置**
- `map_source`: 地图数据源 (`"gaode"` | `"osm"`)
- `api_key`: 高德地图API密钥
- `security_key`: 高德地图安全密钥
- `log_level`: 日志级别 (`"DEBUG"` | `"INFO"` | `"WARNING"` | `"ERROR"`)
- `is_first_run`: 是否首次运行标记

### **路线优化配置** (可选)
- `route_optimization.enabled`: 是否启用路线优化
- `route_optimization.max_points_per_segment`: 每段路线最大点数
- `route_optimization.auto_zoom_calculation`: 是否自动计算缩放级别

## 🛠️ 开发者指南

### **添加新配置项**
1. 在模板文件中添加新配置项和默认值
2. 在 `MapConfig` 类中添加对应的getter/setter方法
3. 更新此文档说明

### **配置迁移**
如果需要修改配置结构：
1. 保持向后兼容性
2. 在代码中处理缺失的配置项
3. 提供合理的默认值

### **测试配置**
```python
# 测试配置加载
config = MapConfig()
assert config.get_map_source() == "gaode"  # 从运行时配置读取

# 测试配置保存
config.save_config({"map_source": "osm"})
assert config.get_map_source() == "osm"
```

## 🚨 注意事项

### ❌ **不要做的事情**
- 不要让程序读取模板配置文件
- 不要在模板配置文件中存储敏感信息
- 不要混合使用两个配置文件

### ✅ **正确的做法**
- 程序只使用运行时配置文件
- 模板配置文件仅作为文档和参考
- 缺失的配置项使用合理的默认值
- 保持配置文件结构的向后兼容性

## 📝 配置文件示例

### **完整的运行时配置示例**
```json
{
  "log_level": "INFO",
  "is_first_run": false,
  "map_source": "gaode",
  "api_key": "your_gaode_api_key_here",
  "security_key": "your_security_key_here",
  "route_optimization": {
    "enabled": true,
    "max_points_per_segment": 500,
    "auto_zoom_calculation": true
  }
}
```

### **最小运行时配置示例**
```json
{
  "map_source": "osm",
  "api_key": "",
  "security_key": ""
}
```

这样的设计确保了配置系统的简洁性和可维护性，避免了复杂的配置合并逻辑。