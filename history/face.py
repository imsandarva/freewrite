"""The Lato used by History and the folder prompt."""

from PyQt5.QtGui import QFont


def face(px, weight, spacing):
    font = QFont("Lato")
    font.setPixelSize(px)
    font.setWeight(weight)
    font.setLetterSpacing(QFont.AbsoluteSpacing, spacing)
    return font
