"""
搜索结果下拉列表组件

该组件在点击搜索按钮后显示，展示搜索返回的多个地址结果
"""

from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon
import os


class SearchResultsPopup(QListWidget):
    """搜索结果下拉列表"""

    # 信号：用户选择了搜索结果
    result_selected = pyqtSignal(dict)  # 传递完整的搜索结果字典

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
        self.setFocusPolicy(Qt.NoFocus)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 连接信号
        self.itemClicked.connect(self._on_item_clicked)

        # 加载搜索图标
        self._load_search_icon()

    def _load_search_icon(self):
        """加载搜索图标"""
        from core.resource_path import resource_path
        icon_path = resource_path('res/Search.png')

        if os.path.exists(icon_path):
            self.search_icon = QIcon(icon_path)
        else:
            self.search_icon = None
            print(f"[搜索结果] 未找到搜索图标: {icon_path}")

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
        添加搜索结果项

        Args:
            result: 搜索结果字典
        """
        name = result.get('name', '')
        address = result.get('address', '')

        # 创建列表项
        item = QListWidgetItem()

        # 设置图标
        if self.search_icon:
            item.setIcon(self.search_icon)
            item.setSizeHint(QSize(0, 55))  # 设置项高度
        else:
            item.setSizeHint(QSize(0, 55))

        # 设置文本（第一行：名称，第二行：地址）
        display_parts = [name]
        if address and address != name:
            display_parts.append(address)

        display_text = '\n'.join(display_parts)
        item.setText(display_text)

        # 保存完整的结果数据
        item.setData(Qt.UserRole, result)

        # 添加到列表
        self.addItem(item)

    def _on_item_clicked(self, item: QListWidgetItem):
        """处理项点击事件"""
        result = item.data(Qt.UserRole)
        if result:
            # 发送信号
            self.result_selected.emit(result)

        # 隐藏下拉列表
        self.hide()

    def hideEvent(self, event):
        """重写隐藏事件"""
        super().hideEvent(event)
        # 清空选择
        self.clearSelection()
