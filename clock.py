"""The fifteen-minute clock.

Idle reads 15:00. Running counts down in place. Each digit has a fixed cell,
so the bar does not shift as the numbers change. A small clay mark is the
only sign that it is going.
"""

from PyQt5.QtCore import QEasingCurve, QEvent, QPropertyAnimation, QRectF, Qt, pyqtProperty, pyqtSignal
from PyQt5.QtGui import QColor, QFontMetrics, QPainter, QPen
from PyQt5.QtWidgets import QSizePolicy, QWidget

from typeface import _advance, _mix, _note_dark, load_lato, specimen


class QuietClock(QWidget):
    clicked = pyqtSignal()

    def __init__(self, dark=False, parent=None):
        super().__init__(parent)
        load_lato()
        self._dark = bool(dark)
        self._seconds, self._running = 900, False
        self._live, self._warm = 0.0, 0.0
        self._hover = self._down = self._pointer = False
        self._font = specimen("Lato", 13)
        self._live_anim = QPropertyAnimation(self, b"live", self)
        self._live_anim.setDuration(220)
        self._live_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._warm_anim = QPropertyAnimation(self, b"warm", self)
        self._warm_anim.setDuration(150)
        self._warm_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.setObjectName("sessionClock")
        self.setProperty("dark", self._dark)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.TabFocus)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(*self._measure())
        self.setStyleSheet("QWidget#sessionClock { background: transparent; border: none; }")
        self._announce()

    def was_pointer(self):
        return self._pointer

    def show_time(self, seconds, running):
        self._seconds = max(0, int(seconds))
        running = bool(running)
        if running != self._running:
            self._running = running
            self._live_anim.stop()
            self._live_anim.setStartValue(self._live)
            self._live_anim.setEndValue(1.0 if running else 0.0)
            self._live_anim.start()
        self._announce()
        self.update()

    def _announce(self):
        state = "running" if self._running else "ready"
        self.setAccessibleName("Timer, %s, %s" % (self._readout(), state))

    def _readout(self):
        seconds = max(0, int(self._seconds))
        return "%02d:%02d" % (seconds // 60, seconds % 60)

    def _measure(self):
        metrics = QFontMetrics(self._font)
        digit, colon = _advance(metrics, "0"), _advance(metrics, ":")
        # Mark, gap, four digits, colon, a little air. The mark's space stays when the clock is idle.
        return int(8 + 6 + 8 + digit * 4 + colon + 8), 34

    def _live_pos(self):
        return self._live

    def _set_live_pos(self, value):
        self._live = float(value)
        self.update()

    live = pyqtProperty(float, _live_pos, _set_live_pos)

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
        self.clicked.emit()
        self.update()

    def mouseReleaseEvent(self, event):
        self._down = False
        self.update()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            self._pointer = False
            self.clicked.emit()
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

    def _digit_color(self):
        if self._dark:
            idle, running, hot = QColor("#9C958C"), QColor("#D4B496"), QColor("#F7F4EF")
        else:
            idle, running, hot = QColor("#8A8178"), QColor("#8C6842"), QColor("#1C1917")
        base = _mix(idle, running, self._live)
        return _mix(base, hot, self._warm * (0.35 if self._running else 1))

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        self._paint_mark(painter)
        self._paint_digits(painter)
        self._paint_focus(painter)

    def _paint_mark(self, painter):
        if self._live <= 0.01: return
        color = QColor("#D4B496") if self._dark else QColor("#A6845B")
        color.setAlphaF(0.95 * self._live)
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(QRectF(8, (self.height() - 5) / 2.0, 5, 5))

    def _paint_digits(self, painter):
        metrics = QFontMetrics(self._font)
        digit, colon = float(_advance(metrics, "0")), float(_advance(metrics, ":"))
        x = 8 + 6 + 8
        painter.setFont(self._font)
        painter.setPen(self._digit_color())
        painter.setOpacity(0.72 if self._down else 1)
        for char in self._readout():
            cell = colon if char == ":" else digit
            painter.drawText(QRectF(x, 0, cell, self.height()), Qt.AlignCenter, char)
            x += cell
        painter.setOpacity(1)

    def _paint_focus(self, painter):
        if not self.hasFocus(): return
        color = QColor("#D4B496") if self._dark else QColor("#B08968")
        painter.setPen(QPen(color, 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(QRectF(0.5, 3.5, self.width() - 1, self.height() - 7), 8, 8)
