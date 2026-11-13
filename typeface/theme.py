"""Follow the dark property when the theme reloads."""

from PyQt5.QtCore import QEvent


def _note_dark(widget, event):
    if event.type() == QEvent.DynamicPropertyChange and bytes(event.propertyName()) == b"dark":
        widget._dark = widget.property("dark") is True
        widget.update()
