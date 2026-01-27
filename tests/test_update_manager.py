"""
UpdateManager 单元测试
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import sys
from datetime import datetime

# 添加项目根目录和src目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

# 导入前先设置 Qt::AA_ShareOpenGLContexts 属性
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
app = QApplication([])

from app.managers.update_manager import UpdateManager
from ui.popups.update_popup import UpdatePopup, CustomMessageDialog


class TestUpdateManager(unittest.TestCase):
    """
    测试 UpdateManager 类的单元测试
    """

    def setUp(self):
        """
        设置测试环境
        """
        self.logger = Mock()
        self.config_manager = Mock()
        self.config_manager.get.return_value = []
        self.config_manager.set = Mock()
        self.current_version = "2.0.0"
        self.update_manager = UpdateManager(
            current_version=self.current_version,
            logger=self.logger,
            config_manager=self.config_manager
        )

    def test_init(self):
        """
        测试初始化方法
        """
        self.assertEqual(self.update_manager.current_version, self.current_version)
        self.assertEqual(self.update_manager.logger, self.logger)
        self.assertEqual(self.update_manager.config_manager, self.config_manager)
        self.assertEqual(self.update_manager.repo_owner, "GpxStudio")
        self.assertEqual(self.update_manager.repo_name, "GpxStudio")
        self.assertEqual(self.update_manager.api_url, "https://api.github.com/repos/GpxStudio/GpxStudio/releases/latest")
        self.assertEqual(self.update_manager.skip_versions, [])

    def test_is_new_version(self):
        """
        测试版本比较方法
        """
        # 测试新版本
        self.assertTrue(self.update_manager._is_new_version("2.0.1"))
        self.assertTrue(self.update_manager._is_new_version("2.1.0"))
        self.assertTrue(self.update_manager._is_new_version("3.0.0"))

        # 测试相同版本
        self.assertFalse(self.update_manager._is_new_version("2.0.0"))

        # 测试旧版本
        self.assertFalse(self.update_manager._is_new_version("1.9.9"))
        self.assertFalse(self.update_manager._is_new_version("1.0.0"))

    def test_skip_version(self):
        """
        测试跳过版本方法
        """
        version_to_skip = "2.0.1"
        self.update_manager.skip_version(version_to_skip)
        self.assertIn(version_to_skip, self.update_manager.skip_versions)
        self.config_manager.set.assert_called_with("update", "skip_versions", [version_to_skip])

    def test_load_skip_versions(self):
        """
        测试加载跳过版本列表方法
        """
        # 测试有配置管理器的情况
        expected_versions = ["2.0.1", "2.0.2"]
        self.config_manager.get.return_value = expected_versions
        skip_versions = self.update_manager._load_skip_versions()
        self.assertEqual(skip_versions, expected_versions)

        # 测试无配置管理器的情况
        self.update_manager.config_manager = None
        skip_versions = self.update_manager._load_skip_versions()
        self.assertEqual(skip_versions, [])

        # 测试配置管理器异常的情况
        self.update_manager.config_manager = self.config_manager
        self.config_manager.get.side_effect = Exception("Config error")
        skip_versions = self.update_manager._load_skip_versions()
        self.assertEqual(skip_versions, [])

    @patch('requests.get')
    def test_check_for_updates_no_update(self, mock_get):
        """
        测试检查更新方法 - 无新版本
        """
        # 模拟响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "tag_name": "v2.0.0",
            "published_at": "2026-01-26T00:00:00Z",
            "body": "发布说明"
        }
        mock_get.return_value = mock_response

        # 模拟信号
        self.update_manager.update_available = Mock()
        self.update_manager.update_error = Mock()

        # 调用方法
        self.update_manager.check_for_updates()

        # 验证结果
        self.update_manager.update_available.assert_not_called()
        self.update_manager.update_error.assert_not_called()

    @patch('requests.get')
    def test_check_for_updates_with_update(self, mock_get):
        """
        测试检查更新方法 - 有新版本
        """
        # 模拟响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "tag_name": "v2.0.1",
            "published_at": "2026-01-26T00:00:00Z",
            "body": "发布说明"
        }
        mock_get.return_value = mock_response

        # 模拟信号
        self.update_manager.update_available = Mock()
        self.update_manager.update_available.emit = Mock()
        self.update_manager.update_error = Mock()
        self.update_manager.update_error.emit = Mock()

        # 调用方法
        self.update_manager.check_for_updates()

        # 验证结果
        self.update_manager.update_available.emit.assert_called_once_with("2.0.1", "发布说明")
        self.update_manager.update_error.emit.assert_not_called()

    @patch('requests.get')
    def test_check_for_updates_skipped_version(self, mock_get):
        """
        测试检查更新方法 - 跳过版本
        """
        # 添加跳过的版本
        self.update_manager.skip_version("2.0.1")

        # 模拟响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "tag_name": "v2.0.1",
            "published_at": "2026-01-26T00:00:00Z",
            "body": "发布说明"
        }
        mock_get.return_value = mock_response

        # 模拟信号
        self.update_manager.update_available = Mock()
        self.update_manager.update_available.emit = Mock()
        self.update_manager.update_error = Mock()
        self.update_manager.update_error.emit = Mock()

        # 调用方法
        self.update_manager.check_for_updates()

        # 验证结果
        self.update_manager.update_available.emit.assert_not_called()
        self.update_manager.update_error.emit.assert_not_called()

    @patch('requests.get')
    def test_check_for_updates_request_error(self, mock_get):
        """
        测试检查更新方法 - 请求错误
        """
        # 模拟请求错误
        mock_get.side_effect = Exception("Request error")

        # 模拟信号
        self.update_manager.update_available = Mock()
        self.update_manager.update_available.emit = Mock()
        self.update_manager.update_error = Mock()
        self.update_manager.update_error.emit = Mock()

        # 调用方法
        self.update_manager.check_for_updates()

        # 验证结果
        self.update_manager.update_available.emit.assert_not_called()
        self.update_manager.update_error.emit.assert_called_once()

    @patch('requests.get')
    def test_download_update(self, mock_get):
        """
        测试下载更新方法
        """
        # 模拟临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 模拟响应
            mock_response = Mock()
            mock_response.json.return_value = {
                "assets": [
                    {
                        "name": "GPXStudio-2.0.1.exe",
                        "browser_download_url": "https://github.com/GpxStudio/GpxStudio/releases/download/v2.0.1/GPXStudio-2.0.1.exe"
                    }
                ]
            }
            mock_get.return_value = mock_response

            # 模拟文件下载
            mock_download_response = Mock()
            mock_download_response.iter_content.return_value = [b"fake content"]
            mock_download_response.headers.get.return_value = "12"
            mock_get.side_effect = [mock_response, mock_download_response]

            # 模拟信号
            self.update_manager.update_progress = Mock()
            self.update_manager.update_progress.emit = Mock()
            self.update_manager.update_downloaded = Mock()
            self.update_manager.update_downloaded.emit = Mock()
            self.update_manager.update_error = Mock()
            self.update_manager.update_error.emit = Mock()

            # 模拟 QProgressDialog
            with patch('app.managers.update_manager.QProgressDialog') as mock_progress_dialog:
                mock_dialog = Mock()
                mock_dialog.wasCanceled.return_value = False
                # 模拟 exec_ 方法立即返回，不阻塞
                mock_dialog.exec_.return_value = 0
                mock_progress_dialog.return_value = mock_dialog

                # 模拟下载线程
                with patch('threading.Thread') as mock_thread:
                    # 模拟线程立即执行
                    mock_thread_instance = Mock()
                    mock_thread.return_value = mock_thread_instance

                    # 调用方法
                    self.update_manager.download_update("2.0.1")

                    # 验证线程被创建和启动
                    mock_thread.assert_called_once()
                    mock_thread_instance.daemon = True
                    mock_thread_instance.start.assert_called_once()

    @patch('os.path.exists')
    @patch('subprocess.Popen')
    def test_install_update(self, mock_popen, mock_exists):
        """
        测试安装更新方法
        """
        # 模拟文件存在
        mock_exists.return_value = True

        # 模拟 QApplication
        with patch('app.managers.update_manager.QApplication') as mock_app:
            mock_app.quit = Mock()

            # 调用方法
            download_path = "fake/path/GPXStudio-2.0.1.exe"
            self.update_manager.install_update(download_path)

            # 验证结果
            mock_popen.assert_called_once_with([download_path])
            mock_app.quit.assert_called_once()

    @patch('os.path.exists')
    def test_install_update_file_not_exists(self, mock_exists):
        """
        测试安装更新方法 - 文件不存在
        """
        # 模拟文件不存在
        mock_exists.return_value = False

        # 模拟信号
        self.update_manager.update_error = Mock()
        self.update_manager.update_error.emit = Mock()

        # 调用方法
        download_path = "fake/path/GPXStudio-2.0.1.exe"
        self.update_manager.install_update(download_path)

        # 验证结果
        self.update_manager.update_error.emit.assert_called_once_with("更新文件不存在")


if __name__ == '__main__':
    unittest.main()
