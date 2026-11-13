"""The list of notes, the header, and the pinned folder row."""

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import QFrame, QScrollArea, QVBoxLayout, QWidget

from history.empty_history import EmptyHistory
from history.grouping import count_label, group_by_month
from history.header import SheetHeader
from history.layout import drop_children
from history.location_bar import LocationBar
from history.month_heading import MonthHeading
from history.palette import colors
from history.paper import Paper
from history.row import HistoryRow


class HistorySheet(QWidget):
    chosen = pyqtSignal(object)
    delete_requested = pyqtSignal(object)
    export_requested = pyqtSignal(object)
    close_requested = pyqtSignal()
    change_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._colors = colors(False)
        self._entries, self._selected_id, self._signature = [], None, None
        self.header = SheetHeader()
        self.header.close_requested.connect(self.close_requested)
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
        self.scroll.setStyleSheet(self._scroll_css(palette))
        line = palette["line"]
        self._edge.setStyleSheet("background: rgba(%d, %d, %d, %d);" % (line.red(), line.green(), line.blue(), line.alpha()))
        self._refill()
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._paper)

    def set_entries(self, entries, selected_id):
        self._entries, self._selected_id = list(entries), selected_id
        self._refill()

    def set_place(self, shown, full):
        self.place.set_place(shown, full)

    def mousePressEvent(self, event):
        event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._edge.setGeometry(0, 0, 1, self.height())
        self._edge.raise_()

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
            self.list_layout.addWidget(EmptyHistory(self._colors["muted"], self._colors["sheet"]))
            self.list_layout.addStretch(1)
        else:
            self._add_rows()
        QTimer.singleShot(0, lambda value=place: self._restore(value))

    def _add_rows(self):
        first = True
        for label, rows in group_by_month(self._entries):
            self.list_layout.addWidget(MonthHeading(label, self._colors["muted"], self._colors["sheet"], first))
            first = False
            for entry in rows: self._add_row(entry)
        self.list_layout.addStretch(1)

    def _add_row(self, entry):
        row = HistoryRow(entry, entry.id == self._selected_id, self._colors)
        row.chosen.connect(self.chosen)
        row.delete_requested.connect(self.delete_requested)
        row.export_requested.connect(self.export_requested)
        self.list_layout.addWidget(row)

    def _restore(self, value):
        self.scroll.verticalScrollBar().setValue(value)

    def _scroll_css(self, palette):
        sheet = palette["sheet"].name()
        handle = "rgba(212,180,150,0.45)" if palette["sheet"].lightness() < 40 else "rgba(140,104,66,0.38)"
        hover = "rgba(212,180,150,0.75)" if palette["sheet"].lightness() < 40 else "rgba(140,104,66,0.62)"
        return (
            f"QScrollArea {{ border: none; background: {sheet}; }}"
            f"QScrollBar:vertical {{ background: transparent; width: 8px; margin: 8px 2px 8px 0; }}"
            f"QScrollBar::handle:vertical {{ background: {handle}; border-radius: 4px; min-height: 36px; }}"
            f"QScrollBar::handle:vertical:hover {{ background: {hover}; }}"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
            "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }"
        )
