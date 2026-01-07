"""
面板工厂
负责创建各种UI面板
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QListWidget, QComboBox,
                             QGroupBox, QTimeEdit, QScrollArea, QProgressBar)
from PyQt5.QtCore import QTime


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

        # 结果列表
        result_list = QListWidget()
        result_list.setMaximumHeight(40)
        result_list.itemClicked.connect(lambda item: parent.select_location(item, location_type))
        layout.addWidget(result_list)

        group.setLayout(layout)

        # 保存到父对象
        setattr(parent, f"{location_type}_input", search_input)
        setattr(parent, f"{location_type}_list", result_list)

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

        # 删除按钮
        remove_button = QPushButton("删除选中的途径点")
        remove_button.clicked.connect(parent.remove_waypoint)
        layout.addWidget(remove_button)

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
        创建时间设置组

        Args:
            parent: 父窗口对象

        Returns:
            QGroupBox: 组件
        """
        group = QGroupBox("时间设置")
        layout = QVBoxLayout()

        # 起始时间
        start_time_layout = QHBoxLayout()
        start_time_layout.addWidget(QLabel("起始时间:"))
        start_time_edit = QTimeEdit()
        start_time_edit.setTime(QTime(8, 0))
        start_time_edit.timeChanged.connect(parent.calculate_times)
        start_time_layout.addWidget(start_time_edit)
        layout.addLayout(start_time_layout)

        # 经历时间
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("经历时间:"))
        duration_time_edit = QTimeEdit()
        duration_time_edit.setTime(QTime(1, 0))
        duration_time_edit.timeChanged.connect(parent.calculate_times)
        duration_layout.addWidget(duration_time_edit)
        layout.addLayout(duration_layout)

        # 结束时间
        end_time_layout = QHBoxLayout()
        end_time_layout.addWidget(QLabel("结束时间:"))
        end_time_edit = QTimeEdit()
        end_time_edit.setTime(QTime(9, 0))
        end_time_edit.timeChanged.connect(parent.calculate_times)
        end_time_layout.addWidget(end_time_edit)
        layout.addLayout(end_time_layout)

        group.setLayout(layout)

        # 保存到父对象
        parent.start_time_edit = start_time_edit
        parent.duration_time_edit = duration_time_edit
        parent.end_time_edit = end_time_edit

        return group

    @staticmethod
    def create_progress_bar():
        """
        创建进度条

        Returns:
            QProgressBar: 进度条组件
        """
        from .styles import UIStyles

        progress_bar = QProgressBar()
        progress_bar.setMaximum(100)
        progress_bar.setMinimum(0)
        progress_bar.setValue(0)
        progress_bar.setTextVisible(False)
        progress_bar.setVisible(True)
        progress_bar.setFixedHeight(20)
        progress_bar.setStyleSheet(UIStyles.PROGRESS_BAR)

        return progress_bar
