# 定位功能修复说明

## 🔧 修复内容

### 1. JavaScript控制台日志格式修正
**问题**: JavaScript脚本输出的日志格式与Python处理器期望的格式不匹配
- 原格式: `[定位] 定位成功: lat, lon, accuracy`
- 期望格式: `定位成功: lat, lon, accuracy`

**修复**: 修改了`utils/map_renderer.py`中的`add_geolocation_script`方法，使用正确的日志格式

### 2. 增加定位超时时间
**问题**: 原超时时间为10秒，可能不足以获取定位信息
**修复**: 将超时时间增加到30秒

```javascript
{
    enableHighAccuracy: true,
    timeout: 30000,  // 从10000改为30000
    maximumAge: 0
}
```

### 3. 添加地理定位权限处理
**问题**: WebEngine可能没有正确处理地理定位权限请求
**修复**: 在`handlers/webengine.py`中添加了`featurePermissionRequested`方法来自动授予地理定位权限

```python
def featurePermissionRequested(self, securityOrigin, feature):
    """处理功能权限请求（如地理定位）"""
    if feature == QWebEnginePage.Geolocation:
        self.setFeaturePermission(
            securityOrigin,
            QWebEnginePage.Geolocation,
            QWebEnginePage.PermissionGrantedByUser
        )
```

### 4. 改进地图加载和定位触发逻辑
**修复**: 确保在地图完全加载后才触发定位请求

## 🔍 定位功能工作原理

1. **创建地图**: 使用Folium创建HTML地图
2. **注入脚本**: 添加JavaScript定位脚本到HTML
3. **加载地图**: WebEngineView加载HTML文件
4. **权限请求**: JavaScript调用`navigator.geolocation.getCurrentPosition()`
5. **权限授予**: WebEngine的`featurePermissionRequested`自动授予权限
6. **获取位置**: JavaScript获取位置信息
7. **发送信号**: 通过console.log输出"定位成功: lat, lon, accuracy"
8. **接收处理**: ConsoleWebEnginePage拦截日志并解析
9. **触发信号**: 通过Qt信号发送到主窗口
10. **更新界面**: 主窗口显示定位结果

## ⚠️ 常见问题排查

### 问题1: 长时间无法获取位置

**可能原因**:
1. Windows定位服务未启用
2. 网络连接问题
3. GPS/WiFi定位硬件不可用

**解决方法**:
1. 检查Windows设置 → 隐私 → 位置 → 确保"位置服务"已打开
2. 检查应用是否有位置访问权限
3. 尝试重启程序
4. 查看控制台输出的详细日志

### 问题2: 每次都使用IP地址定位

**原因**: 电脑定位服务失败后，程序会自动回退到IP地址定位

**检查步骤**:
1. 运行测试程序: `python tests/test_geolocation.py`
2. 查看控制台输出，确认是否有"[权限]"相关日志
3. 确认JavaScript是否成功调用定位API

### 问题3: 浏览器中可以定位，但程序中不行

**原因**:
- 浏览器有完整的定位API支持
- WebEngine可能需要额外的权限配置

**解决方法**:
1. 确保使用的PyQt5版本支持地理定位 (>= 5.12)
2. 检查是否正确实现了`featurePermissionRequested`方法
3. 查看控制台是否有权限请求日志

## 🧪 测试定位功能

### 方法1: 使用测试程序
```bash
python tests/test_geolocation.py
```

这将打开一个简化的测试窗口，专注于测试定位功能。

### 方法2: 使用主程序
```bash
python main.py
```

点击"📍 定位我的位置"按钮，观察：
1. 进度条开始转圈
2. 控制台输出日志
3. 30秒内是否获取到位置

### 查看详细日志

程序会在控制台输出详细的定位流程日志：
- `[定位] 开始定位...` - 定位流程开始
- `[权限] 地理定位权限请求` - 收到权限请求
- `[权限] 已授予地理定位权限` - 权限已授予
- `[Console] 定位成功: ...` - JavaScript成功获取位置
- `[定位] 成功获取位置` - Python成功解析位置

## 📝 代码改动文件

1. `utils/map_renderer.py` - 修复JavaScript定位脚本
2. `handlers/webengine.py` - 添加权限处理
3. `tests/test_geolocation.py` - 新增定位测试程序

## 💡 提示

如果定位仍然不工作：
1. 确保Windows定位服务已启用
2. 尝试在不同的网络环境下测试
3. 检查防火墙或安全软件是否阻止了定位请求
4. 使用测试程序查看详细的错误信息
5. 如果电脑定位始终失败，程序会自动使用IP定位作为备用方案
