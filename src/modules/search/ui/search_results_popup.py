"""
搜索结果下拉列表组件

该组件在点击搜索按钮后显示，展示搜索返回的多个地址结果
"""

from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon
import os


class SearchResultsPopup(QListWidget):
    """搜索结果下拉列表"""

    # 信号：用户选择了搜索结果
    result_selected = pyqtSignal(dict)  # 传递完整的搜索结果字典
    favorite_requested = pyqtSignal(dict)  # 用户点击收藏按钮，传递完整的搜索结果字典

    def __init__(self, parent=None):
        """初始化搜索结果下拉列表"""
        super().__init__(parent)

        # 设置样式
        self.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid rgba(0, 0, 0, 0.15);
                border-radius: 4px;
                outline: none;
            }
            QListWidget::item {
                padding: 10px 12px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
            QListWidget::item:selected {
                background-color: #e8f4fd;
                color: #333333;
            }
        """)

        # 设置属性
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating)  # 显示时不激活窗口
        self.setFocusPolicy(Qt.StrongFocus)  # 改为StrongFocus以接收键盘事件
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 连接信号
        self.itemClicked.connect(self._on_item_clicked)

        # 加载搜索图标
        self._load_search_icon()

    def _load_search_icon(self):
        """设置搜索图标为emoji"""
        # 使用emoji作为搜索图标
        self.search_icon = None

    def show_results(self, results_list: list, search_container_widget):
        """
        显示搜索结果

        Args:
            results_list: 搜索结果列表
            search_container_widget: 搜索容器控件（用于定位和宽度）
        """
        # 清空现有项
        self.clear()

        if not results_list:
            # 没有搜索结果，不显示
            self.hide()
            return

        # 添加搜索结果项
        for result in results_list:
            self._add_result_item(result)

        # 计算位置和大小
        container_rect = search_container_widget.rect()
        container_pos = search_container_widget.mapToGlobal(container_rect.bottomLeft())

        # 设置宽度与搜索容器一致
        self.setFixedWidth(search_container_widget.width())

        # 计算高度（最多显示10项，每项约55px）
        item_height = 55
        max_height = min(len(results_list) * item_height, 550)
        self.setMaximumHeight(max_height)

        # 移动到搜索容器下方（增加间距，避免遮挡按钮）
        self.move(container_pos.x(), container_pos.y() + 4)

        # 显示
        self.show()
        # 不要调用 raise_()，让按钮保持在上层

    def _add_result_item(self, result: dict):
        """
        添加搜索结果项（名称/地址 + 收藏按钮）

        Args:
            result: 搜索结果字典
        """
        name = result.get('name', '')
        address = result.get('address', '')

        # 创建列表项
        item = QListWidgetItem()
        item.setSizeHint(QSize(0, 55))  # 设置项高度

        # 保存完整的结果数据
        item.setData(Qt.UserRole, result)

        # 创建行控件：左侧名称/地址，右侧收藏按钮
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(12, 6, 8, 6)
        row_layout.setSpacing(8)

        # 左侧文本区域
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        name_label = QLabel(f"🔍 {name}")
        name_label.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 13px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)
        # 让文本穿透鼠标事件，点击行仍触发 itemClicked
        name_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        text_layout.addWidget(name_label)

        if address and address != name:
            address_label = QLabel(address)
            address_label.setStyleSheet("""
                QLabel {
                    color: #888888;
                    font-size: 12px;
                    font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                }
            """)
            address_label.setAttribute(Qt.WA_TransparentForMouseEvents)
            text_layout.addWidget(address_label)

        row_layout.addWidget(text_container, 1)

        # 右侧收藏按钮（点击收藏，不关闭下拉列表）
        favorite_button = QPushButton("☆")
        favorite_button.setToolTip("收藏此地点")
        favorite_button.setFixedSize(28, 28)
        favorite_button.setCursor(Qt.PointingHandCursor)
        favorite_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 18px;
                color: #888888;
                padding: 0;
            }
            QPushButton:hover {
                color: #FFD700;
                font-size: 20px;
            }
        """)
        favorite_button.clicked.connect(lambda checked=False, r=result: self.favorite_requested.emit(r))
        row_layout.addWidget(favorite_button, 0, Qt.AlignTop)

        # 将行控件设置为列表项
        self.addItem(item)
        self.setItemWidget(item, row_widget)

    def _on_item_clicked(self, item: QListWidgetItem):
        """处理项点击事件"""
        result = item.data(Qt.UserRole)
        if result:
            # 发送信号
            self.result_selected.emit(result)

        # 隐藏下拉列表
        self.hide()

    def keyPressEvent(self, event):
        """处理键盘事件"""
        if event.key() == Qt.Key_Escape:
            self.hide()
            event.accept()
        else:
            super().keyPressEvent(event)

    def hideEvent(self, event):
        """重写隐藏事件"""
        super().hideEvent(event)
        # 清空选择
        self.clearSelection()
