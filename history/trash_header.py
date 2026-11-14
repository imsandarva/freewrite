"""The title of Trash, the way back, and the word that empties it."""

from PyQt5.QtCore import Qt, QRectF, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QPen
from PyQt5.QtWidgets import QWidget

from history.back_button import BackButton
from history.close_button import CloseButton
from history.empty_link import EmptyLink
from history.face import face
from history.palette import colors


class TrashHeader(QWidget):
    back_requested = pyqtSignal()
    close_requested = pyqtSignal()
    empty_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._colors = colors(False)
        self._count = ""
        self.setFixedHeight(108)
        self.back_btn = BackButton(self)
        self.close_btn = CloseButton(self)
        self.empty_link = EmptyLink(self)
        self.back_btn.clicked.connect(self.back_requested)
        self.close_btn.clicked.connect(self.close_requested)
        self.empty_link.clicked.connect(self.empty_requested)
        self.close_btn.setAccessibleName("Close")

    def apply_colors(self, palette):
        self._colors = palette
        self.back_btn.apply_colors(palette)
        self.close_btn.apply_colors(palette)
        self.empty_link.apply_colors(palette)
        self.update()

    def set_count(self, text, can_empty):
        self._count = text
        self.empty_link.setVisible(bool(can_empty))
        self._place()
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._place()

    def wheelEvent(self, event):
        event.accept()

    def _place(self):
        self.back_btn.move(12, 12)
        self.close_btn.move(self.width() - 18 - self.close_btn.width(), 12)
        self.empty_link.move(self.width() - 22 - self.empty_link.width(), 58)
        self.back_btn.raise_()
        self.close_btn.raise_()
        self.empty_link.raise_()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._colors["sheet"])
        painter.setRenderHint(QPainter.TextAntialiasing)
        title_x, width = 54, max(40, self.width() - 54 - 64)
        painter.setPen(self._colors["title"])
        painter.setFont(face(22, QFont.Bold, -0.4))
        painter.drawText(QRectF(title_x, 16, width, 30), Qt.AlignLeft | Qt.AlignVCenter, "Trash")
        count_right = self.empty_link.x() - 12 if self.empty_link.isVisible() else self.width() - 26
        painter.setPen(self._colors["muted"])
        painter.setFont(face(13, QFont.Light, 0.15))
        painter.drawText(QRectF(title_x, 62, max(40, count_right - title_x), 22), Qt.AlignLeft | Qt.AlignVCenter, self._count)
        painter.setPen(QPen(self._colors["line"], 1))
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
