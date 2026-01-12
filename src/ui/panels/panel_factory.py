"""
面板工厂
负责创建各种UI面板
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QListWidget, QComboBox,
                             QGroupBox, QTimeEdit, QScrollArea, QProgressBar)
from PyQt5.QtCore import QTime, QDateTime

from .time_date_panel import DateSelectPanel, TimeSelectPanel


class PanelFactory:
    """面板工厂，负责创建各种UI面板"""

    @staticmethod
    def create_location_group(title, location_type, parent):
        """
        创建地点搜索组（起点/终点）

        Args:
            title: 组标题
            location_type: 类型标识（start/end）
            parent: 父窗口对象

        Returns:
            QGroupBox: 组件
        """
        group = QGroupBox(title)
        layout = QVBoxLayout()

        # 搜索框
        search_layout = QHBoxLayout()
        search_input = QLineEdit()
        search_input.setPlaceholderText(f"搜索{title}...")
        search_input.returnPressed.connect(lambda: parent.search_location(location_type))

        search_button = QPushButton("搜索")
        search_button.clicked.connect(lambda: parent.search_location(location_type))

        search_layout.addWidget(search_input)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)

        # 自定义地址展示控件，解决滚动条遮挡问题
        address_display = QWidget()
        address_display.setMaximumHeight(40)
        address_layout = QHBoxLayout(address_display)
        address_layout.setContentsMargins(0, 0, 0, 0)
        address_layout.setSpacing(0)
        
        # 地址显示标签
        address_label = QLabel()
        address_label.setStyleSheet("""
            QLabel {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #cccccc;
                padding: 5px 10px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
        """)
        address_layout.addWidget(address_label)
        
        # 保存到父对象
        setattr(parent, f"{location_type}_label", address_label)
        
        layout.addWidget(address_display)

        group.setLayout(layout)

        # 保存到父对象
        setattr(parent, f"{location_type}_input", search_input)
        setattr(parent, f"{location_type}_label", address_label)
        setattr(parent, f"{location_type}_address_display", address_display)

        return group

    @staticmethod
    def create_waypoint_group(parent):
        """
        创建途径点组

        Args:
            parent: 父窗口对象

        Returns:
            QGroupBox: 组件
        """
        group = QGroupBox("途径点")
        layout = QVBoxLayout()

        # 搜索框
        search_layout = QHBoxLayout()
        waypoint_input = QLineEdit()
        waypoint_input.setPlaceholderText("搜索途径点...")
        waypoint_input.returnPressed.connect(parent.search_waypoint)

        search_button = QPushButton("搜索")
        search_button.clicked.connect(parent.search_waypoint)

        search_layout.addWidget(waypoint_input)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)

        # 已添加列表
        layout.addWidget(QLabel("已添加的途径点:"))
        waypoint_list = QListWidget()
        layout.addWidget(waypoint_list)

        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 删除按钮
        remove_button = QPushButton("删除选中的途径点")
        remove_button.clicked.connect(parent.remove_waypoint)
        button_layout.addWidget(remove_button)
        
        # 清空所有按钮
        clear_all_button = QPushButton("清空所有途径点")
        clear_all_button.clicked.connect(parent.clear_all_waypoints)
        button_layout.addWidget(clear_all_button)
        
        layout.addLayout(button_layout)

        group.setLayout(layout)

        # 保存到父对象
        parent.waypoint_input = waypoint_input
        parent.waypoint_list = waypoint_list

        return group

    @staticmethod
    def create_transport_group(parent):
        """
        创建交通方式组

        Args:
            parent: 父窗口对象

        Returns:
            QGroupBox: 组件
        """
        group = QGroupBox("交通方式")
        layout = QVBoxLayout()

        transport_combo = QComboBox()
        transport_combo.addItems(["步行", "骑行", "驾车"])
        transport_combo.setCurrentIndex(2)
        layout.addWidget(transport_combo)

        group.setLayout(layout)

        # 保存到父对象
        parent.transport_combo = transport_combo

        return group

    @staticmethod
    def create_time_group(parent):
        """
        创建时间设置组，包括起始时间、经历时间和结束时间
        """
        group = QGroupBox("时间设置")
        layout = QVBoxLayout()

        # 创建日期和时间选择面板
        parent.date_panel = DateSelectPanel(parent)
        parent.date_panel.hide()

        parent.time_panel = TimeSelectPanel(parent)
        parent.time_panel.hide()

        # 起始时间
        start_time_layout = QVBoxLayout()
        start_time_layout.setSpacing(5)

        # 第一行：提示文字和选择按钮
        start_buttons_layout = QHBoxLayout()
        start_buttons_layout.addWidget(QLabel("起始时间:"))

        # 创建按钮容器，精确控制总宽度
        buttons_container = QWidget()
        buttons_container.setFixedWidth(199)
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setSpacing(6)
        buttons_layout.setContentsMargins(0, 0, 0, 0)

        parent.start_date_button = QPushButton("选择日期")
        parent.start_date_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #000000;
                border: 1px solid #cccccc;
                padding: 6px 8px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        parent.start_date_button.clicked.connect(lambda: parent.show_date_panel("start"))
        buttons_layout.addWidget(parent.start_date_button, 1)

        parent.start_time_button = QPushButton("选择时间")
        parent.start_time_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #000000;
                border: 1px solid #cccccc;
                padding: 6px 8px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        parent.start_time_button.clicked.connect(lambda: parent.show_time_panel("start"))
        buttons_layout.addWidget(parent.start_time_button, 1)

        start_buttons_layout.addWidget(buttons_container)
        start_buttons_layout.addStretch()
        start_time_layout.addLayout(start_buttons_layout)

        # 第二行：使用只读文本框显示起始时间
        start_display_layout = QHBoxLayout()
        # 添加拉伸因子，将文本框推到右侧
        start_display_layout.addStretch()

        parent.start_time_display = QLineEdit()
        initial_start_time = QDateTime.currentDateTime()
        parent.start_time_display.setText(initial_start_time.toString("yyyy-MM-dd HH:mm"))
        parent.start_time_display.setReadOnly(True)
        parent.start_time_display.setFixedWidth(199)
        parent.start_time_display.setStyleSheet("""
            QLineEdit {
                background-color: #f5f5f5;
                color: #000000;
                border: 1px solid #cccccc;
                padding: 4px;
            }
        """)
        start_display_layout.addWidget(parent.start_time_display)
        start_time_layout.addLayout(start_display_layout)
        layout.addLayout(start_time_layout)

        # 经历时间（小时）
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("经历小时:"))
        duration_time_edit = QLineEdit()
        duration_time_edit.setText("1")
        duration_time_edit.setPlaceholderText("请输入小时数")
        duration_time_edit.textChanged.connect(parent.calculate_times)
        duration_layout.addWidget(duration_time_edit)
        duration_layout.addWidget(QLabel("小时"))
        layout.addLayout(duration_layout)

        # 结束时间（只读显示，单行）
        end_time_layout = QHBoxLayout()
        end_time_layout.addWidget(QLabel("结束时间:"))

        # 使用只读文本框显示结束时间
        parent.end_time_display = QLineEdit()
        initial_end_time = QDateTime.currentDateTime().addSecs(3600)
        parent.end_time_display.setText(initial_end_time.toString("yyyy-MM-dd HH:mm"))
        parent.end_time_display.setReadOnly(True)
        parent.end_time_display.setFixedWidth(199)
        parent.end_time_display.setStyleSheet("""
            QLineEdit {
                background-color: #f5f5f5;
                color: #000000;
                border: 1px solid #cccccc;
                padding: 4px;
            }
        """)
        end_time_layout.addWidget(parent.end_time_display)
        layout.addLayout(end_time_layout)

        # 保存到父对象
        parent.duration_time_edit = duration_time_edit

        # 创建隐藏的QDateTime对象来存储完整的日期时间信息
        parent.start_time_edit = type('obj', (object,), {
            'dateTime': lambda *args, **kwargs: QDateTime.fromString(
                parent.start_time_display.text(),
                "yyyy-MM-dd HH:mm"
            ),
            'setDateTime': lambda datetime: parent.start_time_display.setText(datetime.toString("yyyy-MM-dd HH:mm"))
        })

        parent.end_time_edit = type('obj', (object,), {
            'dateTime': lambda *args, **kwargs: QDateTime.fromString(
                parent.end_time_display.text(),
                "yyyy-MM-dd HH:mm"
            ),
            'setDateTime': lambda datetime: parent.end_time_display.setText(datetime.toString("yyyy-MM-dd HH:mm"))
        })

        # 结束时间自动计算，无需手动按钮

        group.setLayout(layout)
        return group

    @staticmethod
    def create_progress_bar():
        """
        创建进度条

        Returns:
            QProgressBar: 进度条组件
        """
        from ui.styles import UIStyles

        progress_bar = QProgressBar()
        progress_bar.setMaximum(100)
        progress_bar.setMinimum(0)
        progress_bar.setValue(0)
        progress_bar.setTextVisible(False)
        progress_bar.setVisible(True)
        progress_bar.setFixedHeight(20)
        progress_bar.setStyleSheet(UIStyles.PROGRESS_BAR)

        return progress_bar
