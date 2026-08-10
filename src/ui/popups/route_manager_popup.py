# -*- coding: utf-8 -*-
"""
路线管理列表弹出面板

工具栏"路线管理"按钮触发，提供路线库的管理能力：
- 顶部 5 按钮：导入 / 导出 / 选择 / 清空 / 关闭（均分宽度）
- 条目：路线名称（起点→终点）+ 里程·耗时详情 + 右侧海拔获取按钮
- "选择"按钮切换多选模式（多选时条目点击不渲染，导出多条独立 GPX）
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QListWidget, QListWidgetItem, QPushButton, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer
from ui.theme import theme


class RouteManagerPopup(QWidget):
    """路线管理列表弹出面板"""

    # 每行高度（PopupPositioner 计算弹窗最大高度时引用）
    ITEM_HEIGHT = 50

    # 顶部按钮行高度（导入/导出/选择/清空/关闭 + 边距）
    HEADER_HEIGHT = 59

    # 信号
    import_clicked = pyqtSignal()  # 导入按钮
    export_clicked = pyqtSignal()  # 导出按钮
    select_all_clicked = pyqtSignal()  # 全选按钮（勾选当前列表全部条目）
    delete_clicked = pyqtSignal()  # 删除按钮（删除勾选的条目）
    render_clicked = pyqtSignal(dict)  # 条目渲染按钮（单条目 toggle 渲染，携带路线记录）
    item_render_clicked = pyqtSignal(dict)  # 条目点击（仅渲染该路线，不取消；取消需点渲染按钮）
    elevation_fetch_clicked = pyqtSignal(dict)  # 条目海拔按钮（单条目获取海拔，携带路线记录）
    closed = pyqtSignal()  # 弹窗关闭（含失去焦点自动关闭），主窗口恢复工具栏按钮态

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        theme.set_theme_stylesheet(self, """
            RouteManagerPopup {
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
            QPushButton#selectButton {
                background-color: transparent;
                border: 1px solid __BORDER__;
                border-radius: 3px;
                color: __TEXT__;
                font-size: 12px;
                padding: 2px 10px;
            }
            QPushButton#selectButton:checked {
                background-color: rgba(74, 144, 226, 0.15);
                border: 1px solid __ACCENT__;
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
                background-color: rgba(74, 144, 226, 0.2);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 顶部工具按钮行：导入 / 导出 / 清空 / 关闭（四按钮均分；多选由条目勾选驱动）
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(4)

        self.import_btn = QPushButton("导入")
        self.import_btn.setObjectName("toolButton")
        self.import_btn.setToolTip("导入 GPX 文件（支持多选，每个文件独立条目）")
        self.import_btn.clicked.connect(self.import_clicked.emit)
        self.import_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        toolbar_layout.addWidget(self.import_btn, 1)

        self.export_btn = QPushButton("导出")
        self.export_btn.setObjectName("toolButton")
        self.export_btn.setToolTip("导出选中路线为 GPX（多选时逐条导出独立文件）")
        self.export_btn.clicked.connect(self.export_clicked.emit)
        self.export_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        toolbar_layout.addWidget(self.export_btn, 1)

        # 全选按钮（toggle）：首次点击全选全部条目并高亮；再次点击取消全部选中并取消高亮
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.setObjectName("selectButton")
        self.select_all_btn.setToolTip("全选全部路线（再次点击取消全选）")
        self.select_all_btn.setCheckable(True)
        self.select_all_btn.clicked.connect(self.select_all_clicked.emit)
        self.select_all_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        toolbar_layout.addWidget(self.select_all_btn, 1)

        # 删除按钮：删除勾选的条目（危险样式）
        self.delete_btn = QPushButton("删除")
        self.delete_btn.setObjectName("clearButton")
        self.delete_btn.setToolTip("删除勾选的路线")
        self.delete_btn.clicked.connect(self.delete_clicked.emit)
        self.delete_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        toolbar_layout.addWidget(self.delete_btn, 1)

        # （无关闭按钮：再次点击工具栏路线管理按钮 / 点击面板外区域自动关闭）
        layout.addLayout(toolbar_layout)

        # 路线列表
        self.routes_list = QListWidget()
        self.routes_list.setSelectionMode(QListWidget.NoSelection)
        self.routes_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.routes_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.routes_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.routes_list)

        # 空状态提示
        self.empty_label = QLabel("暂无路线\n可通过导入 GPX 或收藏历史路线添加")
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
        """列表条目数（供 PopupPositioner 高度公式调用）"""
        return self.routes_list.count()

    def refresh(self, records: list):
        """重建列表

        Args:
            records: 路线库记录列表（RouteLibraryStorage.get_all()）
        """
        self.routes_list.clear()

        if not records:
            self.routes_list.setVisible(False)
            self.empty_label.setVisible(True)
            return

        self.routes_list.setVisible(True)
        self.empty_label.setVisible(False)

        for rec in records:
            self._add_route_item(rec)

    def _add_route_item(self, rec: dict):
        """添加单个路线条目（名称+详情 + 海拔获取按钮）"""
        item = QListWidgetItem()
        item.setSizeHint(QSize(0, self.ITEM_HEIGHT))
        item.setData(Qt.UserRole, rec)

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(10, 4, 8, 4)
        row_layout.setSpacing(8)

        # 文本列：路线名称 + 里程·耗时详情
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        name_label = QLabel(f"{rec.get('start', '起点')} → {rec.get('end', '终点')}")
        theme.apply_to_sub(name_label, """
            QLabel {
                color: __TEXT__;
                font-size: 13px;
                font-weight: bold;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)
        name_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        name_label.setWordWrap(True)
        text_layout.addWidget(name_label)

        detail_text = self._format_detail(rec)
        if detail_text:
            detail_label = QLabel(detail_text)
            theme.apply_to_sub(detail_label, """
                QLabel {
                    color: __TEXT_SECONDARY__;
                    font-size: 11px;
                    font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
                }
            """)
            detail_label.setAttribute(Qt.WA_TransparentForMouseEvents)
            text_layout.addWidget(detail_label)

        row_layout.addWidget(text_container, 1)

        # 渲染按钮（单条目控制，样式与海拔按钮一致：emoji + 32px + 实心高亮）
        render_btn = QPushButton("🚩")
        render_btn.setFixedSize(32, 30)
        render_btn.setCheckable(True)
        render_btn.setToolTip("渲染该路线到地图（再次点击取消渲染）")
        render_btn.clicked.connect(
            lambda checked=False, r=rec: self.render_clicked.emit(r))
        theme.apply_to_sub(render_btn, """
            QPushButton {
                font-size: 15px;
                background-color: __HOVER__;
                border: 1px solid __BORDER__;
                border-radius: 4px;
            }
            QPushButton:hover:enabled {
                background-color: __HOVER_STRONG__;
                border: 1px solid __BORDER__;
            }
            QPushButton:checked {
                background-color: #459c50;
                border: 1px solid #2e6b37;
            }
        """)
        row_layout.addWidget(render_btn, 0, Qt.AlignVCenter)

        # 海拔获取按钮（单条目控制，已含海拔 → 高亮，逻辑与历史列表 ⛰ 一致）
        elevation_btn = QPushButton("⛰")
        elevation_btn.setFixedSize(32, 30)
        elevation_btn.setToolTip('获取海拔数据')
        elevation_btn.clicked.connect(
            lambda checked=False, r=rec: self.elevation_fetch_clicked.emit(r))
        has_elevation = any(
            p is not None and len(p) >= 3 and p[2] is not None
            for p in (rec.get('route_points') or []))
        if has_elevation:
            elevation_btn.setToolTip('已获取海拔数据，点击重新获取')
            theme.apply_to_sub(elevation_btn, """
                QPushButton {
                    font-size: 15px;
                    background-color: #4a90e2;
                    border: 1px solid #2c5a9c;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #5aa0f0;
                }
            """)
        else:
            theme.apply_to_sub(elevation_btn, """
                QPushButton {
                    font-size: 15px;
                    background-color: __HOVER__;
                    border: 1px solid __BORDER__;
                    border-radius: 4px;
                }
                QPushButton:hover:enabled {
                    background-color: __HOVER_STRONG__;
                    border: 1px solid __BORDER__;
                }
            """)
        row_layout.addWidget(elevation_btn, 0, Qt.AlignVCenter)

        # 勾选按钮（最右侧）：点击 → 方框内显示对勾并高亮；再点取消（导出以勾选为准）
        check_btn = QPushButton("☐")
        check_btn.setFixedSize(32, 30)
        check_btn.setCheckable(True)
        check_btn.setToolTip("勾选该路线（导出时以勾选结果为准）")
        theme.apply_to_sub(check_btn, """
            QPushButton {
                font-size: 15px;
                background-color: __HOVER__;
                border: 1px solid __BORDER__;
                border-radius: 4px;
                color: __TEXT__;
            }
            QPushButton:hover:enabled {
                background-color: __HOVER_STRONG__;
                border: 1px solid __BORDER__;
            }
            QPushButton:checked {
                background-color: rgba(69, 156, 80, 0.25);
                border: 1px solid #459c50;
                color: #459c50;
            }
        """)
        check_btn.toggled.connect(
            lambda checked: check_btn.setText("☑" if checked else "☐"))
        # 勾选状态变化时同步全选按钮高亮（全部勾选 → 高亮；否则取消高亮）
        check_btn.toggled.connect(lambda checked: self._sync_select_all_state())
        row_layout.addWidget(check_btn, 0, Qt.AlignVCenter)

        self.routes_list.addItem(item)
        self.routes_list.setItemWidget(item, row_widget)

        # 按列表实际宽度设置名称换行宽度并校正行高
        def _adjust_name_wrap():
            try:
                view_width = self.routes_list.viewport().width()
                avail_width = max(view_width - 52, 100)
                name_label.setMaximumWidth(avail_width)
                item.setSizeHint(QSize(0, row_widget.sizeHint().height()))
            except RuntimeError:
                pass

        QTimer.singleShot(0, _adjust_name_wrap)

    @staticmethod
    def _format_detail(rec: dict) -> str:
        """格式化里程·耗时详情文本（无数据返回空串）"""
        parts = []
        distance = rec.get('distance')
        if distance:
            parts.append(f"{distance / 1000:.1f} 公里" if distance >= 1000
                         else f"{distance:.0f} 米")
        duration = rec.get('duration')
        if duration:
            if duration >= 3600:
                h, m = divmod(duration, 3600)
                parts.append(f"{h} 小时 {m // 60} 分钟" if m // 60 else f"{h} 小时")
            elif duration >= 60:
                parts.append(f"{duration // 60} 分钟")
            else:
                parts.append(f"{duration:.0f} 秒")
        return " · ".join(parts)

    def set_rendered_ids(self, rendered_ids: set):
        """更新各条目渲染按钮的高亮状态（已渲染 → 绿色高亮）

        Args:
            rendered_ids: 当前已渲染的路线记录 id 集合
        """
        for i in range(self.routes_list.count()):
            item = self.routes_list.item(i)
            rec = item.data(Qt.UserRole)
            row = self.routes_list.itemWidget(item)
            if row is None:
                continue
            for btn in row.findChildren(QPushButton):
                if btn.text() == "🚩":
                    btn.setChecked(bool(rec) and rec.get('id') in rendered_ids)
                    break

    def get_export_records(self) -> list:
        """获取勾选的路线记录（导出/删除以勾选结果为准）"""
        return self.get_checked_records()

    def get_checked_records(self) -> list:
        """获取当前勾选的路线记录列表"""
        checked = []
        for i in range(self.routes_list.count()):
            item = self.routes_list.item(i)
            row = self.routes_list.itemWidget(item)
            if row is None:
                continue
            for btn in row.findChildren(QPushButton):
                if btn.text() in ("☑", "☐") and btn.isChecked():
                    checked.append(item.data(Qt.UserRole))
                    break
        return checked

    def toggle_select_all(self):
        """全选按钮 toggle：全选全部条目（按钮高亮）↔ 取消全部选中（按钮取消高亮）

        按钮 checked 状态由点击自动切换，此处按状态执行条目勾选同步。
        """
        if self.select_all_btn.isChecked():
            self.select_all()
        else:
            self.deselect_all()

    def select_all(self):
        """全选：勾选当前列表中的全部条目"""
        for i in range(self.routes_list.count()):
            item = self.routes_list.item(i)
            row = self.routes_list.itemWidget(item)
            if row is None:
                continue
            for btn in row.findChildren(QPushButton):
                if btn.text() in ("☑", "☐") and not btn.isChecked():
                    btn.setChecked(True)
                    break

    def deselect_all(self):
        """取消全选：取消当前列表中全部条目的勾选"""
        for i in range(self.routes_list.count()):
            item = self.routes_list.item(i)
            row = self.routes_list.itemWidget(item)
            if row is None:
                continue
            for btn in row.findChildren(QPushButton):
                if btn.text() in ("☑", "☐") and btn.isChecked():
                    btn.setChecked(False)
                    break

    def _sync_select_all_state(self):
        """同步全选按钮高亮：全部条目均已勾选 → 高亮；否则取消高亮

        用户在列表中勾选/取消勾选条目时自动联动。
        """
        total = self.routes_list.count()
        checked = len(self.get_checked_records())
        self.select_all_btn.setChecked(total > 0 and checked == total)

    # ── 交互 ────────────────────────────────────────────────────────────

    def _on_item_clicked(self, item: QListWidgetItem):
        """条目点击：请求渲染该路线（已渲染时无操作，取消渲染需点击条目右侧渲染按钮）"""
        rec = item.data(Qt.UserRole)
        if rec:
            self.item_render_clicked.emit(rec)

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
        self.routes_list.clearSelection()
        self.closed.emit()
