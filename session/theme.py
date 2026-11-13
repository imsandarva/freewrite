"""The writing paper, reloaded from the stylesheet that ships with the app."""

from PyQt5.QtWidgets import QApplication

from app.paths import resource
from papers.catalog import remember_paper
from papers.style import chrome_qss


class ThemeControl:
    def _apply_paper(self, paper):
        self.paper = paper
        self.color_scheme = paper.key
        remember_paper(paper)
        self.update_styles()
        self._apply_writing_font()
        for widget in self._paper_widgets(): widget.apply_paper(paper)
        self.history.apply_paper(paper)
        hint = getattr(self, "_exit_hint", None)
        if hint is not None: hint.apply_paper(paper)
        self._paint_history_button()
        self.update_entries_display()

    def _paper_widgets(self):
        return (
            self.size_cycle, self.type_cycle, self.paper_cycle, self.bar_rule,
            self.backspace_switch, self.sound_switch, self.clock,
        )

    def update_styles(self):
        try:
            with open(resource("assets", "style.qss"), encoding="utf-8") as handle:
                QApplication.instance().setStyleSheet(handle.read() + "\n" + chrome_qss(self.paper))
        except Exception as error:
            print("Error loading styles: %s" % error)
