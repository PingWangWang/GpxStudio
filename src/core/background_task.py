"""
后台任务管理系统
提供异步任务执行、进度报告、任务中断等功能
"""

from PyQt5.QtCore import QObject, QThread, pyqtSignal
from enum import Enum
from typing import Callable, Any, Optional, Dict
import traceback
import time


class TaskPriority(Enum):
    """任务优先级"""
    HIGH = 1      # 用户直接操作（立即中断其他任务）
    NORMAL = 2    # 普通任务
    LOW = 3       # 低优先级任务


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"       # 等待执行
    RUNNING = "running"       # 正在执行
    COMPLETED = "completed"   # 完成
    CANCELLED = "cancelled"   # 已取消
    FAILED = "failed"         # 失败


class BackgroundTask(QObject):
    """后台任务Worker

    在独立线程中执行长时间任务，支持：
    - 进度报告
    - 任务中断
    - 错误处理
    - 结果返回
    """

    # 信号定义
    started = pyqtSignal(str)                    # 任务开始：任务ID
    progress = pyqtSignal(str, int, str)         # 进度更新：任务ID, 百分比, 消息
    completed = pyqtSignal(str, object)          # 任务完成：任务ID, 结果
    failed = pyqtSignal(str, str)                # 任务失败：任务ID, 错误消息
    cancelled = pyqtSignal(str)                  # 任务取消：任务ID
    log_message = pyqtSignal(str, str, str)      # 日志消息：任务ID, 级别, 消息

    def __init__(self, task_id: str, task_type: str, task_func: Callable,
                 priority: TaskPriority = TaskPriority.NORMAL, **kwargs):
        """
        初始化后台任务

        参数:
            task_id: 任务唯一标识符
            task_type: 任务类型（如：location、search、routing）
            task_func: 要执行的函数
            priority: 任务优先级
            **kwargs: 传递给task_func的参数
        """
        super().__init__()
        self.task_id = task_id
        self.task_type = task_type
        self.task_func = task_func
        self.priority = priority
        self.kwargs = kwargs
        self.status = TaskStatus.PENDING
        self._cancelled = False
        self._thread = None

    def run(self):
        """执行任务"""
        if self._cancelled:
            self.cancelled.emit(self.task_id)
            return

        try:
            self.status = TaskStatus.RUNNING
            self.started.emit(self.task_id)
            self.log("INFO", f"开始执行 {self.task_type} 任务")

            # 创建进度回调
            progress_callback = lambda percent, msg: self._report_progress(percent, msg)
            log_callback = lambda level, msg: self.log(level, msg)
            cancel_check = lambda: self._cancelled

            # 注入回调到kwargs
            self.kwargs['progress_callback'] = progress_callback
            self.kwargs['log_callback'] = log_callback
            self.kwargs['cancel_check'] = cancel_check

            # 执行任务
            result = self.task_func(**self.kwargs)

            # 检查是否被取消
            if self._cancelled:
                self.status = TaskStatus.CANCELLED
                self.cancelled.emit(self.task_id)
                self.log("WARNING", f"{self.task_type} 任务已取消")
            else:
                self.status = TaskStatus.COMPLETED
                self.completed.emit(self.task_id, result)
                self.log("INFO", f"{self.task_type} 任务完成")

        except Exception as e:
            self.status = TaskStatus.FAILED
            error_msg = f"{self.task_type} 任务失败: {str(e)}"
            self.log("ERROR", error_msg)
            self.log("DEBUG", traceback.format_exc())
            self.failed.emit(self.task_id, error_msg)

    def cancel(self):
        """取消任务"""
        if self.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            self._cancelled = True
            self.log("WARNING", f"正在取消 {self.task_type} 任务...")

    def is_cancelled(self) -> bool:
        """检查任务是否已取消"""
        return self._cancelled

    def _report_progress(self, percent: int, message: str):
        """报告进度（内部方法）"""
        if not self._cancelled:
            self.progress.emit(self.task_id, percent, message)

    def log(self, level: str, message: str):
        """记录日志"""
        self.log_message.emit(self.task_id, level, message)


class TaskManager(QObject):
    """任务管理器

    管理所有后台任务的生命周期：
    - 任务队列管理
    - 优先级处理
    - 任务中断
    - 线程池管理
    """

    # 信号定义
    task_queued = pyqtSignal(str, str)           # 任务入队：任务ID, 任务类型
    task_started = pyqtSignal(str, str)          # 任务开始：任务ID, 任务类型
    task_progress = pyqtSignal(str, int, str)    # 任务进度：任务ID, 百分比, 消息
    task_completed = pyqtSignal(str, object)     # 任务完成：任务ID, 结果
    task_failed = pyqtSignal(str, str)           # 任务失败：任务ID, 错误
    task_cancelled = pyqtSignal(str)             # 任务取消：任务ID
    task_log = pyqtSignal(str, str, str)         # 任务日志：任务ID, 级别, 消息

    def __init__(self, logger=None):
        """初始化任务管理器"""
        super().__init__()
        self.logger = logger
        self.tasks: Dict[str, BackgroundTask] = {}  # 任务字典
        self.threads: Dict[str, QThread] = {}        # 线程字典
        self.current_task_id: Optional[str] = None   # 当前正在执行的任务ID
        self._task_counter = 0                        # 任务计数器

    def submit_task(self, task_type: str, task_func: Callable,
                    priority: TaskPriority = TaskPriority.NORMAL,
                    **kwargs) -> str:
        """
        提交新任务

        参数:
            task_type: 任务类型
            task_func: 任务函数
            priority: 任务优先级
            **kwargs: 任务参数

        返回:
            任务ID
        """
        # 生成任务ID
        self._task_counter += 1
        task_id = f"{task_type}_{self._task_counter}_{int(time.time() * 1000)}"

        # 如果是高优先级任务，取消当前同类型任务
        if priority == TaskPriority.HIGH:
            self._cancel_tasks_by_type(task_type)

        # 创建任务
        task = BackgroundTask(task_id, task_type, task_func, priority, **kwargs)

        # 连接信号
        task.started.connect(lambda tid: self._on_task_started(tid))
        task.progress.connect(lambda tid, pct, msg: self.task_progress.emit(tid, pct, msg))
        task.completed.connect(lambda tid, result: self._on_task_completed(tid, result))
        task.failed.connect(lambda tid, error: self._on_task_failed(tid, error))
        task.cancelled.connect(lambda tid: self._on_task_cancelled(tid))
        task.log_message.connect(lambda tid, level, msg: self.task_log.emit(tid, level, msg))

        # 创建线程
        thread = QThread()
        task.moveToThread(thread)
        thread.started.connect(task.run)

        # 保存任务和线程
        self.tasks[task_id] = task
        self.threads[task_id] = thread

        # 发射入队信号
        self.task_queued.emit(task_id, task_type)
        if self.logger:
            self.logger.debug(f"[任务管理器] 任务已入队: {task_id} ({task_type})")

        # 启动线程
        thread.start()

        return task_id

    def cancel_task(self, task_id: str):
        """取消指定任务"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.cancel()
            if self.logger:
                self.logger.info(f"[任务管理器] 取消任务: {task_id}")

    def cancel_all_tasks(self):
        """取消所有任务"""
        for task_id in list(self.tasks.keys()):
            self.cancel_task(task_id)

    def _cancel_tasks_by_type(self, task_type: str):
        """取消指定类型的所有任务"""
        for task_id, task in list(self.tasks.items()):
            if task.task_type == task_type and task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                task.cancel()
                if self.logger:
                    self.logger.info(f"[任务管理器] 取消同类型任务: {task_id}")

    def _on_task_started(self, task_id: str):
        """任务开始回调"""
        if task_id in self.tasks:
            self.current_task_id = task_id
            task = self.tasks[task_id]
            self.task_started.emit(task_id, task.task_type)
            if self.logger:
                self.logger.info(f"[任务管理器] 任务开始: {task_id} ({task.task_type})")

    def _on_task_completed(self, task_id: str, result):
        """任务完成回调"""
        self.task_completed.emit(task_id, result)
        self._cleanup_task(task_id)
        if self.logger:
            self.logger.info(f"[任务管理器] 任务完成: {task_id}")

    def _on_task_failed(self, task_id: str, error: str):
        """任务失败回调"""
        self.task_failed.emit(task_id, error)
        self._cleanup_task(task_id)
        if self.logger:
            self.logger.error(f"[任务管理器] 任务失败: {task_id} - {error}")

    def _on_task_cancelled(self, task_id: str):
        """任务取消回调"""
        self.task_cancelled.emit(task_id)
        self._cleanup_task(task_id)
        if self.logger:
            self.logger.warning(f"[任务管理器] 任务已取消: {task_id}")

    def _cleanup_task(self, task_id: str):
        """清理任务资源"""
        if task_id in self.threads:
            thread = self.threads[task_id]
            thread.quit()
            thread.wait(1000)  # 等待最多1秒
            if thread.isRunning():
                thread.terminate()
            del self.threads[task_id]

        if task_id in self.tasks:
            del self.tasks[task_id]

        if self.current_task_id == task_id:
            self.current_task_id = None

    def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            return {
                'task_id': task.task_id,
                'task_type': task.task_type,
                'priority': task.priority,
                'status': task.status
            }
        return None

    def get_running_tasks(self) -> list:
        """获取所有正在运行的任务"""
        return [
            task_id for task_id, task in self.tasks.items()
            if task.status == TaskStatus.RUNNING
        ]
