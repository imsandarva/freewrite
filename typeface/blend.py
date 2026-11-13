"""Blend two colors. t is clamped to the unit interval."""

from PyQt5.QtGui import QColor


def _mix(a, b, t):
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    return QColor(
        int(a.red() + (b.red() - a.red()) * t), int(a.green() + (b.green() - a.green()) * t),
        int(a.blue() + (b.blue() - a.blue()) * t), int(a.alpha() + (b.alpha() - a.alpha()) * t),
    )
