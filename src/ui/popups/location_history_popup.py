"""
地点搜索历史弹出列表

当用户点击路线规划面板的输入框时，显示最近搜索过的地点
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QListWidget, QListWidgetItem, QPushButton, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QCursor
from ui.theme import theme
from typing import List, Dict


class LocationHistoryItem(QWidget):
    """地点历史记录列表项"""
    
    clicked = pyqtSignal(dict)  # 点击事件，携带地点数据
    
    def __init__(self, location_data: dict, parent=None):
        super().__init__(parent)
        self.location_data = location_data
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)
        
        # 地点名称
        name = self.location_data.get('name', '')
        name_label = QLabel(name)
        theme.apply_to_sub(name_label, """
            QLabel {
                color: __TEXT__;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        layout.addWidget(name_label)
        
        # 地址信息
        address = self.location_data.get('address', '')
        if address:
            address_label = QLabel(address)
            theme.apply_to_sub(address_label, """
                QLabel {
                    color: __TEXT_SECONDARY__;
                    font-size: 12px;
                }
            """)
            address_label.setWordWrap(True)
            layout.addWidget(address_label)
        
        # 设置样式
        theme.set_theme_stylesheet(self, """
            LocationHistoryItem {
                background-color: __PANEL_BG__;
                border-radius: 4px;
            }
            LocationHistoryItem:hover {
                background-color: __HOVER__;
            }
        """)
        
        # 设置鼠标形状
        self.setCursor(QCursor(Qt.PointingHandCursor))
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.location_data)
        super().mousePressEvent(event)


class LocationHistoryPopup(QWidget):
    """地点搜索历史弹出列表"""

    # 头部固定高度（标题行 + 边距），高度公式计入总高
    HEADER_HEIGHT = 45

    # 信号
    location_selected = pyqtSignal(dict)  # 地点被选中：(地点数据)
    my_location_clicked = pyqtSignal()  # 点击固定"我的位置"首行（定位当前位置并填入输入框）
    
    def __init__(self, parent=None, map_manager=None):
        super().__init__(parent)
        self._map_manager = map_manager

        # 设置窗口标志 - 使用Tool而非Popup，避免捕获所有键盘事件导致输入框无法使用
        # Qt.Popup会捕获所有事件，导致输入框的退格键、回车键等按键无法工作
        # 不加 WindowStaysOnTopHint：置顶会使弹窗在切换其他软件时仍浮于最上层，
        # Tool 子窗口层级随主窗口，切后台时自然下沉
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # 历史记录列表（面板每次弹出时填充）
        self.history_items = []

        # 当前显示的列表项（用于 show_at 时计算高度）
        self._current_items = []

        # 锚点输入框（_reposition 重定位/重算高度用）
        self._anchor_widget = None

        # 当前 tab：history / favorites（保留上次选择，切换后再次弹出不重置）
        self._current_tab = 'history'

        # 初始化UI
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        # 设置样式
        theme.set_theme_stylesheet(self, """
            LocationHistoryPopup {
                background-color: __PANEL_BG__;
                border: 1px solid __BORDER__;
                border-radius: 6px;
            }
            QLabel {
                color: __TEXT__;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: __ACCENT__;
                font-size: 12px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: rgba(24, 144, 255, 0.1);
                border-radius: 3px;
            }
            QPushButton:pressed {
                background-color: rgba(24, 144, 255, 0.2);
            }
            QListWidget {
                background-color: __PANEL_BG__;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background-color: __PANEL_BG__;
                border: none;
                padding: 0px;
                margin: 2px 0px;
            }
            QListWidget::item:hover {
                background-color: __HOVER__;
            }
            QListWidget::item:selected {
                background-color: #e6f7ff;
                border: 1px solid #91d5ff;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # 头部：最近搜索/收藏夹 tab 切换 + 清空按钮
        header_layout = QHBoxLayout()
        header_layout.setSpacing(4)

        # Tab 按钮样式：选中蓝色加粗 + 下划线，未选中灰色
        tab_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                color: __TEXT_TERTIARY__;
                font-size: 13px;
                padding: 2px 6px;
            }
            QPushButton:hover {
                color: __TEXT_SECONDARY__;
            }
            QPushButton:checked {
                color: __ACCENT__;
                font-weight: bold;
                border-bottom: 2px solid __ACCENT__;
            }
        """

        self.history_tab_btn = QPushButton("🕒 最近搜索")
        self.history_tab_btn.setCheckable(True)
        self.history_tab_btn.setChecked(True)
        theme.apply_to_sub(self.history_tab_btn, tab_style)
        self.history_tab_btn.clicked.connect(lambda: self._switch_tab('history'))
        header_layout.addWidget(self.history_tab_btn)

        self.favorites_tab_btn = QPushButton("⭐ 收藏夹")
        self.favorites_tab_btn.setCheckable(True)
        theme.apply_to_sub(self.favorites_tab_btn, tab_style)
        self.favorites_tab_btn.clicked.connect(lambda: self._switch_tab('favorites'))
        header_layout.addWidget(self.favorites_tab_btn)

        header_layout.addStretch()

        layout.addLayout(header_layout)
        
        # 历史记录列表
        self.history_list = QListWidget()
        self.history_list.setSelectionMode(QListWidget.SingleSelection)
        self.history_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.history_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.history_list.setSpacing(0)
        self.history_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.history_list)
        
        # 空状态提示
        self.empty_label = QLabel("暂无搜索历史")
        self.empty_label.setAlignment(Qt.AlignCenter)
        theme.apply_to_sub(self.empty_label, """
            QLabel {
                color: __TEXT_TERTIARY__;
                font-size: 13px;
                padding: 20px;
            }
        """)
        self.empty_label.setVisible(False)
        layout.addWidget(self.empty_label)
    
    def _get_map_manager(self):
        """获取 MapManager（构造注入优先，否则经父窗口链实时获取）

        弹窗 parent 为 RoutePlanPanel，其 parent 为主窗口（持有 map_manager）。
        """
        if self._map_manager is not None:
            return self._map_manager
        parent = self.parent()
        if parent is not None:
            return getattr(getattr(parent, 'parent', lambda: None)(), 'map_manager', None)
        return None

    def _get_favorites_items(self) -> List[Dict]:
        """从收藏存储构造列表项（与历史记录字段格式兼容）"""
        map_manager = self._get_map_manager()
        if map_manager is None:
            return []
        items = []
        for fav in map_manager.favorites_storage.get_all():
            items.append({
                'name': fav.get('name', '收藏点'),
                'address': fav.get('address', ''),
                'lat': fav.get('lat', 0),
                'lon': fav.get('lon', 0),
                'coord_system': fav.get('coord_system', 'WGS-84'),
                'data_source': 'favorite',
            })
        return items

    def _switch_tab(self, mode: str):
        """切换最近搜索/收藏夹 tab

        Args:
            mode: 'history' 或 'favorites'
        """
        self._current_tab = mode
        is_history = (mode == 'history')
        self.history_tab_btn.setChecked(is_history)
        self.favorites_tab_btn.setChecked(not is_history)

        if is_history:
            self._update_list(self.history_items, '暂无搜索历史')
        else:
            self._update_list(self._get_favorites_items(), '暂无收藏地点')

    def set_history_items(self, items: List[Dict]):
        """设置历史记录列表

        Args:
            items: 历史记录列表，每项包含 name, address, lat, lon 等字段
        """
        self.history_items = items
        # 仅当当前为最近搜索 tab 时刷新列表（收藏夹 tab 保留其显示）
        if self._current_tab == 'history':
            self._update_list(items, '暂无搜索历史')

    def _update_list(self, items: List[Dict], empty_text: str = '暂无搜索历史'):
        """更新列表显示

        Args:
            items: 列表项数据
            empty_text: 空状态提示文案
        """
        self._current_items = items
        self.history_list.clear()

        # 第一行固定"我的位置"（点击定位当前位置并填入输入框）
        my_item = QListWidgetItem()
        my_item.setData(Qt.UserRole, '__MY_LOCATION__')
        my_item.setSizeHint(QSize(0, 40))

        # 使用行控件与历史条目相同的边距/字体，保证文本左对齐
        my_widget = QWidget()
        my_layout = QHBoxLayout(my_widget)
        my_layout.setContentsMargins(12, 8, 12, 8)
        my_label = QLabel("📍 我的位置")
        theme.apply_to_sub(my_label, """
            QLabel {
                color: __TEXT__;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        my_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        my_layout.addWidget(my_label)
        my_layout.addStretch()

        self.history_list.addItem(my_item)
        self.history_list.setItemWidget(my_item, my_widget)

        if not items:
            # 无历史记录时仍显示"我的位置"首行（列表保持可见，不显示空提示）
            self.history_list.setVisible(True)
            self.empty_label.setVisible(False)
            return

        self.history_list.setVisible(True)
        self.empty_label.setVisible(False)

        for item_data in items:
            # 创建列表项
            list_item = QListWidgetItem()
            list_item.setData(Qt.UserRole, item_data)
            
            # 创建自定义 Widget
            item_widget = LocationHistoryItem(item_data)
            item_widget.clicked.connect(self._on_location_clicked)
            
            # 计算高度（基于内容）
            name = item_data.get('name', '')
            address = item_data.get('address', '')
            height = 50 if address else 40
            list_item.setSizeHint(QSize(0, height))
            
            # 添加到列表
            self.history_list.addItem(list_item)
            self.history_list.setItemWidget(list_item, item_widget)
    
    def _on_item_clicked(self, item: QListWidgetItem):
        """列表项被点击"""
        location_data = item.data(Qt.UserRole)
        if location_data == '__MY_LOCATION__':
            # 点击"我的位置"：定位当前位置并填入输入框（由面板处理）
            self.my_location_clicked.emit()
            self.hide()
        elif location_data:
            self.location_selected.emit(location_data)
            self.hide()
    
    def _on_location_clicked(self, location_data: dict):
        """地点被点击"""
        self.location_selected.emit(location_data)
        self.hide()
    
    def show_at(self, widget: QWidget):
        """在指定widget下方显示

        Args:
            widget: 目标输入框
        """
        self._anchor_widget = widget
        self._reposition()

    def _reposition(self):
        """按锚点输入框重算位置与尺寸（主窗口移动/缩放时联动调用）

        高度逻辑与搜索/收藏列表同构：条目少时随条目数动态变化，
        最大高度受主窗口底部边界约束（弹窗底不超主窗口底），超限滚动条生效。
        """
        if self._anchor_widget is None:
            return

        # 位置：输入框下方
        global_pos = self._anchor_widget.mapToGlobal(self._anchor_widget.rect().bottomLeft())

        # 宽度与输入框相同
        self.setFixedWidth(self._anchor_widget.width())

        # 高度：头部固定部分 + 列表条目自然高（逐条目 sizeHint 求和，含"我的位置"首行）
        list_natural = sum(
            self.history_list.item(i).sizeHint().height()
            for i in range(self.history_list.count()))
        target_height = self.HEADER_HEIGHT + list_natural

        # 边界约束：主窗口底边 - 弹窗顶 - 4px（弹窗 parent 为路线面板，其 parent 为主窗口）
        max_height = None
        main_window = self.parent().parent() if self.parent() is not None else None
        if main_window is not None:
            top_y = global_pos.y()
            max_height = main_window.frameGeometry().bottom() - top_y - 4
            if max_height is not None:
                target_height = min(target_height, max_height)

        if max_height is not None:
            self.setMaximumHeight(max_height)
        self.resize(self.width(), max(target_height, self.HEADER_HEIGHT))

        # 显示在输入框下方
        self.move(global_pos)
        self.show()
        self.raise_()
    
    def keyPressEvent(self, event):
        """处理键盘事件"""
        # 按ESC键关闭弹出窗口
        if event.key() == Qt.Key_Escape:
            self.hide()
            event.accept()
        else:
            # 其他按键不处理，让事件继续传递
            event.ignore()
    
    def hideEvent(self, event):
        """窗口隐藏事件"""
        super().hideEvent(event)
        # 清除选择状态
        if hasattr(self, 'history_list'):
            self.history_list.clearSelection()
