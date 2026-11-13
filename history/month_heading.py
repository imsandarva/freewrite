"""The month name above a group of notes."""

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QFont, QPainter
from PyQt5.QtWidgets import QWidget

from history.face import face


class MonthHeading(QWidget):
    def __init__(self, text, color, paper, first):
        super().__init__()
        self._text, self._color, self._paper = text, color, paper
        self.setFixedHeight(30 if first else 44)
        self.setAutoFillBackground(False)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._paper)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setPen(self._color)
        painter.setFont(face(12, QFont.Bold, 0.35))
        painter.drawText(QRectF(26, 0, self.width() - 52, self.height() - 4), Qt.AlignLeft | Qt.AlignBottom, self._text)
