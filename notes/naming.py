"""The opening words, as History shows them and as a filename."""

import os

from notes.constants import PREVIEW_CHARS, _UNSAFE


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
