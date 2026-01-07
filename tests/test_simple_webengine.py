"""
最简单的QWebEngineView测试
用于诊断信号和JavaScript控制台问题
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage


class SimpleTestPage(QWebEnginePage):
    def __init__(self):
        super().__init__()
        print("[SimpleTestPage] 初始化")

    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        print(f"[JS控制台] {message}")


class SimpleTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("简单测试")
        self.resize(800, 600)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.view = QWebEngineView()
        self.page = SimpleTestPage()
        self.view.setPage(self.page)

        self.page.loadStarted.connect(lambda: print("[信号] 开始加载"))
        self.page.loadProgress.connect(lambda p: print(f"[信号] 进度: {p}%"))
        self.page.loadFinished.connect(self.on_load_finished)

        layout.addWidget(self.view)

        # 加载简单HTML
        html = """
        <html>
        <head><title>测试</title></head>
        <body>
            <h1>测试页面</h1>
            <script>
                console.log('[JS] 页面加载完成');
                console.log('[JS] navigator.geolocation: ' + (!!navigator.geolocation));
            </script>
        </body>
        </html>
        """
        self.view.setHtml(html)
        print("[主程序] HTML已设置")

    def on_load_finished(self, ok):
        print(f"[信号] 加载完成: {ok}")
        # 尝试执行JS
        self.page.runJavaScript("console.log('[runJS] 手动执行的JS');")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimpleTest()
    window.show()
    sys.exit(app.exec_())
