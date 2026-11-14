"""Ctrl+N, Ctrl+H, and the type-size keys.

Arrows and Enter are watched here too. The writing page accepts those keys before a normal shortcut can see them, so History would never hear them.
"""

from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtWidgets import QApplication

from session.commands import command_for
from typeface.step import step_size

_HISTORY_KEYS = frozenset({Qt.Key_Up, Qt.Key_Down, Qt.Key_Return, Qt.Key_Enter})
_ONCE = frozenset({"new", "history"})


class SessionKeys:
    def _wire_keys(self):
        app = QApplication.instance()
        if app is None: return
        app.installEventFilter(self)
        self.destroyed.connect(self._unwire_keys)

    def _unwire_keys(self):
        app = QApplication.instance()
        if app is not None: app.removeEventFilter(self)

    def eventFilter(self, _watched, event):
        if event.type() == QEvent.KeyPress and self._take_key(event): return True
        return super().eventFilter(_watched, event)

    def _take_key(self, event):
        if QApplication.activeModalWidget() is not None: return False
        if not self._key_window_is_ours(): return False
        if self._take_command(event): return True
        if self._history_keys_on() and self._take_history_key(event): return True
        return False

    def _key_window_is_ours(self):
        focus = QApplication.focusWidget()
        window = focus.window() if focus is not None else QApplication.activeWindow()
        return window is not None and window is self.window()

    def _take_command(self, event):
        action = command_for(event.key(), event.modifiers())
        if action is None: return False
        if event.isAutoRepeat() and action in _ONCE: return True
        self._run_command(action)
        return True

    def _run_command(self, action):
        if action == "new": self.create_new_entry()
        elif action == "history": self.toggle_history()
        elif action == "larger": self._step_font(1)
        elif action == "smaller": self._step_font(-1)

    def _step_font(self, direction):
        size = step_size(self.font_sizes, self.font_size, direction)
        if size == self.font_size: return
        self.font_size = size
        self._apply_writing_font()

    def _history_keys_on(self):
        return bool(getattr(self, "_history_open", False)) and getattr(self, "history", None) is not None

    def _take_history_key(self, event):
        if event.modifiers() & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier): return False
        key = event.key()
        if key not in _HISTORY_KEYS: return False
        # Trash is covering the list, so the keys do nothing there, and they also stay off the page.
        if self.history.trash_covers(): return True
        if key == Qt.Key_Up: self.history.move_cursor(-1)
        elif key == Qt.Key_Down: self.history.move_cursor(1)
        elif not event.isAutoRepeat(): self.history.open_cursor()
        return True
