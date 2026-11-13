"""A plain text button on the bottom bar."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton


def text_button(label, dark):
    button = QPushButton(label)
    button.setProperty("dark", bool(dark))
    button.setCursor(Qt.PointingHandCursor)
    button.setFocusPolicy(Qt.TabFocus)
    return button
