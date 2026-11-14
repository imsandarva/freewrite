"""One note waiting in Trash."""

from trash.phrase import deleted_phrase


class TrashedNote:
    def __init__(self, note_id, created, filename, preview_text, deleted):
        self.id = note_id
        self.created = created
        self.filename = filename
        self.preview_text = preview_text
        self.deleted = deleted

    @property
    def when(self):
        return deleted_phrase(self.deleted)
