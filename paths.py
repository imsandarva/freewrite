"""Where the app's own files live.

The same folder holds the code when you run it from the source tree and after
it is installed under /usr/share/freewrite. Looking beside this file, instead
of at the folder the app was started from, is what lets a menu launch find
the stylesheet, the welcome note, and the icon.
"""

import os

ROOT = os.path.dirname(os.path.abspath(__file__))


def resource(*parts):
    """A file that ships with the app."""
    return os.path.join(ROOT, *parts)


def app_icon():
    """The pencil, with the plain backdrop already removed when that copy exists."""
    processed = resource("assets", "app-icon.png")
    if os.path.isfile(processed): return processed
    return resource("assets", "pencil_icon.png")


def prepare_app(app):
    """Tell the desktop which app this window is, and load the stylesheet."""
    app.setApplicationName("Freewrite")
    if hasattr(app, "setDesktopFileName"): app.setDesktopFileName("freewrite")
    with open(resource("assets", "style.qss"), encoding="utf-8") as handle:
        app.setStyleSheet(handle.read())
