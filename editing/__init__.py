"""Backspace as a choice on the writing surface, and which keys count as typing."""

from editing.backspace_pref import remember_backspace, saved_backspace_on
from editing.gap import without_top_gap
from editing.keys import is_backspace, key_kind
from editing.writing_edit import WritingEdit
from utils.settings_flag import setting_is_on

__all__ = [
    "WritingEdit", "is_backspace", "key_kind", "remember_backspace",
    "saved_backspace_on", "setting_is_on", "without_top_gap",
]
