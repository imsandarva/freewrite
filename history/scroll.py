"""The thin scrollbar shared by History and Trash."""


def scroll_css(palette):
    sheet = palette["sheet"].name()
    dark = palette["sheet"].lightness() < 40
    handle = "rgba(212,180,150,0.45)" if dark else "rgba(140,104,66,0.38)"
    hover = "rgba(212,180,150,0.75)" if dark else "rgba(140,104,66,0.62)"
    return (
        "QScrollArea { border: none; background: %s; }"
        "QScrollBar:vertical { background: transparent; width: 8px; margin: 8px 2px 8px 0; }"
        "QScrollBar::handle:vertical { background: %s; border-radius: 4px; min-height: 36px; }"
        "QScrollBar::handle:vertical:hover { background: %s; }"
        "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
        "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }"
    ) % (sheet, handle, hover)
