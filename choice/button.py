"""A choice on the prompt. The filled one is the move."""

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QFont, QPainter, QPen
from PyQt5.QtWidgets import QAbstractButton, QSizePolicy

from history.face import face


def _mix(a, b, t):
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    return QColor(
        int(a.red() + (b.red() - a.red()) * t), int(a.green() + (b.green() - a.green()) * t),
        int(a.blue() + (b.blue() - a.blue()) * t), int(a.alpha() + (b.alpha() - a.alpha()) * t),
    )


def _ink_on(accent):
    return QColor("#1C1917") if accent.lightness() > 150 else QColor("#FBF9F6")

class _Button(QAbstractButton):
    def __init__(self, text, primary, palette):
        super().__init__()
        self._text, self._primary, self._colors = text, primary, palette
        self._ink = _ink_on(palette["accent"])
        self.setFixedHeight(44)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.TabFocus)
        self.setAccessibleName(text)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
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
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        self._paint_fill(painter, rect)
        painter.setFont(face(14, QFont.Normal, 0.12))
        painter.setPen(self._ink if self._primary else (self._colors["title"] if self.underMouse() else self._colors["body"]))
        painter.drawText(self.rect(), Qt.AlignCenter, self._text)
        if self.hasFocus(): self._paint_ring(painter)

    def _paint_fill(self, painter, rect):
        if self._primary:
            fill = self._colors["accent"]
            if self.isDown(): fill = _mix(fill, QColor("#1C1917"), 0.14)
            elif self.underMouse(): fill = _mix(fill, QColor("#FFFFFF"), 0.12)
            painter.setPen(Qt.NoPen)
            painter.setBrush(fill)
        else:
            border = QColor(self._colors["muted"])
            border.setAlpha(88)
            painter.setPen(QPen(border, 1))
            painter.setBrush(self._colors["hover"] if self.underMouse() or self.isDown() else Qt.NoBrush)
        painter.drawRoundedRect(rect, 12, 12)

    def _paint_ring(self, painter):
        ring = self._ink if self._primary else self._colors["accent"]
        painter.setPen(QPen(ring, 1.4))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(2, 2, -2, -2), 10, 10)
