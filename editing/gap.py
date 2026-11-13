"""Older notes were stored with two blank lines so the cursor sat lower."""


def without_top_gap(text):
    """Older notes were stored with two blank lines so the cursor sat lower. Open them on the first line."""
    return text[2:] if text.startswith("\n\n") else text
