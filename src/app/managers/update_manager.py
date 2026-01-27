"""
更新管理器
负责软件更新检测、版本比较、下载和安装
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
from datetime import datetime
from typing import Optional, Dict, Tuple

import requests
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QProgressDialog, QApplication

from core.resource_path import resource_path


class UpdateManager(QObject):
    """
    更新管理器类
    负责软件更新检测、版本比较、下载和安装
    """

    # 信号定义
    update_available = pyqtSignal(str, str)  # 发现新版本信号 (最新版本, 发布日期)
    update_downloaded = pyqtSignal(str)  # 更新下载完成信号 (下载文件路径)
    update_progress = pyqtSignal(int)  # 下载进度信号 (百分比)
    update_error = pyqtSignal(str)  # 更新错误信号 (错误信息)

    def __init__(self, current_version: str, logger, config_manager=None):
        """
        初始化更新管理器

        Args:
            current_version: 当前软件版本
            logger: 日志记录器
            config_manager: 配置管理器
        """
        super().__init__()
        self.current_version = current_version
        self.logger = logger
        self.config_manager = config_manager
        self.repo_owner = "GpxStudio"  # GitHub 仓库所有者
        self.repo_name = "GpxStudio"  # GitHub 仓库名称
        self.api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
        self.skip_versions = self._load_skip_versions()

    def _load_skip_versions(self) -> list:
        """
        加载用户跳过的版本列表

        Returns:
            跳过的版本列表
        """
        try:
            if self.config_manager:
                return self.config_manager.get("update", "skip_versions", [])
            return []
        except Exception as e:
            self.logger.error(f"加载跳过版本列表失败: {e}")
            return []

    def _save_skip_versions(self):
        """
        保存用户跳过的版本列表
        """
        try:
            if self.config_manager:
                self.config_manager.set("update", "skip_versions", self.skip_versions)
        except Exception as e:
            self.logger.error(f"保存跳过版本列表失败: {e}")

    def check_for_updates(self):
        """
        检查是否有新版本
        """
        try:
            self.logger.info("开始检查更新...")
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()
            release_data = response.json()

            # 提取版本号和发布日期
            latest_version = release_data.get("tag_name", "").lstrip("v")
            release_date = release_data.get("published_at", "").split("T")[0]
            release_notes = release_data.get("body", "")

            self.logger.info(f"当前版本: {self.current_version}")
            self.logger.info(f"最新版本: {latest_version}")
            self.logger.info(f"发布日期: {release_date}")

            # 检查是否有新版本
            if self._is_new_version(latest_version) and latest_version not in self.skip_versions:
                self.logger.info("发现新版本!")
                self.update_available.emit(latest_version, release_notes)
            else:
                self.logger.info("当前已是最新版本或版本已被跳过")

        except requests.RequestException as e:
            self.logger.error(f"检查更新失败: {e}")
            self.update_error.emit(f"检查更新失败: {str(e)}")
        except Exception as e:
            self.logger.error(f"检查更新时发生错误: {e}")
            self.update_error.emit(f"检查更新时发生错误: {str(e)}")

    def _is_new_version(self, latest_version: str) -> bool:
        """
        比较版本号，判断是否为新版本

        Args:
            latest_version: 最新版本号

        Returns:
            如果是新版本返回True，否则返回False
        """
        try:
            # 将版本号转换为数字列表进行比较
            current_parts = list(map(int, re.findall(r"\d+", self.current_version)))
            latest_parts = list(map(int, re.findall(r"\d+", latest_version)))

            # 补齐版本号长度
            max_len = max(len(current_parts), len(latest_parts))
            current_parts.extend([0] * (max_len - len(current_parts)))
            latest_parts.extend([0] * (max_len - len(latest_parts)))

            # 比较版本号
            for current, latest in zip(current_parts, latest_parts):
                if latest > current:
                    return True
                elif latest < current:
                    return False
            return False

        except Exception as e:
            self.logger.error(f"版本号比较失败: {e}")
            return False

    def download_update(self, latest_version: str):
        """
        下载更新

        Args:
            latest_version: 最新版本号
        """
        try:
            # 获取最新发布信息
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()
            release_data = response.json()

            # 找到Windows可执行文件
            asset_url = None
            for asset in release_data.get("assets", []):
                if asset.get("name", "").endswith(".exe"):
                    asset_url = asset.get("browser_download_url")
                    break

            if not asset_url:
                self.logger.error("未找到Windows可执行文件")
                self.update_error.emit("未找到Windows可执行文件")
                return

            self.logger.info(f"开始下载更新: {asset_url}")

            # 创建临时文件
            temp_dir = tempfile.gettempdir()
            download_path = os.path.join(temp_dir, f"GPXStudio-{latest_version}.exe")

            # 显示下载进度对话框
            progress_dialog = QProgressDialog("正在下载更新...", "取消", 0, 100)
            progress_dialog.setWindowTitle("下载更新")
            progress_dialog.setMinimumWidth(400)
            progress_dialog.setModal(True)

            # 下载文件
            def download_file():
                try:
                    with requests.get(asset_url, stream=True, timeout=30) as r:
                        r.raise_for_status()
                        total_size = int(r.headers.get("content-length", 0))
                        downloaded_size = 0

                        with open(download_path, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if progress_dialog.wasCanceled():
                                    return
                                if chunk:
                                    f.write(chunk)
                                    downloaded_size += len(chunk)
                                    if total_size > 0:
                                        progress = int((downloaded_size / total_size) * 100)
                                        self.update_progress.emit(progress)
                                        QApplication.processEvents()
                                        progress_dialog.setValue(progress)

                    if not progress_dialog.wasCanceled():
                        self.logger.info(f"更新下载完成: {download_path}")
                        self.update_downloaded.emit(download_path)
                except Exception as e:
                    self.logger.error(f"下载更新失败: {e}")
                    self.update_error.emit(f"下载更新失败: {str(e)}")

            # 在后台线程中下载
            download_thread = threading.Thread(target=download_file)
            download_thread.daemon = True
            download_thread.start()

            # 显示进度对话框
            progress_dialog.exec_()

        except Exception as e:
            self.logger.error(f"下载更新时发生错误: {e}")
            self.update_error.emit(f"下载更新时发生错误: {str(e)}")

    def skip_version(self, version: str):
        """
        跳过指定版本

        Args:
            version: 要跳过的版本号
        """
        if version not in self.skip_versions:
            self.skip_versions.append(version)
            self._save_skip_versions()
            self.logger.info(f"已跳过版本: {version}")

    def install_update(self, download_path: str):
        """
        安装更新

        Args:
            download_path: 下载文件路径
        """
        try:
            self.logger.info(f"开始安装更新: {download_path}")

            # 检查文件是否存在
            if not os.path.exists(download_path):
                self.logger.error(f"更新文件不存在: {download_path}")
                self.update_error.emit("更新文件不存在")
                return

            # 启动新程序并退出当前程序
            subprocess.Popen([download_path])
            QApplication.quit()

        except Exception as e:
            self.logger.error(f"安装更新时发生错误: {e}")
            self.update_error.emit(f"安装更新时发生错误: {str(e)}")
