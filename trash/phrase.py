"""How Trash talks about a deleted note."""

from datetime import date, timedelta


def trash_count(count):
    if count == 0: return "Nothing here"
    if count == 1: return "1 note"
    return "%d notes" % count


def deleted_phrase(when, today=None):
    """A short line for the row. Today and yesterday stay in words."""
    today = today or date.today()
    day = when.date()
    if day == today: return "Deleted today"
    if day == today - timedelta(days=1): return "Deleted yesterday"
    return "Deleted %s %d" % (when.strftime("%b"), when.day)
