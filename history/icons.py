"""The close, export, delete, restore, and back marks drawn on the sheet."""

from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QPen


def paint_icon(painter, kind, rect, color):
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(color, 1.6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(Qt.NoBrush)
    center = rect.center()
    if kind == "close": _paint_close(painter, center)
    elif kind == "export": _paint_export(painter, center)
    elif kind == "restore": _paint_restore(painter, center)
    elif kind == "chevron": _paint_chevron(painter, center)
    elif kind == "trash": _paint_trash(painter, center)
    painter.restore()


def _paint_close(painter, center):
    span = 5.2
    painter.drawLine(QPointF(center.x() - span, center.y() - span), QPointF(center.x() + span, center.y() + span))
    painter.drawLine(QPointF(center.x() + span, center.y() - span), QPointF(center.x() - span, center.y() + span))


def _paint_export(painter, center):
    painter.drawLine(QPointF(center.x(), center.y() - 6), QPointF(center.x(), center.y() + 1))
    painter.drawLine(QPointF(center.x(), center.y() - 6), QPointF(center.x() - 3.4, center.y() - 2.4))
    painter.drawLine(QPointF(center.x(), center.y() - 6), QPointF(center.x() + 3.4, center.y() - 2.4))
    painter.drawLine(QPointF(center.x() - 5.5, center.y() + 1.2), QPointF(center.x() - 5.5, center.y() + 6))
    painter.drawLine(QPointF(center.x() - 5.5, center.y() + 6), QPointF(center.x() + 5.5, center.y() + 6))
    painter.drawLine(QPointF(center.x() + 5.5, center.y() + 6), QPointF(center.x() + 5.5, center.y() + 1.2))


def _paint_restore(painter, center):
    painter.drawLine(QPointF(center.x() + 5.4, center.y()), QPointF(center.x() - 4.6, center.y()))
    painter.drawLine(QPointF(center.x() - 4.6, center.y()), QPointF(center.x() - 1.0, center.y() - 3.5))
    painter.drawLine(QPointF(center.x() - 4.6, center.y()), QPointF(center.x() - 1.0, center.y() + 3.5))


def _paint_chevron(painter, center):
    painter.drawLine(QPointF(center.x() + 2.3, center.y() - 5.0), QPointF(center.x() - 2.7, center.y()))
    painter.drawLine(QPointF(center.x() - 2.7, center.y()), QPointF(center.x() + 2.3, center.y() + 5.0))


def _paint_trash(painter, center):
    painter.drawLine(QPointF(center.x() - 1.5, center.y() - 6.2), QPointF(center.x() + 1.5, center.y() - 6.2))
    painter.drawLine(QPointF(center.x() - 1.5, center.y() - 6.2), QPointF(center.x() - 1.5, center.y() - 4.4))
    painter.drawLine(QPointF(center.x() + 1.5, center.y() - 6.2), QPointF(center.x() + 1.5, center.y() - 4.4))
    painter.drawLine(QPointF(center.x() - 5.2, center.y() - 4.4), QPointF(center.x() + 5.2, center.y() - 4.4))
    painter.drawLine(QPointF(center.x() - 4.2, center.y() - 3.2), QPointF(center.x() - 3.2, center.y() + 6))
    painter.drawLine(QPointF(center.x() + 4.2, center.y() - 3.2), QPointF(center.x() + 3.2, center.y() + 6))
    painter.drawLine(QPointF(center.x() - 3.2, center.y() + 6), QPointF(center.x() + 3.2, center.y() + 6))
    painter.drawLine(QPointF(center.x() - 1.1, center.y() - 1.6), QPointF(center.x() - 1.1, center.y() + 3.6))
    painter.drawLine(QPointF(center.x() + 1.1, center.y() - 1.6), QPointF(center.x() + 1.1, center.y() + 3.6))
