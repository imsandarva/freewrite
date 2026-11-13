"""The font the page and the specimen word are drawn in."""

from PyQt5.QtGui import QFont

from typeface.lato import load_lato


def specimen(family, px):
    load_lato()
    font = QFont(family)
    font.setPixelSize(int(px))
    font.setWeight(QFont.Normal)
    font.setStyleStrategy(QFont.PreferAntialias)
    return font
