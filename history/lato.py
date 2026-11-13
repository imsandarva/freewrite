"""Load the real Lato weights so titles are not a faked bold."""

import os

from PyQt5.QtGui import QFontDatabase

_FACES = ("Lato-Light.ttf", "Lato-Regular.ttf", "Lato-Bold.ttf")
_lato_ready = False


def ensure_lato():
    """Load the real Lato weights so titles are not a faked bold."""
    global _lato_ready
    if _lato_ready: return
    _lato_ready = True
    from app.paths import resource
    folder = resource("fonts")
    library = QFontDatabase()
    for name in _FACES:
        path = os.path.join(folder, name)
        if os.path.isfile(path): library.addApplicationFont(path)
