"""HiddenUIMixin — 隐藏 UI 组件初始化（后台逻辑所需的隐藏 QWidget）"""
from PyQt5.QtWidgets import (QListWidget, QLabel, QLineEdit, QComboBox,
                              QPushButton, QTimeEdit)


class HiddenUIMixin:
    """负责创建在 UI 中不可见、但由后台逻辑使用的隐藏组件。"""

    def _init_hidden_ui_components(self):
        """初始化隐藏的UI组件（用于后台逻辑）"""
        # 创建隐藏的搜索结果列表
        self.search_results_list = QListWidget(self)
        self.search_results_list.itemClicked.connect(self.on_search_result_clicked)
        self.search_results_list.hide()

        # 创建隐藏的搜索结果标题
        self.search_results_title = QLabel("搜索结果", self)
        self.search_results_title.hide()

        # 创建隐藏的任务进度面板
        from ui.panels.task_progress_panel import TaskInfoPanel
        self.task_progress_panel = TaskInfoPanel(self)
        self.task_progress_panel.cancel_task_requested.connect(self._on_cancel_task_requested)
        self.task_progress_panel.hide()

        # 创建隐藏的地图缩放比例尺显示面板
        from ui.panels.scale_panel import ScalePanel
        self.scale_panel = ScalePanel(self)
        self.scale_panel.hide()

        # 创建隐藏的输入框和列表（用于后台逻辑）
        self.start_input = QLineEdit(self)
        self.start_input.hide()
        self.start_label = QLineEdit(self)
        self.start_label.hide()
        self.start_list = QListWidget(self)
        self.start_list.hide()

        self.end_input = QLineEdit(self)
        self.end_input.hide()
        self.end_label = QLineEdit(self)
        self.end_label.hide()
        self.end_list = QListWidget(self)
        self.end_list.hide()

        self.waypoint_input = QLineEdit(self)
        self.waypoint_input.hide()
        self.waypoint_list = QListWidget(self)
        self.waypoint_list.hide()

        # 创建隐藏的交通方式选择框
        self.transport_combo = QComboBox(self)
        self.transport_combo.addItems(["驾车", "步行", "骑行", "公交"])
        self.transport_combo.hide()

        # 创建隐藏的时间编辑器
        from PyQt5.QtCore import QDateTime
        self.start_time_edit = QTimeEdit(self)
        self.start_time_edit.setDateTime(QDateTime.currentDateTime())
        self.start_time_edit.hide()

        self.end_time_edit = QTimeEdit(self)
        self.end_time_edit.setDateTime(QDateTime.currentDateTime())
        self.end_time_edit.hide()

        self.duration_time_edit = QLineEdit(self)
        self.duration_time_edit.hide()

        # 创建隐藏的按钮
        self.plan_button = QPushButton("规划路线", self)
        self.plan_button.clicked.connect(self.on_plan_route_clicked)
        self.plan_button.hide()

        self.export_button = QPushButton("导出GPX", self)
        self.export_button.clicked.connect(self.on_export_gpx_clicked)
        self.export_button.hide()
