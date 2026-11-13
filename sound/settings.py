"""Whether typing makes a click, remembered between sessions."""

from PyQt5.QtCore import QSettings

from utils.qsettings_identity import APP as _APP, ORG as _ORG
from utils.settings_flag import setting_is_on

_KEY = "soundEnabled"


def saved_sound_on():
    return setting_is_on(QSettings(_ORG, _APP).value(_KEY, True))


def remember_sound(on):
    QSettings(_ORG, _APP).setValue(_KEY, bool(on))
