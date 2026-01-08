"""
地图缩放比例尺显示组件
显示当前地图的缩放级别和比例尺信息
"""

from typing import Optional
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import pyqtSignal


class ScalePanel(QWidget):
    """地图缩放比例尺显示面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 标题
        title_label = QLabel("地图缩放:")
        title_label.setStyleSheet("font-weight: bold; color: #333333;")
        title_label.setToolTip("显示当前地图的缩放级别和比例尺信息")
        layout.addWidget(title_label)

        # 缩放级别显示
        self.zoom_label = QLabel("级别: -")
        self.zoom_label.setStyleSheet("color: #666666;")
        self.zoom_label.setToolTip("地图缩放级别：数字越大，地图显示越详细\n范围：3-18（3为国家级，18为建筑级）")
        layout.addWidget(self.zoom_label)

        # 分隔符
        separator = QLabel("|")
        separator.setStyleSheet("color: #cccccc;")
        layout.addWidget(separator)

        # 比例尺显示
        self.scale_label = QLabel("比例: -")
        self.scale_label.setStyleSheet("color: #666666;")
        self.scale_label.setToolTip("地图比例尺：表示地图上的距离与实际距离的比值\n例如 1:50,000 表示地图上1厘米代表实际50,000厘米(500米)")
        layout.addWidget(self.scale_label)

        layout.addStretch()

        # 设置面板样式
        self.setStyleSheet("""
            ScalePanel {
                background-color: #f9f9f9;
                border: 1px solid #dddddd;
                border-radius: 3px;
            }
        """)

    def update_zoom(self, zoom_level: int):
        """
        更新缩放级别显示

        Args:
            zoom_level: 地图缩放级别 (通常是3-18)
        """
        # 显示级别和说明
        level_description = self._get_level_description(zoom_level)
        self.zoom_label.setText(f"级别: {zoom_level} ({level_description})")

        # 根据缩放级别计算近似比例尺
        # 高德地图在赤道附近，每个缩放级别的比例尺约为：
        # scale = 591657550.5 / (2^zoom) 米/像素
        # 这里假设屏幕宽度约为1920像素
        scale_meters_per_pixel = 591657550.5 / (2 ** zoom_level)

        # 根据比例尺大小选择合适的单位显示
        if scale_meters_per_pixel > 1000:
            scale_km = scale_meters_per_pixel / 1000
            if scale_km > 1000:
                scale_text = f"约 1:{int(scale_km * 1000):,}"
            else:
                scale_text = f"约 1:{int(scale_km * 1000):,}"
        else:
            scale_text = f"约 1:{int(scale_meters_per_pixel * 1000):,}"

        self.scale_label.setText(f"比例: {scale_text}")

    def _get_level_description(self, zoom_level: int) -> str:
        """
        根据缩放级别返回描述性文字

        Args:
            zoom_level: 地图缩放级别
        level_description = self._get_level_description(zoom_level)
        self.zoom_label.setText(f"级别: {zoom_level} ({level_description})
        Returns:
            描述性文字
        """
        if zoom_level <= 4:
            return "国家级"
        elif zoom_level <= 7:
            return "省级"
        elif zoom_level <= 10:
            return "城市级"
        elif zoom_level <= 13:
            return "区县级"
        elif zoom_level <= 15:
            return "街道级"
        elif zoom_level <= 17:
            return "小区级"
        else:
            return "建筑级"

    def update_scale(self, zoom_level: int, scale_text: Optional[str] = None):
        """
        更新比例尺信息

        Args:
            zoom_level: 地图缩放级别
            scale_text: 自定义比例尺文本（可选）
        """
        self.zoom_label.setText(f"级别: {zoom_level}")

        if scale_text:
            self.scale_label.setText(f"比例: {scale_text}")
        else:
            # 使用默认计算方式
            self.update_zoom(zoom_level)

    def clear(self):
        """清空显示"""
        self.zoom_label.setText("级别: -")
        self.scale_label.setText("比例: -")
