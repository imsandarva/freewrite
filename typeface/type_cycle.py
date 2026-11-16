"""The face control. The word is drawn in the face it names."""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor, QFontMetrics

from typeface.constants import _SPECIMEN
from typeface.fade_word import _FadeWord
from typeface.families import writing_faces
from typeface.metrics import _advance
from typeface.specimen import specimen


class TypeCycle(_FadeWord):
    chosen = pyqtSignal(str)

    def __init__(self, paper, face="Lato", parent=None):
        self._faces = writing_faces()
        self._index = _index_for(self._faces, face)
        super().__init__("typeCycle", paper, parent)
        self._fit_faces()
        label, family = self._faces[self._index]
        self._set_word(label, specimen(family, _SPECIMEN), False)
        self._announce()

    def family(self):
        return self._faces[self._index][1]

    def label(self):
        return self._faces[self._index][0]

    def _fit_faces(self):
        widest = 0
        for label, family in self._faces:
            widest = max(widest, _advance(QFontMetrics(specimen(family, _SPECIMEN)), label))
        self.setFixedWidth(int(widest + 12))

    def _access(self):
        return "%s, typeface" % self._faces[self._index][0]

    def _rest_ink(self):
        return QColor(self._paper.ink)

    def _hot_ink(self):
        return QColor(self._paper.hover)

    def _activate(self):
        self._index = (self._index + 1) % len(self._faces)
        label, family = self._faces[self._index]
        self._set_word(label, specimen(family, _SPECIMEN), True)
        self.chosen.emit(family)


def _index_for(faces, face):
    want = str(face or "").strip().lower()
    for index, (label, _family) in enumerate(faces):
        if label.lower() == want: return index
    return 0
