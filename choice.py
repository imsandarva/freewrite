"""The question asked when the notes folder changes.

Dismissing it, or Cancel, keeps the current folder. Leave keeps the old notes
where they are. Move is the only path that relocates them. Enter is ignored
for a moment after the folder picker closes, so confirming that picker cannot
also answer this one.
"""

import time

from PyQt5.QtCore import QPoint, QRectF, Qt, QTimer, QVariantAnimation
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PyQt5.QtWidgets import QAbstractButton, QDialog, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from history import colors, ease_out, ensure_lato, face

_GUARD_S = 0.22


def ask_move(parent, path, dark, count, crowded):
    """'move', 'leave', or 'cancel'. Cancel keeps the folder that was already in use."""
    title = "Bring this note with you?" if count == 1 else "Bring your notes with you?"
    leave, move = ("Leave it", "Move it") if count == 1 else ("Leave them", "Move them")
    return _Prompt.open(parent, dark, title, _sentence(count, crowded), path, ((leave, "leave", False), (move, "move", True)), True)


def tell(parent, title, body, dark):
    _Prompt.open(parent, dark, title, body, "", (("Okay", "okay", True),), False)


def _sentence(count, crowded):
    if count == 1:
        opening = "Your note can move into this folder and sit alongside the notes already there" if crowded else "Your note can move into this folder"
        return "%s, or it can stay where it is. Anything you write from now on will be saved here." % opening
    opening = "Your %d notes can move into this folder and sit alongside the notes already there" if crowded else "Your %d notes can move into this folder"
    return "%s, or they can stay where they are. Anything you write from now on will be saved here." % (opening % count)


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


def _ink_on(accent):
    return QColor("#1C1917") if accent.lightness() > 150 else QColor("#FBF9F6")


class _Line(QWidget):
    def __init__(self, text, color, px, weight, spacing, height):
        super().__init__()
        self._text, self._color, self._font = text, color, face(px, weight, spacing)
        self.setFixedHeight(height)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setPen(self._color)
        painter.setFont(self._font)
        painter.drawText(self.rect(), Qt.AlignLeft | Qt.AlignVCenter, self._text)


class _Wrapped(QWidget):
    """Body copy with a set line height, so the paragraph has room to breathe."""

    def __init__(self, text, color, width):
        super().__init__()
        self._color = color
        self._font = face(14, QFont.Light, 0.04)
        self._line = 22
        self._lines = _wrap(text, self._font, width)
        self.setFixedSize(width, max(self._line, len(self._lines) * self._line))

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setPen(self._color)
        painter.setFont(self._font)
        for index, line in enumerate(self._lines):
            painter.drawText(QRectF(0, index * self._line, self.width(), self._line), Qt.AlignLeft | Qt.AlignVCenter, line)


def _wrap(text, font, width):
    metrics, lines, line = QFontMetrics(font), [], ""
    for word in text.split():
        trial = word if not line else "%s %s" % (line, word)
        if _advance(metrics, trial) <= width or not line: line = trial
        else:
            lines.append(line)
            line = word
    if line: lines.append(line)
    return lines or [""]


class _Chip(QWidget):
    def __init__(self, path, palette):
        super().__init__()
        self._path, self._colors = path, palette
        self.setFixedHeight(44)
        self.setToolTip(path)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._colors["icon_bg"])
        painter.drawRoundedRect(QRectF(self.rect()), 11, 11)
        font = face(13, QFont.Normal, 0.02)
        painter.setFont(font)
        painter.setPen(self._colors["title"])
        rect = QRectF(self.rect()).adjusted(14, 0, -14, 0)
        shown = QFontMetrics(font).elidedText(self._path, Qt.ElideMiddle, int(rect.width()))
        painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter, shown)


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


class _Card(QWidget):
    def __init__(self, palette, title, body, path, actions, cancel, choose):
        super().__init__()
        self._colors = palette
        self.setFixedWidth(384)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        inner = 384 - 56
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 16)
        layout.setSpacing(0)
        layout.addWidget(_Line(title, palette["title"], 20, QFont.Bold, -0.32, 30))
        layout.addSpacing(10)
        layout.addWidget(_Wrapped(body, palette["body"], inner))
        if path:
            layout.addSpacing(16)
            layout.addWidget(_Chip(path, palette))
        layout.addSpacing(22)
        row = QHBoxLayout()
        row.setSpacing(10)
        for text, choice, primary in actions:
            button = _Button(text, primary, palette)
            button.clicked.connect(lambda _checked=False, picked=choice: choose(picked))
            row.addWidget(button)
        layout.addLayout(row)
        if cancel:
            layout.addSpacing(2)
            quiet = _Quiet(palette)
            quiet.clicked.connect(lambda _checked=False: choose("cancel"))
            layout.addWidget(quiet)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setPen(QPen(self._colors["line"], 1))
        painter.setBrush(self._colors["sheet"])
        painter.drawRoundedRect(rect, 18, 18)

    def mousePressEvent(self, event):
        event.accept()


class _Prompt(QDialog):
    def __init__(self, parent, dark, title, body, path, actions, cancel):
        super().__init__(parent)
        ensure_lato()
        self._dark = bool(dark)
        self._can_cancel = cancel
        self.choice = "cancel" if cancel else "okay"
        self._lift = 10.0
        self._guard_until = 0.0
        self._colors = colors(self._dark)
        self.card = _Card(self._colors, title, body, path, actions, cancel, self._finish)
        self.card.setParent(self)
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(ease_out())
        self._anim.valueChanged.connect(self._arrive)
        self._anim.finished.connect(self._settled)
        self.setModal(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setStyleSheet("QDialog { background: transparent; }")

    @staticmethod
    def open(parent, dark, title, body, path, actions, cancel):
        host = parent.window() if parent is not None else None
        dialog = _Prompt(host, dark, title, body, path, actions, cancel)
        if host is not None:
            origin = host.mapToGlobal(QPoint(0, 0))
            dialog.setGeometry(origin.x(), origin.y(), max(host.width(), 420), max(host.height(), 320))
        else:
            dialog.resize(640, 420)
        dialog.exec_()
        return dialog.choice

    def showEvent(self, event):
        super().showEvent(event)
        self._guard_until = time.monotonic() + _GUARD_S
        self.setWindowOpacity(0)
        self._anim.stop()
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()
        QTimer.singleShot(0, lambda: self.setFocus(Qt.OtherFocusReason))
        QTimer.singleShot(420, self._settled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._place()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 124) if self._dark else QColor(36, 28, 20, 72))
        self._paint_shadow(painter)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.card.geometry().contains(event.pos()):
            self._finish("cancel" if self._can_cancel else "okay")
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and time.monotonic() < self._guard_until:
            event.accept()
            return
        if event.key() == Qt.Key_Escape:
            self._finish("cancel" if self._can_cancel else "okay")
            return
        super().keyPressEvent(event)

    def _finish(self, choice):
        self.choice = choice
        self.done(QDialog.Accepted)

    def _arrive(self, value):
        value = float(value)
        self.setWindowOpacity(0.01 + 0.99 * value)
        self._lift = 10 * (1 - value)
        self._place()

    def _settled(self):
        """If the fade never runs, the prompt must still be visible. A hidden modal would trap the window."""
        if not self.isVisible(): return
        self._lift = 0
        self.setWindowOpacity(1)
        self._place()

    def _place(self):
        self.card.adjustSize()
        width, height = self.card.width(), self.card.sizeHint().height()
        x = max(12, (self.width() - width) // 2)
        y = max(12, int((self.height() - height) / 2 + self._lift))
        self.card.setGeometry(x, y, width, height)
        self.card.raise_()

    def _paint_shadow(self, painter):
        rect = QRectF(self.card.geometry())
        painter.setPen(Qt.NoPen)
        for spread, alpha, drop in ((22, 12, 14), (12, 18, 8), (5, 24, 3)):
            painter.setBrush(QColor(40, 26, 16, alpha))
            painter.drawRoundedRect(rect.adjusted(-spread, drop - spread * 0.25, spread, spread + drop), 22, 22)
