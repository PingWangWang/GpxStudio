# 面板跟随窗口移动功能修复总结

## 问题描述
用户反馈：路线规划面板的位置应该跟随主窗口移动

## 问题分析
当前实现中，路线规划面板使用全局坐标定位（`mapToGlobal`），但是当主窗口移动时，面板位置不会自动更新，导致面板与主窗口分离。

## 修复方案
在主窗口类中添加窗口移动和大小变化事件监听，当窗口位置或大小发生变化时，自动更新相关面板的位置。

## 修复详情

### 1. 添加窗口事件监听
在 `src/app/app.py` 中添加了以下方法：

```python
def moveEvent(self, event):
    """窗口移动事件 - 更新路线规划面板位置"""
    super().moveEvent(event)
    self._update_route_panel_position()

def resizeEvent(self, event):
    """窗口大小变化事件 - 更新路线规划面板位置"""
    super().resizeEvent(event)
    self._update_route_panel_position()
```

### 2. 实现面板位置更新方法
添加了 `_update_route_panel_position` 方法：

```python
def _update_route_panel_position(self):
    """更新路线规划面板和相关弹出面板位置"""
    # 更新路线规划面板位置
    if (hasattr(self, 'route_plan_panel') and 
        hasattr(self, 'search_container') and 
        self.route_plan_panel.isVisible()):
        
        # 获取搜索容器的全局位置
        container_rect = self.search_container.rect()
        container_global_pos = self.search_container.mapToGlobal(container_rect.topLeft())
        
        # 更新路线规划面板的位置
        self.route_plan_panel.move(container_global_pos.x(), container_global_pos.y())
    
    # 更新GPX导出弹出面板位置
    if (hasattr(self, 'gpx_export_popup') and 
        hasattr(self, 'route_plan_panel') and 
        self.gpx_export_popup and 
        self.gpx_export_popup.isVisible() and 
        self.route_plan_panel.isVisible()):
        
        # 重新计算GPX导出弹出面板的位置（相对于路线面板）
        panel_global_pos = self.route_plan_panel.mapToGlobal(self.route_plan_panel.rect().topLeft())
        panel_rect = self.route_plan_panel.rect()
        
        # 在面板右侧显示，包含屏幕边界检查
        popup_x = panel_global_pos.x() + panel_rect.width() + 10
        popup_y = panel_global_pos.y() + 50
        
        # 屏幕边界检查
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        
        if popup_x + self.gpx_export_popup.width() > screen.right():
            popup_x = panel_global_pos.x() - self.gpx_export_popup.width() - 10
        
        if popup_y + 200 > screen.bottom():
            popup_y = screen.bottom() - 250
        
        self.gpx_export_popup.move(popup_x, popup_y)
```

## 功能特性

### ✅ 支持的面板类型
1. **路线规划面板** - 跟随搜索容器位置移动
2. **GPX导出弹出面板** - 跟随路线规划面板移动

### ✅ 支持的窗口操作
1. **窗口移动** - 拖拽标题栏移动窗口
2. **窗口大小调整** - 调整窗口大小
3. **程序化移动** - 通过代码移动窗口

### ✅ 智能特性
1. **条件检查** - 只有当面板可见时才更新位置
2. **屏幕边界检查** - 防止面板超出屏幕边界
3. **相对定位** - GPX面板相对于路线面板定位
4. **性能优化** - 只在必要时更新位置

## 验证结果

### ✅ 功能测试通过
- moveEvent方法添加正确
- resizeEvent方法添加正确
- _update_route_panel_position方法实现正确
- 方法逻辑正确
- 与现有代码集成正确

### ✅ 实际测试通过
- 创建了测试程序验证面板跟随效果
- 窗口移动时面板位置正确更新
- 窗口大小调整时面板位置正确更新
- GPX导出面板跟随路线规划面板移动

## 代码影响

### 修改文件
- `src/app/app.py` - 添加了窗口事件监听和面板位置更新逻辑

### 新增方法
- `moveEvent(self, event)` - 窗口移动事件处理
- `resizeEvent(self, event)` - 窗口大小变化事件处理
- `_update_route_panel_position(self)` - 面板位置更新逻辑

### 兼容性
- ✅ 完全向后兼容
- ✅ 不影响现有功能
- ✅ 不改变现有API

## 使用效果

### 修复前
- 路线规划面板位置固定
- 主窗口移动后面板与窗口分离
- GPX导出面板位置不跟随更新

### 修复后
- 路线规划面板跟随主窗口移动
- GPX导出面板跟随路线规划面板移动
- 面板始终保持与主窗口的相对位置
- 智能屏幕边界检查，防止面板超出屏幕

## 结论

面板跟随窗口移动功能已成功实现，用户现在可以自由移动主窗口，所有相关面板都会自动跟随移动，提供了更好的用户体验。