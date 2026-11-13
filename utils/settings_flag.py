"""How a stored on/off value is read back."""


def setting_is_on(value, default=True):
    if value is None: return default
    if isinstance(value, bool): return value
    return str(value).strip().lower() not in {"0", "false", "no", "off"}
