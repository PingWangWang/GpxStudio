"""
GPX Studio - 路线规划工具
主程序入口文件

该文件是GPX Studio应用程序的入口点，负责初始化应用程序环境、加载必要的模块并启动主窗口。
"""

import sys
import os

# 获取当前文件的目录，用于构建相对路径
current_dir = os.path.dirname(os.path.abspath(__file__))

# 将src目录添加到Python路径中，确保可以导入项目中的模块
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)


def main():
    """
    主函数，负责启动应用程序

    流程：
    1. 设置Qt属性（必须在创建QApplication之前）
    2. 创建QApplication实例
    3. 立即显示启动画面
    4. 延迟导入重量级模块
    5. 创建并显示主窗口
    6. 进入事件循环
    """
    # 第一步：导入PyQt5核心模块，并设置必要的Qt属性
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt, QCoreApplication

    # 必须在创建QApplication之前设置此属性，以支持QtWebEngine
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 禁止最后一个窗口关闭时自动退出程序（为了支持最小化到托盘功能）
    app.setQuitOnLastWindowClosed(False)

    # 第二步：立即导入并显示启动画面（轻量级，不依赖重模块）
    from ui.dialogs.splash_screen import SplashScreen
    splash = SplashScreen()
    splash.show()
    splash.update_progress(0, "正在启动 GPX Studio...")

    # 强制处理事件，确保启动画面立即显示
    app.processEvents()

    # 第三步：在启动画面显示后，开始导入重量级模块
    splash.update_progress(5, "正在加载核心模块...")
    app.processEvents()

    # 导入日志配置模块
    import core.logging_setup

    splash.update_progress(8, "正在加载应用模块...")
    app.processEvents()

    # 导入主窗口类（这是最耗时的导入，包含所有依赖）
    from app.app import GpxStudio

    # 第四步：创建主窗口实例（在初始化过程中会更新进度）
    window = GpxStudio(splash_screen=splash)

    # 第五步：主窗口初始化完成，显示它
    splash.update_progress(100, "启动完成！")
    app.processEvents()

    # 显示主窗口
    window.show()

    # 简单隐藏启动画面，不使用finish方法
    splash.hide()

    # 进入应用程序的事件循环，等待用户交互
    sys.exit(app.exec_())


if __name__ == "__main__":
    """
    程序入口点

    使用try-except块捕获所有可能的异常，确保应用程序在出现错误时能够优雅地退出
    并提供详细的错误信息
    """
    try:
        # 调用主函数启动应用程序
        main()
    except Exception as e:
        # 导入traceback模块，用于获取详细的错误堆栈信息
        import traceback

        # 构建错误信息字符串
        error_msg = f"应用程序启动失败: {e}\n"
        error_msg += "详细错误信息:\n"
        error_msg += traceback.format_exc()

        # 将错误信息打印到控制台
        print(error_msg)

        # 尝试使用系统日志记录器记录错误
        try:
            import logging
            logger = logging.getLogger()
            logger.critical("应用程序启动失败", exc_info=True)
            print("错误已记录到系统日志")
        except Exception as log_e:
            # 如果日志记录失败，打印失败信息
            print(f"使用系统日志记录器失败: {log_e}")

        # 等待用户按Enter键退出
        input("按Enter键退出...")
        sys.exit(1)
