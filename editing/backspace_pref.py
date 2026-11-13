"""Backspace as a remembered choice."""

from PyQt5.QtCore import QSettings

from utils.qsettings_identity import APP, ORG
from utils.settings_flag import setting_is_on

_KEY = "backspaceEnabled"


def saved_backspace_on():
    return setting_is_on(QSettings(ORG, APP).value(_KEY, True))


def remember_backspace(on):
    QSettings(ORG, APP).setValue(_KEY, bool(on))
