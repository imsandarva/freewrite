"""The note that appears once the page fills the screen."""

from PyQt5.QtCore import Qt, QRectF, QTimer, QVariantAnimation
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QWidget

from history.face import face
from history.lato import ensure_lato
from history.motion import ease_out
from papers.catalog import mix, paper_for
from typeface.metrics import _advance

_LEAD, _KEY, _REST = "Press", "esc", "to exit fullscreen"
_HOLD_MS, _IN_MS, _OUT_MS = 2000, 420, 320
_PILL_H, _KEY_H, _PAD_X, _GAP, _LIFT, _BOTTOM = 46, 24, 20, 10, 8, 40


def _ink(paper):
    """A capsule lifted off the page. The key is the only clay."""
    dark = bool(paper.dark)
    fill = QColor(mix(paper.page, "#FFFFFF", 0.14 if dark else 0.7))
    text = QColor(paper.hover if dark else paper.ink)
    key = QColor(mix(paper.page, paper.accent, 0.34 if dark else 0.22))
    key_text = QColor(mix(paper.accent, "#FFF8F0" if dark else paper.ink, 0.62 if dark else 0.42))
    key_line, line = QColor(paper.accent), QColor(255, 246, 236, 42) if dark else QColor(paper.ink)
    key_line.setAlpha(120 if dark else 84)
    if not dark: line.setAlpha(36)
    shadow = QColor(0, 0, 0, 110) if dark else QColor(72, 48, 28, 48)
    return {"fill": fill, "line": line, "text": text, "key": key, "key_line": key_line, "key_text": key_text, "shadow": shadow}


def _type(px, weight, spacing):
    """Gray edges only. Color antialiasing fringes the sentence, especially on the dark pill."""
    font = face(px, weight, spacing)
    font.setStyleStrategy(QFont.PreferAntialias | QFont.NoSubpixelAntialias)
    return font


def _measure():
    body, key_font = _type(15, QFont.Normal, 0.25), _type(12, QFont.Bold, 0.45)
    lead = _advance(QFontMetrics(body), _LEAD)
    rest = _advance(QFontMetrics(body), _REST)
    key_w = max(44, _advance(QFontMetrics(key_font), _KEY) + 20)
    width = _PAD_X + lead + _GAP + key_w + _GAP + rest + _PAD_X
    return {"body": body, "key_font": key_font, "lead": lead, "rest": rest, "key_w": key_w, "width": width}


class ExitHint(QWidget):
    """A capsule at the bottom. It fades in, stays two seconds, then fades out."""

    def __init__(self, parent=None):
        super().__init__(parent)
        ensure_lato()
        self._shown = 0.0
        self._leaving = False
        self._rest = (0, 0)
        self._box = _measure()
        self._ink = _ink(paper_for("white"))
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(40)
        self._shadow.setOffset(0, 6)
        self._shadow.setEnabled(False)
        self.setGraphicsEffect(self._shadow)
        self._anim = QVariantAnimation(self)
        self._anim.setEasingCurve(ease_out())
        self._anim.valueChanged.connect(self._on_frame)
        self._anim.finished.connect(self._on_settled)
        self._hold = QTimer(self)
        self._hold.setSingleShot(True)
        self._hold.timeout.connect(self._leave)
        self.setObjectName("exitHint")
        self.setStyleSheet("QWidget#exitHint { background: transparent; border: none; }")
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setAccessibleName("%s %s %s" % (_LEAD, _KEY, _REST))
        self.setFixedSize(self._box["width"], _PILL_H)
        self.hide()

    def apply_paper(self, paper):
        self._ink = _ink(paper)
        self._shadow.setColor(self._ink["shadow"])
        self.update()

    def show_briefly(self, paper):
        """Arrive, hold long enough to read, then leave. A second call starts that over."""
        self.apply_paper(paper)
        self._leaving = False
        self._hold.stop()
        self.place()
        self.show()
        self.raise_()
        self._run(self._shown, 1.0, _IN_MS)

    def dismiss(self):
        self._hold.stop()
        self._anim.stop()
        self._shown = 0.0
        self._leaving = False
        self.hide()

    def place(self):
        parent = self.parentWidget()
        if parent is None: return
        x = max(0, (parent.width() - self.width()) // 2)
        y = max(0, parent.height() - self.height() - _BOTTOM)
        self._rest = (x, y)
        self._move()

    def showEvent(self, event):
        super().showEvent(event)
        self._shadow.setEnabled(True)

    def hideEvent(self, event):
        self._shadow.setEnabled(False)
        super().hideEvent(event)

    def paintEvent(self, _event):
        if self._shown <= 0.001: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setOpacity(self._shown)
        self._paint_capsule(painter)
        self._paint_sentence(painter)

    def _run(self, start, end, duration):
        self._anim.stop()
        self._anim.setStartValue(float(start))
        self._anim.setEndValue(float(end))
        self._anim.setDuration(duration)
        self._anim.start()

    def _on_frame(self, value):
        self._shown = float(value)
        self._move()
        self.update()

    def _on_settled(self):
        if self._leaving:
            self._shown = 0.0
            self._leaving = False
            self.hide()
            return
        self._shown = 1.0
        self._move()
        self.update()
        self._hold.start(_HOLD_MS)

    def _leave(self):
        if not self.isVisible(): return
        self._leaving = True
        self._run(self._shown, 0.0, _OUT_MS)

    def _move(self):
        x, y = self._rest
        self.move(x, y + int(round((1.0 - self._shown) * _LIFT)))

    def _paint_capsule(self, painter):
        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        radius = rect.height() / 2
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._ink["fill"])
        painter.drawRoundedRect(rect, radius, radius)
        pen = QPen(self._ink["line"])
        pen.setWidthF(1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect, radius, radius)

    def _paint_sentence(self, painter):
        box, ink = self._box, self._ink
        key_y = (_PILL_H - _KEY_H) / 2
        key_x = _PAD_X + box["lead"] + _GAP
        key = QRectF(key_x, key_y, box["key_w"], _KEY_H)
        painter.setPen(Qt.NoPen)
        painter.setBrush(ink["key"])
        painter.drawRoundedRect(key, 7, 7)
        pen = QPen(ink["key_line"])
        pen.setWidthF(1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(key.adjusted(0.5, 0.5, -0.5, -0.5), 6.5, 6.5)
        painter.setFont(box["key_font"])
        painter.setPen(ink["key_text"])
        painter.drawText(key.adjusted(0, -0.5, 0, -0.5), Qt.AlignCenter, _KEY)
        painter.setFont(box["body"])
        painter.setPen(ink["text"])
        line = QRectF(0, -0.5, self.width(), _PILL_H)
        painter.drawText(line.adjusted(_PAD_X, 0, 0, 0), Qt.AlignVCenter | Qt.AlignLeft, _LEAD)
        rest_x = key_x + box["key_w"] + _GAP
        painter.drawText(QRectF(rest_x, -0.5, box["rest"] + 2, _PILL_H), Qt.AlignVCenter | Qt.AlignLeft, _REST)
