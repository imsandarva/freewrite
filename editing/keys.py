"""Which keys count as typing, and which one is Backspace."""

from PyQt5.QtCore import Qt

_COMMAND = Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier
_SILENT = frozenset({
    Qt.Key_Shift, Qt.Key_Control, Qt.Key_Alt, Qt.Key_Meta, Qt.Key_AltGr,
    Qt.Key_CapsLock, Qt.Key_NumLock, Qt.Key_ScrollLock, Qt.Key_Escape, Qt.Key_F11, Qt.Key_Tab,
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
