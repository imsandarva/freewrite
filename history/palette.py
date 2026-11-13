"""Warm paper in the light, warm charcoal in the dark."""

from PyQt5.QtGui import QColor


def colors(dark):
    """Warm paper in the light, warm charcoal in the dark. The clay accent matches the rest of the app."""
    if dark:
        return {
            "sheet": QColor("#161412"), "scrim": QColor(0, 0, 0), "scrim_alpha": 64,
            "title": QColor("#F7F4EF"), "muted": QColor("#A39B92"), "body": QColor("#E8E2D8"),
            "line": QColor(255, 255, 255, 28), "hover": QColor(255, 248, 240, 16),
            "selected": QColor(196, 164, 132, 40), "accent": QColor("#D4B496"),
            "icon": QColor("#B7AFA6"), "icon_hot": QColor("#F3E6D6"), "danger": QColor("#E7B1A6"),
            "icon_bg": QColor(255, 255, 255, 20), "shadow": 96,
        }
    return {
        "sheet": QColor("#FBF9F6"), "scrim": QColor(42, 32, 22), "scrim_alpha": 22,
        "title": QColor("#1C1917"), "muted": QColor("#8A8178"), "body": QColor("#2A2622"),
        "line": QColor(48, 38, 28, 32), "hover": QColor(48, 36, 24, 14),
        "selected": QColor(140, 104, 66, 28), "accent": QColor("#8C6842"),
        "icon": QColor("#8A8178"), "icon_hot": QColor("#3E342C"), "danger": QColor("#9C463C"),
        "icon_bg": QColor(48, 36, 24, 16), "shadow": 48,
    }
