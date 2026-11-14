"""Bring Trash along when the notes folder changes, and put it back if that cannot finish."""

import errno
import os
import shutil
import uuid
from datetime import datetime

from notes.catalog import read_records, write_records
from notes.constants import CATALOG_NAME
from notes.naming import allocate_name
from trash.constants import TRASH_DIR
from trash.transfer import move_file


def carry_trash(source, dest):
    """Move Trash into dest. Returns a function that puts it back, or None when there was nothing to move.

    If the move cannot finish, Trash is put back before the error is raised.
    """
    src, dst = os.path.join(source, TRASH_DIR), os.path.join(dest, TRASH_DIR)
    if not _has_notes(src): return None
    if os.path.exists(dst) and not os.path.isdir(dst): raise OSError(dst)
    if not os.path.exists(dst):
        _move_dir(src, dst)
        return lambda: _move_dir(dst, src) if os.path.isdir(dst) and not os.path.exists(src) else None
    return _merge(src, dst)


def _has_notes(path):
    return bool(_md(path))


def _md(path):
    if not os.path.isdir(path): return []
    names = [name for name in os.listdir(path) if name.endswith(".md") and not name.startswith(".") and os.path.isfile(os.path.join(path, name))]
    names.sort()
    return names


def _merge(src, dst):
    dest_records, had_dest = read_records(dst), os.path.isfile(os.path.join(dst, CATALOG_NAME))
    src_records, had_src = read_records(src), os.path.isfile(os.path.join(src, CATALOG_NAME))
    used, plan = set(os.listdir(dst)), []
    for name in _md(src):
        target = allocate_name(_stem(name), used)
        used.add(target)
        plan.append((name, target))
    moved = []
    try:
        for src_name, dst_name in plan:
            move_file(os.path.join(src, src_name), os.path.join(dst, dst_name))
            moved.append((src_name, dst_name))
        write_records(dst, _merged(dest_records, src_records, dict(plan), dst))
        _remove_catalog(src)
        _clear_dir(src)
    except Exception:
        _rewind(src, dst, moved, dest_records, had_dest, src_records, had_src)
        raise
    return lambda: _rewind(src, dst, moved, dest_records, had_dest, src_records, had_src)


def _merged(existing, incoming, renamed, dest):
    seen = {rec.get("id") for rec in existing if isinstance(rec, dict)}
    merged = list(existing)
    for rec in incoming:
        if not isinstance(rec, dict) or rec.get("filename") not in renamed: continue
        updated = dict(rec, filename=renamed[rec.get("filename")])
        if updated.get("id") in seen:
            updated["id"] = str(uuid.uuid4())
        seen.add(updated.get("id"))
        merged.append(updated)
    known = {rec.get("filename") for rec in merged if isinstance(rec, dict)}
    for _src_name, dst_name in renamed.items():
        if dst_name in known: continue
        moment = datetime.fromtimestamp(os.path.getmtime(os.path.join(dest, dst_name))).replace(microsecond=0)
        merged.append({"id": str(uuid.uuid4()), "created": moment.isoformat(timespec="seconds"), "filename": dst_name, "deleted": moment.isoformat(timespec="seconds")})
    return merged


def _rewind(src, dst, moved, dest_records, had_dest, src_records, had_src):
    os.makedirs(src, exist_ok=True)
    for src_name, dst_name in reversed(moved):
        src_path, dst_path = os.path.join(src, src_name), os.path.join(dst, dst_name)
        if os.path.isfile(dst_path) and not os.path.exists(src_path):
            try: move_file(dst_path, src_path)
            except OSError: pass
    _restore_catalog(dst, dest_records, had_dest)
    _restore_catalog(src, src_records, had_src)


def _move_dir(src, dst):
    """Rename when the disk allows it. Across disks, copy the folder, then remove the original only after the copy exists."""
    if os.path.lexists(dst): raise FileExistsError(dst)
    try:
        os.rename(src, dst)
        return
    except OSError as error:
        if error.errno != errno.EXDEV: raise
    shutil.copytree(src, dst)
    try:
        shutil.rmtree(src)
    except Exception:
        shutil.rmtree(dst, ignore_errors=True)
        raise


def _stem(filename):
    stem = filename[:-3] if filename.endswith(".md") else filename
    stem = stem.strip(" .")
    return stem if stem and not stem.startswith(".") else "Untitled"


def _restore_catalog(directory, records, had_catalog):
    try:
        if had_catalog: write_records(directory, records)
        else: _remove_catalog(directory)
    except OSError:
        pass


def _remove_catalog(directory):
    path = os.path.join(directory, CATALOG_NAME)
    try:
        if os.path.isfile(path): os.remove(path)
    except OSError:
        pass


def _clear_dir(path):
    """Remove leftovers and the folder itself when the notes have already moved."""
    if not os.path.isdir(path): return
    for name in os.listdir(path):
        if name.startswith(".freewrite-") and name.endswith(".tmp"):
            try: os.remove(os.path.join(path, name))
            except OSError: pass
    try: os.rmdir(path)
    except OSError: pass
