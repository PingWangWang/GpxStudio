#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置模块初始化文件
"""

from .about_config import AboutConfig
from .map_config import MapConfig

# 创建全局配置对象
about_config = AboutConfig()
map_config = MapConfig()