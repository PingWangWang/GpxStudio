"""
布局管理器模块
负责处理应用程序的整体布局逻辑，包括面板尺寸和拉伸因子的配置。

这个模块定义了LayoutManager类，用于管理应用程序中的三个主要面板（左侧控制面板、中间搜索结果面板和右侧地图面板）的布局。
"""

from PyQt5.QtWidgets import QSplitter
from PyQt5.QtCore import Qt


class LayoutManager:
    """
    布局管理器类

    负责管理应用程序的整体布局，特别是三个主要面板的尺寸和拉伸因子。
    采用静态方法设计，方便在应用程序的任何地方调用布局相关的功能。
    """

    # 面板尺寸配置 - 定义三个面板的初始宽度
    # 顺序：左侧面板、中间面板、右侧面板
    PANEL_SIZES = [200, 200, 400]

    # 面板拉伸因子配置 - 定义面板在窗口大小变化时的伸缩比例
    # 顺序：左侧面板、中间面板、右侧面板
    # 值越大，面板在窗口拉伸时获得的额外空间越多
    PANEL_STRETCH_FACTORS = [1, 1, 3]

    @staticmethod
    def setup_layout(splitter):
        """
        设置分割器的布局

        配置分割器的拉伸因子和初始尺寸分配，确保面板按照预期的方式布局。

        参数:
            splitter: QSplitter对象，包含了应用程序的三个主要面板
        """
        # 设置拉伸因子，控制面板在窗口大小变化时的伸缩比例
        splitter.setStretchFactor(0, LayoutManager.PANEL_STRETCH_FACTORS[0])  # 左侧面板
        splitter.setStretchFactor(1, LayoutManager.PANEL_STRETCH_FACTORS[1])  # 中间面板
        splitter.setStretchFactor(2, LayoutManager.PANEL_STRETCH_FACTORS[2])  # 右侧面板

        # 设置面板的初始尺寸分配
        splitter.setSizes(LayoutManager.PANEL_SIZES)

    @staticmethod
    def get_panel_sizes():
        """
        获取面板尺寸配置

        返回定义的三个面板的初始宽度列表。

        返回:
            list: 面板尺寸列表，包含三个整数值，分别对应左侧、中间和右侧面板的初始宽度
        """
        return LayoutManager.PANEL_SIZES

    @staticmethod
    def get_stretch_factors():
        """
        获取面板拉伸因子配置

        返回定义的三个面板的拉伸因子列表。

        返回:
            list: 拉伸因子列表，包含三个整数值，分别对应左侧、中间和右侧面板的拉伸比例
        """
        return LayoutManager.PANEL_STRETCH_FACTORS
