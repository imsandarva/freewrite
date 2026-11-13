"""The face control. The word is drawn in the face it names."""

from PyQt5.QtCore import QRectF, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFontMetrics, QPainter, QPen

from typeface.constants import _SPECIMEN
from typeface.fade_word import _FadeWord
from typeface.families import writing_faces
from typeface.metrics import _advance
from typeface.specimen import specimen


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
