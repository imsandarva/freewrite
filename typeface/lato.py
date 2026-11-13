"""Register the bundled Lato files once. The family name is Lato, not the file name."""

import os

from PyQt5.QtGui import QFontDatabase

_lato_ready = False


def load_lato():
    """Register the bundled Lato files once. The family name is Lato, not the file name."""
    global _lato_ready
    if _lato_ready: return
    _lato_ready = True
    from app.paths import resource
    folder = resource("fonts")
    library = QFontDatabase()
    for name in ("Lato-Light.ttf", "Lato-Regular.ttf", "Lato-Bold.ttf"):
        path = os.path.join(folder, name)
        if os.path.isfile(path): library.addApplicationFont(path)
