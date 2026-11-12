"""The face you are writing in, shown as one word.

Lato is up when a session starts. Each click brings the next face in, and the
page follows. The word is drawn in that face, so the control is the specimen.
Size sits beside it and steps the same way.
"""

import os

from PyQt5.QtCore import QEasingCurve, QEvent, QPropertyAnimation, QRectF, Qt, pyqtProperty, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QFontDatabase, QFontMetrics, QPainter, QPen, QTextCharFormat, QTextCursor
from PyQt5.QtWidgets import QPushButton, QSizePolicy, QWidget

_SPECIMEN, _CHROME, _HEIGHT = 14, 13, 34
_lato_ready = False


def load_lato():
    """Register the bundled Lato files once. The family name is Lato, not the file name."""
    global _lato_ready
    if _lato_ready: return
    _lato_ready = True
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
    library = QFontDatabase()
    for name in ("Lato-Light.ttf", "Lato-Regular.ttf", "Lato-Bold.ttf"):
        path = os.path.join(folder, name)
        if os.path.isfile(path): library.addApplicationFont(path)


def _advance(metrics, text):
    return metrics.horizontalAdvance(text) if hasattr(metrics, "horizontalAdvance") else metrics.width(text)


def _mix(a, b, t):
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    return QColor(
        int(a.red() + (b.red() - a.red()) * t), int(a.green() + (b.green() - a.green()) * t),
        int(a.blue() + (b.blue() - a.blue()) * t), int(a.alpha() + (b.alpha() - a.alpha()) * t),
    )


def _first_family(candidates, fallback):
    have = set(QFontDatabase().families())
    for name in candidates:
        if name in have: return name
    return fallback


def writing_faces():
    """Lato, then a grotesque, the desktop face, and a book serif. Labels stay short."""
    load_lato()
    system = QFontDatabase.systemFont(QFontDatabase.GeneralFont).family() or "Sans Serif"
    arial = _first_family(("Arial", "Liberation Sans", "Carlito", "DejaVu Sans"), system)
    serif = _first_family(
        ("Gentium Book Basic", "Gentium", "Liberation Serif", "Bitstream Charter", "Caladea", "Times New Roman", "DejaVu Serif", "FreeSerif"),
        "DejaVu Serif",
    )
    lato = _first_family(("Lato",), system)
    return (("Lato", lato), ("Arial", arial), ("System", system), ("Serif", serif))


def specimen(family, px):
    load_lato()
    font = QFont(family)
    font.setPixelSize(int(px))
    font.setWeight(QFont.Normal)
    font.setStyleStrategy(QFont.PreferAntialias)
    return font


def apply_face(edit, family, pixels):
    """Restyle the page, words already written included, without moving the caret.

    A theme reload polishes the editor and puts the widget font back to the
    application default. The characters keep their own font, which is why the
    face is written onto them and onto the caret, not only onto the widget.
    """
    font = specimen(family, pixels)
    cursor = edit.textCursor()
    position, anchor = cursor.position(), cursor.anchor()
    scroll = edit.verticalScrollBar().value()
    edit.setUpdatesEnabled(False)
    edit.blockSignals(True)
    try:
        edit.setFont(font)
        edit.document().setDefaultFont(font)
        fmt = QTextCharFormat()
        fmt.setFont(font)
        if edit.document().characterCount() > 1:
            whole = QTextCursor(edit.document())
            whole.select(QTextCursor.Document)
            whole.setCharFormat(fmt)
        edit.setCurrentCharFormat(fmt)
        restored = edit.textCursor()
        restored.setPosition(anchor)
        if position != anchor: restored.setPosition(position, QTextCursor.KeepAnchor)
        edit.setTextCursor(restored)
        edit.verticalScrollBar().setValue(scroll)
    finally:
        edit.blockSignals(False)
        edit.setUpdatesEnabled(True)


def text_button(label, dark):
    button = QPushButton(label)
    button.setProperty("dark", bool(dark))
    button.setCursor(Qt.PointingHandCursor)
    button.setFocusPolicy(Qt.TabFocus)
    return button


def _note_dark(widget, event):
    if event.type() == QEvent.DynamicPropertyChange and bytes(event.propertyName()) == b"dark":
        widget._dark = widget.property("dark") is True
        widget.update()


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


class SizeCycle(_FadeWord):
    chosen = pyqtSignal(int)

    def __init__(self, sizes, current, dark=False, parent=None):
        self._sizes = [int(size) for size in sizes]
        self._index = self._sizes.index(int(current)) if int(current) in self._sizes else 0
        super().__init__("sizeCycle", dark, parent)
        self._font = specimen("Lato", _CHROME)
        self._fit([self._px(size) for size in self._sizes], self._font)
        self._set_word(self._px(self._sizes[self._index]), self._font, False)
        self._announce()

    def _px(self, size):
        return "%dpx" % int(size)

    def _access(self):
        return "%d pixels" % self._sizes[self._index]

    def _rest_ink(self):
        return QColor("#9C958C") if self._dark else QColor("#8A8178")

    def _hot_ink(self):
        return QColor("#F7F4EF") if self._dark else QColor("#1C1917")

    def _activate(self):
        self._index = (self._index + 1) % len(self._sizes)
        self._set_word(self._px(self._sizes[self._index]), specimen("Lato", _CHROME), True)
        self.chosen.emit(self._sizes[self._index])


class TypeCycle(_FadeWord):
    chosen = pyqtSignal(str)

    def __init__(self, dark=False, parent=None):
        self._faces = writing_faces()
        self._index = 0
        super().__init__("typeCycle", dark, parent)
        self._fit_faces()
        label, family = self._faces[0]
        self._set_word(label, specimen(family, _SPECIMEN), False)
        self._announce()

    def family(self):
        return self._faces[self._index][1]

    def _fit_faces(self):
        widest = 0
        for label, family in self._faces:
            widest = max(widest, _advance(QFontMetrics(specimen(family, _SPECIMEN)), label))
        self.setFixedWidth(int(widest + 12))

    def _access(self):
        return "%s, typeface" % self._faces[self._index][0]

    def _rest_ink(self):
        return QColor("#F4F1EC") if self._dark else QColor("#2A2622")

    def _activate(self):
        self._index = (self._index + 1) % len(self._faces)
        label, family = self._faces[self._index]
        self._set_word(label, specimen(family, _SPECIMEN), True)
        self.chosen.emit(family)

    def _paint_mark(self, painter):
        """A short clay rule under the word. It eases from the old width to the new one."""
        showing, shown_font = (self._prev, self._prev_font) if self._prev and self._blend < 0.38 else (self._text, self._font)
        end = _advance(QFontMetrics(shown_font), showing) if showing else 0
        if end <= 1: return
        strength = 0.42 + 0.58 * self._warm
        if self._blend < 1: strength = min(1.0, strength + 0.35 * (1 - self._blend))
        color = QColor("#D4B496") if self._dark else QColor("#A6845B")
        color.setAlphaF(strength)
        painter.setPen(QPen(color, 1.15, Qt.SolidLine, Qt.RoundCap))
        y = self.height() - 6
        painter.drawLine(QRectF(2, y, end, 0).topLeft(), QRectF(2 + end, y, 0, 0).topLeft())


class BarRule(QWidget):
    """The quiet divider between the type controls and the session controls."""

    def __init__(self, dark=False, parent=None):
        super().__init__(parent)
        self._dark = bool(dark)
        self.setObjectName("barRule")
        self.setProperty("dark", self._dark)
        self.setFixedSize(1, 16)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setStyleSheet("QWidget#barRule { background: transparent; border: none; }")

    def event(self, event):
        _note_dark(self, event)
        return super().event(event)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(244, 241, 236, 70) if self._dark else QColor(42, 34, 26, 58))
