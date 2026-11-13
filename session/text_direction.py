"""Keep the page writing left to right."""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor, QTextOption


class TextDirection:
    def fix_text_direction(self):
        """Fix text direction to ensure horizontal writing"""
        cursor = self.text_edit.textCursor()
        # Set text direction explicitly
        format = cursor.charFormat()
        cursor.select(QTextCursor.Document)
        cursor.setCharFormat(format)
        # Ensure document options are correct
        document = self.text_edit.document()
        option = QTextOption()
        option.setAlignment(Qt.AlignLeft)
        option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        option.setTextDirection(Qt.LeftToRight)
        document.setDefaultTextOption(option)
    # Force layout direction
        self.text_edit.setLayoutDirection(Qt.LeftToRight)
