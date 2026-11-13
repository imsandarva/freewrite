"""A small on/off pill shared by Backspace and Sound."""

from PyQt5.QtCore import QEasingCurve, QEvent, QPropertyAnimation, QRectF, QSize, Qt, pyqtProperty, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PyQt5.QtWidgets import QSizePolicy, QWidget

_TRACK_W, _TRACK_H, _KNOB, _PAD, _RIGHT = 40.0, 22.0, 16.0, 3.0, 8.0


def _clamp(value):
    return 0.0 if value < 0 else 1.0 if value > 1 else value


def _mix(a, b, t):
    t = _clamp(t)
    return QColor(
        int(a.red() + (b.red() - a.red()) * t), int(a.green() + (b.green() - a.green()) * t),
        int(a.blue() + (b.blue() - a.blue()) * t), int(a.alpha() + (b.alpha() - a.alpha()) * t),
    )


def _sink(color, amount):
    return QColor(max(0, color.red() - amount), max(0, color.green() - amount), max(0, color.blue() - amount))


def _width(metrics, text):
    return metrics.horizontalAdvance(text) if hasattr(metrics, "horizontalAdvance") else metrics.width(text)


def _palette(dark, hover):
    """Neutral when off, clay when on. The old pill used the clay for off, so it read backwards."""
    if dark:
        return {"label": QColor("#F4F0EA" if hover else "#9C958C"), "off": QColor("#3A3531"), "on": QColor("#D4B496"), "knob": QColor("#F7F3EE"), "shadow": 90}
    return {"label": QColor("#1C1917" if hover else "#808080"), "off": QColor("#E4DFD8"), "on": QColor("#B08968"), "knob": QColor("#FFFCF8"), "shadow": 46}


class QuietSwitch(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, label, on=True, dark=False, parent=None):
        super().__init__(parent)
        self._label, self._on, self._dark = label, bool(on), bool(dark)
        self._hover = self._pointer = self._down = False
        self._knob = 1.0 if self._on else 0.0
        self._slide = QPropertyAnimation(self, b"knob", self)
        self._slide.setDuration(200)
        self._slide.setEasingCurve(QEasingCurve.OutCubic)
        self.setObjectName("quietSwitch")
        self.setProperty("dark", self._dark)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.TabFocus)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(self.sizeHint())
        self.setStyleSheet("QWidget#quietSwitch { background: transparent; border: none; }")
        self._announce()

    def sizeHint(self):
        text = _width(QFontMetrics(self._font()), self._label)
        return QSize(int(2 + text + 8 + _TRACK_W + _RIGHT), 32)

    def was_pointer(self):
        """True when the last flip came from the pointer, so the page can take the caret back."""
        return self._pointer

    def set_on(self, on, animate=True):
        self._on = bool(on)
        self._announce()
        self._slide.stop()
        end = 1.0 if self._on else 0.0
        if animate and abs(self._knob - end) > 0.001:
            self._slide.setStartValue(self._knob)
            self._slide.setEndValue(end)
            self._slide.start()
            return
        self._knob = end
        self.update()

    def _announce(self):
        self.setAccessibleName("%s, %s" % (self._label, "on" if self._on else "off"))

    def _flip(self, pointer):
        self._pointer = pointer
        self.set_on(not self._on)
        self.toggled.emit(self._on)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._down = True
            self._flip(True)
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._down = False
        self.update()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            self._flip(False)
            return
        super().keyPressEvent(event)

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = self._down = False
        self.update()
        super().leaveEvent(event)

    def event(self, event):
        if event.type() == QEvent.DynamicPropertyChange and bytes(event.propertyName()) == b"dark":
            self._dark = self.property("dark") is True
            self.update()
        return super().event(event)

    def _knob_pos(self):
        return self._knob

    def _set_knob_pos(self, value):
        self._knob = float(value)
        self.update()

    knob = pyqtProperty(float, _knob_pos, _set_knob_pos)

    def _font(self):
        font = QFont("Lato")
        font.setPixelSize(13)
        font.setWeight(QFont.Normal)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 0.15)
        return font

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        colors = _palette(self._dark, self._hover)
        self._paint_label(painter, colors)
        track = self._track_rect()
        self._paint_track(painter, track, colors)
        self._paint_knob(painter, track, colors)
        self._paint_focus(painter, colors)

    def _track_rect(self):
        return QRectF(self.width() - _RIGHT - _TRACK_W, (self.height() - _TRACK_H) / 2.0, _TRACK_W, _TRACK_H)

    def _paint_label(self, painter, colors):
        painter.setFont(self._font())
        painter.setPen(colors["label"])
        track = self._track_rect()
        painter.drawText(QRectF(2, 0, max(0, track.x() - 10), self.height()), Qt.AlignVCenter | Qt.AlignLeft, self._label)

    def _paint_track(self, painter, track, colors):
        fill = _mix(colors["off"], colors["on"], self._knob)
        edge = _mix(_sink(colors["off"], 16), colors["on"], self._knob)
        painter.setPen(QPen(edge, 1))
        painter.setBrush(fill)
        painter.drawRoundedRect(track.adjusted(0.5, 0.5, -0.5, -0.5), _TRACK_H / 2, _TRACK_H / 2)

    def _paint_knob(self, painter, track, colors):
        travel = track.width() - _KNOB - _PAD * 2
        shrink = 1.25 if self._down else 0.0
        side = _KNOB - shrink
        x = track.x() + _PAD + shrink / 2 + travel * _clamp(self._knob)
        y = track.y() + (track.height() - side) / 2
        shadow = QColor(40, 28, 18, int(colors["shadow"] * (0.45 if self._down else 1)))
        painter.setPen(Qt.NoPen)
        painter.setBrush(shadow)
        painter.drawEllipse(QRectF(x, y + 0.8, side, side))
        painter.setPen(QPen(QColor(90, 70, 50, 32 if not self._dark else 60), 1))
        painter.setBrush(colors["knob"])
        painter.drawEllipse(QRectF(x, y, side, side))

    def _paint_focus(self, painter, colors):
        if not self.hasFocus(): return
        painter.setPen(QPen(colors["on"], 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(QRectF(1, 3.5, self.width() - 2, self.height() - 7), 9, 9)
