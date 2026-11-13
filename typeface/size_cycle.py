"""The size control. Each click steps to the next size."""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor

from typeface.constants import _CHROME
from typeface.fade_word import _FadeWord
from typeface.specimen import specimen


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
