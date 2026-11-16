"""One remembered value, flushed before the call returns.

A preference that waits for the process to exit is lost when the app is closed
quickly. Writing it through here keeps the next launch honest.
"""

from PyQt5.QtCore import QSettings

from utils.qsettings_identity import APP, ORG


def remember_value(key, value):
    settings = QSettings(ORG, APP)
    settings.setValue(key, value)
    settings.sync()
    if settings.status() != QSettings.NoError: print("Could not save %s" % key)
