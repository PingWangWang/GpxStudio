from setuptools import setup, find_packages

setup(
    name="GPXStudio",
    version="1.0.0",
    packages=find_packages(where='.', exclude=['tests*', 'tests.*', 'docs*', 'scripts*']),
    install_requires=[
        "PyQt5",
        "folium",
        "requests",
        "geopy",
        "gpxpy",
        "injector",
    ],
)