"""The quiet divider between the type controls and the session controls."""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import QWidget


class BarRule(QWidget):
    """The quiet divider between the type controls and the session controls."""

    def __init__(self, paper, parent=None):
        super().__init__(parent)
        self._paper = paper
        self.setObjectName("barRule")
        self.setFixedSize(1, 16)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setStyleSheet("QWidget#barRule { background: transparent; border: none; }")

    def apply_paper(self, paper):
        self._paper = paper
        self.update()

    def paintEvent(self, _event):
        color = QColor(self._paper.ink)
        color.setAlpha(70 if self._paper.dark else 48)
        painter = QPainter(self)
        painter.fillRect(self.rect(), color)
