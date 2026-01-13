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

# 导入PyQt5的QApplication类，用于创建应用程序实例
from PyQt5.QtWidgets import QApplication

# 导入日志配置模块，确保应用程序的日志系统正常工作
import core.logging_setup

# 导入主窗口类GpxStudio，这是应用程序的核心界面类
from app.app import GpxStudio


def main():
    """
    主函数，负责启动应用程序
    
    流程：
    1. 创建QApplication实例，这是PyQt5应用程序的基础
    2. 创建GpxStudio主窗口实例
    3. 显示主窗口
    4. 进入应用程序的事件循环
    """
    # 创建应用程序实例，传入命令行参数
    app = QApplication(sys.argv)
    
    # 创建主窗口实例
    window = GpxStudio()
    
    # 显示主窗口
    window.show()
    
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
