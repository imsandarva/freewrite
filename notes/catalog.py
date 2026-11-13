"""The hidden catalog that keeps a note's original date after a rename."""

import json
import os
import uuid
from datetime import datetime

from notes.atomic_write import write_atomic
from notes.constants import CATALOG_NAME


def read_records(directory):
    """Catalog rows, or nothing when the file is missing or unreadable."""
    path = os.path.join(directory, CATALOG_NAME)
    try:
        with open(path, "r", encoding="utf-8") as handle: data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return []
    entries = data.get("entries") if isinstance(data, dict) else None
    return entries if isinstance(entries, list) else []


def write_records(directory, records):
    write_atomic(directory, CATALOG_NAME, json.dumps({"entries": records}, ensure_ascii=False, indent=2))


def _parse_time(value):
    try: return datetime.fromisoformat(value)
    except (TypeError, ValueError): return None


def _parse_id(value):
    try: return uuid.UUID(str(value))
    except (TypeError, ValueError): return None
