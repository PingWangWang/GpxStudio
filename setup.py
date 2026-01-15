from setuptools import setup, find_packages
import os
import sys

# 添加项目根目录和src目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), 'src'))

# 导入统一版本号
from version import __version__

setup(
    name="GPXStudio",
    version=__version__,
    packages=find_packages(where='src', exclude=['tests*', 'tests.*', 'docs*', 'scripts*']),
    install_requires=[
        "PyQt5",
        "folium",
        "requests",
        "geopy",
        "gpxpy",
        "injector",
    ],
)
