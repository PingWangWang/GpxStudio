"""
布局管理器
负责处理应用程序的整体布局逻辑
"""

from PyQt5.QtWidgets import QSplitter
from PyQt5.QtCore import Qt


class LayoutManager:
    """布局管理器，负责处理应用程序的整体布局"""
    
    # 面板尺寸配置
    PANEL_SIZES = [320, 220, 350]
    PANEL_STRETCH_FACTORS = [1, 1, 3]
    
    @staticmethod
    def setup_layout(splitter):
        """
        设置分割器的布局
        
        Args:
            splitter: QSplitter对象
        """
        # 设置拉伸因子
        splitter.setStretchFactor(0, LayoutManager.PANEL_STRETCH_FACTORS[0])
        splitter.setStretchFactor(1, LayoutManager.PANEL_STRETCH_FACTORS[1])
        splitter.setStretchFactor(2, LayoutManager.PANEL_STRETCH_FACTORS[2])
        
        # 设置初始尺寸分配
        splitter.setSizes(LayoutManager.PANEL_SIZES)
    
    @staticmethod
    def get_panel_sizes():
        """
        获取面板尺寸配置
        
        Returns:
            list: 面板尺寸列表
        """
        return LayoutManager.PANEL_SIZES
    
    @staticmethod
    def get_stretch_factors():
        """
        获取面板拉伸因子配置
        
        Returns:
            list: 拉伸因子列表
        """
        return LayoutManager.PANEL_STRETCH_FACTORS
