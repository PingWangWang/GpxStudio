"""
面板工厂模块
负责创建应用程序中使用的各种UI面板组件

这个模块定义了PanelFactory类，提供了一系列静态方法来创建不同功能的UI面板，
包括地点搜索组、途经点组、交通方式组、时间设置组和进度条等。
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QListWidget, QComboBox,
                             QGroupBox, QTimeEdit, QScrollArea, QProgressBar,
                             QSizePolicy)
from PyQt5.QtCore import QTime, QDateTime, Qt

from .time_date_panel import DateSelectPanel, TimeSelectPanel


class PanelFactory:
    """面板工厂，负责创建各种UI面板"""

    @staticmethod
    def create_location_group(title, location_type, parent):
        """
        创建地点搜索组（起点/终点）

        生成包含搜索框、搜索按钮和地址显示区域的地点搜索组组件。
        支持起点和终点两种类型的地点搜索。

        参数:
            title: 组标题，显示在组件顶部
            location_type: 类型标识（start/end），用于标识是起点还是终点
            parent: 父窗口对象，用于连接信号和槽

        返回:
            QGroupBox: 创建好的地点搜索组组件
        """
        group = QGroupBox(title)
        layout = QVBoxLayout()

        # 搜索框
        search_layout = QHBoxLayout()
        search_input = QLineEdit()
        search_input.setPlaceholderText(f"搜索{title}...")
        search_input.returnPressed.connect(lambda: parent.search_location(location_type))

        search_button = QPushButton("搜索")
        search_button.setToolTip("搜索地点")
        search_button.clicked.connect(lambda: parent.search_location(location_type))

        search_layout.addWidget(search_input)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)

        # 自定义地址展示控件，解决滚动条遮挡问题
        address_container = QWidget()
        address_container.setMaximumHeight(40)
        # 确保容器能够随面板宽度扩展
        address_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        address_layout = QHBoxLayout(address_container)
        # 设置布局边距，使地址展示框与搜索框左侧对齐
        address_layout.setContentsMargins(0, 0, 0, 0)
        address_layout.setSpacing(0)

        # 地址显示框，使用QLineEdit实现省略号功能
        address_line_edit = QLineEdit()
        address_line_edit.setReadOnly(True)
        # 设置文本对齐方式为左对齐
        address_line_edit.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        # 设置省略号模式（右侧省略）
        address_line_edit.setPlaceholderText("未选择地址")
        # 使用PyQt5的CSS样式
        address_line_edit.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #cccccc;
                padding: 5px 10px;
                font-size: 9pt;
            }
        """)
        # 设置固定高度确保文本不会换行
        address_line_edit.setFixedHeight(30)
        # 允许标签收缩
        address_line_edit.setMinimumWidth(0)
        # 确保标签能够适当扩展并随面板宽度变化
        address_line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # 移除最大宽度限制，让文本框与panel等宽
        # address_line_edit.setMaximumWidth(250)
        address_layout.addWidget(address_line_edit)

        # 保存到父对象
        setattr(parent, f"{location_type}_label", address_line_edit)

        layout.addWidget(address_container)

        group.setLayout(layout)

        # 保存到父对象
        setattr(parent, f"{location_type}_input", search_input)
        setattr(parent, f"{location_type}_label", address_line_edit)
        setattr(parent, f"{location_type}_address_display", address_container)

        return group

    @staticmethod
    def create_waypoint_group(parent):
        """
        创建途经点组

        生成包含搜索框、已添加途径点列表和操作按钮的途经点组组件。
        允许用户搜索、添加、删除和清空途经点。

        参数:
            parent: 父窗口对象，用于连接信号和槽

        返回:
            QGroupBox: 创建好的途经点组组件
        """
        group = QGroupBox("途径点")
        layout = QVBoxLayout()

        # 搜索框
        search_layout = QHBoxLayout()
        waypoint_input = QLineEdit()
        waypoint_input.setPlaceholderText("搜索途径点...")
        waypoint_input.returnPressed.connect(parent.search_waypoint)

        search_button = QPushButton("搜索")
        search_button.setToolTip("搜索地点")
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
        remove_button.setToolTip("删除选中的途径点")
        remove_button.clicked.connect(parent.remove_waypoint)
        button_layout.addWidget(remove_button)

        # 清空所有按钮
        clear_all_button = QPushButton("清空所有途径点")
        clear_all_button.setToolTip("清空所有途径点")
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

        生成包含交通方式选择下拉框的交通方式组组件。
        支持步行、骑行和驾车三种交通方式。

        参数:
            parent: 父窗口对象，用于保存组件引用

        返回:
            QGroupBox: 创建好的交通方式组组件
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
        创建时间设置组

        生成包含起始时间选择、经历时间输入和结束时间显示的时间设置组组件。
        支持日期和时间的选择，并能根据起始时间和经历小时自动计算结束时间。

        参数:
            parent: 父窗口对象，用于连接信号和槽以及保存组件引用

        返回:
            QGroupBox: 创建好的时间设置组组件
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
        parent.start_date_button.setToolTip("选择出发日期")
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
        parent.start_time_button.setToolTip("选择出发时间")
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

        # 添加一个与"结束时间:"标签宽度相同的空白标签，使文本框与结束时间文本框对齐
        blank_label = QLabel("         ")  # 调整空格数量使宽度匹配"结束时间:"标签
        start_display_layout.addWidget(blank_label)

        # 使用只读文本框显示起始时间
        parent.start_time_display = QLineEdit()
        initial_start_time = QDateTime.currentDateTime()
        parent.start_time_display.setText(initial_start_time.toString("yyyy-MM-dd HH:mm"))
        parent.start_time_display.setReadOnly(True)
        # 移除固定宽度，使用动态宽度
        # parent.start_time_display.setFixedWidth(199)
        parent.start_time_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
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
        end_time_label = QLabel("结束时间:")
        end_time_layout.addWidget(end_time_label)

        # 使用只读文本框显示结束时间
        parent.end_time_display = QLineEdit()
        initial_end_time = QDateTime.currentDateTime().addSecs(3600)
        parent.end_time_display.setText(initial_end_time.toString("yyyy-MM-dd HH:mm"))
        parent.end_time_display.setReadOnly(True)
        # 移除固定宽度，使用动态宽度
        # parent.end_time_display.setFixedWidth(199)
        parent.end_time_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
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
        创建进度条组件

        生成一个样式化的进度条，用于显示搜索、路线规划等操作的进度。

        返回:
            QProgressBar: 创建好的进度条组件
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
