"""Backspace as a choice on the writing surface, and which keys count as typing.

On, the key erases. Off, it does nothing. Writing starts on the first line.
"""

from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtWidgets import QTextEdit

_ORG, _APP, _KEY = "humansongs", "freewrite", "backspaceEnabled"
_COMMAND = Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier
_SILENT = frozenset({
    Qt.Key_Shift, Qt.Key_Control, Qt.Key_Alt, Qt.Key_Meta, Qt.Key_AltGr,
    Qt.Key_CapsLock, Qt.Key_NumLock, Qt.Key_ScrollLock, Qt.Key_Escape, Qt.Key_Tab,
    Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down, Qt.Key_Home, Qt.Key_End,
    Qt.Key_PageUp, Qt.Key_PageDown, Qt.Key_Insert, Qt.Key_Menu, Qt.Key_Print, Qt.Key_Pause,
    Qt.Key_Super_L, Qt.Key_Super_R, Qt.Key_Hyper_L, Qt.Key_Hyper_R,
})


def is_backspace(event):
    return event.key() == Qt.Key_Backspace


def key_kind(event):
    """The click a writing key should get. Shortcuts and navigation stay silent."""
    if event.modifiers() & _COMMAND: return None
    key = event.key()
    if key in (Qt.Key_Return, Qt.Key_Enter): return "return"
    if key == Qt.Key_Space: return "space"
    if key in (Qt.Key_Backspace, Qt.Key_Delete): return "erase"
    if key in _SILENT: return None
    text = event.text()
    if text and text.isprintable(): return "type"
    return None


def without_top_gap(text):
    """Older notes were stored with two blank lines so the cursor sat lower. Open them on the first line."""
    return text[2:] if text.startswith("\n\n") else text


def setting_is_on(value, default=True):
    if value is None: return default
    if isinstance(value, bool): return value
    return str(value).strip().lower() not in {"0", "false", "no", "off"}


def saved_backspace_on():
    return setting_is_on(QSettings(_ORG, _APP).value(_KEY, True))


def remember_backspace(on):
    QSettings(_ORG, _APP).setValue(_KEY, bool(on))


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
