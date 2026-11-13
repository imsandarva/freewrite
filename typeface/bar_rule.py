"""The quiet divider between the type controls and the session controls."""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import QWidget

from typeface.theme import _note_dark


class BarRule(QWidget):
    """The quiet divider between the type controls and the session controls."""

    def __init__(self, dark=False, parent=None):
        super().__init__(parent)
        self._dark = bool(dark)
        self.setObjectName("barRule")
        self.setProperty("dark", self._dark)
        self.setFixedSize(1, 16)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setStyleSheet("QWidget#barRule { background: transparent; border: none; }")

    def event(self, event):
        _note_dark(self, event)
        return super().event(event)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(244, 241, 236, 70) if self._dark else QColor(42, 34, 26, 58))
