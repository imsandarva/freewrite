"""The card that holds the question, the path, and the answers."""

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QFont, QPainter, QPen
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from choice.button import _Button
from choice.chip import _Chip
from choice.line import _Line
from choice.quiet_button import _Quiet
from choice.wrapped import _Wrapped


class _Card(QWidget):
    def __init__(self, palette, title, body, path, actions, cancel, choose):
        super().__init__()
        self._colors = palette
        self.setFixedWidth(384)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        inner = 384 - 56
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 16)
        layout.setSpacing(0)
        layout.addWidget(_Line(title, palette["title"], 20, QFont.Bold, -0.32, 30))
        layout.addSpacing(10)
        layout.addWidget(_Wrapped(body, palette["body"], inner))
        if path:
            layout.addSpacing(16)
            layout.addWidget(_Chip(path, palette))
        layout.addSpacing(22)
        row = QHBoxLayout()
        row.setSpacing(10)
        for text, choice, primary in actions:
            button = _Button(text, primary, palette)
            button.clicked.connect(lambda _checked=False, picked=choice: choose(picked))
            row.addWidget(button)
        layout.addLayout(row)
        if cancel:
            layout.addSpacing(2)
            quiet = _Quiet(palette)
            quiet.clicked.connect(lambda _checked=False: choose("cancel"))
            layout.addWidget(quiet)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setPen(QPen(self._colors["line"], 1))
        painter.setBrush(self._colors["sheet"])
        painter.drawRoundedRect(rect, 18, 18)

    def mousePressEvent(self, event):
        event.accept()
