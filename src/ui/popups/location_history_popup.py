"""
地点搜索历史弹出列表

当用户点击路线规划面板的输入框时，显示最近搜索过的地点
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QListWidget, QListWidgetItem, QPushButton, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QCursor
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
        name_label.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        layout.addWidget(name_label)
        
        # 地址信息
        address = self.location_data.get('address', '')
        if address:
            address_label = QLabel(address)
            address_label.setStyleSheet("""
                QLabel {
                    color: #666666;
                    font-size: 12px;
                }
            """)
            address_label.setWordWrap(True)
            layout.addWidget(address_label)
        
        # 设置样式
        self.setStyleSheet("""
            LocationHistoryItem {
                background-color: white;
                border-radius: 4px;
            }
            LocationHistoryItem:hover {
                background-color: #f0f0f0;
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
    
    # 信号
    location_selected = pyqtSignal(dict)  # 地点被选中：(地点数据)
    clear_history_clicked = pyqtSignal()  # 清空历史按钮点击
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置窗口标志 - 弹出窗口，无边框
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        # 历史记录列表
        self.history_items = []
        
        # 初始化UI
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        # 设置样式
        self.setStyleSheet("""
            LocationHistoryPopup {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 6px;
            }
            QLabel {
                color: #333333;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: #1890ff;
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
                background-color: white;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background-color: white;
                border: none;
                padding: 0px;
                margin: 2px 0px;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
            QListWidget::item:selected {
                background-color: #e6f7ff;
                border: 1px solid #91d5ff;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # 头部：标题和清空按钮
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        title_label = QLabel("🕒 最近搜索")
        title_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 清空历史按钮
        clear_button = QPushButton("清空")
        clear_button.clicked.connect(self.clear_history_clicked.emit)
        header_layout.addWidget(clear_button)
        
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
        self.empty_label.setStyleSheet("""
            QLabel {
                color: #999999;
                font-size: 13px;
                padding: 20px;
            }
        """)
        self.empty_label.setVisible(False)
        layout.addWidget(self.empty_label)
    
    def set_history_items(self, items: List[Dict]):
        """设置历史记录列表
        
        Args:
            items: 历史记录列表，每项包含 name, address, lat, lon 等字段
        """
        self.history_items = items
        self._update_list()
    
    def _update_list(self):
        """更新列表显示"""
        self.history_list.clear()
        
        if not self.history_items:
            self.history_list.setVisible(False)
            self.empty_label.setVisible(True)
            return
        
        self.history_list.setVisible(True)
        self.empty_label.setVisible(False)
        
        for item_data in self.history_items:
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
        if location_data:
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
        # 计算位置：在输入框下方
        global_pos = widget.mapToGlobal(widget.rect().bottomLeft())
        
        # 设置固定宽度（与输入框宽度相同）
        width = widget.width()
        
        # 设置最大高度（不超过5个项目的高度）
        max_height = min(250, len(self.history_items) * 50 + 60)
        
        self.setFixedWidth(width)
        self.setMaximumHeight(max_height)
        
        # 显示在输入框下方
        self.move(global_pos)
        self.show()
        self.raise_()
