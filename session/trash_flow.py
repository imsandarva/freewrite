"""Move a note into Trash, and bring it back or let it go."""

from choice.ask import ask_delete, ask_empty, tell
from trash.store import TrashStore


class TrashFlow:
    def _wire_trash(self):
        self.trash = TrashStore(self.documents_directory)
        self.history.trash_requested.connect(self._show_trash)
        self.history.restore_requested.connect(self._restore_note)
        self.history.purge_requested.connect(self._purge_note)
        self.history.empty_requested.connect(self._empty_trash)
        self._reload_trash()

    def _adopt_trash(self, path):
        """The notes folder changed, so Trash is the hidden folder inside that one."""
        self.trash = TrashStore(path)
        self._reload_trash()

    def _reload_trash(self):
        try:
            items = self.trash.load()
        except Exception as error:
            print("Error reading Trash: %s" % error)
            items = []
        self.history.set_trash(items)

    def _show_trash(self):
        self._reload_trash()
        self.history.open_trash()

    def _move_entry_to_trash(self, entry):
        if entry.id == self.selected_entry_id: self.save_current_entry()
        try:
            self.trash.take(entry)
        except Exception as error:
            print("Error moving note to Trash: %s" % error)
            tell(self, "That note is still in History", "It couldn't be moved to Trash just now, so it was left where it was.", self.paper)
            return False
        try:
            self.library.forget(entry)
        except Exception as error:
            print("Error updating History: %s" % error)
        return True

    def _restore_note(self, item):
        try:
            entry = self.trash.restore(item)
        except Exception as error:
            print("Error restoring note: %s" % error)
            tell(self, "That note is still in Trash", "It couldn't be put back just now. Nothing was removed.", self.paper)
            self._reload_trash()
            return
        try:
            self.library.adopt(entry)
        except Exception as error:
            print("Error keeping restored note: %s" % error)
        self.entries.append(entry)
        self.entries.sort(key=lambda note: note.created, reverse=True)
        self.update_entries_display()
        self._reload_trash()

    def _purge_note(self, item):
        if ask_delete(self, self.paper) != "delete": return
        try:
            self.trash.purge(item)
        except Exception as error:
            print("Error deleting note: %s" % error)
            tell(self, "That note is still in Trash", "It couldn't be deleted just now.", self.paper)
        self._reload_trash()

    def _empty_trash(self):
        try:
            count = len(self.trash.load())
        except Exception:
            count = 0
        if count == 0: return
        if ask_empty(self, self.paper, count) != "empty": return
        try:
            self.trash.empty()
        except Exception as error:
            print("Error emptying Trash: %s" % error)
            tell(self, "Trash couldn't be emptied", "Those notes are still there.", self.paper)
        self._reload_trash()
