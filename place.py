"""Which folder holds the notes, and how they move when that folder changes.

The move never overwrites a file already in the new folder. A name that is
taken becomes "stem 2.md", the same way a new note avoids a collision. If a
move fails partway, the files already moved are put back and the catalog in
the new folder is restored, so a failure does not split the notes.
"""

import errno
import os
import shutil
import uuid

from PyQt5.QtCore import QSettings

from notes import CATALOG_NAME, allocate_name, read_records, write_records

_ORG, _APP, _KEY = "humansongs", "freewrite", "notesDirectory"


class PlaceError(Exception):
    """A move that did not finish. title and body are what the person should read."""

    def __init__(self, title, body):
        super().__init__(body)
        self.title, self.body = title, body


def default_directory():
    return os.path.join(os.path.expanduser("~"), "freewrite_notes")


def saved_directory():
    """The remembered folder, or the one in the home folder when nothing is stored or the value is a file."""
    raw = QSettings(_ORG, _APP).value(_KEY, "")
    text = "" if raw is None else str(raw).strip()
    path = settle(text) if text else default_directory()
    if os.path.isfile(path): return default_directory()
    return path


def remember_directory(path):
    QSettings(_ORG, _APP).setValue(_KEY, settle(path))


def prepare_directory():
    """The folder this session writes to. The home folder is the fallback when the remembered one cannot be created."""
    chosen = saved_directory()
    if _ready(chosen): return chosen
    fallback = default_directory()
    _ready(fallback)
    return fallback


def friendly_path(path):
    """~/notes when the folder lives in the home folder. The full path otherwise."""
    home, full = os.path.expanduser("~"), os.path.abspath(path)
    if full == home: return "~"
    prefix = home + os.sep
    if full.startswith(prefix): return "~" + os.sep + full[len(prefix):]
    return full


def settle(path):
    """An absolute path, with links resolved once the folder exists so two routes to one place compare equal."""
    full = os.path.abspath(os.path.expanduser(str(path)))
    return os.path.realpath(full) if os.path.exists(full) else full


def same_place(left, right):
    return settle(left) == settle(right)


def note_count(directory):
    return len(_note_names(directory))


def has_notes(directory):
    return note_count(directory) > 0


def relocate(source, dest):
    """Move every note into dest. Returns old id to new id for the few that had to change.

    Raises PlaceError and leaves the notes in source when the move cannot be finished.
    """
    source, dest = settle(source), settle(dest)
    if source == dest: return {}
    _refuse_unusable(source, dest)
    names = _note_names(source)
    plan = _plan(names, _taken(dest))
    snapshot, had_catalog = read_records(dest), os.path.isfile(os.path.join(dest, CATALOG_NAME))
    moved = []
    try:
        for src_name, dst_name in plan:
            _move_one(os.path.join(source, src_name), os.path.join(dest, dst_name))
            moved.append((src_name, dst_name))
        merged, changed = _merged(source, snapshot, dict(plan))
        write_records(dest, merged)
        _remove_catalog(source)
    except PlaceError:
        raise
    except Exception:
        stuck = _restore(moved, source, dest)
        _restore_catalog(dest, snapshot, had_catalog)
        if stuck: raise PlaceError("The move stopped partway", "Some notes are in the new folder and some are still in the previous one. Take a look at both before you keep writing.")
        raise PlaceError("Your notes stayed where they were", "The notes couldn't be moved, so they were left in the previous folder.")
    return changed


def _ready(path):
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        return False
    return os.path.isdir(path)


def _refuse_unusable(source, dest):
    if not os.path.isdir(source):
        raise PlaceError("Your notes stayed where they were", "The previous folder is no longer there, so nothing was moved.")
    if os.path.exists(dest) and not os.path.isdir(dest):
        raise PlaceError("Your notes stayed where they were", "That isn't a folder, so nothing was moved.")
    if not _ready(dest) or not os.access(dest, os.W_OK):
        raise PlaceError("Your notes stayed where they were", "That folder can't be written to, so nothing was moved.")


def _note_names(directory):
    if not os.path.isdir(directory): return []
    names = []
    for name in os.listdir(directory):
        if name.startswith(".") or not name.endswith(".md"): continue
        if os.path.isfile(os.path.join(directory, name)): names.append(name)
    names.sort()
    return names


def _taken(directory):
    try:
        return set(os.listdir(directory))
    except OSError:
        return set()


def _plan(names, used):
    """Exact names when they are free. Otherwise the next numbered name, held aside so the plan can't collide with itself."""
    used = set(used)
    plan = []
    for name in names:
        target = allocate_name(name[:-3], used)
        used.add(target)
        plan.append((name, target))
    return plan


def _merged(source, existing, renamed):
    seen = {rec.get("id") for rec in existing if isinstance(rec, dict)}
    merged, changed = list(existing), {}
    for rec in read_records(source):
        if not isinstance(rec, dict) or rec.get("filename") not in renamed: continue
        updated = dict(rec, filename=renamed[rec.get("filename")])
        old = updated.get("id")
        if old in seen:
            updated["id"] = str(uuid.uuid4())
            if old: changed[str(old)] = updated["id"]
        seen.add(updated.get("id"))
        merged.append(updated)
    return merged, changed


def _move_one(src, dst):
    """Rename when the disk allows it. Across disks, copy to a hidden temp so a crash never leaves a half-written note under its real name."""
    if os.path.lexists(dst): raise FileExistsError(dst)
    try:
        os.rename(src, dst)
        return
    except OSError as error:
        if error.errno != errno.EXDEV: raise
    _copy_across(src, dst)


def _copy_across(src, dst):
    tmp = os.path.join(os.path.dirname(dst), ".freewrite-%s.tmp" % uuid.uuid4().hex)
    try:
        shutil.copy2(src, tmp)
        if os.path.lexists(dst): raise FileExistsError(dst)
        os.replace(tmp, dst)
    except Exception:
        if os.path.exists(tmp):
            try: os.remove(tmp)
            except OSError: pass
        raise
    try:
        os.remove(src)
    except OSError:
        if not os.path.exists(src): return
        try: os.remove(dst)
        except OSError: pass
        raise


def _restore(moved, source, dest):
    stuck = []
    for src_name, dst_name in reversed(moved):
        try:
            _move_one(os.path.join(dest, dst_name), os.path.join(source, src_name))
        except OSError:
            stuck.append(dst_name)
    return stuck


def _restore_catalog(dest, snapshot, had_catalog):
    try:
        if had_catalog: write_records(dest, snapshot)
        else: _remove_catalog(dest)
    except OSError:
        pass


def _remove_catalog(directory):
    path = os.path.join(directory, CATALOG_NAME)
    try:
        if os.path.isfile(path): os.remove(path)
    except OSError:
        pass
