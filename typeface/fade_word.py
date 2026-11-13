"""One word that crossfades upward into the next word."""

from PyQt5.QtCore import QEasingCurve, QPropertyAnimation, QRectF, Qt, pyqtProperty
from PyQt5.QtGui import QColor, QFontMetrics, QPainter, QPen
from PyQt5.QtWidgets import QSizePolicy, QWidget

from typeface.blend import _mix
from typeface.constants import _CHROME, _HEIGHT
from typeface.metrics import _advance
from typeface.specimen import specimen
from typeface.theme import _note_dark


class _FadeWord(QWidget):
    """One word that crossfades upward into the next word."""

    def __init__(self, name, dark=False, parent=None):
        super().__init__(parent)
        self._dark = bool(dark)
        self._text, self._prev = "", ""
        self._font = self._prev_font = specimen("Lato", _CHROME)
        self._blend, self._warm = 1.0, 0.0
        self._hover = self._down = self._pointer = False
        self._blend_anim = QPropertyAnimation(self, b"blend", self)
        self._blend_anim.setDuration(210)
        self._blend_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._warm_anim = QPropertyAnimation(self, b"warm", self)
        self._warm_anim.setDuration(150)
        self._warm_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.setObjectName(name)
        self.setProperty("dark", self._dark)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.TabFocus)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedHeight(_HEIGHT)
        self.setStyleSheet("QWidget#%s { background: transparent; border: none; }" % name)

    def was_pointer(self):
        """True when the last step came from the pointer, so the page can take the caret back."""
        return self._pointer

    def _set_word(self, text, font, animate):
        if text == self._text and font.family() == self._font.family() and font.pixelSize() == self._font.pixelSize():
            return
        if animate and self._text:
            self._prev, self._prev_font = self._text, self._font
            self._text, self._font = text, font
            self._blend_anim.stop()
            self._blend = 0.0
            self._blend_anim.setStartValue(0.0)
            self._blend_anim.setEndValue(1.0)
            self._blend_anim.start()
        else:
            self._prev, self._text, self._font, self._blend = "", text, font, 1.0
        self._announce()
        self.update()

    def _announce(self):
        self.setAccessibleName(self._access())

    def _access(self):
        return self._text

    def _activate(self):
        pass

    def _fit(self, texts, font):
        widest = max((_advance(QFontMetrics(font), text) for text in texts), default=24)
        self.setFixedWidth(int(widest + 10))

    def _blend_pos(self):
        return self._blend

    def _set_blend_pos(self, value):
        self._blend = float(value)
        if self._blend >= 1: self._prev = ""
        self.update()

    blend = pyqtProperty(float, _blend_pos, _set_blend_pos)

    def _warm_pos(self):
        return self._warm

    def _set_warm_pos(self, value):
        self._warm = float(value)
        self.update()

    warm = pyqtProperty(float, _warm_pos, _set_warm_pos)

    def _move_warm(self, end):
        self._warm_anim.stop()
        self._warm_anim.setStartValue(self._warm)
        self._warm_anim.setEndValue(end)
        self._warm_anim.start()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton: return super().mousePressEvent(event)
        self._down, self._pointer = True, True
        self._activate()
        self.update()

    def mouseReleaseEvent(self, event):
        self._down = False
        self.update()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            self._pointer = False
            self._activate()
            return
        super().keyPressEvent(event)

    def enterEvent(self, event):
        self._hover = True
        self._move_warm(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = self._down = False
        self._move_warm(0.0)
        super().leaveEvent(event)

    def event(self, event):
        _note_dark(self, event)
        return super().event(event)

    def _rest_ink(self):
        return QColor("#F4F1EC") if self._dark else QColor("#1C1917")

    def _hot_ink(self):
        return QColor("#FFFFFF") if self._dark else QColor("#1C1917")

    def _ink(self):
        return _mix(self._rest_ink(), self._hot_ink(), self._warm)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setClipRect(self.rect())
        # The old word leaves before the new one arrives, so the two names never sit on top of each other.
        if self._prev and self._blend < 1:
            if self._blend < 0.38:
                p = self._blend / 0.38
                self._paint_word(painter, self._prev, self._prev_font, 1 - p, -2.5 * p)
            else:
                p = (self._blend - 0.38) / 0.62
                self._paint_word(painter, self._text, self._font, p, 2.5 * (1 - p))
        else:
            self._paint_word(painter, self._text, self._font, 1, 0)
        self._paint_mark(painter)
        self._paint_focus(painter)

    def _paint_word(self, painter, text, font, opacity, dy):
        if opacity <= 0 or not text: return
        painter.save()
        painter.setOpacity(opacity * (0.72 if self._down else 1))
        painter.setFont(font)
        painter.setPen(self._ink())
        painter.drawText(QRectF(2, dy, self.width() - 4, self.height()), Qt.AlignLeft | Qt.AlignVCenter, text)
        painter.restore()

    def _paint_mark(self, _painter):
        return

    def _paint_focus(self, painter):
        if not self.hasFocus(): return
        color = QColor("#D4B496") if self._dark else QColor("#B08968")
        painter.setPen(QPen(color, 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(QRectF(0.5, 3.5, self.width() - 1, self.height() - 7), 8, 8)

