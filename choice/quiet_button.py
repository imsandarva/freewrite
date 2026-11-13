"""A way out that doesn't compete with the two real answers."""

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QFont, QPainter
from PyQt5.QtWidgets import QAbstractButton

from history.face import face


class _Quiet(QAbstractButton):
    """A way out that doesn't compete with the two real answers."""

    def __init__(self, palette):
        super().__init__()
        self._colors = palette
        self.setFixedHeight(32)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.TabFocus)
        self.setAccessibleName("Cancel")
        self.setStyleSheet("QAbstractButton { background: transparent; border: none; outline: none; }")

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
        if self.underMouse() or self.isDown() or self.hasFocus():
            painter.setPen(Qt.NoPen)
            painter.setBrush(self._colors["hover"])
            painter.drawRoundedRect(QRectF(self.width() / 2 - 42, 2, 84, self.height() - 4), 8, 8)
        painter.setFont(face(13, QFont.Light, 0.08))
        painter.setPen(self._colors["title"] if self.underMouse() or self.hasFocus() else self._colors["muted"])
        painter.drawText(self.rect(), Qt.AlignCenter, "Cancel")
