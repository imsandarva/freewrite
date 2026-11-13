"""How wide a run of text is in a given font."""

from PyQt5.QtGui import QFontMetrics


def _advance(metrics, text):
    return metrics.horizontalAdvance(text) if hasattr(metrics, "horizontalAdvance") else metrics.width(text)
