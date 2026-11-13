"""Light and dark, reloaded from the stylesheet that ships with the app."""

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication

from app.paths import resource


class ThemeControl:
    def toggle_theme(self):
        self.color_scheme = "dark" if self.color_scheme == "light" else "light"
        QSettings("humansongs", "freewrite").setValue("colorScheme", self.color_scheme)
        is_dark = self.color_scheme == "dark"
        if hasattr(self, 'parent') and self.parent() is not None:
            self.parent().setProperty("dark", is_dark)
            self.parent().style().unpolish(self.parent())
            self.parent().style().polish(self.parent())
        for widget in (
            self.text_edit, self.bottom_nav, self.size_cycle, self.type_cycle, self.bar_rule,
            self.backspace_switch, self.sound_switch, self.clock, self.chat_btn, self.fullscreen_btn,
            self.new_entry_btn, self.theme_toggle_btn, self.history_btn,
        ):
            widget.setProperty("dark", is_dark)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        # The theme file reloads after this, and that wipes a palette set too early.
        self.update_styles()
        self._apply_writing_font()
        self.history.set_dark(is_dark)
        self._paint_history_button()
        self.update_entries_display()


# Replace the update_styles method
    def update_styles(self):
        try:
            with open(resource("assets", "style.qss"), "r", encoding="utf-8") as f:
                style_content = f.read()
                QApplication.instance().setStyleSheet(style_content)
        except Exception as e:
            print(f"Error loading styles: {e}")
