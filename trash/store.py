"""Keep deleted notes in a hidden folder until they are restored or removed."""

import os
import uuid
from datetime import datetime

from notes.catalog import _parse_id, _parse_time, read_records, write_records
from notes.entry import HumanEntry
from notes.naming import history_preview, unique_filename
from trash.constants import TRASH_DIR
from trash.item import TrashedNote
from trash.transfer import move_file


class TrashStore:
    """Trash for one notes folder. The files live in `.trash` so a folder move can carry them."""

    def __init__(self, directory):
        self.directory = directory

    @property
    def root(self):
        return os.path.join(self.directory, TRASH_DIR)

    def load(self):
        """Notes newest-deleted first. A missing folder means Trash is empty, and it is not created yet."""
        if not os.path.isdir(self.root): return []
        self._clear_temps()
        catalog = {rec.get("filename"): rec for rec in read_records(self.root) if isinstance(rec, dict) and rec.get("filename")}
        items = [self._item_from_file(name, catalog.get(name)) for name in self._names()]
        items.sort(key=lambda item: (item.deleted, item.created), reverse=True)
        self._write([self._record(item) for item in items])
        return items

    def take(self, entry):
        """Move a note out of the folder and into Trash. The file is put back if Trash cannot remember it."""
        src = os.path.join(self.directory, entry.filename or "")
        if not entry.filename or not os.path.isfile(src): raise FileNotFoundError(entry.filename or "")
        os.makedirs(self.root, exist_ok=True)
        desired = unique_filename(self.root, self._stem(entry.filename), "")
        dest = os.path.join(self.root, desired)
        move_file(src, dest)
        deleted = datetime.now().replace(microsecond=0)
        record = {
            "id": str(entry.id),
            "created": entry.created.replace(microsecond=0).isoformat(timespec="seconds"),
            "filename": desired,
            "deleted": deleted.isoformat(timespec="seconds"),
        }
        try:
            kept = [rec for rec in read_records(self.root) if not (isinstance(rec, dict) and rec.get("id") == record["id"])]
            kept.append(record)
            write_records(self.root, kept)
        except Exception:
            self._put_back(dest, src)
            raise
        return self._make(record, history_preview(self._read(desired)))

    def restore(self, item):
        """Put a note back in the notes folder. The original date is kept. A name already in use gets a number."""
        src = os.path.join(self.root, item.filename)
        if not os.path.isfile(src): raise FileNotFoundError(item.filename or "")
        desired = unique_filename(self.directory, self._stem(item.filename), "")
        dest = os.path.join(self.directory, desired)
        move_file(src, dest)
        try:
            self._drop(item.id)
        except Exception:
            self._put_back(dest, src)
            raise
        return HumanEntry(item.id, item.created, desired, history_preview(self._read_at(dest)))

    def purge(self, item):
        """Delete one note for good. A file that is already gone still leaves the list."""
        path = os.path.join(self.root, item.filename) if item.filename else ""
        if path and os.path.isfile(path): os.remove(path)
        self._drop(item.id)

    def empty(self):
        """Delete every note in Trash. A file that stays behind keeps its place in the list."""
        if not os.path.isdir(self.root): return
        failed = []
        for name in self._names():
            try: os.remove(os.path.join(self.root, name))
            except OSError: failed.append(name)
        if not failed:
            self._write([])
            return
        remain = set(failed)
        self._write([rec for rec in read_records(self.root) if isinstance(rec, dict) and rec.get("filename") in remain])
        raise OSError(self.root)

    def _item_from_file(self, name, record):
        note_id, created, deleted = self._identity(name, record)
        return TrashedNote(note_id, created, name, history_preview(self._read(name)), deleted)

    def _identity(self, name, record):
        created = deleted = note_id = None
        if isinstance(record, dict):
            created, note_id = _parse_time(record.get("created")), _parse_id(record.get("id"))
            deleted = _parse_time(record.get("deleted"))
        stamped = datetime.fromtimestamp(os.path.getmtime(os.path.join(self.root, name))).replace(microsecond=0)
        return note_id or uuid.uuid4(), (created or stamped).replace(microsecond=0), (deleted or stamped).replace(microsecond=0)

    def _make(self, record, preview):
        return TrashedNote(_parse_id(record["id"]) or uuid.uuid4(), _parse_time(record["created"]), record["filename"], preview, _parse_time(record["deleted"]))

    def _stem(self, filename):
        stem = filename[:-3] if filename.endswith(".md") else filename
        stem = stem.strip(" .")
        return stem if stem and not stem.startswith(".") else "Untitled"

    def _names(self):
        if not os.path.isdir(self.root): return []
        return sorted(name for name in os.listdir(self.root) if name.endswith(".md") and not name.startswith(".") and os.path.isfile(os.path.join(self.root, name)))

    def _record(self, item):
        return {
            "id": str(item.id),
            "created": item.created.replace(microsecond=0).isoformat(timespec="seconds"),
            "filename": item.filename,
            "deleted": item.deleted.replace(microsecond=0).isoformat(timespec="seconds"),
        }

    def _drop(self, note_id):
        note_id = str(note_id)
        self._write([rec for rec in read_records(self.root) if not (isinstance(rec, dict) and rec.get("id") == note_id)])

    def _write(self, records):
        os.makedirs(self.root, exist_ok=True)
        write_records(self.root, records)

    def _read(self, filename):
        return self._read_at(os.path.join(self.root, filename))

    def _read_at(self, path):
        try:
            with open(path, "r", encoding="utf-8") as handle: return handle.read()
        except (OSError, UnicodeError):
            return ""

    def _put_back(self, dest, src):
        if os.path.isfile(dest) and not os.path.exists(src): move_file(dest, src)

    def _clear_temps(self):
        for name in os.listdir(self.root):
            if name.startswith(".freewrite-") and name.endswith(".tmp"):
                try: os.remove(os.path.join(self.root, name))
                except OSError: pass
