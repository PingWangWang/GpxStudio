"""
搜索历史下拉列表组件

该组件在搜索框获得焦点时显示，展示最近的搜索历史记录
"""

from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon
import os


class SearchHistoryPopup(QListWidget):
    """搜索历史下拉列表"""

    # 信号：用户选择了历史记录
    history_selected = pyqtSignal(dict)  # 传递完整的历史记录字典

    def __init__(self, parent=None):
        """初始化搜索历史下拉列表"""
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
                padding: 8px 12px;
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
        self.setFocusPolicy(Qt.NoFocus)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 连接信号
        self.itemClicked.connect(self._on_item_clicked)

        # 加载历史图标
        self._load_history_icon()

    def _load_history_icon(self):
        """加载历史图标"""
        from core.resource_path import resource_path
        icon_path = resource_path('res/History.png')

        if os.path.exists(icon_path):
            self.history_icon = QIcon(icon_path)
        else:
            self.history_icon = None
            print(f"[搜索历史] 未找到历史图标: {icon_path}")

    def show_history(self, history_list: list, search_container_widget):
        """
        显示搜索历史

        Args:
            history_list: 历史记录列表
            search_container_widget: 搜索容器控件（用于定位和宽度）
        """
        # 清空现有项
        self.clear()

        if not history_list:
            # 没有历史记录，不显示
            self.hide()
            return

        # 添加历史记录项
        for record in history_list:
            self._add_history_item(record)

        # 计算位置和大小
        container_rect = search_container_widget.rect()
        container_pos = search_container_widget.mapToGlobal(container_rect.bottomLeft())

        # 设置宽度与搜索容器一致
        self.setFixedWidth(search_container_widget.width())

        # 计算高度（最多显示10项，每项约40px）
        item_height = 40
        max_height = min(len(history_list) * item_height, 400)
        self.setMaximumHeight(max_height)

        # 移动到搜索容器下方（增加间距）
        self.move(container_pos.x(), container_pos.y() + 4)

        # 显示
        self.show()
        # 不要调用 raise_()，让按钮保持在上层

    def _add_history_item(self, record: dict):
        """
        添加历史记录项

        Args:
            record: 历史记录字典
        """
        name = record.get('name', '')
        address = record.get('address', '')

        # 创建列表项
        item = QListWidgetItem()

        # 设置图标
        if self.history_icon:
            item.setIcon(self.history_icon)
            item.setSizeHint(QSize(0, 40))  # 设置项高度

        # 设置文本（只显示名称）
        display_text = name
        if address and address != name:
            display_text = f"{name} - {address}"

        item.setText(display_text)

        # 保存完整的记录数据
        item.setData(Qt.UserRole, record)

        # 添加到列表
        self.addItem(item)

    def _on_item_clicked(self, item: QListWidgetItem):
        """处理项点击事件"""
        record = item.data(Qt.UserRole)
        if record:
            # 发送信号
            self.history_selected.emit(record)

        # 隐藏下拉列表
        self.hide()

    def hideEvent(self, event):
        """重写隐藏事件"""
        super().hideEvent(event)
        # 清空选择
        self.clearSelection()
