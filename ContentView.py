import os
import random  # Added for random placeholder selection
from datetime import date
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QMenu, QFileDialog, QShortcut
)
from PyQt5.QtGui import QFont, QTextCursor, QTextDocument, QTextOption, QKeySequence
from PyQt5.QtCore import Qt, QTimer, QSettings, QUrl
from PyQt5.Qt import QDesktopServices
from PyQt5.QtPrintSupport import QPrinter
from notes import HumanEntry, NoteLibrary, history_preview
from editing import WritingEdit, remember_backspace, saved_backspace_on, without_top_gap
from history import HistoryDrawer
from sound import KeyClicks, remember_sound, saved_sound_on
from switch import QuietSwitch

class ContentView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.entries = []
        self.text = ""
        self.is_fullscreen = False
        self.selected_font = "Lato-Regular"
        self.current_random_font = ""
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
        self.available_fonts = ["Lato-Regular", "Arial", "Times New Roman"]  # Simplified
        self.font_sizes = [16, 18, 20, 22, 24, 26]
        self.placeholder_options = [
            "Begin writing", "Pick a thought and go", "Start typing",
            "What's on your mind", "Just start", "Type your first thought",
            "Start with one sentence", "Just say it"
        ]
        self.documents_directory = os.path.join(os.path.expanduser("~"), "freewrite_notes")
        os.makedirs(self.documents_directory, exist_ok=True)
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
        self.main_widget = QWidget()
        self.main_layout.addWidget(self.main_widget)
        self.main_v_layout = QVBoxLayout(self.main_widget)
        # Text Editor with proper alignment configuration
        self.text_edit = WritingEdit(self.backspace_enabled, self.key_sound)
        self.text_edit.setPlainText(self.text)
        self.text_edit.setFont(QFont(self.selected_font, self.font_size))
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

        # Bottom Navigation
        self.bottom_nav = QWidget()
        self.bottom_nav.setObjectName("bottomNav")
        self.bottom_nav.setProperty("dark", is_dark)
        self.bottom_nav_layout = QHBoxLayout(self.bottom_nav)
        self.font_buttons = QWidget()
        self.font_buttons_layout = QHBoxLayout(self.font_buttons)
        
        # Font Size Button
        self.font_size_btn = QPushButton(f"{int(self.font_size)}px")
        self.font_size_btn.setProperty("dark", is_dark)
        self.font_size_btn.clicked.connect(self.change_font_size)
        self.font_buttons_layout.addWidget(self.font_size_btn)
        
        # Font Buttons
        for font in ["Lato", "Arial", "System", "Serif", "Random"]:
            btn = QPushButton(font)
            btn.setProperty("dark", is_dark)
            btn.clicked.connect(lambda checked, f=font: self.change_font(f))
            self.font_buttons_layout.addWidget(btn)
        self.bottom_nav_layout.addWidget(self.font_buttons)
        self.bottom_nav_layout.addStretch()
        
        #ensure that cursor doesn't move above third ine
        # Utility Buttons
        self.utility_buttons = QWidget()
        self.utility_buttons_layout = QHBoxLayout(self.utility_buttons)
        self.backspace_switch = QuietSwitch("Backspace", self.backspace_enabled, is_dark)
        self.backspace_switch.toggled.connect(self.on_backspace_toggled)
        self.utility_buttons_layout.addWidget(self.backspace_switch)
        self.sound_switch = QuietSwitch("Sound", self.sound_enabled, is_dark)
        self.sound_switch.toggled.connect(self.on_sound_toggled)
        self.utility_buttons_layout.addWidget(self.sound_switch)
        self.timer_btn = QPushButton("15:00")
        self.timer_btn.setProperty("dark", is_dark)
        self.timer_btn.clicked.connect(self.toggle_timer)
        self.utility_buttons_layout.addWidget(self.timer_btn)
        
        self.chat_btn = QPushButton("Chat")
        self.chat_btn.setProperty("dark", is_dark)
        self.chat_btn.clicked.connect(self.show_chat_menu)
        self.utility_buttons_layout.addWidget(self.chat_btn)
        
        self.fullscreen_btn = QPushButton("Fullscreen")
        self.fullscreen_btn.setProperty("dark", is_dark)
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        self.utility_buttons_layout.addWidget(self.fullscreen_btn)
        
        self.new_entry_btn = QPushButton("New Entry")
        self.new_entry_btn.setProperty("dark", is_dark)
        self.new_entry_btn.clicked.connect(self.create_new_entry)
        self.utility_buttons_layout.addWidget(self.new_entry_btn)
        
        self.theme_toggle_btn = QPushButton("Toggle Theme")
        self.theme_toggle_btn.setProperty("dark", is_dark)
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)
        self.utility_buttons_layout.addWidget(self.theme_toggle_btn)
        
        self.history_btn = QPushButton("History")
        self.history_btn.setProperty("dark", is_dark)
        self.history_btn.clicked.connect(self.toggle_history)
        self.utility_buttons_layout.addWidget(self.history_btn)
        
        self.bottom_nav_layout.addWidget(self.utility_buttons)
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


    def _wire_history(self, is_dark):
        self.history = HistoryDrawer(self)
        self.history.set_dark(bool(is_dark))
        self.history.chosen.connect(self.select_entry)
        self.history.delete_requested.connect(self.delete_entry)
        self.history.export_requested.connect(self.export_entry_as_pdf)
        self.history.opened.connect(self._history_shown)
        self.history.dismissed.connect(self._history_hidden)
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

    def change_font_size(self):
        current_index = self.font_sizes.index(self.font_size)
        self.font_size = self.font_sizes[(current_index + 1) % len(self.font_sizes)]
        self.font_size_btn.setText(f"{int(self.font_size)}px")
        self.text_edit.setFont(QFont(self.selected_font, self.font_size))

    def change_font(self, font):
        if font == "Random":
            self.selected_font = self.available_fonts[random.randint(0, len(self.available_fonts) - 1)]
            self.current_random_font = self.selected_font
        else:
            self.selected_font = {"Lato": "Lato-Regular", "Arial": "Arial", "System": "Arial", "Serif": "Times New Roman"}[font]
            self.current_random_font = ""
        self.text_edit.setFont(QFont(self.selected_font, self.font_size))

    def toggle_timer(self):
        self.timer_is_running = not self.timer_is_running
        if not self.timer_is_running:
            self.time_remaining = 900
        self.update_timer_button()

    def update_timer(self):
        if self.timer_is_running and self.time_remaining > 0:
            self.time_remaining -= 1
            self.update_timer_button()
        elif self.time_remaining == 0:
            self.timer_is_running = False
            self.bottom_nav_opacity = 1.0

    def update_timer_button(self):
        if not self.timer_is_running and self.time_remaining == 900:
            self.timer_btn.setText("15:00")
        else:
            minutes = self.time_remaining // 60
            seconds = self.time_remaining % 60
            self.timer_btn.setText(f"{minutes}:{seconds:02d}")

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

    


    def restore_font_size_on_toggle(self, font_size_before_toggle):
        self.font_size_btn.setText(f"{font_size_before_toggle}px")
        self.text_edit.setFont(QFont(self.selected_font, font_size_before_toggle))


    def toggle_theme(self):
        # Store current font size before theme change
        current_font_size = int(self.font_size)
        self.color_scheme = "dark" if self.color_scheme == "light" else "light"
        QSettings("humansongs", "freewrite").setValue("colorScheme", self.color_scheme)
        
        # Apply theme to all widgets
        is_dark = self.color_scheme == "dark"
        
        # Apply property to parent main window
        if hasattr(self, 'parent') and self.parent() is not None:
            self.parent().setProperty("dark", is_dark)
            self.parent().style().unpolish(self.parent())
            self.parent().style().polish(self.parent())
        
        # Set property for all widgets
        for widget in [self.text_edit, self.bottom_nav, self.font_size_btn,
                      self.timer_btn, self.chat_btn, self.fullscreen_btn,
                      self.new_entry_btn, self.theme_toggle_btn, self.history_btn]:
            if widget:
                widget.setProperty("dark", is_dark)
                widget.style().unpolish(widget)
                widget.style().polish(widget)
        
        # Apply to all buttons in font_buttons
        for i in range(self.font_buttons_layout.count()):
            widget = self.font_buttons_layout.itemAt(i).widget()
            if widget:
                widget.setProperty("dark", is_dark)
                widget.style().unpolish(widget)
                widget.style().polish(widget)
        
        # Apply to all buttons in utility_buttons
        for i in range(self.utility_buttons_layout.count()):
            widget = self.utility_buttons_layout.itemAt(i).widget()
            if widget:
                widget.setProperty("dark", is_dark)
                widget.style().unpolish(widget)
                widget.style().polish(widget)
        
        # The theme file reloads after this, and that wipes a palette set too early.
        self.update_styles()
        self.history.set_dark(is_dark)
        self._paint_history_button()
        
        # Restore font size
        self.restore_font_size_on_toggle(current_font_size)

        # Update entries display to ensure new widgets have the theme
        self.update_entries_display()


# Replace the update_styles method
    def update_styles(self):
        try:
            with open("assets/style.qss", "r") as f:
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
        except Exception as e:
            print(f"Error loading entry: {e}")

    def create_new_entry(self):
        new_entry = HumanEntry.create_new()
        self.entries.insert(0, new_entry)
        self.selected_entry_id = new_entry.id
        if len(self.entries) == 1:
            try:
                with open("assets/default.md", "r", encoding="utf-8") as f:
                    self.text = f.read()
            except:
                self.text = ""
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
