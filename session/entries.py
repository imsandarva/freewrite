"""Open, save, and delete the note on the page."""

import os
import random  # Added for random placeholder selection
from datetime import date

from PyQt5.QtGui import QTextCursor

from app.paths import resource
from editing.gap import without_top_gap
from notes.entry import HumanEntry
from notes.naming import history_preview


class EntryStore:
    def select_entry(self, entry):
        if self.selected_entry_id:
            self.save_current_entry()
        self.selected_entry_id = entry.id
        self.load_entry(entry)
        self.update_entries_display()
    def on_text_changed(self):
        self.text = self.text_edit.toPlainText()
        self.save_current_entry()

    def save_current_entry(self):
        if self.selected_entry_id:
            entry = next((e for e in self.entries if e.id == self.selected_entry_id), None)
            if entry:
                self.save_entry(entry)

    def save_entry(self, entry):
        previous = entry.preview_text
        try:
            self.library.save(entry, self.text)
            self.update_preview_text(entry)
            if entry.preview_text != previous: self.update_entries_display()
        except Exception as e:
            print(f"Error saving entry: {e}")

    def load_entry(self, entry):
        file_path = os.path.join(self.documents_directory, entry.filename)
        try:
            if entry.filename and os.path.exists(file_path):
                self.text = without_top_gap(self.library.read(entry))
                self.text_edit.setPlainText(self.text)
                cursor = self.text_edit.textCursor()
                cursor.movePosition(QTextCursor.End)
                self.text_edit.setTextCursor(cursor)
                self._apply_writing_font()
        except Exception as e:
            print(f"Error loading entry: {e}")

    def create_new_entry(self):
        self._add_entry(not self.entries)

    def _add_entry(self, welcome):
        new_entry = HumanEntry.create_new()
        self.entries.insert(0, new_entry)
        self.selected_entry_id = new_entry.id
        if welcome:
            self.text = self._welcome_text()
            self.save_entry(new_entry)
            self.update_preview_text(new_entry)
        else:
            self.text = ""
            self.placeholder_text = random.choice(self.placeholder_options)
            self.save_entry(new_entry)
        self.text_edit.setPlainText(self.text)
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_edit.setTextCursor(cursor)
        self._apply_writing_font()
        self.update_entries_display()

    def _welcome_text(self):
        try:
            with open(resource("assets", "default.md"), "r", encoding="utf-8") as handle: return handle.read()
        except Exception:
            return ""
    def update_preview_text(self, entry):
        try:
            entry.preview_text = history_preview(self.library.read(entry))
        except Exception as e:
            print(f"Error updating preview: {e}")
    def delete_entry(self, entry):
        try:
            self.library.delete(entry)
            self.entries = [e for e in self.entries if e.id != entry.id]
            if self.selected_entry_id == entry.id:
                if self.entries:
                    self.selected_entry_id = self.entries[0].id
                    self.load_entry(self.entries[0])
                else:
                    self.create_new_entry()
            self.update_entries_display()
        except Exception as e:
            print(f"Error deleting entry: {e}")


    def load_existing_entries(self):
        os.makedirs(self.documents_directory, exist_ok=True)
        try:
            self.entries = self.library.load()
            today = date.today()
            has_empty_entry_today = any(
                e.date == today.strftime("%b %d") and not e.preview_text for e in self.entries
            )
            has_only_welcome = len(self.entries) == 1 and "Welcome to Freewrite" in (open(os.path.join(self.documents_directory, self.entries[0].filename), "r", encoding="utf-8").read() if self.entries else "")
            if not self.entries:
                self.create_new_entry()
            elif not has_empty_entry_today and not has_only_welcome:
                self.create_new_entry()
            else:
                for entry in self.entries:
                    if entry.date == today.strftime("%b %d") and not entry.preview_text:
                        self.selected_entry_id = entry.id
                        self.load_entry(entry)
                        break
                    elif has_only_welcome:
                        self.selected_entry_id = self.entries[0].id
                        self.load_entry(self.entries[0])
                        break
            self.update_entries_display()
        except Exception as e:
            print(f"Error loading entries: {e}")
            self.create_new_entry()
