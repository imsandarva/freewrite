"""The face and the type size, remembered between sessions.

The short name is what gets stored (Lato, Arial, System, Serif). The family
that name resolves to can differ from one computer to the next, so the next
launch asks for the name again and resolves it there.
"""

from PyQt5.QtCore import QSettings

from typeface.families import writing_faces
from typeface.step import SIZES
from utils.qsettings_identity import APP, ORG
from utils.remember import remember_value

_FACE, _SIZE = "writingFace", "writingSize"
_DEFAULT_FACE, _DEFAULT_SIZE = "Lato", 18


def saved_face():
    return _known_face(QSettings(ORG, APP).value(_FACE, _DEFAULT_FACE))


def remember_face(label):
    remember_value(_FACE, _known_face(label))


def saved_size():
    return _known_size(QSettings(ORG, APP).value(_SIZE, _DEFAULT_SIZE))


def remember_size(size):
    remember_value(_SIZE, _known_size(size))


def _known_face(stored):
    want = str(stored or "").strip().lower()
    for label, _family in writing_faces():
        if label.lower() == want: return label
    return _DEFAULT_FACE


def _known_size(stored):
    try: size = int(stored)
    except (TypeError, ValueError): return _DEFAULT_SIZE
    return size if size in SIZES else _DEFAULT_SIZE
