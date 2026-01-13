"""
测试启动画面功能
独立测试启动画面的显示效果
"""

import sys
import os

# 获取当前文件的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 将src目录添加到Python路径中
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from ui.dialogs.splash_screen import SplashScreen


def test_splash():
    """测试启动画面"""
    app = QApplication(sys.argv)

    # 创建并显示启动画面
    splash = SplashScreen()
    splash.show()

    # 模拟加载过程
    def update_progress():
        stages = [
            (0, "正在启动..."),
            (10, "正在初始化管理器..."),
            (25, "正在设置窗口..."),
            (40, "正在初始化服务..."),
            (55, "正在初始化信号系统..."),
            (70, "正在加载用户界面..."),
            (85, "正在初始化日志系统..."),
            (100, "启动完成!")
        ]

        current_stage = [0]

        def next_stage():
            if current_stage[0] < len(stages):
                progress, message = stages[current_stage[0]]
                splash.update_progress(progress, message)
                print(f"进度: {progress}% - {message}")
                current_stage[0] += 1

                if current_stage[0] < len(stages):
                    QTimer.singleShot(500, next_stage)  # 每0.5秒更新一次
                else:
                    QTimer.singleShot(1000, app.quit)  # 完成后1秒退出

        next_stage()

    QTimer.singleShot(100, update_progress)

    sys.exit(app.exec_())


if __name__ == "__main__":
    test_splash()
