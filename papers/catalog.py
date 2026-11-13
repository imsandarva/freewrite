"""The five writing papers, in the order a press walks through them.

White is pure paper. Warm White is ivory. Sepia is a muted beige.
Charcoal is a soft dark gray. Black is true black, for an OLED screen.
A missing setting, and the old light setting, open on White. The old dark
setting opens on Black, which is the black the app used before.
"""

from PyQt5.QtCore import QSettings

from utils.qsettings_identity import APP, ORG

_KEY = "colorScheme"
_LEGACY = {"light": "white", "dark": "black"}


class Paper:
    """One stock of paper. Colors are hex so the catalog does not paint anything."""

    __slots__ = ("key", "label", "dark", "page", "sheet", "ink", "muted", "hover", "accent", "track", "knob", "danger")

    def __init__(self, key, label, dark, page, sheet, ink, muted, hover, accent, track, knob, danger):
        self.key, self.label, self.dark = key, label, bool(dark)
        self.page, self.sheet, self.ink, self.muted = page, sheet, ink, muted
        self.hover, self.accent, self.track, self.knob, self.danger = hover, accent, track, knob, danger


# page is the writing surface. sheet is the same stock, lifted only where a layer needs to separate.
_ALL = (
    Paper("white", "White", False, "#FFFFFF", "#FFFFFF", "#1A1714", "#8A8178", "#1A1714", "#A6845B", "#E7E2DB", "#FFFFFF", "#9C463C"),
    Paper("ivory", "Warm White", False, "#F6F0E6", "#F6F0E6", "#2A241C", "#8A7D70", "#1C1814", "#9A7044", "#E3D8C8", "#FFFCF8", "#9C463C"),
    Paper("sepia", "Sepia", False, "#E5D4B6", "#E5D4B6", "#3F3226", "#7A6854", "#2A2118", "#8A5A32", "#D3C1A4", "#F7F0E2", "#8E4036"),
    Paper("charcoal", "Charcoal", True, "#343230", "#3C3A37", "#E7E1D8", "#A49C93", "#F6F1EA", "#D4B496", "#45423E", "#F4F0EA", "#E7B1A6"),
    Paper("black", "Black", True, "#000000", "#121212", "#E6E2DC", "#8F8880", "#F3EFE9", "#CDB08C", "#2A2A2A", "#F2F0EC", "#E7B1A6"),
)
PAPERS = {paper.key: paper for paper in _ALL}
ORDER = tuple(paper.key for paper in _ALL)


def channels(hex_color):
    text = str(hex_color).lstrip("#")
    return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)


def rgba(hex_color, alpha):
    red, green, blue = channels(hex_color)
    return "rgba(%d, %d, %d, %.3f)" % (red, green, blue, float(alpha))


def mix(origin, toward, amount):
    """Move hex `origin` toward hex `toward`. Amount is 0 through 1."""
    amount = 0.0 if amount < 0 else 1.0 if amount > 1 else float(amount)
    left, right = channels(origin), channels(toward)
    blended = tuple(int(round(a + (b - a) * amount)) for a, b in zip(left, right))
    return "#%02X%02X%02X" % blended


def paper_for(stored):
    """The paper a saved value names. Anything unfamiliar is White."""
    key = str(stored or "white").strip().lower()
    key = _LEGACY.get(key, key)
    return PAPERS.get(key, PAPERS["white"])


def next_paper(paper):
    index = ORDER.index(paper.key)
    return PAPERS[ORDER[(index + 1) % len(ORDER)]]


def saved_paper():
    return paper_for(QSettings(ORG, APP).value(_KEY, "white"))


def remember_paper(paper):
    QSettings(ORG, APP).setValue(_KEY, paper.key)
