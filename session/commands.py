"""The keyboard commands for a new note, History, closing, and the type size."""

from PyQt5.QtCore import Qt

_LARGER = frozenset({Qt.Key_Plus, Qt.Key_Equal})
_SMALLER = frozenset({Qt.Key_Minus, Qt.Key_Underscore})


def command_for(key, modifiers):
    """Ctrl+N, Ctrl+H, Ctrl+W, or Ctrl with plus or minus. Shift counts only on the size keys, since plus is shifted."""
    if not (modifiers & Qt.ControlModifier): return None
    if modifiers & (Qt.AltModifier | Qt.MetaModifier): return None
    shifted = bool(modifiers & Qt.ShiftModifier)
    if key == Qt.Key_N and not shifted: return "new"
    if key == Qt.Key_H and not shifted: return "history"
    if key == Qt.Key_W and not shifted: return "close"
    if key in _LARGER: return "larger"
    if key in _SMALLER: return "smaller"
    return None
