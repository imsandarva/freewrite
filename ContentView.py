import os
import random  # Added for random placeholder selection
from datetime import date
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QMenu, QFileDialog, QShortcut
)
from PyQt5.QtGui import QFont, QTextCursor, QTextDocument, QTextOption, QKeySequence
from PyQt5.QtCore import Qt, QTimer, QSettings, QUrl
from PyQt5.Qt import QDesktopServices
from PyQt5.QtPrintSupport import QPrinter
from notes import HumanEntry, NoteLibrary, history_preview
from editing import WritingEdit, remember_backspace, saved_backspace_on, without_top_gap
from history import HistoryDrawer
from place import PlaceError, friendly_path, has_notes, note_count, prepare_directory, relocate, remember_directory, same_place, settle
from choice import ask_move, tell
from sound import KeyClicks, remember_sound, saved_sound_on
from switch import QuietSwitch
from clock import QuietClock
from typeface import BarRule, SizeCycle, TypeCycle, apply_face, text_button
from paths import resource

class ContentView(QWidget):
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
        self.color_scheme = QSettings("humansongs", "freewrite").value("colorScheme", "light")
        self.backspace_enabled = saved_backspace_on()
        self.sound_enabled = saved_sound_on()
        self.key_sound = KeyClicks(self.sound_enabled)
        self.is_hovering_theme_toggle = False
        self.did_copy_prompt = False
        self.placeholder_text = ""
        self.font_sizes = [16, 18, 20, 22, 24, 26]
        self.placeholder_options = [
            "Begin writing", "Pick a thought and go", "Start typing",
            "What's on your mind", "Just start", "Type your first thought",
            "Start with one sentence", "Just say it"
        ]
        self.documents_directory = prepare_directory()
        self.library = NoteLibrary(self.documents_directory)
        self.ai_chat_prompt = """
below is my journal entry. wyt? talk through it with me like a friend. don't therpaize me and give me a whole breakdown, don't repeat my thoughts with headings. really take all of this, and tell me back stuff truly as if you're an old homie.

Keep it casual, dont say yo, help me make new connections i don't see, comfort, validate, challenge, all of it. dont be afraid to say a lot. format with markdown headings if needed.

do not just go through every single thing i say, and say it back to me. you need to proccess everythikng is say, make connections i don't see it, and deliver it all back to me as a story that makes me feel what you think i wanna feel. thats what the best therapists do.

ideally, you're style/tone should sound like the user themselves. it's as if the user is hearing their own tone but it should still feel different, because you have different things to say and don't just repeat back they say.

else, start by saying, "hey, thanks for showing me this. my thoughts:"

my entry:
"""
        self.claude_prompt = """
Take a look at my journal entry below. I'd like you to analyze it and respond with deep insight that feels personal, not clinical.
Imagine you're not just a friend, but a mentor who truly gets both my tech background and my psychological patterns. I want you to uncover the deeper meaning and emotional undercurrents behind my scattered thoughts.
Keep it casual, dont say yo, help me make new connections i don't see, comfort, validate, challenge, all of it. dont be afraid to say a lot. format with markdown headings if needed.
Use vivid metaphors and powerful imagery to help me see what I'm really building. Organize your thoughts with meaningful headings that create a narrative journey through my ideas.
Don't just validate my thoughts - reframe them in a way that shows me what I'm really seeking beneath the surface. Go beyond the product concepts to the emotional core of what I'm trying to solve.
Be willing to be profound and philosophical without sounding like you're giving therapy. I want someone who can see the patterns I can't see myself and articulate them in a way that feels like an epiphany.
Start with 'hey, thanks for showing me this. my thoughts:' and then use markdown headings to structure your response.

Here's my journal entry:
"""
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
        # Set property for theme
        is_dark = self.color_scheme == "dark"
        if hasattr(self, 'parent') and self.parent() is not None:
            self.parent().setProperty("dark", is_dark)
        self.text_edit.setProperty("dark", is_dark)
        self.text_edit.textChanged.connect(self.on_text_changed)
        self.fix_text_direction()
        self.main_v_layout.addWidget(self.text_edit)
        self.main_v_layout.setSpacing(0)
        self._compose_bar(is_dark)
        self.main_v_layout.addWidget(self.bottom_nav)
        # History floats over the page, so the writing does not reflow when it opens.
        self._wire_history(is_dark)

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)

        # Save Timer
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.save_current_entry)
        self.save_timer.start(1000)
        self._apply_writing_font()

    def _compose_bar(self, is_dark):
        """Type on the left, then the session tools. Everything else stays on the right."""
        self.bottom_nav = QWidget()
        self.bottom_nav.setObjectName("bottomNav")
        self.bottom_nav.setProperty("dark", is_dark)
        self.bottom_nav_layout = QHBoxLayout(self.bottom_nav)
        self.bottom_nav_layout.setContentsMargins(18, 2, 12, 6)
        self.bottom_nav_layout.setSpacing(0)
        self.size_cycle = SizeCycle(self.font_sizes, self.font_size, is_dark)
        self.size_cycle.chosen.connect(self.use_size)
        self.type_cycle = TypeCycle(is_dark)
        self.type_cycle.chosen.connect(self.use_typeface)
        self.selected_font = self.type_cycle.family()
        self.bar_rule = BarRule(is_dark)
        self.backspace_switch = QuietSwitch("Backspace", self.backspace_enabled, is_dark)
        self.backspace_switch.toggled.connect(self.on_backspace_toggled)
        self.sound_switch = QuietSwitch("Sound", self.sound_enabled, is_dark)
        self.sound_switch.toggled.connect(self.on_sound_toggled)
        self.clock = QuietClock(is_dark)
        self.clock.clicked.connect(self.toggle_timer)
        self.chat_btn = text_button("Chat", is_dark)
        self.chat_btn.clicked.connect(self.show_chat_menu)
        self.fullscreen_btn = text_button("Fullscreen", is_dark)
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        self.new_entry_btn = text_button("New Entry", is_dark)
        self.new_entry_btn.clicked.connect(self.create_new_entry)
        self.theme_toggle_btn = text_button("Toggle Theme", is_dark)
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)
        self.history_btn = text_button("History", is_dark)
        self.history_btn.clicked.connect(self.toggle_history)
        for widget, gap in (
            (self.size_cycle, 2), (self.type_cycle, 16), (self.bar_rule, 16),
            (self.backspace_switch, 14), (self.sound_switch, 12), (self.clock, 0),
        ):
            self._add_bar(widget, gap)
        self.bottom_nav_layout.addStretch(1)
        for button in (self.chat_btn, self.fullscreen_btn, self.new_entry_btn, self.theme_toggle_btn, self.history_btn):
            self._add_bar(button, 0)

    def _add_bar(self, widget, gap):
        self.bottom_nav_layout.addWidget(widget, 0, Qt.AlignVCenter)
        if gap: self.bottom_nav_layout.addSpacing(gap)

    def _wire_history(self, is_dark):
        self.history = HistoryDrawer(self)
        self.history.set_dark(bool(is_dark))
        self.history.chosen.connect(self.select_entry)
        self.history.delete_requested.connect(self.delete_entry)
        self.history.export_requested.connect(self.export_entry_as_pdf)
        self.history.opened.connect(self._history_shown)
        self.history.dismissed.connect(self._history_hidden)
        self.history.change_requested.connect(self._choose_place)
        self._show_place()
        self._history_escape = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self._history_escape.setContext(Qt.WindowShortcut)
        self._history_escape.setEnabled(False)
        self._history_escape.activated.connect(self.history.close_sheet)

    def _history_shown(self):
        self._history_escape.setEnabled(True)
        self._set_history_open(True)

    def _history_hidden(self):
        self._history_escape.setEnabled(False)
        self._set_history_open(False)
        self.text_edit.setFocus()

    def _set_history_open(self, is_open):
        self._history_open = bool(is_open)
        self._paint_history_button()

    def _paint_history_button(self):
        if not self._history_open:
            self.history_btn.setStyleSheet("")
            return
        color = "#F4F1EC" if self.color_scheme == "dark" else "#1C1917"
        self.history_btn.setStyleSheet("QPushButton { color: %s; }" % color)

    def showEvent(self, event):
        super().showEvent(event)
        self.history.fit_over(self.bottom_nav)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.history.fit_over(self.bottom_nav)

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

    def use_size(self, pixels):
        self.font_size = int(pixels)
        self._apply_writing_font()
        self._return_to_page(self.size_cycle)

    def use_typeface(self, family):
        self.selected_font = family
        self._apply_writing_font()
        self._return_to_page(self.type_cycle)

    def _apply_writing_font(self):
        apply_face(self.text_edit, self.selected_font, self.font_size)

    def _return_to_page(self, control):
        if control.was_pointer(): self.text_edit.setFocus()

    def toggle_timer(self):
        self.timer_is_running = not self.timer_is_running
        # Stopping rests at 15:00. Starting from zero begins a fresh fifteen minutes.
        if not self.timer_is_running or self.time_remaining <= 0: self.time_remaining = 900
        self.update_timer_button()
        self._return_to_page(self.clock)

    def update_timer(self):
        if self.timer_is_running and self.time_remaining > 0:
            self.time_remaining -= 1
            self.update_timer_button()
            return
        if self.timer_is_running and self.time_remaining <= 0:
            self.timer_is_running = False
            self.bottom_nav_opacity = 1.0
            self.update_timer_button()

    def update_timer_button(self):
        self.clock.show_time(self.time_remaining, self.timer_is_running)

    def select_entry(self, entry):
        if self.selected_entry_id:
            self.save_current_entry()
        self.selected_entry_id = entry.id
        self.load_entry(entry)
        self.update_entries_display()

    def update_entries_display(self):
        self.history.set_entries(self.entries, self.selected_entry_id)

    def show_chat_menu(self):
        menu = QMenu(self.chat_btn)
        trimmed_text = self.text_edit.toPlainText().strip()
        gpt_full_text = self.ai_chat_prompt + "\n\n" + trimmed_text
        claude_full_text = self.claude_prompt + "\n\n" + trimmed_text
        gpt_url_length = len("https://chat.openai.com/?m=" + gpt_full_text)
        claude_url_length = len("https://claude.ai/new?q=" + claude_full_text)
        
        if gpt_url_length > 6000 or claude_url_length > 6000:
            menu.addAction("Copy Prompt", self.copy_prompt_to_clipboard)
        elif len(trimmed_text) < 350:
            menu.addAction("Write more first")
        else:
            menu.addAction("ChatGPT", self.open_chat_gpt)
            menu.addAction("Claude", self.open_claude)
            menu.addAction("Copy Prompt", self.copy_prompt_to_clipboard)
        menu.exec_(self.chat_btn.mapToGlobal(self.chat_btn.rect().bottomLeft()))

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        # Call showFullScreen/showNormal on the parent QMainWindow
        if self.is_fullscreen:
            self.parent().showFullScreen()
        else:
            self.parent().showNormal()
        self.fullscreen_btn.setText("Minimize" if self.is_fullscreen else "Fullscreen")

    


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

    def toggle_history(self):
        self.history.toggle()


    def fix_text_direction(self):
        """Fix text direction to ensure horizontal writing"""
        cursor = self.text_edit.textCursor()
        # Set text direction explicitly
        format = cursor.charFormat()
        cursor.select(QTextCursor.Document)
        cursor.setCharFormat(format)
        # Ensure document options are correct
        document = self.text_edit.document()
        option = QTextOption()
        option.setAlignment(Qt.AlignLeft)
        option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        option.setTextDirection(Qt.LeftToRight)
        document.setDefaultTextOption(option)
    # Force layout direction
        self.text_edit.setLayoutDirection(Qt.LeftToRight)

    def on_text_changed(self):
        self.text = self.text_edit.toPlainText()
        self.save_current_entry()

    def save_current_entry(self):
        if self.selected_entry_id:
            entry = next((e for e in self.entries if e.id == self.selected_entry_id), None)
            if entry:
                self.save_entry(entry)

    def save_entry(self, entry):
        previous = entry.preview_text
        try:
            self.library.save(entry, self.text)
            self.update_preview_text(entry)
            if entry.preview_text != previous: self.update_entries_display()
        except Exception as e:
            print(f"Error saving entry: {e}")

    def load_entry(self, entry):
        file_path = os.path.join(self.documents_directory, entry.filename)
        try:
            if entry.filename and os.path.exists(file_path):
                self.text = without_top_gap(self.library.read(entry))
                self.text_edit.setPlainText(self.text)
                cursor = self.text_edit.textCursor()
                cursor.movePosition(QTextCursor.End)
                self.text_edit.setTextCursor(cursor)
                self._apply_writing_font()
        except Exception as e:
            print(f"Error loading entry: {e}")

    def create_new_entry(self):
        self._add_entry(not self.entries)

    def _add_entry(self, welcome):
        new_entry = HumanEntry.create_new()
        self.entries.insert(0, new_entry)
        self.selected_entry_id = new_entry.id
        if welcome:
            self.text = self._welcome_text()
            self.save_entry(new_entry)
            self.update_preview_text(new_entry)
        else:
            self.text = ""
            self.placeholder_text = random.choice(self.placeholder_options)
            self.save_entry(new_entry)
        self.text_edit.setPlainText(self.text)
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_edit.setTextCursor(cursor)
        self._apply_writing_font()
        self.update_entries_display()

    def _welcome_text(self):
        try:
            with open(resource("assets", "default.md"), "r", encoding="utf-8") as handle: return handle.read()
        except Exception:
            return ""

    def _show_place(self):
        path = os.path.abspath(self.documents_directory)
        self.history.set_place(friendly_path(path), path)

    def _choose_place(self):
        try:
            self._apply_chosen_place(self._pick_folder())
        finally:
            self.text_edit.setFocus()

    def _pick_folder(self):
        chosen = QFileDialog.getExistingDirectory(self.window(), "Save notes in", self.documents_directory, QFileDialog.ShowDirsOnly)
        return os.path.abspath(chosen) if chosen else ""

    def _apply_chosen_place(self, chosen):
        if not chosen or same_place(chosen, self.documents_directory): return
        self.save_current_entry()
        keep = None
        if has_notes(self.documents_directory):
            outcome = self._ask_and_maybe_move(chosen)
            if outcome == "cancel": return
            keep = None if outcome == "leave" else outcome
        self._use_directory(chosen, keep)

    def _ask_and_maybe_move(self, chosen):
        dark = self.color_scheme == "dark"
        choice = ask_move(self, os.path.abspath(chosen), dark, note_count(self.documents_directory), has_notes(chosen))
        if choice != "move": return choice
        try:
            changed = relocate(self.documents_directory, chosen)
        except PlaceError as error:
            tell(self, error.title, error.body, dark)
            return "cancel"
        current = str(self.selected_entry_id) if self.selected_entry_id else ""
        return changed.get(current, self.selected_entry_id)

    def _use_directory(self, path, keep_id):
        # Drop the selection before the folder changes, so a save in between cannot write the open page into the new folder.
        previous = self.selected_entry_id
        self.selected_entry_id = None
        path = settle(path)
        try:
            os.makedirs(path, exist_ok=True)
            library = NoteLibrary(path)
            entries = library.load()
        except Exception as error:
            self.selected_entry_id = previous
            print("Error opening notes folder: %s" % error)
            tell(self, "That folder isn't available", "Your notes are still being saved in the previous place.", self.color_scheme == "dark")
            return
        remember_directory(path)
        self.documents_directory = path
        self.library = library
        self.entries = entries
        self._show_place()
        kept = self._kept(keep_id)
        if kept is not None:
            self.selected_entry_id = kept.id
            self.load_entry(kept)
            self.update_entries_display()
            return
        self._open_folder_notes()

    def _kept(self, keep_id):
        if keep_id is None: return None
        want = str(keep_id)
        return next((item for item in self.entries if str(item.id) == want), None)

    def _open_folder_notes(self):
        if not self.entries:
            self._add_entry(False)
            return
        today = date.today().strftime("%b %d")
        entry = next((item for item in self.entries if item.date == today and not item.preview_text), None)
        if entry is None: entry = self.entries[0]
        self.selected_entry_id = entry.id
        self.load_entry(entry)
        self.update_entries_display()

    def update_preview_text(self, entry):
        try:
            entry.preview_text = history_preview(self.library.read(entry))
        except Exception as e:
            print(f"Error updating preview: {e}")

    def open_chat_gpt(self):
        trimmed_text = self.text.strip()
        full_text = self.ai_chat_prompt + "\n\n" + trimmed_text
        encoded_text = QUrl.toPercentEncoding(full_text)
        url = QUrl(f"https://chat.openai.com/?m={encoded_text}")
        QDesktopServices.openUrl(url)

    def open_claude(self):
        trimmed_text = self.text.strip()
        full_text = self.claude_prompt + "\n\n" + trimmed_text
        encoded_text = QUrl.toPercentEncoding(full_text)
        url = QUrl(f"https://claude.ai/new?q={encoded_text}")
        QDesktopServices.openUrl(url)

    def copy_prompt_to_clipboard(self):
        trimmed_text = self.text.strip()
        full_text = self.ai_chat_prompt + "\n\n" + trimmed_text
        QCoreApplication.instance().clipboard().setText(full_text)
        self.did_copy_prompt = True

    def delete_entry(self, entry):
        try:
            self.library.delete(entry)
            self.entries = [e for e in self.entries if e.id != entry.id]
            if self.selected_entry_id == entry.id:
                if self.entries:
                    self.selected_entry_id = self.entries[0].id
                    self.load_entry(self.entries[0])
                else:
                    self.create_new_entry()
            self.update_entries_display()
        except Exception as e:
            print(f"Error deleting entry: {e}")



    def export_entry_as_pdf(self, entry):
        content = None
        if self.selected_entry_id == entry.id:
            self.save_entry(entry)
        file_path = os.path.join(self.documents_directory, entry.filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Get proper filename from entry
            suggested_filename = self.extract_title_from_content(content, entry.date) + ".pdf"
            # Use home directory as safe default
            home_dir = os.path.expanduser("~")
            file_dialog = QFileDialog(self, "Save PDF As", home_dir, "PDF Files (*.pdf)")
            file_dialog.setAcceptMode(QFileDialog.AcceptSave)
            file_dialog.selectFile(suggested_filename)
            if file_dialog.exec_():
                pdf_path = file_dialog.selectedFiles()[0]
                self.create_pdf_from_text(content, pdf_path)
        except Exception as e:
            print(f"Error exporting PDF: {e}")




    def extract_title_from_content(self, content, date):
        trimmed = content.strip()
        if not trimmed:
            return f"Entry {date}"
        words = [w.strip(".,!?;:\"'()[]{}<>").lower() for w in trimmed.replace("\n", " ").split() if w.strip(".,!?;:\"'()[]{}<>")]
        if len(words) >= 4:
            return "-".join(words[:4])
        return "-".join(words) if words else f"Entry {date}"

    def create_pdf_from_text(self, text, output_path):
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(output_path)
        printer.setPageMargins(72, 72, 72, 72, QPrinter.Point)
        text_doc = QTextDocument()
        text_doc.setDefaultFont(QFont(self.selected_font, self.font_size))
        text_doc.setPlainText(text.strip())
        text_doc.print_(printer)

    def load_existing_entries(self):
        os.makedirs(self.documents_directory, exist_ok=True)
        try:
            self.entries = self.library.load()
            today = date.today()
            has_empty_entry_today = any(
                e.date == today.strftime("%b %d") and not e.preview_text for e in self.entries
            )
            has_only_welcome = len(self.entries) == 1 and "Welcome to Freewrite" in (open(os.path.join(self.documents_directory, self.entries[0].filename), "r", encoding="utf-8").read() if self.entries else "")
            if not self.entries:
                self.create_new_entry()
            elif not has_empty_entry_today and not has_only_welcome:
                self.create_new_entry()
            else:
                for entry in self.entries:
                    if entry.date == today.strftime("%b %d") and not entry.preview_text:
                        self.selected_entry_id = entry.id
                        self.load_entry(entry)
                        break
                    elif has_only_welcome:
                        self.selected_entry_id = self.entries[0].id
                        self.load_entry(self.entries[0])
                        break
            self.update_entries_display()
        except Exception as e:
            print(f"Error loading entries: {e}")
            self.create_new_entry()
