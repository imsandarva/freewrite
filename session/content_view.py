"""The writing session: the page, the bar, and the sheet over it."""

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QTextOption
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from editing.backspace_pref import saved_backspace_on
from editing.writing_edit import WritingEdit
from notes.library import NoteLibrary
from place.directory import prepare_directory
from session.bar import BarControls
from session.chat import ChatActions
from session.entries import EntryStore
from session.fullscreen import FullscreenControl
from session.history_chrome import HistoryChrome
from session.pdf_export import PdfExport
from session.place_flow import PlaceFlow
from session.prompts import AI_CHAT_PROMPT, CLAUDE_PROMPT, FONT_SIZES, PLACEHOLDER_OPTIONS
from session.text_direction import TextDirection
from session.theme import ThemeControl
from session.timer_control import TimerControl
from session.trash_flow import TrashFlow
from papers.catalog import saved_paper
from sound.key_clicks import KeyClicks
from sound.settings import saved_sound_on


class ContentView(BarControls, HistoryChrome, TimerControl, ThemeControl, FullscreenControl, TextDirection, EntryStore, ChatActions, PdfExport, PlaceFlow, TrashFlow, QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.entries = []
        self.text = ""
        self.is_fullscreen = False
        self.selected_font = "Lato"
        self.time_remaining = 900
        self.timer_is_running = False
        self.is_hovering_timer = False
        self.is_hovering_fullscreen = False
        self.hovered_font = None
        self.is_hovering_size = False
        self.font_size = 18
        self.bottom_nav_opacity = 1.0
        self.is_hovering_bottom_nav = False
        self.selected_entry_id = None
        self.hovered_entry_id = None
        self.is_hovering_chat = False
        self.showing_chat_menu = False
        self.is_hovering_new_entry = False
        self.is_hovering_clock = False
        self._history_open = False
        self.hovered_trash_id = None
        self.hovered_export_id = None
        self.paper = saved_paper()
        self.color_scheme = self.paper.key
        self.backspace_enabled = saved_backspace_on()
        self.sound_enabled = saved_sound_on()
        self.key_sound = KeyClicks(self.sound_enabled)
        self.did_copy_prompt = False
        self.placeholder_text = ""
        self.font_sizes = list(FONT_SIZES)
        self.placeholder_options = list(PLACEHOLDER_OPTIONS)
        self.documents_directory = prepare_directory()
        self.library = NoteLibrary(self.documents_directory)
        self.ai_chat_prompt = AI_CHAT_PROMPT
        self.claude_prompt = CLAUDE_PROMPT
        self.init_ui()
        self.load_existing_entries()

    def init_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_widget = QWidget()
        self.main_layout.addWidget(self.main_widget)
        self.main_v_layout = QVBoxLayout(self.main_widget)
        self.main_v_layout.setContentsMargins(0, 0, 0, 0)
        # Text Editor with proper alignment configuration
        self.text_edit = WritingEdit(self.backspace_enabled, self.key_sound)
        self.text_edit.setPlainText(self.text)
        # Critical fixes for text direction
        document = self.text_edit.document()
        option = QTextOption()
        option.setAlignment(Qt.AlignLeft)
        option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        option.setTextDirection(Qt.LeftToRight)
        document.setDefaultTextOption(option)
        self.text_edit.textChanged.connect(self.on_text_changed)
        self.fix_text_direction()
        self.main_v_layout.addWidget(self.text_edit)
        self.main_v_layout.setSpacing(0)
        self._compose_bar(self.paper)
        self.main_v_layout.addWidget(self.bottom_nav)
        # History floats over the page, so the writing does not reflow when it opens.
        self._wire_history(self.paper)
        self._wire_trash()
        self._wire_fullscreen()
        self.update_styles()

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)

        # Save Timer
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.save_current_entry)
        self.save_timer.start(1000)
        self._apply_writing_font()
