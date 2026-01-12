#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源路径辅助工具
用于获取打包后的资源文件路径
"""

import os
import sys


def resource_path(relative_path):
    """
    获取资源文件的绝对路径，兼容开发环境和打包环境

    Args:
        relative_path: 相对路径

    Returns:
        str: 资源文件的绝对路径
    """
    try:
        # PyInstaller打包后的路径
        base_path = sys._MEIPASS
    except AttributeError:
        # 开发环境路径
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    return os.path.join(base_path, relative_path)


def get_icon_path():
    """
    获取应用程序图标路径

    Returns:
        str: 图标文件路径
    """
    return resource_path(os.path.join("res", "GPXStudio.png"))


def get_icon_ico_path():
    """
    获取ICO格式图标路径

    Returns:
        str: ICO图标文件路径
    """
    return resource_path(os.path.join("res", "GPXStudio.ico"))