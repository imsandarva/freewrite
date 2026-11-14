"""The list of notes, the header, and the pinned folder row."""

from PyQt5.QtCore import Qt, QRectF, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QLinearGradient, QPainter
from PyQt5.QtWidgets import QFrame, QScrollArea, QVBoxLayout, QWidget

from history.cursor import moved
from history.empty_history import EmptyHistory
from history.grouping import count_label, group_by_month
from history.header import SheetHeader
from history.layout import drop_children
from history.location_bar import LocationBar
from history.month_heading import MonthHeading
from history.palette import colors
from history.paper import Paper
from history.row import HistoryRow
from history.scroll import scroll_css
from history.trash_pane import TrashPane


class HistorySheet(QWidget):
    chosen = pyqtSignal(object)
    delete_requested = pyqtSignal(object)
    export_requested = pyqtSignal(object)
    close_requested = pyqtSignal()
    change_requested = pyqtSignal()
    trash_requested = pyqtSignal()
    restore_requested = pyqtSignal(object)
    purge_requested = pyqtSignal(object)
    empty_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._colors = colors(False)
        self._entries, self._selected_id, self._signature = [], None, None
        self._cursor, self._rows = -1, []
        self.header = SheetHeader()
        self.header.close_requested.connect(self.close_requested)
        self.header.trash_requested.connect(self.trash_requested)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_host = Paper()
        self.list_layout = QVBoxLayout(self.list_host)
        self.list_layout.setContentsMargins(0, 6, 0, 12)
        self.list_layout.setSpacing(0)
        self.scroll.setWidget(self.list_host)
        self._paper = QColor("#FBF9F6")
        self.setAutoFillBackground(False)
        self._edge = QWidget(self)
        self._edge.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.place = LocationBar()
        self.place.clicked.connect(self.change_requested)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.header)
        layout.addWidget(self.scroll, 1)
        layout.addWidget(self.place)
        self.pane = TrashPane()
        self.pane.setParent(self)
        self.pane.restore_requested.connect(self.restore_requested)
        self.pane.purge_requested.connect(self.purge_requested)
        self.pane.empty_requested.connect(self.empty_requested)
        self.pane.back_requested.connect(self.close_trash)
        self.pane.close_requested.connect(self.close_requested)
        self.apply_colors(self._colors)

    def apply_colors(self, palette):
        self._colors = palette
        self._paper = QColor(palette["sheet"])
        self._signature = None
        self.header.apply_colors(palette)
        self.place.apply_colors(palette)
        self.list_host.set_paper(self._paper)
        self.scroll.viewport().setAutoFillBackground(False)
        self.scroll.viewport().setStyleSheet("background: %s;" % self._paper.name())
        self.scroll.setStyleSheet(scroll_css(palette))
        line = palette["line"]
        self._edge.setStyleSheet("background: rgba(%d, %d, %d, %d);" % (line.red(), line.green(), line.blue(), line.alpha()))
        self.pane.apply_colors(palette)
        self._refill()
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._paper)
        self._paint_trash_shadow(painter)

    def set_entries(self, entries, selected_id):
        previous = self._cursor_id()
        follow = selected_id if selected_id != self._selected_id else previous
        self._entries, self._selected_id = list(entries), selected_id
        self._cursor = self._placed(follow)
        self._refill()

    def arm_cursor(self):
        """Start the keyboard mark on the note that is open, then bring that row into view."""
        self._cursor = self._placed(self._selected_id)
        self._mark_rows()
        self._reveal_cursor()
        QTimer.singleShot(0, self._reveal_cursor)

    def move_cursor(self, delta):
        nxt = moved(self._cursor, len(self._entries), delta)
        if nxt == self._cursor: return
        self._cursor = nxt
        self._mark_rows()
        self._reveal_cursor()

    def open_cursor(self):
        if not 0 <= self._cursor < len(self._entries): return
        self.chosen.emit(self._entries[self._cursor])

    def trash_covers(self):
        return self.pane.isVisible() and not self.pane.is_closing()

    def set_place(self, shown, full):
        self.place.set_place(shown, full)

    def set_trash(self, items):
        items = list(items)
        self.header.set_trash_count(len(items))
        self.pane.set_items(items)

    def open_trash(self):
        self.pane.open_pane()
        self.pane.raise_()

    def close_trash(self):
        """Close Trash when it is showing and not already on its way out."""
        if not self.pane.is_open() or self.pane.is_closing(): return False
        self.pane.close_pane()
        return True

    def park_trash(self):
        self.pane.park()

    def dismiss_trash(self):
        self.pane.dismiss()

    def mousePressEvent(self, event):
        event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._edge.setGeometry(0, 0, 1, self.height())
        self.pane.place()
        self._edge.raise_()
        if self.pane.isVisible(): self.pane.raise_()

    def _sign(self):
        rows = tuple((str(entry.id), entry.preview_text, entry.date) for entry in self._entries)
        return (self._colors["sheet"].name(), str(self._selected_id), rows)

    def _refill(self):
        signature = self._sign()
        if signature == self._signature: return
        self._signature = signature
        place = self.scroll.verticalScrollBar().value()
        drop_children(self.list_layout)
        self.header.set_count(count_label(len(self._entries)))
        if not self._entries:
            self._rows = []
            self.list_layout.addWidget(EmptyHistory(self._colors["muted"], self._colors["sheet"]))
            self.list_layout.addStretch(1)
        else:
            self._add_rows()
        QTimer.singleShot(0, lambda value=place: self._restore(value))

    def _add_rows(self):
        self._rows, first, index = [], True, 0
        for label, rows in group_by_month(self._entries):
            self.list_layout.addWidget(MonthHeading(label, self._colors["muted"], self._colors["sheet"], first))
            first = False
            for entry in rows:
                self._add_row(entry, index)
                index += 1
        self.list_layout.addStretch(1)

    def _add_row(self, entry, index):
        row = HistoryRow(entry, entry.id == self._selected_id, self._colors, index == self._cursor)
        row.chosen.connect(self.chosen)
        row.delete_requested.connect(self.delete_requested)
        row.export_requested.connect(self.export_requested)
        self._rows.append(row)
        self.list_layout.addWidget(row)

    def _cursor_id(self):
        if not 0 <= self._cursor < len(self._entries): return None
        return self._entries[self._cursor].id

    def _placed(self, entry_id):
        found = self._index_of(entry_id)
        if found >= 0: return found
        found = self._index_of(self._selected_id)
        if found >= 0: return found
        return 0 if self._entries else -1

    def _index_of(self, entry_id):
        if entry_id is None: return -1
        for index, entry in enumerate(self._entries):
            if entry.id == entry_id: return index
        return -1

    def _mark_rows(self):
        for index, row in enumerate(self._rows): row.set_keyed(index == self._cursor)

    def _reveal_cursor(self):
        if not 0 <= self._cursor < len(self._rows): return
        self.scroll.ensureWidgetVisible(self._rows[self._cursor], 0, 48)

    def _restore(self, value):
        self.scroll.verticalScrollBar().setValue(value)

    def _paint_trash_shadow(self, painter):
        # The shadow sits on History, just left of Trash, and only while Trash is still sliding.
        progress = self.pane.progress if self.pane.isVisible() else 0
        if progress <= 0 or progress >= 1: return
        edge, span = self.pane.x(), 22
        fade = QLinearGradient(edge - span, 0, edge, 0)
        fade.setColorAt(0.0, QColor(0, 0, 0, 0))
        fade.setColorAt(1.0, QColor(0, 0, 0, int(self._colors["shadow"] * progress)))
        painter.fillRect(QRectF(max(0, edge - span), 0, span, self.height()), fade)
