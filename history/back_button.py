"""The chevron that returns from Trash to History."""

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import QAbstractButton

from history.icons import paint_icon


class BackButton(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ink, self._ink_hot = QColor("#8A8178"), QColor("#1C1917")
        self._fill, self._accent = QColor(48, 36, 24, 16), QColor("#8C6842")
        self.setFixedSize(36, 36)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAccessibleName("Back to History")
        self.setToolTip("History")
        self.setStyleSheet("QAbstractButton { background: transparent; border: none; }")

    def apply_colors(self, palette):
        self._ink, self._ink_hot = palette["muted"], palette["title"]
        self._fill, self._accent = palette["hover"], palette["accent"]
        self.update()

    def enterEvent(self, event):
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        hot = self.underMouse() or self.isDown()
        if hot:
            painter.setPen(Qt.NoPen)
            painter.setBrush(self._fill)
            painter.drawRoundedRect(QRectF(1, 1, self.width() - 2, self.height() - 2), 11, 11)
        paint_icon(painter, "chevron", QRectF(self.rect()), self._ink_hot if hot else self._ink)
        if self.hasFocus():
            painter.setPen(QPen(self._accent, 1.2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(QRectF(1.5, 1.5, self.width() - 3, self.height() - 3), 11, 11)
