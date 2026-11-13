"""The title and the count at the top of the sheet."""

from PyQt5.QtCore import Qt, QRectF, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QPen
from PyQt5.QtWidgets import QWidget

from history.close_button import CloseButton
from history.face import face
from history.palette import colors


class SheetHeader(QWidget):
    close_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._colors = colors(False)
        self._count = ""
        self.setFixedHeight(104)
        self.close_btn = CloseButton(self)
        self.close_btn.clicked.connect(self.close_requested)

    def apply_colors(self, palette):
        self._colors = palette
        self.close_btn.apply_colors(palette)
        self.update()

    def set_count(self, text):
        self._count = text
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.close_btn.move(self.width() - 18 - self.close_btn.width(), 18)
        self.close_btn.raise_()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._colors["sheet"])
        painter.setRenderHint(QPainter.TextAntialiasing)
        width = self.width() - 78
        painter.setPen(self._colors["title"])
        painter.setFont(face(22, QFont.Bold, -0.4))
        painter.drawText(QRectF(26, 20, width, 30), Qt.AlignLeft | Qt.AlignVCenter, "History")
        painter.setPen(self._colors["muted"])
        painter.setFont(face(13, QFont.Light, 0.15))
        painter.drawText(QRectF(26, 52, width, 20), Qt.AlignLeft | Qt.AlignVCenter, self._count)
        painter.setPen(QPen(self._colors["line"], 1))
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
