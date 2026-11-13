"""The folder path, elided in the middle."""

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QFont, QFontMetrics, QPainter
from PyQt5.QtWidgets import QWidget

from history.face import face


class _Chip(QWidget):
    def __init__(self, path, palette):
        super().__init__()
        self._path, self._colors = path, palette
        self.setFixedHeight(44)
        self.setToolTip(path)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._colors["icon_bg"])
        painter.drawRoundedRect(QRectF(self.rect()), 11, 11)
        font = face(13, QFont.Normal, 0.02)
        painter.setFont(font)
        painter.setPen(self._colors["title"])
        rect = QRectF(self.rect()).adjusted(14, 0, -14, 0)
        shown = QFontMetrics(font).elidedText(self._path, Qt.ElideMiddle, int(rect.width()))
        painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter, shown)
