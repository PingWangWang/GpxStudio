"""
收藏夹列表弹出面板

工具栏"收藏夹"按钮触发，提供收藏地点的管理能力：
- 条目点击：选择该收藏点（地图缩放定位，由主窗口处理）
- 条目右侧金色★按钮：删除该收藏（从列表与存储移除）
- 顶部导入/导出/清空按钮：JSON 文件导入导出与批量清空
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QListWidget, QListWidgetItem, QPushButton, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer
from typing import List, Dict
from ui.theme import theme


class FavoritesListPopup(QWidget):
    """收藏夹列表弹出面板"""

    # 每行高度（PopupPositioner 计算弹窗最大高度时引用）
    ITEM_HEIGHT = 50

    # 顶部按钮行高度（导入/导出/清空 + 边距），高度公式计入总高
    HEADER_HEIGHT = 59

    # 信号
    favorite_selected = pyqtSignal(dict)  # 条目点击（选择收藏点），携带收藏记录
    favorite_delete_requested = pyqtSignal(int)  # 金星按钮点击（删除收藏），携带收藏ID
    import_clicked = pyqtSignal()  # 导入按钮
    export_clicked = pyqtSignal()  # 导出按钮
    clear_clicked = pyqtSignal()  # 清空按钮
    closed = pyqtSignal()  # 弹窗被关闭（含失去焦点自动关闭），主窗口恢复工具栏按钮态

    def __init__(self, parent=None, map_manager=None):
        """初始化收藏夹列表

        Args:
            parent: 父窗口（主窗口）
            map_manager: MapManager 实例（可选，读取收藏数据；
                         未注入时渲染阶段从父窗口实时获取）
        """
        super().__init__(parent)
        self._map_manager = map_manager

        # 设置窗口标志 - 使用Qt.Tool随主窗口移动（与搜索弹窗一致）
        # 不加 WindowStaysOnTopHint：置顶会使其在切换其他软件时仍浮于最上层，
        # Tool 子窗口层级随主窗口，切后台时自然下沉
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        theme.set_theme_stylesheet(self, """
            FavoritesListPopup {
                background-color: __PANEL_BG__;
                border: 1px solid __BORDER__;
                border-radius: 4px;
            }
            QPushButton#toolButton {
                background-color: transparent;
                border: 1px solid __BORDER__;
                border-radius: 3px;
                color: __TEXT__;
                font-size: 12px;
                padding: 2px 10px;
            }
            QPushButton#toolButton:hover {
                border-color: __ACCENT__;
                color: __ACCENT__;
            }
            QPushButton#clearButton {
                background-color: transparent;
                border: 1px solid __DANGER__;
                border-radius: 3px;
                color: __DANGER__;
                font-size: 12px;
                padding: 2px 10px;
            }
            QPushButton#clearButton:hover {
                background-color: rgba(245, 34, 45, 0.1);
            }
            QListWidget {
                background-color: __PANEL_BG__;
                border: none;
                outline: none;
            }
            QListWidget::item {
                border-bottom: 1px solid __DIVIDER__;
            }
            QListWidget::item:hover {
                background-color: __HOVER__;
            }
            QListWidget::item:selected {
                background-color: __ACCENT__;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 顶部工具按钮行：导入 / 导出 / 清空 / 关闭（四按钮均分整个宽度）
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(6)

        self.import_btn = QPushButton("导入")
        self.import_btn.setObjectName("toolButton")
        self.import_btn.setToolTip("从 JSON 文件导入收藏")
        self.import_btn.clicked.connect(self.import_clicked.emit)
        self.import_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        toolbar_layout.addWidget(self.import_btn, 1)

        self.export_btn = QPushButton("导出")
        self.export_btn.setObjectName("toolButton")
        self.export_btn.setToolTip("导出收藏到 JSON 文件")
        self.export_btn.clicked.connect(self.export_clicked.emit)
        self.export_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        toolbar_layout.addWidget(self.export_btn, 1)

        self.clear_btn = QPushButton("清空")
        self.clear_btn.setObjectName("clearButton")
        self.clear_btn.setToolTip("清空全部收藏")
        self.clear_btn.clicked.connect(self.clear_clicked.emit)
        self.clear_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        toolbar_layout.addWidget(self.clear_btn, 1)

        # 关闭按钮：hide 经 hideEvent → closed 信号自动恢复工具栏按钮态
        self.close_btn = QPushButton("关闭")
        self.close_btn.setObjectName("toolButton")
        self.close_btn.setToolTip("关闭收藏夹列表")
        self.close_btn.clicked.connect(self.hide)
        self.close_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        toolbar_layout.addWidget(self.close_btn, 1)

        layout.addLayout(toolbar_layout)

        # 收藏列表
        self.favorites_list = QListWidget()
        self.favorites_list.setSelectionMode(QListWidget.NoSelection)
        self.favorites_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.favorites_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.favorites_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.favorites_list)

        # 空状态提示
        self.empty_label = QLabel("暂无收藏地点")
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

    # ── 数据 ────────────────────────────────────────────────────────────

    def count(self) -> int:
        """列表条目数

        与 QListWidget 弹窗（搜索历史/结果）的 count() 接口对齐，
        供 PopupPositioner 高度公式统一调用（QWidget 本身无 count()）。
        """
        return self.favorites_list.count()

    def _get_map_manager(self):
        """获取 MapManager（构造注入优先，否则从父窗口实时获取）"""
        if self._map_manager is not None:
            return self._map_manager
        parent = self.parent()
        return getattr(parent, 'map_manager', None) if parent is not None else None

    def refresh(self):
        """从收藏存储重新拉取列表（删除/导入/清空后调用）"""
        self.favorites_list.clear()

        map_manager = self._get_map_manager()
        if map_manager is None:
            favorites = []
        else:
            favorites = map_manager.favorites_storage.get_all()

        if not favorites:
            self.favorites_list.setVisible(False)
            self.empty_label.setVisible(True)
            return

        self.favorites_list.setVisible(True)
        self.empty_label.setVisible(False)

        for fav in favorites:
            self._add_favorite_item(fav)

    def _add_favorite_item(self, fav: dict):
        """添加单个收藏条目（名称/地址 + 金色★删除按钮）"""
        item = QListWidgetItem()
        item.setSizeHint(QSize(0, self.ITEM_HEIGHT))
        item.setData(Qt.UserRole, fav)

        # 行控件：左侧名称/地址，右侧金星删除按钮
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(10, 4, 8, 4)
        row_layout.setSpacing(8)

        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        # 左侧图标按地址类型分类（搜索/历史/收藏夹三处图标一致；名称兜底推断类型）
        from modules.search.type_icons import get_type_emoji
        name_label = QLabel(
            f"{get_type_emoji(fav.get('type', ''), fav.get('name', ''))} {fav.get('name', '收藏点')}")
        theme.apply_to_sub(name_label, """
            QLabel {
                color: __TEXT__;
                font-size: 13px;
                font-weight: bold;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)
        # 文本穿透鼠标事件，点击行触发条目选择
        name_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        # 长名称自动换行，避免地址名称过长时显示不全；
        # 换行宽度在条目入列后按列表实际宽度动态设置（见条目尾部调整逻辑）
        name_label.setWordWrap(True)
        text_layout.addWidget(name_label)

        address = fav.get('address', '')
        if address:
            address_label = QLabel(address)
            theme.apply_to_sub(address_label, """
                QLabel {
                    color: __TEXT_SECONDARY__;
                    font-size: 12px;
                    font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                }
            """)
            address_label.setAttribute(Qt.WA_TransparentForMouseEvents)
            # 地址文字过长显示不全时，悬停显示完整地址（tooltip）
            # 可用宽度估算：弹窗宽 280 - 左右边距(18) - 金星按钮与间距(34)
            from PyQt5.QtGui import QFontMetrics
            available_width = 280 - 18 - 34
            if QFontMetrics(address_label.font()).horizontalAdvance(address) > available_width:
                address_label.setToolTip(address)
            text_layout.addWidget(address_label)

        row_layout.addWidget(text_container, 1)

        # 金星删除按钮（收藏夹内必为已收藏，点击即删除）
        delete_btn = QPushButton("★")
        delete_btn.setToolTip("删除此收藏")
        delete_btn.setFixedSize(26, 26)
        delete_btn.setCursor(Qt.PointingHandCursor)
        theme.apply_to_sub(delete_btn, """
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 17px;
                color: __GOLD__;
                padding: 0;
            }
            QPushButton:hover {
                color: __DANGER__;
            }
        """)
        delete_btn.clicked.connect(
            lambda checked=False, fav_id=fav.get('id'):
                self.favorite_delete_requested.emit(fav_id))
        # 垂直居中：条目高度高于按钮时按钮保持居中，避免贴顶部
        row_layout.addWidget(delete_btn, 0, Qt.AlignVCenter)

        self.favorites_list.addItem(item)
        self.favorites_list.setItemWidget(item, row_widget)

        # 按列表实际宽度设置名称换行宽度并校正行高：
        # 延迟到事件循环（弹窗已定位、宽度已确定）后执行，
        # 避免硬编码宽度导致换行过窄、第一行右侧留白
        def _adjust_name_wrap():
            try:
                view_width = self.favorites_list.viewport().width()
                # 可用宽度 = 列表宽 - 左右边距 - 金星按钮与间距
                avail_width = max(view_width - 52, 100)
                name_label.setMaximumWidth(avail_width)
                item.setSizeHint(QSize(0, row_widget.sizeHint().height()))
            except RuntimeError:
                pass  # 条目已被移除（列表刷新），无需调整

        QTimer.singleShot(0, _adjust_name_wrap)

    # ── 交互 ────────────────────────────────────────────────────────────

    def _on_item_clicked(self, item: QListWidgetItem):
        """条目点击：选择该收藏点（地图缩放定位由主窗口处理），弹窗保持展开"""
        fav = item.data(Qt.UserRole)
        if fav:
            self.favorite_selected.emit(fav)

    def keyPressEvent(self, event):
        """处理键盘事件：ESC 关闭"""
        if event.key() == Qt.Key_Escape:
            self.hide()
            event.accept()
        else:
            super().keyPressEvent(event)

    def hideEvent(self, event):
        """窗口隐藏事件：通知主窗口恢复工具栏按钮态"""
        super().hideEvent(event)
        self.favorites_list.clearSelection()
        self.closed.emit()
