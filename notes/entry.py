"""One row in the notes catalog."""

import uuid
from datetime import datetime


class HumanEntry:
    def __init__(self, id, created, filename, preview_text):
        self.id = id
        self.created = created
        self.date = created.strftime("%b %d")
        self.filename = filename
        self.preview_text = preview_text

    @staticmethod
    def create_new():
        return HumanEntry(uuid.uuid4(), datetime.now(), "", "")
