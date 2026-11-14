"""One deleted note, with restore and a permanent delete when the pointer is over it."""

from PyQt5.QtCore import Qt, QRect, QRectF, pyqtSignal
from PyQt5.QtGui import QFont, QFontMetrics, QPainter
from PyQt5.QtWidgets import QWidget

from history.face import face
from history.icons import paint_icon


class TrashRow(QWidget):
    restore_requested = pyqtSignal(object)
    purge_requested = pyqtSignal(object)

    def __init__(self, item, palette):
        super().__init__()
        self._item, self._colors = item, palette
        self._hover, self._hot = False, ""
        self.setFixedHeight(76)
        self.setAutoFillBackground(False)
        self.setMouseTracking(True)
        self.setAccessibleName(self._title())

    def _title(self):
        text = (self._item.preview_text or "").strip()
        return text if text else "Untitled"

    def _slots(self):
        side, y = 34, (self.height() - 34) // 2
        purge = QRect(self.width() - 16 - side, y, side, side)
        restore = QRect(purge.x() - 2 - side, y, side, side)
        return restore, purge

    def _hit(self, pos):
        restore, purge = self._slots()
        if purge.contains(pos): return "purge"
        if restore.contains(pos): return "restore"
        return ""

    def mouseMoveEvent(self, event):
        hot = self._hit(event.pos()) if self._hover else ""
        if hot != self._hot:
            self._hot = hot
            self.setToolTip({"restore": "Restore", "purge": "Delete forever"}.get(hot, ""))
            self.setCursor(Qt.PointingHandCursor if hot else Qt.ArrowCursor)
            self.update()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton: return
        hot = self._hit(event.pos())
        if hot == "restore": self.restore_requested.emit(self._item)
        elif hot == "purge": self.purge_requested.emit(self._item)
        else: event.accept()

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover, self._hot = False, ""
        self.setToolTip("")
        self.setCursor(Qt.ArrowCursor)
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.fillRect(self.rect(), self._colors["sheet"])
        self._paint_wash(painter)
        self._paint_words(painter)
        if self._hover: self._paint_actions(painter)

    def _paint_wash(self, painter):
        if not self._hover: return
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._colors["hover"])
        painter.drawRoundedRect(QRectF(10, 3, self.width() - 20, self.height() - 6), 12, 12)

    def _paint_words(self, painter):
        restore, _purge = self._slots()
        text_x, text_w = 28, max(40, restore.x() - 36)
        painter.setPen(self._colors["accent"])
        painter.setFont(face(12, QFont.Normal, 0.2))
        painter.drawText(QRectF(text_x, 15, text_w, 16), Qt.AlignLeft | Qt.AlignVCenter, self._item.when)
        untitled = not (self._item.preview_text or "").strip()
        painter.setPen(self._colors["muted"] if untitled else self._colors["body"])
        title_font = face(15, QFont.Normal, -0.12)
        painter.setFont(title_font)
        title = QFontMetrics(title_font).elidedText(self._title(), Qt.ElideRight, text_w)
        painter.drawText(QRectF(text_x, 36, text_w, 24), Qt.AlignLeft | Qt.AlignVCenter, title)

    def _paint_actions(self, painter):
        restore, purge = self._slots()
        self._paint_action(painter, restore, "restore", self._hot == "restore", self._colors["accent"] if self._hot == "restore" else self._colors["icon"])
        self._paint_action(painter, purge, "trash", self._hot == "purge", self._colors["danger"] if self._hot == "purge" else self._colors["icon"])

    def _paint_action(self, painter, rect, kind, hot, color):
        if hot:
            painter.setPen(Qt.NoPen)
            painter.setBrush(self._colors["icon_bg"])
            painter.drawRoundedRect(QRectF(rect).adjusted(2, 2, -2, -2), 9, 9)
        paint_icon(painter, kind, QRectF(rect), color)
