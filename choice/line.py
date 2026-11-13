"""One line of the prompt, drawn rather than set as a label."""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QWidget

from history.face import face


class _Line(QWidget):
    def __init__(self, text, color, px, weight, spacing, height):
        super().__init__()
        self._text, self._color, self._font = text, color, face(px, weight, spacing)
        self.setFixedHeight(height)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setPen(self._color)
        painter.setFont(self._font)
        painter.drawText(self.rect(), Qt.AlignLeft | Qt.AlignVCenter, self._text)
