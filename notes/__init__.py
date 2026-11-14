"""How a note is named and stored."""

from notes.atomic_write import write_atomic
from notes.catalog import read_records, write_records
from notes.constants import CATALOG_NAME, PREVIEW_CHARS
from notes.entry import HumanEntry
from notes.library import NoteLibrary
from notes.naming import allocate_name, flattened, has_writing, history_preview, stem_from_content, unique_filename

__all__ = [
    "CATALOG_NAME", "HumanEntry", "NoteLibrary", "PREVIEW_CHARS", "allocate_name",
    "flattened", "has_writing", "history_preview", "read_records", "stem_from_content",
    "unique_filename", "write_atomic", "write_records",
]
