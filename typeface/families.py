"""Lato, then a grotesque, the desktop face, and a book serif."""

from PyQt5.QtGui import QFont, QFontDatabase

from typeface.lato import load_lato


def _first_family(candidates, fallback):
    have = set(QFontDatabase().families())
    for name in candidates:
        if name in have: return name
    return fallback


def writing_faces():
    """Lato, then a grotesque, the desktop face, and a book serif. Labels stay short."""
    load_lato()
    system = QFontDatabase.systemFont(QFontDatabase.GeneralFont).family() or "Sans Serif"
    arial = _first_family(("Arial", "Liberation Sans", "Carlito", "DejaVu Sans"), system)
    serif = _first_family(
        ("Gentium Book Basic", "Gentium", "Liberation Serif", "Bitstream Charter", "Caladea", "Times New Roman", "DejaVu Serif", "FreeSerif"),
        "DejaVu Serif",
    )
    lato = _first_family(("Lato",), system)
    return (("Lato", lato), ("Arial", arial), ("System", system), ("Serif", serif))
