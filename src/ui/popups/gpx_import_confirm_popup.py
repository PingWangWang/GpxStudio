# -*- coding: utf-8 -*-
"""
GPX 导入信息确认面板

GPX 文件解析成功后弹出，展示本次导入的路线信息
（起点名称/终点名称/路线点数/里程/耗时/是否含海拔），
由用户手动确认后才入库。
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame)
from PyQt5.QtCore import Qt
from ui.theme import theme


class GpxImportConfirmPopup(QDialog):
    """GPX 导入信息确认面板"""

    def __init__(self, parent=None, parsed: dict = None, source_name: str = ''):
        """
        Args:
            parent: 父窗口
            parsed: GpxImportParser.parse 的解析结果
            source_name: 源文件名称（展示用）
        """
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self._init_ui(parsed or {}, source_name)

    def _init_ui(self, parsed: dict, source_name: str):
        """初始化UI：标题 + 字段列表 + 导入/取消按钮"""
        theme.set_theme_stylesheet(self, """
            GpxImportConfirmPopup {
                background-color: __PANEL_BG__;
                border: 1px solid __BORDER__;
                border-radius: 8px;
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QLabel { font-family: "Microsoft YaHei", "微软雅黑", sans-serif; }
            QPushButton {
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # 标题
        title = QLabel("GPX 导入信息确认")
        theme.apply_to_sub(title, """
            QLabel { color: __TEXT__; font-size: 15px; font-weight: bold; }""")
        layout.addWidget(title)

        # 源文件
        source_label = QLabel(f"文件: {source_name}")
        theme.apply_to_sub(source_label, """
            QLabel { color: __TEXT_SECONDARY__; font-size: 12px; }""")
        layout.addWidget(source_label)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        theme.apply_to_sub(line, "QFrame { color: __DIVIDER__; }")
        layout.addWidget(line)

        # 字段列表
        def _add_field(key, value):
            row = QHBoxLayout()
            row.setSpacing(10)
            key_label = QLabel(key)
            theme.apply_to_sub(key_label, """
                QLabel { color: __TEXT_SECONDARY__; font-size: 13px; }""")
            key_label.setFixedWidth(80)
            value_label = QLabel(value)
            theme.apply_to_sub(value_label, """
                QLabel { color: __TEXT__; font-size: 13px; font-weight: bold; }""")
            row.addWidget(key_label)
            row.addWidget(value_label, 1)
            layout.addLayout(row)

        # 里程格式化
        distance_m = parsed.get('distance') or 0
        if distance_m >= 1000:
            distance_text = f"{distance_m / 1000:.1f} 公里"
        else:
            distance_text = f"{distance_m:.0f} 米"
        # 耗时格式化
        duration_s = parsed.get('duration') or 0
        h, rem = divmod(duration_s, 3600)
        m, s = divmod(rem, 60)
        if h > 0:
            duration_text = f"{h} 小时 {m} 分钟"
        elif m > 0:
            duration_text = f"{m} 分钟"
        else:
            duration_text = f"{s} 秒"

        _add_field("起点:", parsed.get('start', '起点'))
        _add_field("终点:", parsed.get('end', '终点'))
        _add_field("路线点数:", f"{parsed.get('point_count', 0)} 个")
        _add_field("里程:", distance_text)
        _add_field("耗时:", duration_text)
        _add_field("海拔信息:", "已包含" if parsed.get('has_elevation') else "未包含")

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        ok_btn = QPushButton("确认导入")
        ok_btn.setObjectName("primaryButton")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        layout.addLayout(button_layout)

        self.setMinimumWidth(380)
        self.setMaximumWidth(420)

    def _center_on_screen(self):
        """居中显示"""
        self.updateGeometry()
        from PyQt5.QtWidgets import QApplication
        if self.parent() and self.parent().isVisible():
            parent_geo = self.parent().geometry()
            x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
            y = parent_geo.y() + (parent_geo.height() - self.height()) // 2
            self.move(x, y)
        else:
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)

    def exec_(self):
        """重写 exec_：显示前居中"""
        self.adjustSize()
        self._center_on_screen()
        return super().exec_()
