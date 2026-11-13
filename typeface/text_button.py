"""A plain text button on the bottom bar."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton


def text_button(label):
    button = QPushButton(label)
    button.setCursor(Qt.PointingHandCursor)
    button.setFocusPolicy(Qt.TabFocus)
    return button
