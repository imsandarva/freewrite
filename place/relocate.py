"""Move every note into a new folder, and put them back if that cannot finish."""

import errno
import os
import shutil
import uuid

from notes.constants import CATALOG_NAME
from notes.naming import allocate_name
from notes.catalog import read_records, write_records
from place.directory import _ready
from place.display import settle
from place.error import PlaceError
from place.inventory import _note_names, _taken
from trash.moving import carry_trash


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
    moved, undo_trash = [], lambda: None
    try:
        for src_name, dst_name in plan:
            _move_one(os.path.join(source, src_name), os.path.join(dest, dst_name))
            moved.append((src_name, dst_name))
        merged, changed = _merged(source, snapshot, dict(plan))
        # Trash travels with the notes. If a later step fails, it is put back before the notes are.
        undo_trash = carry_trash(source, dest) or (lambda: None)
        write_records(dest, merged)
        _remove_catalog(source)
    except PlaceError:
        raise
    except Exception:
        try: undo_trash()
        except Exception: pass
        stuck = _restore(moved, source, dest)
        _restore_catalog(dest, snapshot, had_catalog)
        if stuck: raise PlaceError("The move stopped partway", "Some notes are in the new folder and some are still in the previous one. Take a look at both before you keep writing.")
        raise PlaceError("Your notes stayed where they were", "The notes couldn't be moved, so they were left in the previous folder.")
    return changed


def _refuse_unusable(source, dest):
    if not os.path.isdir(source):
        raise PlaceError("Your notes stayed where they were", "The previous folder is no longer there, so nothing was moved.")
    if os.path.exists(dest) and not os.path.isdir(dest):
        raise PlaceError("Your notes stayed where they were", "That isn't a folder, so nothing was moved.")
    if not _ready(dest) or not os.access(dest, os.W_OK):
        raise PlaceError("Your notes stayed where they were", "That folder can't be written to, so nothing was moved.")


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
