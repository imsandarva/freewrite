"""Swap a finished file into place so a crash cannot leave a half-written note."""

import os
import uuid


def write_atomic(directory, filename, text):
    """Swap the finished text into place so a crash cannot leave a half-written note."""
    path = os.path.join(directory, filename)
    tmp = os.path.join(directory, f".freewrite-{uuid.uuid4().hex}.tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as handle: handle.write(text)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp): os.remove(tmp)
        raise
    return path
