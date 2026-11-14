"""Newest first, with a heading only when the month changes."""

from datetime import date


def count_label(count):
    if count == 0: return "No notes yet"
    if count == 1: return "1 note"
    return f"{count} notes"


def month_name(created, today):
    if created.year == today.year: return created.strftime("%B")
    return created.strftime("%B %Y")


def group_by_month(entries, today=None, moment=None):
    """Newest first, already sorted. A heading appears only when the month changes."""
    today = today or date.today()
    moment = moment or (lambda entry: entry.created)
    groups = []
    for entry in entries:
        label = month_name(moment(entry), today)
        if not groups or groups[-1][0] != label: groups.append((label, [entry]))
        else: groups[-1][1].append(entry)
    return groups
