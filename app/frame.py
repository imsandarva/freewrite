"""The ordinary window, and whether it was maximized.

The rectangle of a maximized window is just the screen, so that size is never
what gets kept. The ordinary rectangle is taken while the window is restored,
including the moment before maximize. The next launch puts that rectangle back,
then asks the desktop to maximize when that was the form last used. Fullscreen
and the taskbar are not a form to reopen in.
"""

from PyQt5.QtCore import QByteArray, QSettings, QTimer, Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QApplication

from utils.qsettings_identity import APP, ORG
from utils.remember import remember_value
from utils.settings_flag import setting_is_on

_GEOMETRY, _MAXIMIZED = "windowGeometry", "windowMaximized"
_DEFAULT_W, _DEFAULT_H = 1100, 600
_MIN_W, _MIN_H = 320, 200
# The desktop ignores a maximize request made before it has taken the window.
_SETTLE_MS, _RETRY_MS, _REVEAL_MS, _FLUSH_MS = 80, 180, 420, 300


class _Slot:
    def __init__(self, maximized):
        self.maximized = maximized
        self.blob = None
        self.live = False
        self.hiding = False
        self.closed = False
        self.tries = 0
        self.flush_timer = None


_slots = {}


def place(window):
    """Size the window before it is shown. A saved rectangle that misses every screen is centered."""
    if _restore(window): return
    window.resize(_DEFAULT_W, _DEFAULT_H)
    _center(window)


def present(window):
    """Open in the form last used. Maximized stays unseen until the desktop has actually done it."""
    place(window)
    slot = _Slot(_saved_maximized())
    _slots[window] = slot
    if slot.maximized:
        slot.hiding = True
        window.setWindowOpacity(0)
    window.show()
    _later(window, _SETTLE_MS, _settle)
    _later(window, _REVEAL_MS, _reveal)


def keep(window):
    """Write the form now. Closing does not wait for the trailing timer."""
    slot = _slots.get(window)
    if slot is None: return
    slot.closed = True
    if window.windowState() == Qt.WindowNoState: _capture(window)
    else: slot.maximized = bool(window.windowState() & Qt.WindowMaximized)
    _flush(window)


def note_frame(window):
    slot = _slots.get(window)
    if slot is None or not slot.live or slot.closed: return
    if slot.hiding and window.isMaximized() and _fills_screen(window): _reveal(window)
    if window.windowState() != Qt.WindowNoState: return
    _capture(window)
    _flush_later(window)


def note_state(window):
    slot = _slots.get(window)
    if slot is None or not slot.live or slot.closed: return
    slot.maximized = bool(window.windowState() & Qt.WindowMaximized)
    _flush_later(window)


def _saved_maximized():
    return setting_is_on(QSettings(ORG, APP).value(_MAXIMIZED), False)


def _saved_blob():
    value = QSettings(ORG, APP).value(_GEOMETRY)
    if isinstance(value, QByteArray) and not value.isEmpty(): return value
    if isinstance(value, (bytes, bytearray)) and value: return QByteArray(bytes(value))
    return None


def _restore(window):
    blob = _saved_blob()
    if blob is None or not window.restoreGeometry(blob): return False
    rect = window.geometry()
    if rect.width() < _MIN_W or rect.height() < _MIN_H: return False
    if not _on_screen(window): _center(window)
    return True


def _center(window):
    frame = window.frameGeometry()
    screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
    if screen is None: return
    frame.moveCenter(screen.availableGeometry().center())
    window.move(frame.topLeft())


def _on_screen(window):
    frame = window.frameGeometry()
    return any(_overlaps(frame, screen.availableGeometry()) for screen in QApplication.screens())


def _overlaps(frame, area):
    hit = area.intersected(frame)
    return hit.width() >= 80 and hit.height() >= 40


def _settle(window):
    slot = _slots.get(window)
    if slot is None or slot.closed or slot.live or not window.isVisible(): return
    slot.live = True
    if window.windowState() == Qt.WindowNoState: _capture(window)
    if not slot.maximized:
        _flush(window)
        return
    window.showMaximized()
    _later(window, _RETRY_MS, _retry_max)


def _retry_max(window):
    slot = _slots.get(window)
    if slot is None or slot.closed or not slot.maximized or window.isMaximized(): return
    if slot.tries >= 2: return
    slot.tries += 1
    window.showMaximized()
    _later(window, _RETRY_MS, _retry_max)


def _reveal(window):
    slot = _slots.get(window)
    if slot is None or slot.closed or not slot.hiding: return
    if slot.maximized and not window.isMaximized():
        # The desktop left the ordinary window. Remember that, so the next open does not wait unseen.
        slot.maximized = False
        if window.windowState() == Qt.WindowNoState: _capture(window)
        _flush(window)
    slot.hiding = False
    window.setWindowOpacity(1)
    window.raise_()
    window.activateWindow()


def _fills_screen(window):
    screen = window.screen() or QApplication.primaryScreen()
    if screen is None: return False
    return window.geometry().width() >= int(screen.availableGeometry().width() * 0.9)


def _capture(window):
    slot = _slots.get(window)
    if slot is None: return
    blob = bytes(window.saveGeometry())
    if blob: slot.blob = blob


def _flush_later(window):
    slot = _slots.get(window)
    if slot is None or slot.closed: return
    if slot.flush_timer is None:
        timer = QTimer(window)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: _flush(window))
        slot.flush_timer = timer
    slot.flush_timer.start(_FLUSH_MS)


def _flush(window):
    slot = _slots.get(window)
    if slot is None: return
    if slot.flush_timer is not None: slot.flush_timer.stop()
    if slot.blob: remember_value(_GEOMETRY, QByteArray(slot.blob))
    remember_value(_MAXIMIZED, bool(slot.maximized))


def _later(window, delay, action):
    QTimer.singleShot(delay, lambda: action(window))
