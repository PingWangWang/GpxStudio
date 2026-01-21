"""
GPX导出弹出面板
用于设置路线起始时间并导出GPX文件
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QApplication, QLineEdit)
from PyQt5.QtCore import Qt, QDateTime, pyqtSignal, QEvent, QTimer, QSize
from PyQt5.QtGui import QFont
import os


class GpxExportPopup(QWidget):
    """GPX导出弹出面板"""

    export_confirmed = pyqtSignal(QDateTime)  # 确认导出信号，传递起始时间
    closed = pyqtSignal()  # 关闭信号

    def __init__(self, route_data: dict, parent=None):
        super().__init__(parent)
        self.route_data = route_data
        self._init_ui()

        # 设置窗口标志 - 使用Tool而不是ToolTip，避免自动关闭
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)  # 不透明背景

        # 设置焦点策略以接收键盘事件
        self.setFocusPolicy(Qt.StrongFocus)

        # 安装事件过滤器以监听焦点变化
        self.installEventFilter(self)

    def _init_ui(self):
        """初始化UI"""
        # 设置弹出面板样式 - 与路线面板颜色统一
        self.setStyleSheet("""
            GpxExportPopup {
                background-color: #3d93fd;
                border-radius: 8px;
                border: 1px solid rgba(0, 0, 0, 0.15);
                font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            }
            QLabel {
                color: white;
                font-size: 13px;
            }
            CustomDateTimeEdit {
                background-color: transparent;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.9);
                color: #4A90E2;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: white;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.8);
            }
            QPushButton#cancelButton {
                background-color: rgba(255, 255, 255, 0.7);
                color: #666666;
            }
            QPushButton#cancelButton:hover {
                background-color: rgba(255, 255, 255, 0.85);
            }
            QPushButton#cancelButton:pressed {
                background-color: rgba(255, 255, 255, 0.6);
            }
            QFrame {
                color: rgba(255, 255, 255, 0.3);
            }
        """)

        # 设置自动填充背景
        self.setAutoFillBackground(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 标题
        title_label = QLabel("导出GPX文件")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("QFrame { color: #e0e0e0; }")
        layout.addWidget(separator)

        # 路线信息
        route_info = self._get_route_info()
        info_label = QLabel(route_info)
        info_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                padding: 8px;
            }
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # 时间设置区域
        time_container = QWidget()
        time_layout = QHBoxLayout(time_container)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(8)

        time_label = QLabel("起始时间:")
        time_layout.addWidget(time_label)

        # 时间文本编辑框
        from PyQt5.QtWidgets import QLineEdit
        self.datetime_text_edit = QLineEdit()
        self.datetime_text_edit.setText(QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm"))
        self.datetime_text_edit.setReadOnly(True)  # 设置为只读
        self.datetime_text_edit.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 13px;
                color: #333333;
            }
            QLineEdit:focus {
                border: 1px solid rgba(255, 255, 255, 0.7);
                background-color: white;
            }
        """)
        time_layout.addWidget(self.datetime_text_edit, 1)

        # 设置按钮
        self.settings_button = QPushButton()
        self.settings_button.setFixedSize(32, 32)
        self.settings_button.setToolTip("设置时间")

        # 使用emoji作为图标
        self.settings_button.setText("⏰")
        self.settings_button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                text-align: center;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.7);
            }
        """)
        self.settings_button.clicked.connect(self._show_datetime_picker)
        time_layout.addWidget(self.settings_button)

        layout.addWidget(time_container)

        # 按钮区域
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)

        button_layout.addStretch()

        # 取消按钮
        cancel_button = QPushButton("取消")
        cancel_button.setObjectName("cancelButton")
        cancel_button.clicked.connect(self._on_cancel_clicked)
        button_layout.addWidget(cancel_button)

        # 确认导出按钮
        export_button = QPushButton("确认导出")
        export_button.clicked.connect(self._on_export_clicked)
        export_button.setDefault(True)
        button_layout.addWidget(export_button)

        layout.addWidget(button_container)

        # 设置固定宽度
        self.setFixedWidth(320)

    def _get_route_info(self):
        """获取路线信息文本"""
        description = self.route_data.get('description', '路线方案')
        distance = self.route_data.get('distance', 0)
        duration = self.route_data.get('duration', 0)

        distance_km = distance / 1000
        hours = duration // 3600
        minutes = (duration % 3600) // 60

        if hours > 0:
            time_text = f"{hours}小时{minutes}分钟"
        else:
            time_text = f"{minutes}分钟"

        return f"路线: {description}\n距离: {distance_km:.1f}公里\n预计时间: {time_text}"

    def _show_datetime_picker(self):
        """显示日期时间选择器"""
        # 导入自定义日期时间选择器
        from ui.widgets.custom_datetime_picker import CustomDateTimePicker
        from PyQt5.QtWidgets import QFrame

        # 如果已经有弹出窗口，先关闭
        if hasattr(self, 'picker_popup') and self.picker_popup and self.picker_popup.isVisible():
            self.picker_popup.hide()
            return

        # 创建弹出面板 - 使用QWidget作为独立窗口，确保没有标题栏且不被裁剪
        from PyQt5.QtWidgets import QWidget
        # 创建为独立窗口，这样就不会被GPX导出面板的边界裁剪
        self.picker_popup = QWidget()
        # 使用FramelessWindowHint确保没有标题栏
        self.picker_popup.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        # 确保窗口标题为空，避免显示默认标题
        self.picker_popup.setWindowTitle("")
        self.picker_popup.setStyleSheet("""
            QWidget {
                background-color: #3d93fd;
                border: 1px solid rgba(0, 0, 0, 0.15);
                border-radius: 6px;
            }
        """)

        # 设置焦点策略以接收键盘事件
        self.picker_popup.setFocusPolicy(Qt.StrongFocus)

        # 重写键盘事件处理
        def keyPressEvent(event):
            if event.key() == Qt.Key_Escape:
                print("[日期时间设置] ESC键关闭日期时间设置面板")
                self.picker_popup.hide()
                # 将焦点返回给GPX导出面板
                self.setFocus()
                print("[日期时间设置] 焦点返回给GPX导出面板")
                event.accept()
            else:
                QWidget.keyPressEvent(self.picker_popup, event)

        self.picker_popup.keyPressEvent = keyPressEvent

        # 添加日期时间选择器
        from PyQt5.QtWidgets import QVBoxLayout
        popup_layout = QVBoxLayout(self.picker_popup)
        popup_layout.setContentsMargins(0, 0, 0, 0)

        picker = CustomDateTimePicker()
        # 设置当前时间
        current_datetime_text = self.datetime_text_edit.text()
        try:
            current_datetime = QDateTime.fromString(current_datetime_text, "yyyy-MM-dd hh:mm")
            if current_datetime.isValid():
                picker.setDateTime(current_datetime)
        except:
            picker.setDateTime(QDateTime.currentDateTime())

        picker.dateTimeChanged.connect(self._on_datetime_changed)
        popup_layout.addWidget(picker)

        # 计算弹出位置（在设置按钮下方）
        button_global_pos = self.settings_button.mapToGlobal(self.settings_button.rect().bottomLeft())
        popup_x = button_global_pos.x() - 200  # 向左偏移以避免超出屏幕
        popup_y = button_global_pos.y() + 5

        # 确保不超出屏幕边界
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()

        if popup_x < 0:
            popup_x = 10
        if popup_x + 400 > screen.right():  # 估算弹出面板宽度
            popup_x = screen.right() - 410

        if popup_y + 250 > screen.bottom():  # 估算弹出面板高度
            popup_y = button_global_pos.y() - 255  # 显示在按钮上方

        # 直接使用全局坐标，因为picker_popup现在是一个独立窗口
        from PyQt5.QtCore import QPoint
        global_pos = QPoint(popup_x, popup_y)
        self.picker_popup.move(global_pos)

        # 调整大小并显示
        self.picker_popup.adjustSize()
        self.picker_popup.show()
        self.picker_popup.raise_()
        self.picker_popup.activateWindow()  # 激活窗口以确保获得焦点
        self.picker_popup.setFocus()  # 设置焦点以接收键盘事件

        print("[GPX导出] 显示日期时间设置面板并设置焦点")

    def _on_datetime_changed(self, datetime):
        """日期时间改变处理"""
        self.datetime_text_edit.setText(datetime.toString("yyyy-MM-dd hh:mm"))

        # 关闭日期时间选择器弹出窗口
        if hasattr(self, 'picker_popup') and self.picker_popup:
            self.picker_popup.hide()

        # 将焦点返回给GPX导出面板
        self.setFocus()
        print("[GPX导出] 日期时间选择完成，焦点返回给GPX导出面板")

        print(f"[GPX导出] 选择的时间: {datetime.toString('yyyy-MM-dd hh:mm')}")

    def get_start_time(self):
        """获取设置的起始时间"""
        datetime_text = self.datetime_text_edit.text()
        try:
            datetime = QDateTime.fromString(datetime_text, "yyyy-MM-dd hh:mm")
            if datetime.isValid():
                return datetime
        except:
            pass
        return QDateTime.currentDateTime()

    def _on_export_clicked(self):
        """确认导出按钮点击"""
        start_time = self.get_start_time()
        self.export_confirmed.emit(start_time)
        self.hide()
        self.closed.emit()

    def _on_cancel_clicked(self):
        """取消按钮点击"""
        self.hide()
        self.closed.emit()

    def show_at_position(self, pos):
        """在指定位置显示弹出面板"""
        self.move(pos)
        self.show()
        self.raise_()
        self.activateWindow()  # 激活窗口以确保获得焦点
        # 自动设置焦点到弹出面板
        self.setFocus()
        print("[GPX导出] 显示弹出面板并设置焦点")

    def mousePressEvent(self, event):
        """鼠标按下事件 - 防止点击面板外部时关闭"""
        super().mousePressEvent(event)
        event.accept()  # 接受事件，防止传播到父组件

    def eventFilter(self, obj, event):
        """事件过滤器 - 监听焦点变化"""
        # 如果正在显示时间日期选择器，忽略焦点丢失事件
        if hasattr(self, 'picker_popup') and self.picker_popup and self.picker_popup.isVisible():
            if event.type() == QEvent.WindowDeactivate or event.type() == QEvent.FocusOut:
                print("[GPX导出] 时间日期选择器显示中，忽略焦点丢失事件")
                return True  # 拦截事件，防止自动关闭

        return super().eventFilter(obj, event)

    def _check_and_close(self):
        """检查并关闭弹出面板 - 已禁用自动关闭"""
        # 不再自动关闭，只通过ESC键或按钮关闭
        pass

    def focusOutEvent(self, event):
        """焦点丢失事件 - 已禁用自动关闭"""
        super().focusOutEvent(event)
        # 不再延迟检查自动关闭

    def keyPressEvent(self, event):
        """键盘按键事件"""
        if event.key() == Qt.Key_Escape:
            # 检查是否有日期时间选择器弹出窗口正在显示
            if hasattr(self, 'picker_popup') and self.picker_popup and self.picker_popup.isVisible():
                # 如果日期时间选择器正在显示，优先关闭它
                self.picker_popup.hide()
                # 重新设置焦点到GPX导出面板
                self.setFocus()
                print("[GPX导出] ESC键关闭日期时间选择器，焦点回到GPX导出面板")
                event.accept()
                return

            # 如果没有子弹出窗口，则关闭GPX导出面板
            print("[GPX导出] ESC键关闭GPX导出面板")
            self.hide()
            self.closed.emit()

            # 将焦点返回给路线规划面板
            parent_app = self.parent()
            while parent_app and not hasattr(parent_app, 'route_plan_panel'):
                parent_app = parent_app.parent()

            if parent_app and hasattr(parent_app, 'route_plan_panel'):
                if parent_app.route_plan_panel and parent_app.route_plan_panel.isVisible():
                    parent_app.route_plan_panel.setFocus()
                    print("[GPX导出] 焦点返回给路线规划面板")

            event.accept()
        else:
            super().keyPressEvent(event)