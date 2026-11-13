"""Which folder this session writes to, and remembering that choice."""

import os

from PyQt5.QtCore import QSettings

from place.display import settle
from utils.qsettings_identity import APP, ORG

_KEY = "notesDirectory"


def default_directory():
    return os.path.join(os.path.expanduser("~"), "freewrite_notes")


def saved_directory():
    """The remembered folder, or the one in the home folder when nothing is stored or the value is a file."""
    raw = QSettings(ORG, APP).value(_KEY, "")
    text = "" if raw is None else str(raw).strip()
    path = settle(text) if text else default_directory()
    if os.path.isfile(path): return default_directory()
    return path


def remember_directory(path):
    QSettings(ORG, APP).setValue(_KEY, settle(path))


def prepare_directory():
    """The folder this session writes to. The home folder is the fallback when the remembered one cannot be created."""
    chosen = saved_directory()
    if _ready(chosen): return chosen
    fallback = default_directory()
    _ready(fallback)
    return fallback


def _ready(path):
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        return False
    return os.path.isdir(path)
