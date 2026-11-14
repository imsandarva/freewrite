"""Load, save, and delete the notes in one folder."""

import os
import uuid
from datetime import datetime

from notes.catalog import _parse_id, _parse_time, read_records, write_records
from notes.constants import _LEGACY_NAME, _STAMP
from notes.entry import HumanEntry
from notes.naming import allocate_name, history_preview, stem_from_content, unique_filename
from notes.atomic_write import write_atomic


class NoteLibrary:
    def __init__(self, directory):
        self.directory = directory

    def load(self):
        os.makedirs(self.directory, exist_ok=True)
        self._clear_temps()
        catalog = self._catalog_by_name()
        entries = [self._entry_from_file(name, catalog.get(name)) for name in self._note_names()]
        self._rename_legacy(entries)
        entries.sort(key=lambda entry: entry.created, reverse=True)
        self._write_catalog(entries)
        return entries

    def save(self, entry, text):
        os.makedirs(self.directory, exist_ok=True)
        desired = unique_filename(self.directory, stem_from_content(text), entry.filename)
        if self._unchanged(entry, desired, text):
            entry.preview_text = history_preview(text)
            return
        self._store(entry, desired, text)
        entry.filename = desired
        entry.preview_text = history_preview(text)
        self._remember(entry)

    def read(self, entry):
        return self._read_name(entry.filename)

    def delete(self, entry):
        """Remove a note for good. History does not call this. It moves the file into Trash instead."""
        path = os.path.join(self.directory, entry.filename) if entry.filename else ""
        if path and os.path.isfile(path): os.remove(path)
        self.forget(entry)

    def forget(self, entry):
        """Drop a note from the catalog after its file has already left this folder."""
        note_id = str(entry.id)
        self._write_records([rec for rec in self._read_catalog() if rec.get("id") != note_id])

    def adopt(self, entry):
        """Remember a note whose file is already in this folder."""
        self._remember(entry)

    def _unchanged(self, entry, desired, text):
        if entry.filename != desired or not entry.filename: return False
        path = os.path.join(self.directory, entry.filename)
        if not os.path.isfile(path): return False
        return self._read_name(entry.filename) == text

    def _store(self, entry, desired, text):
        current = os.path.join(self.directory, entry.filename) if entry.filename else ""
        target = os.path.join(self.directory, desired)
        # Write onto the current file first, then rename, so the note is never in two places.
        if entry.filename and os.path.isfile(current) and desired != entry.filename:
            write_atomic(self.directory, entry.filename, text)
            if os.path.lexists(target): raise FileExistsError(desired)
            os.rename(current, target)
            return
        write_atomic(self.directory, desired, text)

    def _note_names(self):
        return [name for name in os.listdir(self.directory) if name.endswith(".md") and not name.startswith(".")]

    def _entry_from_file(self, name, record):
        created, note_id = self._identity(name, record)
        return HumanEntry(note_id, created, name, history_preview(self._read_name(name)))

    def _identity(self, name, record):
        if record:
            created, note_id = _parse_time(record.get("created")), _parse_id(record.get("id"))
            if created and note_id: return created, note_id
        legacy = _LEGACY_NAME.match(name)
        if legacy: return datetime.strptime(legacy.group(2), _STAMP), uuid.UUID(legacy.group(1))
        return datetime.fromtimestamp(os.path.getmtime(os.path.join(self.directory, name))), uuid.uuid4()

    def _rename_legacy(self, entries):
        """Older builds stored a random id in the name. Move those to the opening words."""
        legacy = [entry for entry in entries if _LEGACY_NAME.match(entry.filename)]
        if not legacy: return
        used = {entry.filename for entry in entries if not _LEGACY_NAME.match(entry.filename)}
        plans = []
        for entry in sorted(legacy, key=lambda item: item.created):
            text = self._read_name(entry.filename)
            desired = allocate_name(stem_from_content(text), used)
            used.add(desired)
            plans.append((entry, desired, text))
        self._write_catalog(self._snapshot(entries, {entry.id: desired for entry, desired, _text in plans}))
        for entry, desired, text in plans:
            self._move_legacy(entry, desired)
            entry.preview_text = history_preview(text)

    def _snapshot(self, entries, planned):
        return [HumanEntry(entry.id, entry.created, planned.get(entry.id, entry.filename), entry.preview_text) for entry in entries]

    def _move_legacy(self, entry, desired):
        if desired == entry.filename: return
        target = os.path.join(self.directory, desired)
        if os.path.lexists(target): raise FileExistsError(desired)
        os.rename(os.path.join(self.directory, entry.filename), target)
        entry.filename = desired

    def _read_name(self, filename):
        try:
            with open(os.path.join(self.directory, filename), "r", encoding="utf-8") as handle: return handle.read()
        except (OSError, UnicodeError):
            return ""

    def _remember(self, entry):
        records = [rec for rec in self._read_catalog() if rec.get("id") != str(entry.id) and rec.get("filename") != entry.filename]
        records.append(self._record(entry))
        self._write_records(records)

    def _catalog_by_name(self):
        return {rec.get("filename"): rec for rec in self._read_catalog() if rec.get("filename")}

    def _read_catalog(self):
        return read_records(self.directory)

    def _write_catalog(self, entries):
        self._write_records([self._record(entry) for entry in entries])

    def _record(self, entry):
        return {"id": str(entry.id), "created": entry.created.isoformat(timespec="seconds"), "filename": entry.filename}

    def _write_records(self, records):
        write_records(self.directory, records)

    def _clear_temps(self):
        for name in os.listdir(self.directory):
            if name.startswith(".freewrite-") and name.endswith(".tmp"):
                try: os.remove(os.path.join(self.directory, name))
                except OSError: pass
