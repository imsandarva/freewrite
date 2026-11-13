"""Which markdown files are already in a folder."""

import os


def note_count(directory):
    return len(_note_names(directory))


def has_notes(directory):
    return note_count(directory) > 0


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
