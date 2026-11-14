"""The word that opens Trash, sitting on the count line in History."""

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PyQt5.QtWidgets import QAbstractButton

from history.face import face
from typeface.metrics import _advance


class TrashLink(QAbstractButton):
    """Trash, with a small count when something is waiting there."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._count = 0
        self._ink = QColor("#8A8178")
        self._hot = QColor("#A6845B")
        self._fill = QColor(166, 132, 91, 22)
        self._accent = QColor("#A6845B")
        self._pill = QColor(166, 132, 91, 36)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAccessibleName("Trash")
        self.setToolTip("Open Trash")
        self.setStyleSheet("QAbstractButton { background: transparent; border: none; }")
        self._fit()

    def apply_colors(self, palette):
        self._ink = QColor(palette["muted"])
        self._hot = QColor(palette["title"])
        self._accent = QColor(palette["accent"])
        self._fill = QColor(palette["hover"])
        self._pill = QColor(palette["accent"])
        self._pill.setAlpha(42 if palette["sheet"].lightness() >= 40 else 64)
        self.update()

    def set_count(self, count):
        self._count = max(0, int(count))
        self.setAccessibleName("Trash" if not self._count else "Trash, %d" % self._count)
        self._fit()
        self.update()

    def _font(self):
        return face(13, QFont.Normal, 0.35)

    def _count_font(self):
        return face(11, QFont.Bold, 0.15)

    def _pill_width(self):
        if not self._count: return 0
        label = "99+" if self._count > 99 else str(self._count)
        return max(16, _advance(QFontMetrics(self._count_font()), label) + 8)

    def _fit(self):
        word = _advance(QFontMetrics(self._font()), "Trash")
        extra = (6 + self._pill_width()) if self._count else 0
        self.setFixedSize(int(12 + word + extra + 12), 32)

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
        if hot: self._paint_wash(painter)
        font = self._font()
        painter.setFont(font)
        painter.setPen(self._hot if hot else self._accent)
        word = _advance(QFontMetrics(font), "Trash")
        painter.drawText(QRectF(12, 0, word + 2, self.height()), Qt.AlignLeft | Qt.AlignVCenter, "Trash")
        if self._count: self._paint_count(painter, 12 + word + 6)
        if self.hasFocus(): self._paint_ring(painter)

    def _paint_wash(self, painter):
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._fill)
        painter.drawRoundedRect(QRectF(1, 2, self.width() - 2, self.height() - 4), 10, 10)

    def _paint_count(self, painter, x):
        label = "99+" if self._count > 99 else str(self._count)
        font = self._count_font()
        width = self._pill_width()
        rect = QRectF(x, (self.height() - 16) / 2, width, 16)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._pill)
        painter.drawRoundedRect(rect, 8, 8)
        painter.setFont(font)
        painter.setPen(self._accent)
        painter.drawText(rect, Qt.AlignCenter, label)

    def _paint_ring(self, painter):
        painter.setPen(QPen(self._accent, 1.2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(QRectF(1.5, 2.5, self.width() - 3, self.height() - 5), 10, 10)
