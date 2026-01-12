"""
GPX Studio - 路线规划工具
主程序入口文件
"""

import sys
import os

# 获取当前文件的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 将src目录添加到Python路径中
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

from PyQt5.QtWidgets import QApplication

# 导入日志配置，确保重定向功能生效
import core.logging_setup

from app.app import GpxStudio


def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = GpxStudio()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        error_msg = f"应用程序启动失败: {e}\n"
        error_msg += "详细错误信息:\n"
        error_msg += traceback.format_exc()

        # 打印到控制台
        print(error_msg)

        # 尝试使用系统日志记录器
        try:
            import logging
            logger = logging.getLogger()
            logger.critical("应用程序启动失败", exc_info=True)
            print("错误已记录到系统日志")
        except Exception as log_e:
            print(f"使用系统日志记录器失败: {log_e}")

        input("按Enter键退出...")
        sys.exit(1)
