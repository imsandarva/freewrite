"""Body copy with a set line height, so the paragraph has room to breathe."""

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QFont, QFontMetrics, QPainter
from PyQt5.QtWidgets import QWidget

from history.face import face


def _advance(font, text):
    metrics = QFontMetrics(font)
    if hasattr(metrics, "horizontalAdvance"): return metrics.horizontalAdvance(text)
    return metrics.width(text)

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
