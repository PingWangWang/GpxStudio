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
from PyQt5.QtWidgets import QMessageBox, QApplication

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

    def __init__(self, current_version: str, logger, config_manager=None, main_window=None):
        """
        初始化更新管理器

        Args:
            current_version: 当前软件版本
            logger: 日志记录器
            config_manager: 配置管理器
            main_window: 主窗口对象（用于显示对话框）
        """
        super().__init__()
        self.current_version = current_version
        self.logger = logger
        self.config_manager = config_manager
        self.main_window = main_window
        self.repo_owner = "PingWangWang"  # GitHub 仓库所有者
        self.repo_name = "GpxStudio"  # GitHub 仓库名称
        
        # 多个API地址，按优先级尝试（国内镜像优先）
        self.api_urls = [
            f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest",
            # 可以添加其他镜像地址
        ]
        
        # 下载文件的镜像地址（用于加速）
        self.download_proxies = [
            "",  # 直连
            "https://ghproxy.com/",  # GitHub文件加速
            "https://mirror.ghproxy.com/",  # 备用镜像
        ]
        
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

    def check_for_updates(self, silent: bool = False):
        """
        检查是否有新版本（带重试机制）

        Args:
            silent: 是否静默检查（失败时不发射错误信号）
        """
        try:
            self.logger.info("开始检查更新...")
            
            # 尝试多个API地址
            release_data = None
            last_error = None
            
            for api_url in self.api_urls:
                try:
                    self.logger.info(f"尝试从 {api_url} 获取更新信息...")
                    
                    # 增加重试机制
                    for attempt in range(3):
                        try:
                            response = requests.get(
                                api_url, 
                                timeout=15,  # 增加超时时间
                                headers={
                                    'User-Agent': 'GpxStudio-UpdateChecker',
                                    'Accept': 'application/vnd.github.v3+json'
                                }
                            )
                            response.raise_for_status()
                            release_data = response.json()
                            self.logger.info(f"✅ 成功获取更新信息（尝试 {attempt + 1}/3）")
                            break
                        except requests.Timeout:
                            if attempt < 2:
                                self.logger.warning(f"请求超时，重试 {attempt + 2}/3...")
                                continue
                            raise
                        except requests.RequestException as e:
                            if attempt < 2:
                                self.logger.warning(f"请求失败，重试 {attempt + 2}/3: {e}")
                                continue
                            raise
                    
                    if release_data:
                        break
                        
                except Exception as e:
                    last_error = e
                    self.logger.warning(f"从 {api_url} 获取更新信息失败: {e}")
                    continue
            
            # 如果所有API地址都失败
            if not release_data:
                raise Exception(f"无法连接到更新服务器，请检查网络连接。最后的错误: {last_error}")

            # 提取版本号和发布日期
            latest_version = release_data.get("tag_name", "").lstrip("vV")
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
            if not silent:
                self.update_error.emit(f"检查更新失败: {str(e)}")
        except Exception as e:
            self.logger.error(f"检查更新时发生错误: {e}")
            if not silent:
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
        下载更新（带镜像加速和重试机制）

        Args:
            latest_version: 最新版本号
        """
        try:
            # 获取最新发布信息
            release_data = None
            for api_url in self.api_urls:
                try:
                    response = requests.get(api_url, timeout=15)
                    response.raise_for_status()
                    release_data = response.json()
                    break
                except Exception as e:
                    self.logger.warning(f"从 {api_url} 获取发布信息失败: {e}")
                    continue
            
            if not release_data:
                self.update_error.emit("无法获取版本信息，请检查网络连接")
                return

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

            self.logger.info(f"原始下载地址: {asset_url}")

            # 创建临时文件
            temp_dir = tempfile.gettempdir()
            download_path = os.path.join(temp_dir, f"GPXStudio-{latest_version}.exe")

            # 显示下载进度对话框（使用自定义暗色主题对话框）
            from ui.popups.update_popup import DownloadProgressDialog
            progress_dialog = DownloadProgressDialog(self.main_window)

            # 状态标志
            state = {'canceled': False, 'success': False}

            def on_cancel():
                state['canceled'] = True

            def update_progress(value):
                if not state['canceled']:
                    progress_dialog.set_value(value)

            def close_dialog(*args):
                if not state['canceled'] and state['success']:
                    progress_dialog.accept()

            # 断开信号连接的清理函数
            def cleanup():
                try:
                    self.update_progress.disconnect(update_progress)
                    self.update_downloaded.disconnect(close_dialog)
                    self.update_error.disconnect(close_dialog)
                except Exception:
                    pass

            progress_dialog.canceled.connect(on_cancel)
            progress_dialog.finished.connect(cleanup)

            # 连接信号用于更新UI
            self.update_progress.connect(update_progress)
            self.update_downloaded.connect(close_dialog)
            self.update_error.connect(close_dialog)

            # 下载文件（尝试多个镜像地址）
            def download_file():
                download_success = False
                last_error = None
                
                # 尝试每个代理/镜像
                for proxy_prefix in self.download_proxies:
                    if state['canceled']:
                        return
                    
                    try:
                        # 构建下载URL
                        download_url = f"{proxy_prefix}{asset_url}" if proxy_prefix else asset_url
                        self.logger.info(f"尝试从 {download_url} 下载...")
                        
                        with requests.get(download_url, stream=True, timeout=30) as r:
                            r.raise_for_status()
                            total_size = int(r.headers.get("content-length", 0))
                            downloaded_size = 0

                            with open(download_path, "wb") as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    if state['canceled']:
                                        return
                                    if chunk:
                                        f.write(chunk)
                                        downloaded_size += len(chunk)
                                        if total_size > 0:
                                            progress = int((downloaded_size / total_size) * 100)
                                            self.update_progress.emit(progress)

                        if not state['canceled']:
                            self.logger.info(f"✅ 更新下载完成: {download_path}")
                            state['success'] = True
                            self.update_downloaded.emit(download_path)
                            download_success = True
                            break
                            
                    except Exception as e:
                        last_error = e
                        self.logger.warning(f"从 {proxy_prefix or '直连'} 下载失败: {e}")
                        # 如果不是最后一个镜像，继续尝试下一个
                        if proxy_prefix != self.download_proxies[-1]:
                            continue
                
                # 如果所有镜像都失败
                if not download_success and not state['canceled']:
                    error_msg = f"下载更新失败，已尝试所有镜像地址。最后的错误: {last_error}"
                    self.logger.error(error_msg)
                    self.update_error.emit(error_msg)

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
