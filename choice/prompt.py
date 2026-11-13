"""The frameless question shown over the writing window."""

import time

from PyQt5.QtCore import QPoint, QRectF, Qt, QTimer, QVariantAnimation
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import QDialog

from choice.card import _Card
from history.lato import ensure_lato
from history.motion import ease_out
from history.palette import colors

_GUARD_S = 0.22


class _Prompt(QDialog):
    def __init__(self, parent, dark, title, body, path, actions, cancel):
        super().__init__(parent)
        ensure_lato()
        self._dark = bool(dark)
        self._can_cancel = cancel
        self.choice = "cancel" if cancel else "okay"
        self._lift = 10.0
        self._guard_until = 0.0
        self._colors = colors(self._dark)
        self.card = _Card(self._colors, title, body, path, actions, cancel, self._finish)
        self.card.setParent(self)
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(ease_out())
        self._anim.valueChanged.connect(self._arrive)
        self._anim.finished.connect(self._settled)
        self.setModal(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setStyleSheet("QDialog { background: transparent; }")

    @staticmethod
    def open(parent, dark, title, body, path, actions, cancel):
        host = parent.window() if parent is not None else None
        dialog = _Prompt(host, dark, title, body, path, actions, cancel)
        if host is not None:
            origin = host.mapToGlobal(QPoint(0, 0))
            dialog.setGeometry(origin.x(), origin.y(), max(host.width(), 420), max(host.height(), 320))
        else:
            dialog.resize(640, 420)
        dialog.exec_()
        return dialog.choice

    def showEvent(self, event):
        super().showEvent(event)
        self._guard_until = time.monotonic() + _GUARD_S
        self.setWindowOpacity(0)
        self._anim.stop()
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()
        QTimer.singleShot(0, lambda: self.setFocus(Qt.OtherFocusReason))
        QTimer.singleShot(420, self._settled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._place()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 124) if self._dark else QColor(36, 28, 20, 72))
        self._paint_shadow(painter)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.card.geometry().contains(event.pos()):
            self._finish("cancel" if self._can_cancel else "okay")
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and time.monotonic() < self._guard_until:
            event.accept()
            return
        if event.key() == Qt.Key_Escape:
            self._finish("cancel" if self._can_cancel else "okay")
            return
        super().keyPressEvent(event)

    def _finish(self, choice):
        self.choice = choice
        self.done(QDialog.Accepted)

    def _arrive(self, value):
        value = float(value)
        self.setWindowOpacity(0.01 + 0.99 * value)
        self._lift = 10 * (1 - value)
        self._place()

    def _settled(self):
        """If the fade never runs, the prompt must still be visible. A hidden modal would trap the window."""
        if not self.isVisible(): return
        self._lift = 0
        self.setWindowOpacity(1)
        self._place()

    def _place(self):
        self.card.adjustSize()
        width, height = self.card.width(), self.card.sizeHint().height()
        x = max(12, (self.width() - width) // 2)
        y = max(12, int((self.height() - height) / 2 + self._lift))
        self.card.setGeometry(x, y, width, height)
        self.card.raise_()

    def _paint_shadow(self, painter):
        rect = QRectF(self.card.geometry())
        painter.setPen(Qt.NoPen)
        for spread, alpha, drop in ((22, 12, 14), (12, 18, 8), (5, 24, 3)):
            painter.setBrush(QColor(40, 26, 16, alpha))
            painter.drawRoundedRect(rect.adjusted(-spread, drop - spread * 0.25, spread, spread + drop), 22, 22)
