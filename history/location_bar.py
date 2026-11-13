"""Where the notes are saved, pinned under the list so it stays in reach."""

from PyQt5.QtCore import QEasingCurve, Qt, QRectF, QVariantAnimation
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PyQt5.QtWidgets import QAbstractButton, QSizePolicy

from history.face import face
from history.palette import colors


def _advance(font, text):
    metrics = QFontMetrics(font)
    if hasattr(metrics, "horizontalAdvance"): return metrics.horizontalAdvance(text)
    return metrics.width(text)


def _mix(a, b, t):
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    return QColor(
        int(a.red() + (b.red() - a.red()) * t), int(a.green() + (b.green() - a.green()) * t),
        int(a.blue() + (b.blue() - a.blue()) * t), int(a.alpha() + (b.alpha() - a.alpha()) * t),
    )


class LocationBar(QAbstractButton):
    """Where the notes are saved, pinned under the list so it stays in reach."""

    def __init__(self):
        super().__init__()
        self._colors = colors(False)
        self._shown, self._full = "", ""
        self._wash, self._blend = 0.0, 0.0
        self._wash_anim = QVariantAnimation(self)
        self._wash_anim.setDuration(180)
        self._wash_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._wash_anim.valueChanged.connect(self._set_wash)
        self._glow_anim = QVariantAnimation(self)
        self._glow_anim.setDuration(680)
        self._glow_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._glow_anim.valueChanged.connect(self._set_blend)
        self.setFixedHeight(86)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.TabFocus)
        self.setAccessibleName("Change where notes are saved")
        self.setStyleSheet("QAbstractButton { background: transparent; border: none; outline: none; }")
        self.setAutoFillBackground(False)
        self.pressed.connect(self.update)
        self.released.connect(self.update)

    def apply_colors(self, palette):
        self._colors = palette
        self.update()

    def set_place(self, shown, full):
        changed = bool(self._full) and full != self._full
        self._shown, self._full = shown, full
        self.setToolTip(full)
        self.setAccessibleDescription("Notes are saved in %s" % full)
        self.update()
        if changed: self._glow()

    def enterEvent(self, event):
        self._glide(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._glide(0.0)
        super().leaveEvent(event)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.fillRect(self.rect(), self._colors["sheet"])
        self._paint_wash(painter)
        self._paint_rule(painter)
        self._paint_words(painter)
        if self.hasFocus(): self._paint_focus(painter)

    def _paint_wash(self, painter):
        amount = 1.0 if self.isDown() else self._wash
        if amount <= 0: return
        color = QColor(self._colors["selected"] if self.isDown() else self._colors["hover"])
        color.setAlpha(int(color.alpha() * amount))
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawRoundedRect(QRectF(10, 8, self.width() - 20, self.height() - 16), 12, 12)

    def _paint_rule(self, painter):
        warm = QColor(self._colors["accent"])
        warm.setAlpha(min(150, self._colors["line"].alpha() + 80))
        painter.setPen(QPen(_mix(self._colors["line"], warm, self._wash), 1))
        painter.drawLine(0, 0, self.width(), 0)

    def _paint_words(self, painter):
        change_font, path_font = face(13, QFont.Normal, 0.16), face(15, QFont.Normal, -0.12)
        change_w = _advance(change_font, "Change")
        shift = 2 * (1.0 if self.isDown() else self._wash)
        change_x = self.width() - 26 - change_w + shift
        path_w = max(24, change_x - 18 - 26)
        painter.setPen(self._colors["muted"])
        painter.setFont(face(12, QFont.Bold, 0.3))
        painter.drawText(QRectF(26, 16, path_w, 18), Qt.AlignLeft | Qt.AlignVCenter, "Saved in")
        painter.setPen(_mix(self._colors["title"], self._colors["accent"], self._blend))
        painter.setFont(path_font)
        shown = QFontMetrics(path_font).elidedText(self._shown, Qt.ElideMiddle, int(path_w))
        painter.drawText(QRectF(26, 38, path_w, 26), Qt.AlignLeft | Qt.AlignVCenter, shown)
        painter.setPen(self._colors["accent"])
        painter.setFont(change_font)
        painter.drawText(QRectF(change_x, 38, change_w + 4, 26), Qt.AlignLeft | Qt.AlignVCenter, "Change")

    def _paint_focus(self, painter):
        painter.setPen(QPen(self._colors["accent"], 1.2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(QRectF(10.5, 8.5, self.width() - 21, self.height() - 17), 12, 12)

    def _glide(self, end):
        self._wash_anim.stop()
        self._wash_anim.setStartValue(self._wash)
        self._wash_anim.setEndValue(end)
        self._wash_anim.start()

    def _glow(self):
        self._glow_anim.stop()
        self._blend = 1.0
        self._glow_anim.setStartValue(1.0)
        self._glow_anim.setEndValue(0.0)
        self._glow_anim.start()

    def _set_wash(self, value):
        self._wash = float(value)
        self.update()

    def _set_blend(self, value):
        self._blend = float(value)
        self.update()
