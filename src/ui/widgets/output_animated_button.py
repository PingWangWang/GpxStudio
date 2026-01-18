"""
OutPut动画按钮组件
实现文件夹下载图标的动画效果
"""

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath
from PyQt5.QtSvg import QSvgRenderer
from core.resource_path import resource_path
import os


class OutputAnimatedButton(QPushButton):
    """OutPut动画按钮 - 文件夹下载动画"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        
        # 动画状态
        self._animation_progress = 0.0
        self._is_animating = False
        
        # 加载SVG渲染器
        self.svg_renderer = None
        self._load_svg()
        
        # 创建动画
        self.animation = QPropertyAnimation(self, b"animationProgress")
        self.animation.setDuration(500)  # 0.5秒
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # 设置按钮样式
        self.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
            }
        """)
    
    def _load_svg(self):
        """加载SVG文件"""
        svg_path = resource_path('res/icons/OutPut.svg')
        if os.path.exists(svg_path):
            self.svg_renderer = QSvgRenderer(svg_path)
            print(f"[OutPut按钮] 成功加载SVG: {svg_path}")
        else:
            print(f"[OutPut按钮] SVG文件不存在: {svg_path}")
    
    @pyqtProperty(float)
    def animationProgress(self):
        """动画进度属性"""
        return self._animation_progress
    
    @animationProgress.setter
    def animationProgress(self, value):
        """设置动画进度"""
        self._animation_progress = value
        self.update()  # 触发重绘
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        super().enterEvent(event)
        self.start_animation()
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        super().leaveEvent(event)
        self.stop_animation()
    
    def start_animation(self):
        """开始动画"""
        if self._is_animating:
            return
        
        self._is_animating = True
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()
    
    def stop_animation(self):
        """停止动画"""
        if not self._is_animating:
            return
        
        self._is_animating = False
        self.animation.setStartValue(self._animation_progress)
        self.animation.setEndValue(0.0)
        self.animation.start()
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 获取绘制区域
        rect = self.rect()
        size = min(rect.width(), rect.height()) - 4  # 留出边距
        x = (rect.width() - size) // 2
        y = (rect.height() - size) // 2
        
        # 设置颜色 - 统一的深色 (32,32,32)
        color = QColor(32, 32, 32)
        painter.setPen(QPen(color, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QBrush(Qt.NoBrush))
        
        # 绘制文件夹
        self._draw_folder(painter, x, y, size)
        
        # 绘制下载箭头（带动画）
        self._draw_download_arrow(painter, x, y, size)
    
    def _draw_folder(self, painter, x, y, size):
        """绘制文件夹"""
        # 文件夹主体路径
        folder_path = QPainterPath()
        
        # 文件夹尺寸
        folder_width = size * 0.8
        folder_height = size * 0.6
        folder_x = x + (size - folder_width) / 2
        folder_y = y + size * 0.2
        
        # 文件夹标签
        tab_width = folder_width * 0.35
        tab_height = size * 0.15
        
        # 绘制文件夹标签
        folder_path.moveTo(folder_x, folder_y)
        folder_path.lineTo(folder_x + tab_width * 0.7, folder_y)
        folder_path.lineTo(folder_x + tab_width, folder_y - tab_height)
        folder_path.lineTo(folder_x + folder_width, folder_y - tab_height)
        folder_path.lineTo(folder_x + folder_width, folder_y + folder_height - tab_height)
        folder_path.lineTo(folder_x, folder_y + folder_height - tab_height)
        folder_path.closeSubpath()
        
        painter.drawPath(folder_path)
    
    def _draw_download_arrow(self, painter, x, y, size):
        """绘制下载箭头（带动画）"""
        # 箭头位置（在文件夹中央）
        arrow_x = x + size / 2
        arrow_y = y + size * 0.4
        
        # 根据动画进度计算Y偏移
        # 动画效果：箭头上下移动
        y_offset = self._animation_progress * 2  # 最大移动2像素
        arrow_y += y_offset
        
        # 绘制垂直线
        line_length = size * 0.25
        painter.drawLine(int(arrow_x), int(arrow_y), int(arrow_x), int(arrow_y + line_length))
        
        # 绘制箭头头部
        arrow_size = size * 0.08
        arrow_tip_y = arrow_y + line_length
        
        # 左箭头线
        painter.drawLine(
            int(arrow_x), int(arrow_tip_y),
            int(arrow_x - arrow_size), int(arrow_tip_y - arrow_size)
        )
        
        # 右箭头线
        painter.drawLine(
            int(arrow_x), int(arrow_tip_y),
            int(arrow_x + arrow_size), int(arrow_tip_y - arrow_size)
        )