"""
更新功能集成测试
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录和src目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

# 导入前先设置 Qt::AA_ShareOpenGLContexts 属性
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QDialog
QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
app = QApplication([])

from app.app import GpxStudio
from app.managers.update_manager import UpdateManager


class TestUpdateIntegration(unittest.TestCase):
    """
    测试更新功能与应用的集成
    """

    def setUp(self):
        """
        设置测试环境
        """
        # 模拟启动画面
        self.splash_screen = Mock()
        self.splash_screen.update_progress = Mock()

    @patch('app.app.QTimer')
    @patch('app.app.SignalManager')
    @patch('app.app.GeolocationHandler')
    @patch('app.app.WindowManager')
    @patch('app.app.ServiceManager')
    @patch('app.app.DataManager')
    @patch('app.app.QApplication')
    def test_start_update_check(self, mock_qapp, mock_data_manager, mock_service_manager, mock_window_manager, mock_geolocation_handler, mock_signal_manager, mock_timer):
        """
        测试应用启动时是否调用 start_update_check 方法
        """
        # 模拟必要的属性和方法
        mock_window_manager.return_value = Mock()
        mock_service_manager.return_value = Mock()
        mock_data_manager.return_value = Mock()
        mock_geolocation_handler.return_value = Mock()
        mock_signal_manager.return_value = Mock()

        # 模拟 QTimer
        mock_single_shot = Mock()
        mock_timer.singleShot = mock_single_shot
        mock_timer_instance = Mock()
        mock_timer.return_value = mock_timer_instance

        # 创建应用实例
        app = GpxStudio(splash_screen=self.splash_screen)

        # 验证 start_update_check 方法是否被调用
        # 验证 QTimer.singleShot 是否被调用
        self.assertTrue(mock_single_shot.called)
        # 验证 QTimer 是否被创建和启动
        mock_timer.assert_called_once()
        mock_timer_instance.timeout.connect.assert_called_once()
        mock_timer_instance.start.assert_called_once_with(24 * 60 * 60 * 1000)

    @patch('ui.popups.update_popup.UpdatePopup')
    @patch('app.app.UpdateManager')
    @patch('app.app.SignalManager')
    @patch('app.app.GeolocationHandler')
    @patch('app.app.WindowManager')
    @patch('app.app.ServiceManager')
    @patch('app.app.DataManager')
    @patch('app.app.QApplication')
    def test_update_available_signal(self, mock_qapp, mock_data_manager, mock_service_manager, mock_window_manager, mock_geolocation_handler, mock_signal_manager, mock_update_manager, mock_update_popup):
        """
        测试更新可用信号的处理
        """
        # 模拟必要的属性和方法
        mock_window_manager.return_value = Mock()
        mock_service_manager.return_value = Mock()
        mock_data_manager.return_value = Mock()
        mock_geolocation_handler.return_value = Mock()
        mock_signal_manager.return_value = Mock()

        # 模拟 UpdateManager
        mock_update_manager_instance = Mock()
        mock_update_manager.return_value = mock_update_manager_instance

        # 模拟 QTimer
        with patch('app.app.QTimer') as mock_timer:
            mock_single_shot = Mock()
            mock_timer.singleShot = mock_single_shot
            mock_timer_instance = Mock()
            mock_timer.return_value = mock_timer_instance

            # 创建应用实例
            app = GpxStudio(splash_screen=self.splash_screen)
            
            # 设置 UpdatePopup 的 Mock
            # 在 sys.modules 中注册 ui.popups.update_popup，以防 import 失败
            sys.modules['ui.popups.update_popup'] = Mock()
            sys.modules['ui.popups.update_popup'].UpdatePopup = mock_update_popup

            # 模拟用户选择立即更新
            mock_popup_instance = Mock()
            # UpdatePopup.RESULT_UPDATE = 1
            mock_popup_instance.exec_.return_value = 1
            mock_update_popup.return_value = mock_popup_instance
            mock_update_popup.RESULT_UPDATE = 1
            mock_update_popup.RESULT_SKIP = 2
            mock_update_popup.RESULT_LATER = 0

            # 触发更新可用信号
            app._on_update_available("2.0.1", "发布说明")

            # 验证 download_update 方法是否被调用
            mock_update_manager_instance.download_update.assert_called_once_with("2.0.1")

    @patch('ui.popups.update_popup.UpdatePopup')
    @patch('app.app.UpdateManager')
    @patch('app.app.SignalManager')
    @patch('app.app.GeolocationHandler')
    @patch('app.app.WindowManager')
    @patch('app.app.ServiceManager')
    @patch('app.app.DataManager')
    @patch('app.app.QApplication')
    def test_update_skip_version(self, mock_qapp, mock_data_manager, mock_service_manager, mock_window_manager, mock_geolocation_handler, mock_signal_manager, mock_update_manager, mock_update_popup):
        """
        测试跳过版本的处理
        """
        # 模拟必要的属性和方法
        mock_window_manager.return_value = Mock()
        mock_service_manager.return_value = Mock()
        mock_data_manager.return_value = Mock()
        mock_geolocation_handler.return_value = Mock()
        mock_signal_manager.return_value = Mock()

        # 模拟 UpdateManager
        mock_update_manager_instance = Mock()
        mock_update_manager.return_value = mock_update_manager_instance

        # 模拟 QTimer
        with patch('app.app.QTimer') as mock_timer:
            mock_single_shot = Mock()
            mock_timer.singleShot = mock_single_shot
            mock_timer_instance = Mock()
            mock_timer.return_value = mock_timer_instance

            # 创建应用实例
            app = GpxStudio(splash_screen=self.splash_screen)
            
            # 设置 UpdatePopup 的 Mock
            sys.modules['ui.popups.update_popup'] = Mock()
            sys.modules['ui.popups.update_popup'].UpdatePopup = mock_update_popup

            # 模拟用户选择跳过此版本
            mock_popup_instance = Mock()
            # UpdatePopup.RESULT_SKIP = 2
            mock_popup_instance.exec_.return_value = 2
            mock_update_popup.return_value = mock_popup_instance
            mock_update_popup.RESULT_UPDATE = 1
            mock_update_popup.RESULT_SKIP = 2
            mock_update_popup.RESULT_LATER = 0

            # 触发更新可用信号
            app._on_update_available("2.0.1", "发布说明")

            # 验证 skip_version 方法是否被调用
            mock_update_manager_instance.skip_version.assert_called_once_with("2.0.1")

    @patch('ui.popups.update_popup.CustomMessageDialog')
    @patch('app.app.UpdateManager')
    @patch('app.app.SignalManager')
    @patch('app.app.GeolocationHandler')
    @patch('app.app.WindowManager')
    @patch('app.app.ServiceManager')
    @patch('app.app.DataManager')
    @patch('app.app.QApplication')
    def test_update_downloaded(self, mock_qapp, mock_data_manager, mock_service_manager, mock_window_manager, mock_geolocation_handler, mock_signal_manager, mock_update_manager, mock_custom_dialog):
        """
        测试更新下载完成的处理
        """
        # 模拟必要的属性和方法
        mock_window_manager.return_value = Mock()
        mock_service_manager.return_value = Mock()
        mock_data_manager.return_value = Mock()
        mock_geolocation_handler.return_value = Mock()
        mock_signal_manager.return_value = Mock()

        # 模拟 UpdateManager
        mock_update_manager_instance = Mock()
        mock_update_manager.return_value = mock_update_manager_instance

        # 模拟 QTimer
        with patch('app.app.QTimer') as mock_timer:
            mock_timer.singleShot = Mock()
            mock_timer_instance = Mock()
            mock_timer.return_value = mock_timer_instance

            # 创建应用实例
            app = GpxStudio(splash_screen=self.splash_screen)
            
            # 设置 CustomMessageDialog 的 Mock
            sys.modules['ui.popups.update_popup'] = Mock()
            sys.modules['ui.popups.update_popup'].CustomMessageDialog = mock_custom_dialog
            
            # 模拟用户点击确认
            mock_dialog_instance = Mock()
            mock_dialog_instance.exec_.return_value = QDialog.Accepted
            mock_custom_dialog.return_value = mock_dialog_instance

            # 触发更新下载完成信号
            download_path = "fake/path/GPXStudio-2.0.1.exe"
            app._on_update_downloaded(download_path)

            # 验证 install_update 方法是否被调用
            mock_update_manager_instance.install_update.assert_called_once_with(download_path)

    @patch('ui.popups.update_popup.CustomMessageDialog')
    @patch('app.app.SignalManager')
    @patch('app.app.GeolocationHandler')
    @patch('app.app.WindowManager')
    @patch('app.app.ServiceManager')
    @patch('app.app.DataManager')
    @patch('app.app.QApplication')
    def test_update_error(self, mock_qapp, mock_data_manager, mock_service_manager, mock_window_manager, mock_geolocation_handler, mock_signal_manager, mock_custom_dialog):
        """
        测试更新错误的处理
        """
        # 模拟必要的属性和方法
        mock_window_manager.return_value = Mock()
        mock_service_manager.return_value = Mock()
        mock_data_manager.return_value = Mock()
        mock_geolocation_handler.return_value = Mock()
        mock_signal_manager.return_value = Mock()

        # 模拟 QTimer
        with patch('app.app.QTimer') as mock_timer:
            mock_single_shot = Mock()
            mock_timer.singleShot = mock_single_shot
            mock_timer_instance = Mock()
            mock_timer.return_value = mock_timer_instance

            # 创建应用实例
            app = GpxStudio(splash_screen=self.splash_screen)
            
            # 设置 CustomMessageDialog 的 Mock
            sys.modules['ui.popups.update_popup'] = Mock()
            sys.modules['ui.popups.update_popup'].CustomMessageDialog = mock_custom_dialog
            
            mock_dialog_instance = Mock()
            mock_custom_dialog.return_value = mock_dialog_instance

            # 触发更新错误信号
            error_message = "更新失败"
            app._on_update_error(error_message)

            # 验证 exec_ 是否被调用
            mock_dialog_instance.exec_.assert_called_once()


if __name__ == '__main__':
    unittest.main()
