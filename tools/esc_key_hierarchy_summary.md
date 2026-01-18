# ESC键层级关闭功能实现总结

## 功能概述

实现了完整的4层级ESC键关闭功能，支持两个主要场景：

1. **历史记录场景**：路线规划面板 → 路线历史记录列表 → GPX设置面板 → 时间日期设置面板
2. **路线规划场景**：路线规划面板 → 路线规划列表 → GPX设置面板 → 时间日期设置面板

## 层级结构

```
第4层：时间日期设置面板（最上层）
  ↓ ESC键关闭，焦点返回第3层
第3层：GPX设置面板
  ↓ ESC键关闭，焦点返回第1层
第2层：路线历史记录列表 或 路线规划列表（内嵌在第1层中）
  ↓ 
第1层：路线规划面板（底层）
  ↓ ESC键关闭，完全退出
```

## 核心实现文件

### 1. 路线规划面板 (`src/modules/routing/ui/route_plan_panel.py`)

**关键方法：`keyPressEvent`**
```python
def keyPressEvent(self, event: QKeyEvent):
    """处理键盘事件"""
    if event.key() == Qt.Key_Escape:
        # 检查是否有GPX设置面板正在显示
        if parent_app.gpx_export_popup and parent_app.gpx_export_popup.isVisible():
            # 检查GPX面板是否有子弹出窗口（时间日期设置面板）
            if gpx_popup.datetime_edit.picker_popup and gpx_popup.datetime_edit.picker_popup.isVisible():
                # 如果有子弹出窗口，不处理ESC键，让子窗口处理
                return
            else:
                # 如果GPX面板显示但没有子窗口，不处理ESC键，让GPX面板处理
                return
        
        # 如果没有任何子弹出窗口显示，则关闭路线规划面板
        self.cancel_clicked.emit()
```

**特性：**
- ✅ 使用 `Qt.Popup` 窗口标志以接收键盘焦点
- ✅ 设置 `Qt.StrongFocus` 焦点策略
- ✅ 智能检查子面板状态，避免冲突
- ✅ 正确的焦点管理

### 2. GPX导出弹出面板 (`src/ui/popups/gpx_export_popup.py`)

**关键方法：`keyPressEvent`**
```python
def keyPressEvent(self, event):
    if event.key() == Qt.Key_Escape:
        # 检查是否有日期时间选择器弹出窗口正在显示
        if self.datetime_edit.picker_popup and self.datetime_edit.picker_popup.isVisible():
            # 如果日期时间选择器正在显示，优先关闭它
            self.datetime_edit.picker_popup.hide()
            self.setFocus()  # 重新设置焦点到GPX导出面板
            return
        
        # 如果没有子弹出窗口，则关闭GPX导出面板
        self.hide()
        self.closed.emit()
        
        # 将焦点返回给路线规划面板
        if parent_app.route_plan_panel and parent_app.route_plan_panel.isVisible():
            parent_app.route_plan_panel.setFocus()
```

**特性：**
- ✅ 优先处理子面板（时间日期设置）
- ✅ 正确的焦点返回机制
- ✅ 不会在子面板显示时自动关闭

### 3. 自定义日期时间编辑控件 (`src/ui/widgets/custom_datetime_edit.py`)

**关键方法：`_show_picker`**
```python
def _show_picker(self):
    # 重写键盘事件处理
    def keyPressEvent(event):
        if event.key() == Qt.Key_Escape:
            self.picker_popup.hide()
            # 将焦点返回给父级GPX导出面板
            parent_popup = self.parent()
            while parent_popup:
                if parent_popup.__class__.__name__ == 'GpxExportPopup':
                    parent_popup.setFocus()
                    break
                parent_popup = parent_popup.parent()
    
    self.picker_popup.keyPressEvent = keyPressEvent
    
    # 显示并设置焦点
    self.picker_popup.show()
    self.picker_popup.raise_()
    self.picker_popup.activateWindow()  # 激活窗口以确保获得焦点
    self.picker_popup.setFocus()
```

**特性：**
- ✅ 自动获得焦点
- ✅ ESC键关闭后焦点返回父级
- ✅ 使用 `activateWindow()` 确保焦点获取

### 4. 自定义日期时间选择器 (`src/ui/widgets/custom_datetime_picker.py`)

**关键特性：**
- ✅ 双击确认选择（日历和时间列表）
- ✅ 单击仅显示视觉反馈，不确认选择
- ✅ 30分钟间隔的时间列表
- ✅ ESC键支持

## 历史记录导出按钮逻辑

### 路线历史记录项 (`RouteHistoryItem`)

**状态管理逻辑：**
```python
def _update_export_button_state(self):
    # 只有当记录被选中且有路线数据时才启用导出按钮
    should_enable = self.is_selected and self.has_route_data
    self.export_button.setEnabled(should_enable)
    
    # 更新图标
    if self.export_button.isEnabled():
        # 启用状态：使用白色图标
        icon_path = resource_path('res/Downloading_white.png')
    else:
        # 禁用状态：使用灰色图标
        icon_path = resource_path('res/Downloading_gray.png')
```

**初始化逻辑：**
```python
def load_history(self, history_list: list):
    for record in history_list:
        history_widget = RouteHistoryItem(record)
        
        # 确保初始状态：未选中，无路线数据（导出按钮禁用）
        history_widget.set_selected(False)
        history_widget.set_route_data_available(False)
```

**特性：**
- ✅ 初始状态：所有按钮禁用（灰色图标）
- ✅ 选中记录且有路线数据：按钮启用（白色图标）
- ✅ 其他情况：按钮禁用（灰色图标）
- ✅ 智能状态管理

## 焦点管理机制

### 焦点传递顺序

1. **显示路线规划面板**
   ```python
   self.route_plan_panel.show()
   self.route_plan_panel.setFocus()
   ```

2. **显示GPX设置面板**
   ```python
   self.gpx_export_popup.show_at_position(pos)
   # 内部调用：
   self.show()
   self.raise_()
   self.activateWindow()
   self.setFocus()
   ```

3. **显示时间日期设置面板**
   ```python
   self.picker_popup.show()
   self.picker_popup.raise_()
   self.picker_popup.activateWindow()
   self.picker_popup.setFocus()
   ```

### 焦点返回机制

- **时间日期设置面板关闭** → 焦点返回GPX设置面板
- **GPX设置面板关闭** → 焦点返回路线规划面板
- **路线规划面板关闭** → 完全退出

## ESC键处理流程

```
用户按下ESC键
    ↓
检查时间日期设置面板是否显示
    ↓ 是
关闭时间日期设置面板，焦点返回GPX面板
    ↓ 否
检查GPX设置面板是否显示
    ↓ 是
关闭GPX设置面板，焦点返回路线规划面板
    ↓ 否
关闭路线规划面板，完全退出
```

## 重要特性

### 1. 防止意外关闭
- ✅ 在GPX设置面板点击弹出时间日期设置面板时，已经弹出的面板不会自动关闭
- ✅ 只有通过ESC键或按钮才能关闭面板

### 2. 智能层级检测
- ✅ 每个面板都会检查是否有子面板正在显示
- ✅ 如果有子面板，ESC键会传递给子面板处理
- ✅ 避免了ESC键冲突和意外关闭

### 3. 完整的焦点管理
- ✅ 每个面板显示时自动获得焦点
- ✅ 面板关闭时焦点正确返回父级
- ✅ 使用 `activateWindow()` 确保焦点获取成功

### 4. 用户体验优化
- ✅ 双击确认选择，单击仅显示反馈
- ✅ 按钮状态智能管理（灰色/白色图标）
- ✅ 层级关闭顺序符合用户直觉

## 测试验证

### 自动化测试
- ✅ 逻辑测试：`tools/verify_esc_functionality.py`
- ✅ GUI测试：`tools/test_complete_hierarchical_esc.py`

### 测试场景覆盖
- ✅ 历史记录场景的4层级ESC关闭
- ✅ 路线规划场景的4层级ESC关闭
- ✅ 焦点管理正确性
- ✅ 按钮状态逻辑正确性
- ✅ 防止意外关闭

## 总结

完整实现了用户要求的所有功能：

1. ✅ **点击GPX导出设置面板的日期时间设置按钮，弹出设置界面时，自动将焦点设置到该界面**
2. ✅ **用户按下ESC键时，优先关闭日期时间设置界面；再次按下ESC时，关闭GPX导出设置界面，以此类推**
3. ✅ **路线规划面板刚打开时，路线搜索历史记录条目中，所有的GPX导出按钮应该都禁用，置灰**
4. ✅ **用户点击某一条记录后，才将该条设置为白色，需判断该条记录的路线数据是否存在**
5. ✅ **路线规划面板支持ESC按键关闭**
6. ✅ **完整的4层级ESC键依次关闭功能**
7. ✅ **在GPX设置面板点击弹出时间日期设置面板时，已经弹出的面板不能自动关闭**

所有功能都经过了充分的测试验证，确保用户体验流畅、直观。