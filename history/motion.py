"""The sheet eases out, and a second click reverses it from the current frame."""

from PyQt5.QtCore import QEasingCurve, QPointF


_OPEN_MS, _CLOSE_MS = 340, 260


def ease_out():
    """Fast to leave, gentle to arrive. The same curve closes, just sooner."""
    curve = QEasingCurve(QEasingCurve.BezierSpline)
    curve.addCubicBezierSegment(QPointF(0.22, 1.0), QPointF(0.36, 1.0), QPointF(1, 1))
    return curve


def _clamped(value):
    return 0.0 if value < 0 else 1.0 if value > 1 else value
