"""The PulseAudio stream the clicks are written to."""

import ctypes

from sound.constants import _RATE

_simple = _pulse = None
_reported = False


def _report(detail):
    global _reported
    if _reported: return
    _reported = True
    print("Key sound is unavailable (%s)." % detail)


def _bind():
    """Open the system sound library once. Missing here means a quiet app, not a crash."""
    global _simple, _pulse
    if _simple is not None: return _simple
    _simple = ctypes.cdll.LoadLibrary("libpulse-simple.so.0")
    _pulse = ctypes.cdll.LoadLibrary("libpulse.so.0")
    _simple.pa_simple_new.restype = ctypes.c_void_p
    _simple.pa_simple_new.argtypes = [
        ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p,
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_int),
    ]
    _simple.pa_simple_write.restype = ctypes.c_int
    _simple.pa_simple_write.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_int)]
    _simple.pa_simple_flush.restype = ctypes.c_int
    _simple.pa_simple_flush.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
    _simple.pa_simple_free.argtypes = [ctypes.c_void_p]
    _pulse.pa_strerror.restype = ctypes.c_char_p
    _pulse.pa_strerror.argtypes = [ctypes.c_int]
    return _simple


def _reason(code):
    try:
        text = _pulse.pa_strerror(code) if _pulse is not None else None
        return text.decode() if text else str(code)
    except Exception:
        return str(code)


class _Spec(ctypes.Structure):
    _fields_ = [("format", ctypes.c_int), ("rate", ctypes.c_uint32), ("channels", ctypes.c_uint8)]


class _Attr(ctypes.Structure):
    _fields_ = [("maxlength", ctypes.c_uint32), ("tlength", ctypes.c_uint32), ("prebuf", ctypes.c_uint32), ("minreq", ctypes.c_uint32), ("fragsize", ctypes.c_uint32)]


def _open_stream():
    try: lib = _bind()
    except OSError as exc:
        _report(exc)
        return None
    spec = _Spec(3, _RATE, 1)  # 3 is signed 16-bit little-endian
    frames = int(_RATE * 0.018)
    attr = _Attr(ctypes.c_uint32(-1).value, frames * 2, 0, ctypes.c_uint32(-1).value, ctypes.c_uint32(-1).value)
    err = ctypes.c_int(0)
    handle = lib.pa_simple_new(None, b"Freewrite", 1, None, b"Keys", ctypes.byref(spec), None, ctypes.byref(attr), ctypes.byref(err))
    if handle: return handle
    _report(_reason(err.value))
    return None


def _close_stream(handle):
    if not handle or _simple is None: return
    err = ctypes.c_int(0)
    _simple.pa_simple_flush(handle, ctypes.byref(err))
    _simple.pa_simple_free(handle)


def _write_stream(handle, payload):
    err = ctypes.c_int(0)
    return _simple.pa_simple_write(handle, payload, len(payload), ctypes.byref(err)) >= 0
