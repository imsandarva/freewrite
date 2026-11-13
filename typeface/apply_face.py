"""Restyle the page, words already written included, without moving the caret."""

from PyQt5.QtGui import QTextCharFormat, QTextCursor

from typeface.specimen import specimen


def apply_face(edit, family, pixels):
    """Restyle the page, words already written included, without moving the caret.

    A theme reload polishes the editor and puts the widget font back to the
    application default. The characters keep their own font, which is why the
    face is written onto them and onto the caret, not only onto the widget.
    """
    font = specimen(family, pixels)
    cursor = edit.textCursor()
    position, anchor = cursor.position(), cursor.anchor()
    scroll = edit.verticalScrollBar().value()
    edit.setUpdatesEnabled(False)
    edit.blockSignals(True)
    try:
        edit.setFont(font)
        edit.document().setDefaultFont(font)
        fmt = QTextCharFormat()
        fmt.setFont(font)
        if edit.document().characterCount() > 1:
            whole = QTextCursor(edit.document())
            whole.select(QTextCursor.Document)
            whole.setCharFormat(fmt)
        edit.setCurrentCharFormat(fmt)
        restored = edit.textCursor()
        restored.setPosition(anchor)
        if position != anchor: restored.setPosition(position, QTextCursor.KeepAnchor)
        edit.setTextCursor(restored)
        edit.verticalScrollBar().setValue(scroll)
    finally:
        edit.blockSignals(False)
        edit.setUpdatesEnabled(True)
