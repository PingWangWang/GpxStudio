"""
UI样式定义
集中管理应用的UI样式
"""


class UIStyles:
    """UI样式定义"""

    # 按钮样式
    LOCATE_BUTTON = """
        QPushButton {
            background-color: #FF9800;
            color: white;
            padding: 10px;
            font-size: 9pt;
            border-radius: 5px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #F57C00;
        }
    """

    TEST_BUTTON = """
        QPushButton {
            background-color: #2196F3;
            color: white;
            padding: 10px;
            font-size: 9pt;
            border-radius: 5px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #1976D2;
        }
    """

    PLAN_BUTTON = """
        QPushButton {
            background-color: #4CAF50;
            color: white;
            padding: 10px;
            font-size: 9pt;
        }
    """

    EXPORT_BUTTON = """
        QPushButton {
            background-color: #2196F3;
            color: white;
            padding: 10px;
            font-size: 9pt;
        }
    """

    CLEAR_BUTTON = """
        QPushButton {
            background-color: #9E9E9E;
            color: white;
            padding: 8px;
            font-size: 9pt;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #757575;
        }
    """

    # 进度条样式
    PROGRESS_BAR = """
        QProgressBar {
            border: 2px solid grey;
            border-radius: 5px;
            text-align: center;
            background-color: #f0f0f0;
            font-size: 9pt;
        }
        QProgressBar::chunk {
            background-color: #3b82f6;
            width: 20px;
        }
    """

    # 标题样式
    TITLE_LABEL = "font-size: 9pt; font-weight: bold; padding: 10px;"
