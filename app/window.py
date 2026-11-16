from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QEvent
from typeface.lato import load_lato
from app.frame import keep, note_frame, note_state, place, present
from app.paths import app_icon
from session.content_view import ContentView


class FreewriteApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Freewrite")
        self.setWindowIcon(QIcon(app_icon()))
        load_lato()
        self.content_view = ContentView(self)
        self.setCentralWidget(self.content_view)
        place(self)

    def present(self):
        present(self)

    def closeEvent(self, event):
        keep(self)
        super().closeEvent(event)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() != QEvent.WindowStateChange: return
        if hasattr(self, "content_view"): self.content_view.apply_fullscreen(self.isFullScreen())
        note_state(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        note_frame(self)

    def moveEvent(self, event):
        super().moveEvent(event)
        note_frame(self)
