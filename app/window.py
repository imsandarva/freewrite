from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QEvent
from typeface.lato import load_lato
from app.paths import app_icon
from session.content_view import ContentView


class FreewriteApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Freewrite")
        self.setGeometry(100, 100, 1100, 600)
        self.setWindowIcon(QIcon(app_icon()))
        load_lato()

        # Set central widget
        self.content_view = ContentView(self)
        self.setCentralWidget(self.content_view)

        # Center window
        self.center()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() != QEvent.WindowStateChange or not hasattr(self, "content_view"): return
        self.content_view.apply_fullscreen(self.isFullScreen())

    def center(self):
        frame = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        center_point = QApplication.desktop().screenGeometry(screen).center()
        frame.moveCenter(center_point)
        self.move(frame.topLeft())
