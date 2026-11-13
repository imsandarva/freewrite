"""Shared helpers that more than one feature imports."""

from utils.qsettings_identity import APP, ORG
from utils.settings_flag import setting_is_on

__all__ = ["APP", "ORG", "setting_is_on"]
