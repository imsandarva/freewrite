"""The writing surface. Backspace can be turned off, and writing keys can click."""

from PyQt5.QtWidgets import QTextEdit

from editing.keys import is_backspace, key_kind


class WritingEdit(QTextEdit):
    def __init__(self, backspace_on=True, clicks=None, parent=None):
        super().__init__(parent)
        self._backspace_on = backspace_on
        self._clicks = clicks

    def set_backspace_allowed(self, on):
        self._backspace_on = bool(on)

    def keyPressEvent(self, event):
        if is_backspace(event) and not self._backspace_on: return
        self._click(event)
        super().keyPressEvent(event)

    def _click(self, event):
        if self._clicks is None: return
        kind = key_kind(event)
        if kind: self._clicks.play(kind)
