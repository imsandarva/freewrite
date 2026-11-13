"""The colors the stylesheet cannot know until a paper is chosen."""

from papers.catalog import rgba


def chrome_qss(paper):
    """Rules appended after the shared stylesheet, so they win on equal specificity."""
    page, ink, muted, hover = paper.page, paper.ink, paper.muted, paper.hover
    hair = rgba("#F4F0EA" if paper.dark else ink, 0.09)
    select = rgba(paper.accent, 0.30)
    thumb = rgba(paper.accent, 0.42)
    menu = rgba(paper.accent, 0.18)
    return (
        "QMainWindow, QTextEdit, QWidget#bottomNav { background-color: %s; }\n"
        "QTextEdit { color: %s; selection-background-color: %s; selection-color: %s; }\n"
        "QPushButton { color: %s; }\n"
        "QPushButton:hover { color: %s; }\n"
        "QWidget#bottomNav { background-color: %s; border-top: 1px solid %s; }\n"
        "QLabel { color: %s; }\n"
        "QLabel:hover { color: %s; }\n"
        "QMenu { background-color: %s; color: %s; border: 1px solid %s; padding: 6px; }\n"
        "QMenu::item { padding: 6px 18px; background: transparent; }\n"
        "QMenu::item:selected { background: %s; color: %s; }\n"
        "QScrollBar:vertical { background: transparent; width: 10px; margin: 0; }\n"
        "QScrollBar::handle:vertical { background: %s; min-height: 28px; border-radius: 5px; }\n"
        "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }\n"
        "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }\n"
    ) % (page, ink, select, ink, muted, hover, page, hair, muted, hover, page, ink, hair, menu, ink, thumb)
