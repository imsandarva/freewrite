"""How a note is named and stored.

History shows the opening words of a note. The file uses those same words,
so the notes folder reads the way the History list does.
"""

import json
import os
import re
import uuid
from datetime import datetime

# History cuts the title here. The filename uses this same stretch of text.
PREVIEW_CHARS = 30
CATALOG_NAME = ".entries.json"
_STAMP = "%Y-%m-%d-%H-%M-%S"
_LEGACY_NAME = re.compile(
    r"^\[([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\]-\[(\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})\]\.md$"
)
_UNSAFE = re.compile(r'[/\\\x00-\x1f]')


class HumanEntry:
    def __init__(self, id, created, filename, preview_text):
        self.id = id
        self.created = created
        self.date = created.strftime("%b %d")
        self.filename = filename
        self.preview_text = preview_text

    @staticmethod
    def create_new():
        return HumanEntry(uuid.uuid4(), datetime.now(), "", "")


def flattened(text):
    """One line of the note, matching what History reads."""
    return text.replace("\r\n", " ").replace("\r", " ").replace("\n", " ").replace("\t", " ").strip()


def history_preview(text):
    flat = flattened(text)
    if len(flat) > PREVIEW_CHARS: return flat[:PREVIEW_CHARS] + "..."
    return flat


def stem_from_content(text):
    """Opening words, made safe to keep as a file name. The trailing ... is only for History."""
    raw = _UNSAFE.sub(" ", flattened(text)[:PREVIEW_CHARS]).strip(" .")
    while raw.startswith("."): raw = raw[1:].strip(" .")
    if not raw: return "Untitled"
    return raw


def allocate_name(stem, used):
    """stem.md, then stem 2.md, when another note already opens the same way."""
    number = 1
    while True:
        name = f"{stem}.md" if number == 1 else f"{stem} {number}.md"
        if name not in used: return name
        number += 1


def unique_filename(directory, stem, current_name):
    used = set(os.listdir(directory)) if os.path.isdir(directory) else set()
    if current_name: used.discard(current_name)
    return allocate_name(stem, used)


def write_atomic(directory, filename, text):
    """Swap the finished text into place so a crash cannot leave a half-written note."""
    path = os.path.join(directory, filename)
    tmp = os.path.join(directory, f".freewrite-{uuid.uuid4().hex}.tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as handle: handle.write(text)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp): os.remove(tmp)
        raise
    return path


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
        path = os.path.join(self.directory, entry.filename) if entry.filename else ""
        if path and os.path.isfile(path): os.remove(path)
        kept = [rec for rec in self._read_catalog() if rec.get("id") != str(entry.id)]
        self._write_records(kept)

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
        path = os.path.join(self.directory, CATALOG_NAME)
        try:
            with open(path, "r", encoding="utf-8") as handle: data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return []
        entries = data.get("entries") if isinstance(data, dict) else None
        return entries if isinstance(entries, list) else []

    def _write_catalog(self, entries):
        self._write_records([self._record(entry) for entry in entries])

    def _record(self, entry):
        return {"id": str(entry.id), "created": entry.created.isoformat(timespec="seconds"), "filename": entry.filename}

    def _write_records(self, records):
        write_atomic(self.directory, CATALOG_NAME, json.dumps({"entries": records}, ensure_ascii=False, indent=2))

    def _clear_temps(self):
        for name in os.listdir(self.directory):
            if name.startswith(".freewrite-") and name.endswith(".tmp"):
                try: os.remove(os.path.join(self.directory, name))
                except OSError: pass


def _parse_time(value):
    try: return datetime.fromisoformat(value)
    except (TypeError, ValueError): return None


def _parse_id(value):
    try: return uuid.UUID(str(value))
    except (TypeError, ValueError): return None
