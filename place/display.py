"""Absolute paths, and the short form shown under History."""

import os


def friendly_path(path):
    """~/notes when the folder lives in the home folder. The full path otherwise."""
    home, full = os.path.expanduser("~"), os.path.abspath(path)
    if full == home: return "~"
    prefix = home + os.sep
    if full.startswith(prefix): return "~" + os.sep + full[len(prefix):]
    return full


def settle(path):
    """An absolute path, with links resolved once the folder exists so two routes to one place compare equal."""
    full = os.path.abspath(os.path.expanduser(str(path)))
    return os.path.realpath(full) if os.path.exists(full) else full


def same_place(left, right):
    return settle(left) == settle(right)
