"""A shade over the writing, and the sheet sliding in from the right."""

from PyQt5.QtCore import Qt, QPoint, QRectF, QPropertyAnimation, pyqtProperty, pyqtSignal
from PyQt5.QtGui import QColor, QLinearGradient, QPainter
from PyQt5.QtWidgets import QWidget

from history.lato import ensure_lato
from history.motion import _CLOSE_MS, _OPEN_MS, _clamped, ease_out
from history.palette import colors
from history.sheet import HistorySheet


class HistoryDrawer(QWidget):
    """A shade over the writing, and the sheet sliding in from the right."""

    chosen = pyqtSignal(object)
    delete_requested = pyqtSignal(object)
    export_requested = pyqtSignal(object)
    change_requested = pyqtSignal()
    dismissed = pyqtSignal()
    opened = pyqtSignal()
    trash_requested = pyqtSignal()
    restore_requested = pyqtSignal(object)
    purge_requested = pyqtSignal(object)
    empty_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        ensure_lato()
        self._progress, self._closing, self._host = 0.0, False, None
        self._colors = colors(False)
        self.sheet = HistorySheet()
        self.sheet.setParent(self)
        self.sheet.chosen.connect(self.chosen)
        self.sheet.delete_requested.connect(self.delete_requested)
        self.sheet.export_requested.connect(self.export_requested)
        self.sheet.close_requested.connect(self.close_sheet)
        self.sheet.change_requested.connect(self.change_requested)
        self.sheet.trash_requested.connect(self.trash_requested)
        self.sheet.restore_requested.connect(self.restore_requested)
        self.sheet.purge_requested.connect(self.purge_requested)
        self.sheet.empty_requested.connect(self.empty_requested)
        self._anim = QPropertyAnimation(self, b"progress", self)
        self._anim.finished.connect(self._on_finished)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.hide()

    def fit_over(self, bar):
        """Dock to the top and right, and stop at the bar. A hidden bar means the sheet uses the whole window."""
        self._host = bar
        parent = self.parentWidget()
        if parent is None: return
        if bar is None or not bar.isVisible():
            self.setGeometry(0, 0, parent.width(), parent.height())
        else:
            bottom = bar.mapTo(parent, QPoint(0, 0)).y()
            self.setGeometry(0, 0, parent.width(), max(0, bottom))
        if self.isVisible(): self.raise_()

    def apply_paper(self, paper):
        self._colors = colors(paper)
        self.sheet.apply_colors(self._colors)
        self.update()

    def set_entries(self, entries, selected_id):
        self.sheet.set_entries(entries, selected_id)

    def set_place(self, shown, full):
        self.sheet.set_place(shown, full)

    def set_trash(self, items):
        self.sheet.set_trash(items)

    def open_trash(self):
        self.sheet.open_trash()

    def close_trash(self):
        return self.sheet.close_trash()

    def is_open(self):
        return self.isVisible() and self._progress > 0.01

    def toggle(self):
        if self.isVisible() and not self._closing: self.close_sheet()
        else: self.open_sheet()

    def open_sheet(self):
        if self._host is not None: self.fit_over(self._host)
        self._closing = False
        self.show()
        self.raise_()
        self._run(1.0, _OPEN_MS)
        self.opened.emit()

    def close_sheet(self):
        if not self.isVisible() or self._closing: return
        self.sheet.park_trash()
        self._closing = True
        self._run(0.0, _CLOSE_MS)

    def mousePressEvent(self, event):
        # A press on the shaded page, not the sheet, puts history away.
        if event.button() == Qt.LeftButton and event.x() < self.sheet.x():
            self.close_sheet()
            return
        super().mousePressEvent(event)

    def wheelEvent(self, event):
        event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._place_sheet()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        shade = QColor(self._colors["scrim"])
        shade.setAlpha(int(self._colors["scrim_alpha"] * _clamped(self._progress)))
        painter.fillRect(self.rect(), shade)
        self._paint_shadow(painter)

    def _paint_shadow(self, painter):
        if self._progress <= 0: return
        edge, span = self.sheet.x(), 24
        fade = QLinearGradient(edge - span, 0, edge, 0)
        fade.setColorAt(0.0, QColor(0, 0, 0, 0))
        fade.setColorAt(1.0, QColor(0, 0, 0, int(self._colors["shadow"] * _clamped(self._progress))))
        painter.fillRect(QRectF(edge - span, 0, span, self.height()), fade)

    def _sheet_width(self):
        room = self.width()
        if room < 300: return max(0, room)
        return min(400, room - 72)

    def _place_sheet(self):
        width = self._sheet_width()
        shown = int(round(width * _clamped(self._progress)))
        self.sheet.setGeometry(self.width() - shown, 0, width, self.height())

    def _run(self, end, duration):
        self._anim.stop()
        self._anim.setEasingCurve(ease_out())
        self._anim.setDuration(duration)
        self._anim.setStartValue(self._progress)
        self._anim.setEndValue(end)
        if abs(self._progress - end) < 0.001:
            self._progress = end
            self._place_sheet()
            self._on_finished()
            return
        self._anim.start()

    def _on_finished(self):
        if self._closing and self._progress <= 0.001:
            self.sheet.dismiss_trash()
            self.hide()
            self._closing = False
            self.dismissed.emit()

    def _progress_value(self):
        return self._progress

    def _set_progress(self, value):
        self._progress = float(value)
        self._place_sheet()
        self.update()

    progress = pyqtProperty(float, _progress_value, _set_progress)
