"""Hand the note to ChatGPT or Claude, or copy the prompt."""

from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QMenu
from PyQt5.Qt import QDesktopServices


class ChatActions:
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
