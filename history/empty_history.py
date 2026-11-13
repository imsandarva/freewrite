"""What the list says before any notes exist."""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPainter
from PyQt5.QtWidgets import QWidget

from history.face import face


class EmptyHistory(QWidget):
    def __init__(self, color, paper):
        super().__init__()
        self._color, self._paper = color, paper
        self.setMinimumHeight(168)
        self.setAutoFillBackground(False)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._paper)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setPen(self._color)
        painter.setFont(face(14, QFont.Light, 0.1))
        painter.drawText(self.rect().adjusted(32, 28, -32, -28), Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, "When you start writing, your notes will gather here.")
