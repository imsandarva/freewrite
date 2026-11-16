"""The page filling the screen. The bar leaves with it, and Escape brings the bar back."""

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut

from session.exit_hint import ExitHint

ENTER_LABEL = "Fullscreen(F11)"


class FullscreenControl:
    def _wire_fullscreen(self):
        self._exit_hint = ExitHint(self)
        self._enter_full = self._shortcut(Qt.Key_F11, self.enter_fullscreen, True)
        # Escape already closes History. This one stays off while that sheet is up.
        self._leave_full = self._shortcut(Qt.Key_Escape, self.leave_fullscreen, False)

    def _shortcut(self, key, slot, enabled):
        shortcut = QShortcut(QKeySequence(key), self)
        shortcut.setContext(Qt.WindowShortcut)
        shortcut.setAutoRepeat(False)
        shortcut.setEnabled(enabled)
        shortcut.activated.connect(slot)
        return shortcut

    def enter_fullscreen(self):
        window = self.window()
        if window is None or window.isFullScreen(): return
        window.setWindowState(window.windowState() | Qt.WindowFullScreen)

    def leave_fullscreen(self):
        window = self.window()
        if window is None or not window.isFullScreen(): return
        window.setWindowState(window.windowState() & ~Qt.WindowFullScreen)

    def apply_fullscreen(self, is_full):
        """Follow the window. The window is the source of truth, including when the desktop changes it."""
        is_full = bool(is_full)
        if is_full == bool(self.is_fullscreen): return
        self.is_fullscreen = is_full
        self.bottom_nav.setVisible(not is_full)
        self._page_scrollbar(is_full)
        self.main_v_layout.activate()
        self._sync_fullscreen_keys()
        self._fit_history()
        self._show_exit_hint(is_full)
        self.text_edit.setFocus()
        QTimer.singleShot(0, self._fit_history)

    def _page_scrollbar(self, is_full):
        # Scrolling stays on the wheel and the keys. Only the bar leaves the page.
        policy = Qt.ScrollBarAlwaysOff if is_full else Qt.ScrollBarAsNeeded
        self.text_edit.setVerticalScrollBarPolicy(policy)
        self.text_edit.setHorizontalScrollBarPolicy(policy)

    def _show_exit_hint(self, is_full):
        hint = getattr(self, "_exit_hint", None)
        if hint is None: return
        if is_full: hint.show_briefly(self.paper)
        else: hint.dismiss()

    def _fit_history(self):
        if getattr(self, "history", None) is None: return
        self.history.fit_over(self.bottom_nav)

    def _sync_fullscreen_keys(self):
        leave = getattr(self, "_leave_full", None)
        if leave is None: return
        # The sheet counts as open from the moment it starts, not after the slide finishes.
        history_open = bool(getattr(self, "_history_open", False))
        leave.setEnabled(bool(self.is_fullscreen) and not history_open)
