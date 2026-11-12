"""History as a sheet over the writing.

The sheet is not part of the page layout, so opening it does not shove the
writing aside. One progress value, from 0 (parked past the right edge) to 1
(docked), drives the slide and the shade together. Closing starts from the
frame you are on, which is what makes a second click feel like a reversal
instead of a restart.
"""

import os
from datetime import date

from PyQt5.QtCore import QEasingCurve, QPoint, QPointF, QPropertyAnimation, QRect, QRectF, Qt, QTimer, pyqtProperty, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QFontDatabase, QFontMetrics, QLinearGradient, QPainter, QPen
from PyQt5.QtWidgets import QAbstractButton, QFrame, QScrollArea, QVBoxLayout, QWidget

_FACES = ("Lato-Light.ttf", "Lato-Regular.ttf", "Lato-Bold.ttf")
_lato_ready = False
_OPEN_MS, _CLOSE_MS = 340, 260


def ensure_lato():
    """Load the real Lato weights so titles are not a faked bold."""
    global _lato_ready
    if _lato_ready: return
    _lato_ready = True
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
    library = QFontDatabase()
    for name in _FACES:
        path = os.path.join(folder, name)
        if os.path.isfile(path): library.addApplicationFont(path)


def face(px, weight, spacing):
    font = QFont("Lato")
    font.setPixelSize(px)
    font.setWeight(weight)
    font.setLetterSpacing(QFont.AbsoluteSpacing, spacing)
    return font


def colors(dark):
    """Warm paper in the light, warm charcoal in the dark. The clay accent matches the rest of the app."""
    if dark:
        return {
            "sheet": QColor("#161412"), "scrim": QColor(0, 0, 0), "scrim_alpha": 64,
            "title": QColor("#F7F4EF"), "muted": QColor("#A39B92"), "body": QColor("#E8E2D8"),
            "line": QColor(255, 255, 255, 28), "hover": QColor(255, 248, 240, 16),
            "selected": QColor(196, 164, 132, 40), "accent": QColor("#D4B496"),
            "icon": QColor("#B7AFA6"), "icon_hot": QColor("#F3E6D6"), "danger": QColor("#E7B1A6"),
            "icon_bg": QColor(255, 255, 255, 20), "shadow": 96,
        }
    return {
        "sheet": QColor("#FBF9F6"), "scrim": QColor(42, 32, 22), "scrim_alpha": 22,
        "title": QColor("#1C1917"), "muted": QColor("#8A8178"), "body": QColor("#2A2622"),
        "line": QColor(48, 38, 28, 32), "hover": QColor(48, 36, 24, 14),
        "selected": QColor(140, 104, 66, 28), "accent": QColor("#8C6842"),
        "icon": QColor("#8A8178"), "icon_hot": QColor("#3E342C"), "danger": QColor("#9C463C"),
        "icon_bg": QColor(48, 36, 24, 16), "shadow": 48,
    }


def ease_out():
    """Fast to leave, gentle to arrive. The same curve closes, just sooner."""
    curve = QEasingCurve(QEasingCurve.BezierSpline)
    curve.addCubicBezierSegment(QPointF(0.22, 1.0), QPointF(0.36, 1.0), QPointF(1, 1))
    return curve


def count_label(count):
    if count == 0: return "No notes yet"
    if count == 1: return "1 note"
    return f"{count} notes"


def month_name(created, today):
    if created.year == today.year: return created.strftime("%B")
    return created.strftime("%B %Y")


def group_by_month(entries, today=None):
    """Newest first, already sorted. A heading appears only when the month changes."""
    today = today or date.today()
    groups = []
    for entry in entries:
        label = month_name(entry.created, today)
        if not groups or groups[-1][0] != label: groups.append((label, [entry]))
        else: groups[-1][1].append(entry)
    return groups


class Paper(QWidget):
    """Fills itself. A palette would be wiped the next time the app theme reloads."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._paper = QColor("#FBF9F6")
        self.setAutoFillBackground(False)

    def set_paper(self, color):
        self._paper = QColor(color)
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._paper)


def drop_children(layout):
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.hide()
            widget.deleteLater()


def paint_icon(painter, kind, rect, color):
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(color, 1.6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(Qt.NoBrush)
    center = rect.center()
    if kind == "close": _paint_close(painter, center)
    elif kind == "export": _paint_export(painter, center)
    else: _paint_trash(painter, center)
    painter.restore()


def _paint_close(painter, center):
    span = 5.2
    painter.drawLine(QPointF(center.x() - span, center.y() - span), QPointF(center.x() + span, center.y() + span))
    painter.drawLine(QPointF(center.x() + span, center.y() - span), QPointF(center.x() - span, center.y() + span))


def _paint_export(painter, center):
    painter.drawLine(QPointF(center.x(), center.y() - 6), QPointF(center.x(), center.y() + 1))
    painter.drawLine(QPointF(center.x(), center.y() - 6), QPointF(center.x() - 3.4, center.y() - 2.4))
    painter.drawLine(QPointF(center.x(), center.y() - 6), QPointF(center.x() + 3.4, center.y() - 2.4))
    painter.drawLine(QPointF(center.x() - 5.5, center.y() + 1.2), QPointF(center.x() - 5.5, center.y() + 6))
    painter.drawLine(QPointF(center.x() - 5.5, center.y() + 6), QPointF(center.x() + 5.5, center.y() + 6))
    painter.drawLine(QPointF(center.x() + 5.5, center.y() + 6), QPointF(center.x() + 5.5, center.y() + 1.2))


def _paint_trash(painter, center):
    painter.drawLine(QPointF(center.x() - 1.5, center.y() - 6.2), QPointF(center.x() + 1.5, center.y() - 6.2))
    painter.drawLine(QPointF(center.x() - 1.5, center.y() - 6.2), QPointF(center.x() - 1.5, center.y() - 4.4))
    painter.drawLine(QPointF(center.x() + 1.5, center.y() - 6.2), QPointF(center.x() + 1.5, center.y() - 4.4))
    painter.drawLine(QPointF(center.x() - 5.2, center.y() - 4.4), QPointF(center.x() + 5.2, center.y() - 4.4))
    painter.drawLine(QPointF(center.x() - 4.2, center.y() - 3.2), QPointF(center.x() - 3.2, center.y() + 6))
    painter.drawLine(QPointF(center.x() + 4.2, center.y() - 3.2), QPointF(center.x() + 3.2, center.y() + 6))
    painter.drawLine(QPointF(center.x() - 3.2, center.y() + 6), QPointF(center.x() + 3.2, center.y() + 6))
    painter.drawLine(QPointF(center.x() - 1.1, center.y() - 1.6), QPointF(center.x() - 1.1, center.y() + 3.6))
    painter.drawLine(QPointF(center.x() + 1.1, center.y() - 1.6), QPointF(center.x() + 1.1, center.y() + 3.6))


class CloseButton(QAbstractButton):
    """The X in the top corner. The hit target is larger than the mark."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ink, self._ink_hot = QColor("#8A8178"), QColor("#1C1917")
        self._fill, self._accent = QColor(48, 36, 24, 16), QColor("#8C6842")
        self.setFixedSize(36, 36)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAccessibleName("Close history")
        self.setToolTip("Close")
        self.setStyleSheet("QAbstractButton { background: transparent; border: none; }")

    def apply_colors(self, palette):
        self._ink, self._ink_hot = palette["muted"], palette["title"]
        self._fill, self._accent = palette["hover"], palette["accent"]
        self.update()

    def enterEvent(self, event):
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        hot = self.underMouse() or self.isDown()
        if hot:
            painter.setPen(Qt.NoPen)
            painter.setBrush(self._fill)
            painter.drawRoundedRect(QRectF(1, 1, self.width() - 2, self.height() - 2), 11, 11)
        paint_icon(painter, "close", QRectF(self.rect()), self._ink_hot if hot else self._ink)
        if self.hasFocus():
            painter.setPen(QPen(self._accent, 1.2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(QRectF(1.5, 1.5, self.width() - 3, self.height() - 3), 11, 11)


class MonthHeading(QWidget):
    def __init__(self, text, color, paper, first):
        super().__init__()
        self._text, self._color, self._paper = text, color, paper
        self.setFixedHeight(30 if first else 44)
        self.setAutoFillBackground(False)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._paper)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setPen(self._color)
        painter.setFont(face(12, QFont.Bold, 0.35))
        painter.drawText(QRectF(26, 0, self.width() - 52, self.height() - 4), Qt.AlignLeft | Qt.AlignBottom, self._text)


class EmptyHistory(QWidget):
    def __init__(self, color, paper):
        super().__init__()
        self._color, self._paper = color, paper
        self.setMinimumHeight(168)
        self.setAutoFillBackground(False)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._paper)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setPen(self._color)
        painter.setFont(face(14, QFont.Light, 0.1))
        painter.drawText(self.rect().adjusted(32, 28, -32, -28), Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, "When you start writing, your notes will gather here.")


class HistoryRow(QWidget):
    chosen = pyqtSignal(object)
    delete_requested = pyqtSignal(object)
    export_requested = pyqtSignal(object)

    def __init__(self, entry, selected, palette):
        super().__init__()
        self._entry, self._selected, self._colors = entry, selected, palette
        self._hover, self._hot = False, ""
        self.setFixedHeight(76)
        self.setAutoFillBackground(False)
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setAccessibleName(self._title())

    def _title(self):
        text = (self._entry.preview_text or "").strip()
        return text if text else "Untitled"

    def _slots(self):
        side, y = 34, (self.height() - 34) // 2
        delete = QRect(self.width() - 16 - side, y, side, side)
        export = QRect(delete.x() - 2 - side, y, side, side)
        return export, delete

    def _hit(self, pos):
        export, delete = self._slots()
        if delete.contains(pos): return "delete"
        if export.contains(pos): return "export"
        return ""

    def mouseMoveEvent(self, event):
        hot = self._hit(event.pos())
        if hot != self._hot:
            self._hot = hot
            self.setToolTip({"delete": "Delete", "export": "Save as PDF"}.get(hot, ""))
            self.update()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton: return
        hot = self._hit(event.pos())
        if hot == "delete": self.delete_requested.emit(self._entry)
        elif hot == "export": self.export_requested.emit(self._entry)
        else: self.chosen.emit(self._entry)

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover, self._hot = False, ""
        self.setToolTip("")
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.fillRect(self.rect(), self._colors["sheet"])
        self._paint_wash(painter)
        self._paint_words(painter)
        if self._hover or self._selected: self._paint_actions(painter)

    def _paint_wash(self, painter):
        if not (self._selected or self._hover): return
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._colors["selected"] if self._selected else self._colors["hover"])
        painter.drawRoundedRect(QRectF(10, 3, self.width() - 20, self.height() - 6), 12, 12)
        if not self._selected: return
        painter.setBrush(self._colors["accent"])
        painter.drawRoundedRect(QRectF(16, (self.height() - 18) / 2, 3, 18), 1.5, 1.5)

    def _paint_words(self, painter):
        export, _delete = self._slots()
        text_x, text_w = 28, max(40, export.x() - 36)
        painter.setPen(self._colors["accent"])
        painter.setFont(face(12, QFont.Normal, 0.2))
        painter.drawText(QRectF(text_x, 15, text_w, 16), Qt.AlignLeft | Qt.AlignVCenter, self._entry.date)
        untitled = not (self._entry.preview_text or "").strip()
        painter.setPen(self._colors["muted"] if untitled else self._colors["body"])
        title_font = face(15, QFont.Normal, -0.12)
        painter.setFont(title_font)
        title = QFontMetrics(title_font).elidedText(self._title(), Qt.ElideRight, text_w)
        painter.drawText(QRectF(text_x, 36, text_w, 24), Qt.AlignLeft | Qt.AlignVCenter, title)

    def _paint_actions(self, painter):
        export, delete = self._slots()
        self._paint_action(painter, export, "export", self._hot == "export", self._colors["icon_hot"] if self._hot == "export" else self._colors["icon"])
        self._paint_action(painter, delete, "trash", self._hot == "delete", self._colors["danger"] if self._hot == "delete" else self._colors["icon"])

    def _paint_action(self, painter, rect, kind, hot, color):
        if hot:
            painter.setPen(Qt.NoPen)
            painter.setBrush(self._colors["icon_bg"])
            painter.drawRoundedRect(QRectF(rect).adjusted(2, 2, -2, -2), 9, 9)
        paint_icon(painter, kind, QRectF(rect), color)


class SheetHeader(QWidget):
    close_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._colors = colors(False)
        self._count = ""
        self.setFixedHeight(104)
        self.close_btn = CloseButton(self)
        self.close_btn.clicked.connect(self.close_requested)

    def apply_colors(self, palette):
        self._colors = palette
        self.close_btn.apply_colors(palette)
        self.update()

    def set_count(self, text):
        self._count = text
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.close_btn.move(self.width() - 18 - self.close_btn.width(), 18)
        self.close_btn.raise_()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._colors["sheet"])
        painter.setRenderHint(QPainter.TextAntialiasing)
        width = self.width() - 78
        painter.setPen(self._colors["title"])
        painter.setFont(face(22, QFont.Bold, -0.4))
        painter.drawText(QRectF(26, 20, width, 30), Qt.AlignLeft | Qt.AlignVCenter, "History")
        painter.setPen(self._colors["muted"])
        painter.setFont(face(13, QFont.Light, 0.15))
        painter.drawText(QRectF(26, 52, width, 20), Qt.AlignLeft | Qt.AlignVCenter, self._count)
        painter.setPen(QPen(self._colors["line"], 1))
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)


class HistorySheet(QWidget):
    chosen = pyqtSignal(object)
    delete_requested = pyqtSignal(object)
    export_requested = pyqtSignal(object)
    close_requested = pyqtSignal()

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
        self.list_layout.setContentsMargins(0, 6, 0, 28)
        self.list_layout.setSpacing(0)
        self.scroll.setWidget(self.list_host)
        self._paper = QColor("#FBF9F6")
        self.setAutoFillBackground(False)
        self._edge = QWidget(self)
        self._edge.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.header)
        layout.addWidget(self.scroll, 1)
        self.apply_colors(self._colors)

    def apply_colors(self, palette):
        self._colors = palette
        self._paper = QColor(palette["sheet"])
        self._signature = None
        self.header.apply_colors(palette)
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


class HistoryDrawer(QWidget):
    """A shade over the writing, and the sheet sliding in from the right."""

    chosen = pyqtSignal(object)
    delete_requested = pyqtSignal(object)
    export_requested = pyqtSignal(object)
    dismissed = pyqtSignal()
    opened = pyqtSignal()

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
        self._anim = QPropertyAnimation(self, b"progress", self)
        self._anim.finished.connect(self._on_finished)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.hide()

    def fit_over(self, bar):
        """Dock to the top and right of the window, and stop at the bar along the bottom."""
        self._host = bar
        parent = self.parentWidget()
        if bar is None or parent is None: return
        bottom = bar.mapTo(parent, QPoint(0, 0)).y()
        self.setGeometry(0, 0, parent.width(), max(0, bottom))
        if self.isVisible(): self.raise_()

    def set_dark(self, dark):
        self._colors = colors(bool(dark))
        self.sheet.apply_colors(self._colors)
        self.update()

    def set_entries(self, entries, selected_id):
        self.sheet.set_entries(entries, selected_id)

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


def _clamped(value):
    return 0.0 if value < 0 else 1.0 if value > 1 else value
