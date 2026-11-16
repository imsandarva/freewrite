"""The bottom bar: face, the pills, the clock, and the session buttons."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QWidget

from clock.quiet_clock import QuietClock
from editing.backspace_pref import remember_backspace
from papers.catalog import paper_for
from papers.cycle import PaperCycle
from session.fullscreen import ENTER_LABEL
from sound.settings import remember_sound
from switch.quiet_switch import QuietSwitch
from typeface.apply_face import apply_face
from typeface.bar_rule import BarRule
from typeface.settings import remember_face
from typeface.text_button import text_button
from typeface.type_cycle import TypeCycle


class BarControls:
    def _compose_bar(self, paper):
        """Type on the left, then the session tools. The paper name sits with the actions."""
        self.bottom_nav = QWidget()
        self.bottom_nav.setObjectName("bottomNav")
        self.bottom_nav_layout = QHBoxLayout(self.bottom_nav)
        self.bottom_nav_layout.setContentsMargins(18, 2, 12, 6)
        self.bottom_nav_layout.setSpacing(0)
        self.type_cycle = TypeCycle(paper, self.selected_font)
        self.type_cycle.chosen.connect(self.use_typeface)
        self.selected_font = self.type_cycle.family()
        self.bar_rule = BarRule(paper)
        self.backspace_switch = QuietSwitch("Backspace", self.backspace_enabled, paper)
        self.backspace_switch.toggled.connect(self.on_backspace_toggled)
        self.sound_switch = QuietSwitch("Sound", self.sound_enabled, paper)
        self.sound_switch.toggled.connect(self.on_sound_toggled)
        self.clock = QuietClock(paper)
        self.clock.clicked.connect(self.toggle_timer)
        self.chat_btn = text_button("Chat")
        self.chat_btn.clicked.connect(self.show_chat_menu)
        self.fullscreen_btn = text_button(ENTER_LABEL)
        self.fullscreen_btn.clicked.connect(self.enter_fullscreen)
        self.new_entry_btn = text_button("New Entry")
        self.new_entry_btn.clicked.connect(self.create_new_entry)
        self.paper_cycle = PaperCycle(paper)
        self.paper_cycle.chosen.connect(self.use_paper)
        self.history_btn = text_button("History")
        self.history_btn.clicked.connect(self.toggle_history)
        for widget, gap in (
            (self.type_cycle, 16), (self.bar_rule, 16),
            (self.backspace_switch, 14), (self.sound_switch, 12), (self.clock, 0),
        ):
            self._add_bar(widget, gap)
        self.bottom_nav_layout.addStretch(1)
        for button in (self.chat_btn, self.fullscreen_btn, self.new_entry_btn, self.paper_cycle, self.history_btn):
            self._add_bar(button, 0)

    def _add_bar(self, widget, gap):
        self.bottom_nav_layout.addWidget(widget, 0, Qt.AlignVCenter)
        if gap: self.bottom_nav_layout.addSpacing(gap)
    def on_backspace_toggled(self, on):
        self.backspace_enabled = on
        remember_backspace(on)
        self.text_edit.set_backspace_allowed(on)
        if self.backspace_switch.was_pointer(): self.text_edit.setFocus()

    def on_sound_toggled(self, on):
        self.sound_enabled = on
        remember_sound(on)
        self.key_sound.set_enabled(on)
        if self.sound_switch.was_pointer(): self.text_edit.setFocus()

    def use_typeface(self, family):
        self.selected_font = family
        remember_face(self.type_cycle.label())
        self._apply_writing_font()
        self._return_to_page(self.type_cycle)

    def use_paper(self, key):
        self._apply_paper(paper_for(key))
        self._return_to_page(self.paper_cycle)

    def _apply_writing_font(self):
        apply_face(self.text_edit, self.selected_font, self.font_size)

    def _return_to_page(self, control):
        if control.was_pointer(): self.text_edit.setFocus()
