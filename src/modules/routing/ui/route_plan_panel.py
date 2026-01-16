"""
路线规划面板组件

参考高德地图的路线规划界面设计
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLineEdit, QLabel, QScrollArea, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QPixmap, QTransform
import os


class RoutePlanPanel(QWidget):
    """路线规划面板"""

    # 信号
    cancel_clicked = pyqtSignal()  # 取消按钮点击
    plan_route_clicked = pyqtSignal(str, str, str, list)  # 规划路线：(起点, 终点, 交通方式, 途径点列表)
    search_location_clicked = pyqtSignal(str, str)  # 搜索地点：(搜索文本, 类型: start/end/waypoint)
    history_selected = pyqtSignal(dict)  # 选择历史记录

    def __init__(self, parent=None):
        """初始化路线规划面板"""
        super().__init__(parent)

        # 设置窗口标志 - 作为工具提示窗口，不抢夺焦点
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)  # 不透明背景

        # 当前交通方式
        self.current_transport_mode = "driving"  # driving, cycling, walking

        # 途径点列表
        self.waypoint_widgets = []

        # 初始化UI
        self._init_ui()

        # 加载图标
        self._load_icons()

        # 加载图标
        self._load_icons()

    def _init_ui(self):
        """初始化UI"""
        # 设置面板样式 - 使用 RoutePlanPanel 作为选择器确保背景色应用
        self.setStyleSheet("""
            RoutePlanPanel {
                background-color: #4A90E2;
                border-radius: 6px;
                border: 1px solid rgba(0, 0, 0, 0.15);
            }
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.9);
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
                color: #333333;
            }
            QLineEdit:focus {
                background-color: white;
            }
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
            /* 交通方式按钮特殊样式 - 无背景框 */
            QPushButton[transportMode="true"] {
                background-color: transparent;
                border: none;
            }
            QPushButton[transportMode="true"]:hover {
                background-color: rgba(255, 255, 255, 0.15);
            }
            QPushButton[transportMode="true"]:pressed {
                background-color: rgba(255, 255, 255, 0.25);
            }
            QPushButton[transportMode="true"][selected="true"] {
                background-color: rgba(255, 255, 255, 0.2);
                border: none;
            }
            /* 切换按钮特殊样式 - 无背景框 */
            QPushButton[switchButton="true"] {
                background-color: transparent;
                border: none;
            }
            QPushButton[switchButton="true"]:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton[switchButton="true"]:pressed {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)

        # 设置自动填充背景
        self.setAutoFillBackground(True)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # 1. 顶部：交通方式选择和取消按钮
        top_layout = QHBoxLayout()
        top_layout.setSpacing(8)

        # 取消按钮（左侧，用于占位保持居中）
        cancel_spacer = QWidget()
        cancel_spacer.setFixedSize(36, 36)
        top_layout.addWidget(cancel_spacer)

        # 左侧弹簧（用于居中交通方式按钮）
        top_layout.addStretch(1)

        # 驾车按钮
        self.driving_button = QPushButton()
        self.driving_button.setFixedSize(36, 36)
        self.driving_button.setToolTip("驾车")
        self.driving_button.setProperty("transportMode", True)
        self.driving_button.clicked.connect(lambda: self._switch_transport_mode("driving"))
        top_layout.addWidget(self.driving_button)

        # 骑行按钮
        self.cycling_button = QPushButton()
        self.cycling_button.setFixedSize(36, 36)
        self.cycling_button.setToolTip("骑行")
        self.cycling_button.setProperty("transportMode", True)
        self.cycling_button.clicked.connect(lambda: self._switch_transport_mode("cycling"))
        top_layout.addWidget(self.cycling_button)

        # 步行按钮
        self.walking_button = QPushButton()
        self.walking_button.setFixedSize(36, 36)
        self.walking_button.setToolTip("步行")
        self.walking_button.setProperty("transportMode", True)
        self.walking_button.clicked.connect(lambda: self._switch_transport_mode("walking"))
        top_layout.addWidget(self.walking_button)

        # 右侧弹簧（用于居中交通方式按钮）
        top_layout.addStretch(1)

        # 取消按钮（右侧）
        self.cancel_button = QPushButton()
        self.cancel_button.setFixedSize(36, 36)
        self.cancel_button.setToolTip("取消")
        self.cancel_button.clicked.connect(self.cancel_clicked.emit)
        top_layout.addWidget(self.cancel_button)

        main_layout.addLayout(top_layout)

        # 2. 中部：起点、终点、途径点
        locations_layout = QVBoxLayout()
        locations_layout.setSpacing(8)

        # 主容器（包含切换按钮、起点终点途径点、添加按钮）
        main_locations_container = QWidget()
        main_locations_layout = QHBoxLayout(main_locations_container)
        main_locations_layout.setContentsMargins(0, 0, 0, 0)
        main_locations_layout.setSpacing(8)

        # 保存主容器引用，用于后续添加按钮位置调整
        self.main_locations_container = main_locations_container
        self.main_locations_layout = main_locations_layout

        # 切换按钮（左侧，垂直居中）
        self.switch_button = QPushButton()
        self.switch_button.setFixedSize(32, 32)
        self.switch_button.setToolTip("切换起点和终点")
        self.switch_button.setProperty("switchButton", True)
        self.switch_button.clicked.connect(self._switch_start_end)
        main_locations_layout.addWidget(self.switch_button, 0, Qt.AlignVCenter)

        # 中间的垂直容器（起点、途径点、终点）
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(8)

        # 起点行
        self.start_layout = QHBoxLayout()
        self.start_layout.setSpacing(8)

        # 起点标签
        start_label = QLabel("起")
        start_label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.3);
                color: white;
                font-size: 12px;
                font-weight: bold;
                border-radius: 12px;
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
            }
        """)
        start_label.setAlignment(Qt.AlignCenter)
        self.start_layout.addWidget(start_label)

        # 起点输入框
        self.start_input = QLineEdit()
        self.start_input.setPlaceholderText("请输入起点")
        self.start_input.returnPressed.connect(lambda: self._on_search_location("start"))
        self.start_layout.addWidget(self.start_input)

        # 起点右侧占位符（用于保持输入框宽度一致）
        self.start_spacer = QWidget()
        self.start_spacer.setFixedSize(32, 32)
        self.start_layout.addWidget(self.start_spacer)

        center_layout.addLayout(self.start_layout)

        # 途径点容器
        self.waypoints_container = QWidget()
        self.waypoints_layout = QVBoxLayout(self.waypoints_container)
        self.waypoints_layout.setContentsMargins(0, 0, 0, 0)
        self.waypoints_layout.setSpacing(8)
        # 初始化时隐藏，确保不占用空间
        self.waypoints_container.setVisible(False)
        center_layout.addWidget(self.waypoints_container)

        # 终点行（保存引用以便后续添加按钮）
        self.end_layout = QHBoxLayout()
        self.end_layout.setSpacing(8)

        # 终点标签
        end_label = QLabel("终")
        end_label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.3);
                color: white;
                font-size: 12px;
                font-weight: bold;
                border-radius: 12px;
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
            }
        """)
        end_label.setAlignment(Qt.AlignCenter)
        self.end_layout.addWidget(end_label)

        # 终点输入框
        self.end_input = QLineEdit()
        self.end_input.setPlaceholderText("请输入终点")
        self.end_input.returnPressed.connect(lambda: self._on_search_location("end"))
        self.end_layout.addWidget(self.end_input)

        # 终点右侧占位符（用于保持输入框宽度一致）
        self.end_spacer = QWidget()
        self.end_spacer.setFixedSize(32, 32)
        self.end_layout.addWidget(self.end_spacer)

        center_layout.addLayout(self.end_layout)

        main_locations_layout.addWidget(center_container)

        # 添加途径点按钮（右侧，垂直居中）
        self.add_waypoint_button = QPushButton()
        self.add_waypoint_button.setFixedSize(32, 32)
        self.add_waypoint_button.setToolTip("添加途径点")
        self.add_waypoint_button.clicked.connect(self._add_waypoint)
        main_locations_layout.addWidget(self.add_waypoint_button, 0, Qt.AlignVCenter)

        locations_layout.addWidget(main_locations_container)

        main_layout.addLayout(locations_layout)

        # 3. 路线规划按钮和清除路线按钮
        # 使用与起点终点相同的布局结构，确保对齐
        buttons_container = QWidget()
        buttons_container_layout = QHBoxLayout(buttons_container)
        buttons_container_layout.setContentsMargins(0, 0, 0, 0)
        buttons_container_layout.setSpacing(8)

        # 左侧占位符（与切换按钮宽度一致）
        left_spacer = QWidget()
        left_spacer.setFixedSize(32, 32)
        buttons_container_layout.addWidget(left_spacer)

        # 中间按钮容器
        center_buttons_layout = QHBoxLayout()
        center_buttons_layout.setSpacing(8)

        # 清除路线按钮
        self.clear_button = QPushButton("清除路线")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.7);
                color: #666666;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.85);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.6);
            }
        """)
        self.clear_button.clicked.connect(self._on_clear_route)
        center_buttons_layout.addWidget(self.clear_button)

        # 开车去按钮
        self.plan_button = QPushButton("开车去")
        self.plan_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.9);
                color: #4A90E2;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: white;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.8);
            }
        """)
        self.plan_button.clicked.connect(self._on_plan_route)
        center_buttons_layout.addWidget(self.plan_button)

        buttons_container_layout.addLayout(center_buttons_layout)

        # 右侧占位符（与添加按钮宽度一致）
        right_spacer = QWidget()
        right_spacer.setFixedSize(32, 32)
        buttons_container_layout.addWidget(right_spacer)

        main_layout.addWidget(buttons_container)

        # 4. 路线搜索历史记录
        history_header_layout = QHBoxLayout()
        history_header_layout.setSpacing(4)
        history_header_layout.setContentsMargins(0, 8, 0, 8)

        # 历史记录图标
        self.history_icon_label = QLabel()
        self.history_icon_label.setFixedSize(16, 16)
        history_header_layout.addWidget(self.history_icon_label)

        # 历史记录文本
        history_label = QLabel("路线搜索记录")
        history_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                font-size: 12px;
            }
        """)
        history_header_layout.addWidget(history_label)

        # 添加弹簧，使标签靠左
        history_header_layout.addStretch(1)

        main_layout.addLayout(history_header_layout)

        # 历史记录列表
        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(0, 0, 0, 0.3);
                border: none;
                border-radius: 4px;
                color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            QListWidget::item:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QListWidget::item:selected {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        self.history_list.itemClicked.connect(self._on_history_clicked)
        main_layout.addWidget(self.history_list)

        # 初始化交通方式
        self._update_transport_mode_ui()

    def _load_icons(self):
        """加载图标"""
        # 获取项目根目录
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file)))))

        # 驾车图标（白色版本）
        driving_icon_path = os.path.join(project_root, 'res', 'Driving_white.png')
        if os.path.exists(driving_icon_path):
            self.driving_button.setIcon(QIcon(driving_icon_path))
            self.driving_button.setIconSize(QSize(24, 24))

        # 骑行图标（白色版本）
        cycling_icon_path = os.path.join(project_root, 'res', 'Cycling_white.png')
        if os.path.exists(cycling_icon_path):
            self.cycling_button.setIcon(QIcon(cycling_icon_path))
            self.cycling_button.setIconSize(QSize(24, 24))

        # 步行图标（白色版本）
        walking_icon_path = os.path.join(project_root, 'res', 'Waking_white.png')
        if os.path.exists(walking_icon_path):
            self.walking_button.setIcon(QIcon(walking_icon_path))
            self.walking_button.setIconSize(QSize(24, 24))

        # 取消图标（白色版本）
        cancel_icon_path = os.path.join(project_root, 'res', 'Cancel_white.png')
        if os.path.exists(cancel_icon_path):
            self.cancel_button.setIcon(QIcon(cancel_icon_path))
            self.cancel_button.setIconSize(QSize(20, 20))

        # 切换图标（白色版本，旋转90度）
        switch_icon_path = os.path.join(project_root, 'res', 'Switch_white.png')
        if os.path.exists(switch_icon_path):
            pixmap = QPixmap(switch_icon_path)
            # 旋转90度
            transform = QTransform().rotate(90)
            rotated_pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
            self.switch_button.setIcon(QIcon(rotated_pixmap))
            self.switch_button.setIconSize(QSize(20, 20))

        # 添加途径点图标
        add_icon_path = os.path.join(project_root, 'res', 'Add.png')
        if os.path.exists(add_icon_path):
            self.add_waypoint_button.setIcon(QIcon(add_icon_path))
            self.add_waypoint_button.setIconSize(QSize(20, 20))

        # 历史记录图标（白色版本）
        history_icon_path = os.path.join(project_root, 'res', 'History_white.png')
        if os.path.exists(history_icon_path):
            pixmap = QPixmap(history_icon_path)
            # 缩放到16x16
            scaled_pixmap = pixmap.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.history_icon_label.setPixmap(scaled_pixmap)

    def _switch_transport_mode(self, mode: str):
        """切换交通方式"""
        self.current_transport_mode = mode
        self._update_transport_mode_ui()

    def _update_transport_mode_ui(self):
        """更新交通方式UI"""
        # 更新按钮样式（使用property标记选中状态）
        self.driving_button.setProperty("selected", self.current_transport_mode == "driving")
        self.driving_button.style().unpolish(self.driving_button)
        self.driving_button.style().polish(self.driving_button)

        self.cycling_button.setProperty("selected", self.current_transport_mode == "cycling")
        self.cycling_button.style().unpolish(self.cycling_button)
        self.cycling_button.style().polish(self.cycling_button)

        self.walking_button.setProperty("selected", self.current_transport_mode == "walking")
        self.walking_button.style().unpolish(self.walking_button)
        self.walking_button.style().polish(self.walking_button)

        # 更新规划按钮文本
        mode_text = {
            "driving": "开车去",
            "cycling": "骑车去",
            "walking": "走路去"
        }
        self.plan_button.setText(mode_text.get(self.current_transport_mode, "开车去"))

        # 显示/隐藏添加途径点按钮（仅驾车模式）
        self.add_waypoint_button.setVisible(self.current_transport_mode == "driving")

        # 显示/隐藏途径点容器（仅驾车模式且有途径点时显示）
        is_driving = self.current_transport_mode == "driving"
        has_waypoints = len(self.waypoint_widgets) > 0
        self.waypoints_container.setVisible(is_driving and has_waypoints)

        # 更新占位符显示逻辑
        if self.current_transport_mode == "driving":
            # 驾车模式：根据途径点数量决定
            if len(self.waypoint_widgets) == 0:
                # 没有途径点时，添加按钮在右侧垂直居中，起点和终点都不需要占位符
                self.start_spacer.hide()
                self.end_spacer.hide()
            else:
                # 有途径点时，起点需要占位符保持宽度一致，终点不需要（添加按钮在终点右侧）
                self.start_spacer.show()
                self.end_spacer.hide()
        else:
            # 步行和骑行模式：起点和终点都显示占位符
            self.start_spacer.show()
            self.end_spacer.show()

    def _switch_start_end(self):
        """切换起点和终点"""
        start_text = self.start_input.text()
        end_text = self.end_input.text()

        self.start_input.setText(end_text)
        self.end_input.setText(start_text)

    def _add_waypoint(self):
        """添加途径点"""
        # 检查途径点数量限制（最多5个）
        if len(self.waypoint_widgets) >= 5:
            return

        # 创建途径点行
        waypoint_layout = QHBoxLayout()
        waypoint_layout.setSpacing(8)

        # 途径点标签
        waypoint_label = QLabel(f"经{len(self.waypoint_widgets) + 1}")
        waypoint_label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.3);
                color: white;
                font-size: 12px;
                font-weight: bold;
                border-radius: 12px;
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
            }
        """)
        waypoint_label.setAlignment(Qt.AlignCenter)
        waypoint_layout.addWidget(waypoint_label)

        # 途径点输入框
        waypoint_input = QLineEdit()
        waypoint_input.setPlaceholderText(f"请输入途径点{len(self.waypoint_widgets) + 1}")
        waypoint_input.returnPressed.connect(lambda: self._on_search_location("waypoint"))
        waypoint_layout.addWidget(waypoint_input)

        # 删除按钮
        delete_button = QPushButton()
        delete_button.setFixedSize(32, 32)
        delete_button.setToolTip("删除途径点")

        # 加载删除图标
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file)))))
        delete_icon_path = os.path.join(project_root, 'res', 'Delete.png')
        if os.path.exists(delete_icon_path):
            delete_button.setIcon(QIcon(delete_icon_path))
            delete_button.setIconSize(QSize(20, 20))

        # 创建途径点容器widget
        waypoint_widget = QWidget()
        waypoint_widget_layout = QHBoxLayout(waypoint_widget)
        waypoint_widget_layout.setContentsMargins(0, 0, 0, 0)
        waypoint_widget_layout.setSpacing(0)
        waypoint_widget_layout.addLayout(waypoint_layout)

        delete_button.clicked.connect(lambda: self._remove_waypoint(waypoint_widget))

        # 添加到途径点容器
        self.waypoints_layout.addWidget(waypoint_widget)
        self.waypoint_widgets.append({
            'container': waypoint_widget,
            'input': waypoint_input,
            'label': waypoint_label,
            'delete_button': delete_button,
            'delete_layout': waypoint_layout
        })

        # 将删除按钮添加到布局（在输入框右侧）
        waypoint_layout.addWidget(delete_button)

        # 显示途径点容器
        self.waypoints_container.setVisible(True)

        # 更新添加按钮位置
        self._update_add_button_position()

        # 如果达到5个途径点，禁用添加按钮
        if len(self.waypoint_widgets) >= 5:
            self.add_waypoint_button.setEnabled(False)
            self.add_waypoint_button.setToolTip("最多添加5个途径点")

    def _remove_waypoint(self, container):
        """删除途径点"""
        # 找到对应的widget
        for i, widget_dict in enumerate(self.waypoint_widgets):
            if widget_dict['container'] == container:
                # 从父布局中移除并删除容器
                self.waypoints_layout.removeWidget(container)
                container.deleteLater()

                # 从列表中移除
                self.waypoint_widgets.pop(i)

                # 重新编号
                self._renumber_waypoints()

                # 如果没有途径点了，隐藏途径点容器
                if len(self.waypoint_widgets) == 0:
                    self.waypoints_container.setVisible(False)

                # 更新添加按钮位置
                self._update_add_button_position()

                # 重新启用添加按钮（如果之前被禁用）
                if len(self.waypoint_widgets) < 5:
                    self.add_waypoint_button.setEnabled(True)
                    self.add_waypoint_button.setToolTip("添加途径点")

                break

    def _renumber_waypoints(self):
        """重新编号途径点"""
        for i, widget_dict in enumerate(self.waypoint_widgets):
            widget_dict['label'].setText(f"经{i + 1}")
            widget_dict['input'].setPlaceholderText(f"请输入途径点{i + 1}")

    def _update_add_button_position(self):
        """更新添加途径点按钮的位置"""
        if len(self.waypoint_widgets) == 0:
            # 没有途径点时，添加按钮在主容器右侧垂直居中
            # 先从终点行移除（如果存在）
            if self.end_layout.indexOf(self.add_waypoint_button) >= 0:
                self.end_layout.removeWidget(self.add_waypoint_button)

            # 驾车模式下，起点和终点都不显示占位符（添加按钮在右侧垂直居中）
            # 步行和骑行模式下，终点显示占位符
            if self.current_transport_mode == "driving":
                self.start_spacer.hide()
                self.end_spacer.hide()
            else:
                self.end_spacer.show()

            # 添加到主容器右侧
            if self.main_locations_layout.indexOf(self.add_waypoint_button) < 0:
                self.main_locations_layout.addWidget(self.add_waypoint_button, 0, Qt.AlignVCenter)
        else:
            # 有途径点时，将添加按钮移到终点输入框右侧
            # 先从主容器移除（如果存在）
            if self.main_locations_layout.indexOf(self.add_waypoint_button) >= 0:
                self.main_locations_layout.removeWidget(self.add_waypoint_button)

            # 驾车模式下，起点显示占位符保持宽度一致，终点隐藏（添加按钮占据了这个位置）
            self.start_spacer.show()
            self.end_spacer.hide()

            # 添加到终点行（替换占位符位置）
            if self.end_layout.indexOf(self.add_waypoint_button) < 0:
                # 移除占位符
                self.end_layout.removeWidget(self.end_spacer)
                # 添加按钮
                self.end_layout.addWidget(self.add_waypoint_button)
                # 重新添加占位符（保持在最后）
                self.end_layout.addWidget(self.end_spacer)

    def _on_search_location(self, location_type: str):
        """搜索地点"""
        if location_type == "start":
            text = self.start_input.text().strip()
        elif location_type == "end":
            text = self.end_input.text().strip()
        else:  # waypoint
            # 找到当前焦点的输入框
            focused_widget = self.focusWidget()
            if isinstance(focused_widget, QLineEdit):
                text = focused_widget.text().strip()
            else:
                return

        if text:
            self.search_location_clicked.emit(text, location_type)

    def _on_plan_route(self):
        """规划路线"""
        start = self.start_input.text().strip()
        end = self.end_input.text().strip()

        if not start or not end:
            return

        # 获取途径点
        waypoints = []
        for widget_dict in self.waypoint_widgets:
            waypoint_text = widget_dict['input'].text().strip()
            if waypoint_text:
                waypoints.append(waypoint_text)

        # 发送信号
        self.plan_route_clicked.emit(start, end, self.current_transport_mode, waypoints)

    def _on_clear_route(self):
        """清除路线"""
        # 清空起点和终点
        self.start_input.clear()
        self.end_input.clear()

        # 清空所有途径点
        while self.waypoint_widgets:
            widget_dict = self.waypoint_widgets[0]
            self._remove_waypoint(widget_dict['layout'])

    def _on_history_clicked(self, item: QListWidgetItem):
        """点击历史记录"""
        history_data = item.data(Qt.UserRole)
        if history_data:
            self.history_selected.emit(history_data)

    def set_start_location(self, text: str):
        """设置起点"""
        self.start_input.setText(text)

    def set_end_location(self, text: str):
        """设置终点"""
        self.end_input.setText(text)

    def load_history(self, history_list: list):
        """加载历史记录"""
        self.history_list.clear()

        for record in history_list:
            start = record.get('start', '')
            end = record.get('end', '')
            mode = record.get('mode', 'driving')

            # 创建列表项
            item_text = f"{start} → {end}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, record)

            self.history_list.addItem(item)
