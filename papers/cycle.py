"""The paper you are writing on, shown as its name. A press brings the next one."""

from PyQt5.QtCore import Qt, pyqtSignal

from papers.catalog import ORDER, PAPERS
from typeface.constants import _CHROME
from typeface.fade_word import _FadeWord
from typeface.specimen import specimen


class PaperCycle(_FadeWord):
    """The paper you are writing on. The word crossfades; the page follows."""

    chosen = pyqtSignal(str)

    def __init__(self, paper, parent=None):
        self._papers = [PAPERS[key] for key in ORDER]
        self._index = ORDER.index(paper.key)
        super().__init__("paperCycle", paper, parent)
        self._font = specimen("Lato", _CHROME)
        self._fit([item.label for item in self._papers], self._font)
        self.setFixedWidth(self.width() + 8)
        self._set_word(paper.label, self._font, False)
        self._announce()

    def apply_paper(self, paper):
        super().apply_paper(paper)
        self._index = ORDER.index(paper.key)
        # A press already started the crossfade. Applying the paper must not restart it.
        if self._text != paper.label: self._set_word(paper.label, self._font, False)

    def _align(self):
        return Qt.AlignCenter

    def _access(self):
        return "%s, paper" % self._papers[self._index].label

    def _activate(self):
        self._index = (self._index + 1) % len(self._papers)
        paper = self._papers[self._index]
        self._set_word(paper.label, self._font, True)
        self.chosen.emit(paper.key)
