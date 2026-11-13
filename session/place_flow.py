"""Pick another folder for notes, and ask before moving the ones already saved."""

import os
from datetime import date

from PyQt5.QtWidgets import QFileDialog

from choice.ask import ask_move, tell
from notes.library import NoteLibrary
from place.display import friendly_path, same_place, settle
from place.error import PlaceError
from place.inventory import has_notes, note_count
from place.directory import remember_directory
from place.relocate import relocate


class PlaceFlow:
    def _show_place(self):
        path = os.path.abspath(self.documents_directory)
        self.history.set_place(friendly_path(path), path)

    def _choose_place(self):
        try:
            self._apply_chosen_place(self._pick_folder())
        finally:
            self.text_edit.setFocus()

    def _pick_folder(self):
        chosen = QFileDialog.getExistingDirectory(self.window(), "Save notes in", self.documents_directory, QFileDialog.ShowDirsOnly)
        return os.path.abspath(chosen) if chosen else ""

    def _apply_chosen_place(self, chosen):
        if not chosen or same_place(chosen, self.documents_directory): return
        self.save_current_entry()
        keep = None
        if has_notes(self.documents_directory):
            outcome = self._ask_and_maybe_move(chosen)
            if outcome == "cancel": return
            keep = None if outcome == "leave" else outcome
        self._use_directory(chosen, keep)

    def _ask_and_maybe_move(self, chosen):
        dark = self.color_scheme == "dark"
        choice = ask_move(self, os.path.abspath(chosen), dark, note_count(self.documents_directory), has_notes(chosen))
        if choice != "move": return choice
        try:
            changed = relocate(self.documents_directory, chosen)
        except PlaceError as error:
            tell(self, error.title, error.body, dark)
            return "cancel"
        current = str(self.selected_entry_id) if self.selected_entry_id else ""
        return changed.get(current, self.selected_entry_id)

    def _use_directory(self, path, keep_id):
        # Drop the selection before the folder changes, so a save in between cannot write the open page into the new folder.
        previous = self.selected_entry_id
        self.selected_entry_id = None
        path = settle(path)
        try:
            os.makedirs(path, exist_ok=True)
            library = NoteLibrary(path)
            entries = library.load()
        except Exception as error:
            self.selected_entry_id = previous
            print("Error opening notes folder: %s" % error)
            tell(self, "That folder isn't available", "Your notes are still being saved in the previous place.", self.color_scheme == "dark")
            return
        remember_directory(path)
        self.documents_directory = path
        self.library = library
        self.entries = entries
        self._show_place()
        kept = self._kept(keep_id)
        if kept is not None:
            self.selected_entry_id = kept.id
            self.load_entry(kept)
            self.update_entries_display()
            return
        self._open_folder_notes()

    def _kept(self, keep_id):
        if keep_id is None: return None
        want = str(keep_id)
        return next((item for item in self.entries if str(item.id) == want), None)

    def _open_folder_notes(self):
        if not self.entries:
            self._add_entry(False)
            return
        today = date.today().strftime("%b %d")
        entry = next((item for item in self.entries if item.date == today and not item.preview_text), None)
        if entry is None: entry = self.entries[0]
        self.selected_entry_id = entry.id
        self.load_entry(entry)
        self.update_entries_display()
