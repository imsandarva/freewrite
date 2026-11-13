"""Fills itself. A palette would be wiped the next time the app theme reloads."""

from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import QWidget


class Paper(QWidget):
    """Fills itself. A palette would be wiped the next time the app theme reloads."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._paper = QColor("#FBF9F6")
        self.setAutoFillBackground(False)

    def set_paper(self, color):
        self._paper = QColor(color)
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._paper)
