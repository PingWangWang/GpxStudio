"""UpdateMixin — 历史记录删除、版本更新检查与安装处理方法"""
import os
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QDialog


class UpdateMixin:
    """历史记录管理及软件更新相关的所有处理逻辑。"""

    def _on_history_delete_clicked(self, history_data: dict):
        """删除历史记录"""
        from PyQt5.QtCore import QRunnable, QThreadPool, pyqtSlot
        from modules.routing import RouteHistoryStorage

        # 1. 立即从界面中删除该记录
        current_history = []
        for i in range(self.route_plan_panel.history_list.count()):
            item = self.route_plan_panel.history_list.item(i)
            widget = self.route_plan_panel.history_list.itemWidget(item)
            if widget and hasattr(widget, 'history_data'):
                current_history.append(widget.history_data)

        new_history = [h for h in current_history if h != history_data]
        self.route_plan_panel.load_history(new_history)

        # 2. 在后台线程中处理文件删除操作
        class DeleteTask(QRunnable):
            def __init__(self, app, history_data):
                super().__init__()
                self.app = app
                self.history_data = history_data

            @pyqtSlot()
            def run(self):
                try:
                    storage = RouteHistoryStorage()
                    storage.remove_record(self.history_data)
                    updated_history = storage.get_history(10)
                    if hasattr(self.app.route_plan_panel, '_last_history_list'):
                        self.app.route_plan_panel._last_history_list = updated_history
                except Exception as e:
                    if hasattr(self.app, 'logger'):
                        self.app.logger.error(f"[历史记录] 异步删除失败: {str(e)}")

        task = DeleteTask(self, history_data)
        QThreadPool.globalInstance().start(task)

    def _on_history_select_all(self):
        """历史列表全选按钮：toggle 全选/取消全选（按钮高亮随选中状态）"""
        self.route_plan_panel.toggle_select_all()

    def _on_history_batch_delete_clicked(self):
        """删除勾选的历史记录（以勾选结果为准）"""
        records = self.route_plan_panel.get_checked_records()
        if not records:
            self._show_warning("提示", "请先勾选要删除的历史记录（点击条目右侧 ☐ 勾选）")
            return

        # 1. 立即从界面移除勾选记录
        current_history = []
        for i in range(self.route_plan_panel.history_list.count()):
            item = self.route_plan_panel.history_list.item(i)
            widget = self.route_plan_panel.history_list.itemWidget(item)
            if widget and hasattr(widget, 'history_data') \
                    and widget.history_data not in records:
                current_history.append(widget.history_data)
        self.route_plan_panel.load_history(current_history)

        # 2. 在后台线程中逐条删除文件
        from PyQt5.QtCore import QRunnable, QThreadPool, pyqtSlot
        from modules.routing import RouteHistoryStorage

        class DeleteTask(QRunnable):
            def __init__(self, app, to_delete):
                super().__init__()
                self.app = app
                self.to_delete = to_delete

            @pyqtSlot()
            def run(self):
                try:
                    storage = RouteHistoryStorage()
                    for rec in self.to_delete:
                        storage.remove_record(rec)
                    updated_history = storage.get_history(10)
                    if hasattr(self.app.route_plan_panel, '_last_history_list'):
                        self.app.route_plan_panel._last_history_list = updated_history
                except Exception as e:
                    if hasattr(self.app, 'logger'):
                        self.app.logger.error(f"[历史记录] 异步删除失败: {str(e)}")

        QThreadPool.globalInstance().start(DeleteTask(self, records))
        if hasattr(self, '_show_info'):
            self._show_info("删除完成", f"已删除 {len(records)} 条历史记录")

    def _on_update_available(self, latest_version: str, release_notes: str):
        """发现新版本"""
        try:
            from ui.popups.update_popup import UpdatePopup

            popup = UpdatePopup(self, latest_version, release_notes)
            result = popup.exec_()

            if result == UpdatePopup.RESULT_UPDATE:
                self.update_manager.download_update(latest_version)
            elif result == UpdatePopup.RESULT_SKIP:
                self.update_manager.skip_version(latest_version)

        except ImportError:
            from PyQt5.QtWidgets import QMessageBox

            msg_box = QMessageBox()
            msg_box.setWindowTitle("发现新版本")
            msg_box.setText(f"发现新版本: v{latest_version}")
            msg_box.setInformativeText("是否立即更新？")
            msg_box.setDetailedText(release_notes)
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            msg_box.setDefaultButton(QMessageBox.Yes)

            yes_button = msg_box.button(QMessageBox.Yes)
            yes_button.setText("立即更新")
            no_button = msg_box.button(QMessageBox.No)
            no_button.setText("跳过此版本")
            cancel_button = msg_box.button(QMessageBox.Cancel)
            cancel_button.setText("稍后再说")

            result = msg_box.exec_()

            if result == QMessageBox.Yes:
                self.update_manager.download_update(latest_version)
            elif result == QMessageBox.No:
                self.update_manager.skip_version(latest_version)

    def _on_update_downloaded(self, download_path: str):
        """更新下载完成"""
        try:
            from ui.popups.update_popup import CustomMessageDialog

            import re
            version_match = re.search(r'v?(\d+\.\d+\.\d+)', os.path.basename(download_path))
            new_version = version_match.group(1) if version_match else None

            dialog = CustomMessageDialog(
                self,
                title="安装更新",
                message="更新已下载完成，是否立即安装？",
                informative_text="安装过程中会关闭当前程序并启动新程序",
                ok_text="立即安装",
                cancel_text="稍后"
            )

            if dialog.exec_() == QDialog.Accepted:
                self.update_manager.install_update(download_path, new_version)

        except ImportError:
            from PyQt5.QtWidgets import QMessageBox

            msg_box = QMessageBox()
            msg_box.setWindowTitle("安装更新")
            msg_box.setText("更新已下载完成，是否立即安装？")
            msg_box.setInformativeText("安装过程中会关闭当前程序并启动新程序")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.Yes)

            import re
            version_match = re.search(r'v?(\d+\.\d+\.\d+)', os.path.basename(download_path))
            new_version = version_match.group(1) if version_match else None

            if msg_box.exec_() == QMessageBox.Yes:
                self.update_manager.install_update(download_path, new_version)

    def _on_update_error(self, error_message: str):
        """更新错误"""
        try:
            from ui.popups.update_popup import CustomMessageDialog

            dialog = CustomMessageDialog(
                self,
                title="更新错误",
                message="更新过程中发生错误",
                informative_text=error_message,
                show_cancel=False,
                ok_text="确定"
            )
            dialog.exec_()
        except ImportError:
            from PyQt5.QtWidgets import QMessageBox

            msg_box = QMessageBox()
            msg_box.setWindowTitle("更新错误")
            msg_box.setText("更新过程中发生错误")
            msg_box.setInformativeText(error_message)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec_()

    def start_update_check(self):
        """启动定时检查更新的任务"""
        from core.background_task import TaskPriority

        def submit_update_task():
            if not getattr(self, 'task_manager', None):
                QTimer.singleShot(1000, lambda: self.update_manager.check_for_updates(silent=True))
                return

            def update_worker(**kwargs):
                progress_callback = kwargs.get('progress_callback')
                if progress_callback:
                    progress_callback(0, "开始检查更新...")

                self.update_manager.check_for_updates(silent=True)

                if progress_callback:
                    progress_callback(100, "检查更新完成")

            self.task_manager.submit_task(
                task_type="update",
                task_func=update_worker,
                priority=TaskPriority.LOW
            )

        QTimer.singleShot(10000, submit_update_task)

        self.update_timer = QTimer()
        self.update_timer.setInterval(24 * 60 * 60 * 1000)
        self.update_timer.timeout.connect(submit_update_task)
        self.update_timer.start()
        self.update_timer.start(24 * 60 * 60 * 1000)
