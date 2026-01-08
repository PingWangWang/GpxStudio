"""
UI模块
包含面板创建和样式定义
"""

from .styles import UIStyles
from .panels import PanelFactory
from .scale_panel import ScalePanel

__all__ = ['UIStyles', 'PanelFactory', 'ScalePanel']
