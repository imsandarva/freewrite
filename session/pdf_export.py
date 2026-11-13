"""Save a note as a PDF in the face and size currently on the page."""

import os

from PyQt5.QtGui import QFont, QTextDocument
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QFileDialog


class PdfExport:
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
