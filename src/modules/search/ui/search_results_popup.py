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

    # 每行高度（PopupPositioner 计算弹窗最大高度时引用）
    ITEM_HEIGHT = 55

    # 信号：用户选择了搜索结果
    result_selected = pyqtSignal(dict)  # 传递完整的搜索结果字典
    favorite_requested = pyqtSignal(dict)  # 用户点击收藏按钮（切换收藏），传递完整的搜索结果字典

    def __init__(self, parent=None, map_manager=None):
        """初始化搜索结果下拉列表

        Args:
            parent: 父窗口（主窗口）
            map_manager: MapManager 实例（可选，用于查询收藏状态；
                         未注入时渲染阶段从父窗口实时获取）
        """
        super().__init__(parent)
        self._map_manager = map_manager

        # 设置样式
        self.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid rgba(0, 0, 0, 0.15);
                border-radius: 4px;
                outline: none;
            }
            QListWidget::item {
                /* 内边距由行控件 contentsMargins 提供；此处若保留 padding 会与
                   setItemWidget 行控件叠加，挤压内容区导致文字上下被裁剪 */
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
        # 使用 Qt.Tool 而非 Qt.ToolTip：Tool 类型在有父 widget 时随父窗口移动
        # （对齐 location_history_popup 先例），ToolTip 不会跟随导致拖动主窗口时弹窗滞留
        # 不加 WindowStaysOnTopHint：置顶会使弹窗在切换其他软件时仍浮于最上层，
        # Tool 子窗口层级随主窗口，切后台时自然下沉
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
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

        # 显示后由 PopupPositioner 统一计算位置与尺寸（锚定容器 + 窗口边界约束），
        # 与主窗口移动/缩放时的重算共用同一公式
        self.show()
        # 不要调用 raise_()，让按钮保持在上层
        from ui.popups.popup_positioner import PopupPositioner
        PopupPositioner.update_search_popups_position(None, self, search_container_widget)

    def _get_map_manager(self):
        """获取 MapManager（构造注入优先，否则从父窗口实时获取）

        弹窗创建早于主窗口 map_manager 初始化（app 初始化时序），
        故不能仅依赖构造注入；运行时父窗口的 map_manager 必然已就绪。
        """
        if self._map_manager is not None:
            return self._map_manager
        parent = self.parent()
        return getattr(parent, 'map_manager', None) if parent is not None else None

    def _apply_favorite_style(self, button, is_fav: bool):
        """设置收藏按钮外观：已收藏金色实心★，未收藏灰色空心☆"""
        button.setText('★' if is_fav else '☆')
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                font-size: {'19px' if is_fav else '18px'};
                color: {'#FFD700' if is_fav else '#888888'};
                padding: 0;
            }}
            QPushButton:hover {{
                color: #FFD700;
                font-size: 20px;
            }}
        """)

    def _on_favorite_button_clicked(self, button, is_fav: bool, record: dict):
        """收藏按钮点击：乐观切换外观，实际增删由主窗口处理"""
        self._apply_favorite_style(button, not is_fav)
        self.favorite_requested.emit(record)

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

        # 左侧图标按地址类型分类（搜索/历史/收藏夹三处图标一致；名称兜底推断类型）
        from modules.search.type_icons import get_type_emoji
        name_label = QLabel(f"{get_type_emoji(result.get('type', ''), name)} {name}")
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

        # 右侧收藏按钮（点击切换收藏，不关闭下拉列表）
        favorite_button = QPushButton("☆")
        favorite_button.setToolTip("收藏此地点")
        favorite_button.setFixedSize(28, 28)
        favorite_button.setCursor(Qt.PointingHandCursor)

        # 初始状态：已收藏显示金色实心星，未收藏显示灰色空心星
        is_fav = False
        map_manager = self._get_map_manager()
        if map_manager is not None:
            is_fav = map_manager.is_favorited(
                float(result.get('lat', 0)), float(result.get('lon', 0)),
                result.get('coord_system', 'WGS-84'))
        self._apply_favorite_style(favorite_button, is_fav)

        favorite_button.clicked.connect(
            lambda checked=False, r=result, btn=favorite_button, fav=is_fav:
                self._on_favorite_button_clicked(btn, fav, r))
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
