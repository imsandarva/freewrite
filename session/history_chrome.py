"""The history sheet, fitted over the page and closed from the bar, Escape, or the scrim."""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut

from history.drawer import HistoryDrawer


class HistoryChrome:
    def _wire_history(self, paper):
        self.history = HistoryDrawer(self)
        self.history.apply_paper(paper)
        self.history.chosen.connect(self.select_entry)
        self.history.delete_requested.connect(self.delete_entry)
        self.history.export_requested.connect(self.export_entry_as_pdf)
        self.history.opened.connect(self._history_shown)
        self.history.dismissed.connect(self._history_hidden)
        self.history.change_requested.connect(self._choose_place)
        self._show_place()
        self._history_escape = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self._history_escape.setContext(Qt.WindowShortcut)
        self._history_escape.setEnabled(False)
        self._history_escape.activated.connect(self._escape_history)

    def _escape_history(self):
        # Trash closes first. The next Escape closes History, and only then can fullscreen leave.
        if self.history.close_trash(): return
        self.history.close_sheet()

    def _history_shown(self):
        self._reload_trash()
        self.history.arm_cursor()
        self._history_escape.setEnabled(True)
        self._set_history_open(True)
        self._sync_fullscreen_keys()
        hint = getattr(self, "_exit_hint", None)
        if hint is not None and hint.isVisible(): hint.raise_()

    def _history_hidden(self):
        self._history_escape.setEnabled(False)
        self._set_history_open(False)
        self._sync_fullscreen_keys()
        self.text_edit.setFocus()

    def _set_history_open(self, is_open):
        self._history_open = bool(is_open)
        self._paint_history_button()

    def _paint_history_button(self):
        if not self._history_open:
            self.history_btn.setStyleSheet("")
            return
        color = self.paper.hover if self.paper.dark else self.paper.ink
        self.history_btn.setStyleSheet("QPushButton { color: %s; }" % color)

    def showEvent(self, event):
        super().showEvent(event)
        self.history.fit_over(self.bottom_nav)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.history.fit_over(self.bottom_nav)
        hint = getattr(self, "_exit_hint", None)
        if hint is not None: hint.place()
    def update_entries_display(self):
        self.history.set_entries(self._saved_entries(), self.selected_entry_id)

    def _saved_entries(self):
        return [entry for entry in self.entries if entry.filename]
    def toggle_history(self):
        self.history.toggle()

