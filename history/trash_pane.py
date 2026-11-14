"""Trash, sliding in over History from the right edge of the sheet."""

from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, pyqtProperty, pyqtSignal
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import QFrame, QScrollArea, QVBoxLayout, QWidget

from history.grouping import group_by_month
from history.layout import drop_children
from history.month_heading import MonthHeading
from history.motion import _clamped, ease_out
from history.palette import colors
from history.paper import Paper
from history.scroll import scroll_css
from history.trash_empty import EmptyTrash
from history.trash_header import TrashHeader
from history.trash_row import TrashRow
from trash.phrase import trash_count

_OPEN_MS, _CLOSE_MS = 300, 220


class TrashPane(QWidget):
    """A second sheet. It covers History, and History is still underneath when it leaves."""

    restore_requested = pyqtSignal(object)
    purge_requested = pyqtSignal(object)
    empty_requested = pyqtSignal()
    back_requested = pyqtSignal()
    close_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._colors = colors(False)
        self._items, self._signature = [], None
        self._progress, self._closing = 0.0, False
        self.header = TrashHeader()
        self.header.back_requested.connect(self.back_requested)
        self.header.close_requested.connect(self.close_requested)
        self.header.empty_requested.connect(self.empty_requested)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_host = Paper()
        self.list_layout = QVBoxLayout(self.list_host)
        self.list_layout.setContentsMargins(0, 6, 0, 16)
        self.list_layout.setSpacing(0)
        self.scroll.setWidget(self.list_host)
        self._paper = QColor("#FBF9F6")
        self._edge = QWidget(self)
        self._edge.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.header)
        layout.addWidget(self.scroll, 1)
        self._anim = QPropertyAnimation(self, b"progress", self)
        self._anim.finished.connect(self._on_finished)
        self.setAutoFillBackground(False)
        self.apply_colors(self._colors)
        self.hide()

    def apply_colors(self, palette):
        self._colors = palette
        self._paper = QColor(palette["sheet"])
        self._signature = None
        self.header.apply_colors(palette)
        self.list_host.set_paper(self._paper)
        self.scroll.viewport().setAutoFillBackground(False)
        self.scroll.viewport().setStyleSheet("background: %s;" % self._paper.name())
        self.scroll.setStyleSheet(scroll_css(palette))
        line = palette["line"]
        self._edge.setStyleSheet("background: rgba(%d, %d, %d, %d);" % (line.red(), line.green(), line.blue(), line.alpha()))
        self._refill()
        self.update()

    def set_items(self, items):
        self._items = list(items)
        self._refill()

    def is_open(self):
        return self.isVisible() and self._progress > 0.01

    def is_closing(self):
        return self._closing

    def open_pane(self):
        if self.isVisible() and not self._closing and self._progress > 0.98: return
        self._closing = False
        self.place()
        self.show()
        self.raise_()
        self._run(1.0, _OPEN_MS)

    def close_pane(self):
        if not self.isVisible() or self._closing: return
        self._closing = True
        self._run(0.0, _CLOSE_MS)

    def park(self):
        """Hold this frame. History is leaving, and Trash leaves with it."""
        self._anim.stop()

    def dismiss(self):
        # Clear the closing flag first, so stopping the slide cannot treat this as a finished close.
        self._closing = False
        self._anim.stop()
        self._progress = 0.0
        self.place()
        self.hide()

    def place(self):
        parent = self.parentWidget()
        if parent is None: return
        width, height = parent.width(), parent.height()
        shown = int(round(width * _clamped(self._progress)))
        self.setGeometry(width - shown, 0, width, height)

    def mousePressEvent(self, event):
        event.accept()

    def wheelEvent(self, event):
        event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._edge.setGeometry(0, 0, 1, self.height())
        self._edge.raise_()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._paper)

    def _sign(self):
        rows = tuple((str(item.id), item.preview_text, item.when) for item in self._items)
        return (self._colors["sheet"].name(), rows)

    def _refill(self):
        signature = self._sign()
        if signature == self._signature: return
        self._signature = signature
        place = self.scroll.verticalScrollBar().value()
        drop_children(self.list_layout)
        self.header.set_count(trash_count(len(self._items)), bool(self._items))
        if not self._items:
            self.list_layout.addWidget(EmptyTrash(self._colors["muted"], self._colors["sheet"]))
            self.list_layout.addStretch(1)
        else:
            self._add_rows()
        QTimer.singleShot(0, lambda value=place: self.scroll.verticalScrollBar().setValue(value))

    def _add_rows(self):
        first = True
        for label, rows in group_by_month(self._items, moment=lambda item: item.deleted):
            self.list_layout.addWidget(MonthHeading(label, self._colors["muted"], self._colors["sheet"], first))
            first = False
            for item in rows: self._add_row(item)
        self.list_layout.addStretch(1)

    def _add_row(self, item):
        row = TrashRow(item, self._colors)
        row.restore_requested.connect(self.restore_requested)
        row.purge_requested.connect(self.purge_requested)
        self.list_layout.addWidget(row)

    def _run(self, end, duration):
        self._anim.stop()
        self._anim.setEasingCurve(ease_out())
        self._anim.setDuration(duration)
        self._anim.setStartValue(self._progress)
        self._anim.setEndValue(end)
        if abs(self._progress - end) < 0.001:
            self._progress = end
            self.place()
            self._on_finished()
            return
        self._anim.start()

    def _on_finished(self):
        if self._closing and self._progress <= 0.001:
            self.hide()
            self._closing = False

    def _progress_value(self):
        return self._progress

    def _set_progress(self, value):
        self._progress = float(value)
        self.place()
        parent = self.parentWidget()
        if parent is not None: parent.update()

    progress = pyqtProperty(float, _progress_value, _set_progress)
