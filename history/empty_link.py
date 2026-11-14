"""The quiet word that empties Trash. It stays calm until the pointer is over it."""

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PyQt5.QtWidgets import QAbstractButton

from history.face import face
from typeface.metrics import _advance


class EmptyLink(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ink = QColor("#8A8178")
        self._danger = QColor("#9C463C")
        self._fill = QColor(156, 70, 60, 18)
        self._accent = QColor("#8C6842")
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAccessibleName("Empty Trash")
        self.setToolTip("Empty Trash")
        self.setStyleSheet("QAbstractButton { background: transparent; border: none; }")
        self._fit()

    def apply_colors(self, palette):
        self._ink = QColor(palette["muted"])
        self._danger = QColor(palette["danger"])
        self._accent = QColor(palette["accent"])
        self._fill = QColor(palette["danger"])
        self._fill.setAlpha(28 if palette["sheet"].lightness() >= 40 else 46)
        self.update()

    def _font(self):
        return face(13, QFont.Normal, 0.2)

    def _fit(self):
        word = _advance(QFontMetrics(self._font()), "Empty")
        self.setFixedSize(int(word + 22), 28)

    def enterEvent(self, event):
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        hot = self.underMouse() or self.isDown() or self.hasFocus()
        if hot:
            painter.setPen(Qt.NoPen)
            painter.setBrush(self._fill)
            painter.drawRoundedRect(QRectF(1, 1, self.width() - 2, self.height() - 2), 9, 9)
        painter.setFont(self._font())
        painter.setPen(self._danger if hot else self._ink)
        painter.drawText(self.rect(), Qt.AlignCenter, "Empty")
        if self.hasFocus():
            painter.setPen(QPen(self._accent, 1.2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(QRectF(1.5, 1.5, self.width() - 3, self.height() - 3), 9, 9)
