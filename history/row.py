"""One note in the list, with delete and export when the pointer is over it."""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QFontMetrics, QPainter
from PyQt5.QtCore import QRect, QRectF
from PyQt5.QtWidgets import QWidget

from history.face import face
from history.icons import paint_icon


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
