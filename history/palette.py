"""Sheet colors taken from the writing paper, so History is the same stock as the page."""

from PyQt5.QtGui import QColor

from papers.catalog import paper_for


def _tint(hex_color, alpha):
    color = QColor(hex_color)
    color.setAlpha(int(alpha))
    return color


def colors(paper=None):
    """One palette for the sheet. A bare true/false still resolves, for the moment before a paper arrives."""
    if paper is True: paper = paper_for("black")
    elif not hasattr(paper, "page"): paper = paper_for("white")
    dark = paper.dark
    return {
        "sheet": QColor(paper.sheet),
        "scrim": QColor(0, 0, 0) if dark else QColor(42, 32, 22),
        "scrim_alpha": 78 if dark else 26,
        "title": QColor(paper.hover if dark else paper.ink),
        "muted": QColor(paper.muted), "body": QColor(paper.ink),
        "line": _tint("#FFFFFF" if dark else paper.ink, 32 if dark else 28),
        "hover": _tint("#FFFFFF" if dark else paper.ink, 16 if dark else 14),
        "selected": _tint(paper.accent, 46 if dark else 36),
        "accent": QColor(paper.accent),
        "icon": QColor(paper.muted), "icon_hot": QColor(paper.hover), "danger": QColor(paper.danger),
        "icon_bg": _tint("#FFFFFF" if dark else paper.ink, 22 if dark else 16),
        "shadow": 96 if dark else 42,
    }
