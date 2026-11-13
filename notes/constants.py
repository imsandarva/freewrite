"""Lengths and filenames the notes folder shares."""

import re

# History cuts the title here. The filename uses this same stretch of text.
PREVIEW_CHARS = 30
CATALOG_NAME = ".entries.json"
_STAMP = "%Y-%m-%d-%H-%M-%S"
_LEGACY_NAME = re.compile(
    r"^\[([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\]-\[(\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})\]\.md$"
)
_UNSAFE = re.compile(r'[/\\\x00-\x1f]')
