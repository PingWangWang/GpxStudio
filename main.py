"""
GPX Studio - 路线规划工具
主程序入口文件
"""

import sys
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
    main()
