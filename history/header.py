"""The title and the count at the top of the sheet."""

from PyQt5.QtCore import Qt, QRectF, pyqtSignal
from PyQt5.QtGui import QFont, QFontMetrics, QPainter, QPen
from PyQt5.QtWidgets import QWidget

from history.close_button import CloseButton
from history.face import face
from history.palette import colors
from history.trash_link import TrashLink
from typeface.metrics import _advance


class SheetHeader(QWidget):
    close_requested = pyqtSignal()
    trash_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._colors = colors(False)
        self._count, self._dot = "", 0
        self.setFixedHeight(104)
        self.close_btn = CloseButton(self)
        self.trash_link = TrashLink(self)
        self.close_btn.clicked.connect(self.close_requested)
        self.trash_link.clicked.connect(self.trash_requested)

    def apply_colors(self, palette):
        self._colors = palette
        self.close_btn.apply_colors(palette)
        self.trash_link.apply_colors(palette)
        self.update()

    def set_count(self, text):
        self._count = text
        self._place()
        self.update()

    def set_trash_count(self, count):
        self.trash_link.set_count(count)
        self._place()
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._place()

    def _place(self):
        self.close_btn.move(self.width() - 18 - self.close_btn.width(), 18)
        metrics = QFontMetrics(face(13, QFont.Light, 0.15))
        count_w = _advance(metrics, self._count or "")
        self._dot = 26 + count_w + 11
        x = self._dot + 14
        limit = self.close_btn.x() - 8
        if x + self.trash_link.width() > limit: x = max(26, limit - self.trash_link.width())
        self.trash_link.move(int(x), 46)
        self.trash_link.raise_()
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
        count_width = max(0, self._dot - 34) if self._dot else width
        painter.drawText(QRectF(26, 52, count_width, 20), Qt.AlignLeft | Qt.AlignVCenter, self._count)
        if self._count:
            painter.drawText(QRectF(self._dot, 52, 12, 20), Qt.AlignCenter, "·")
        painter.setPen(QPen(self._colors["line"], 1))
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
