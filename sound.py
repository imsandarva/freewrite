"""Soft key clicks, played only while Sound is on.

A writing key gets a short knock: a few inharmonic tones, the way wood and
plastic ring, plus a very quiet tick. Integer harmonics would sound like a
beep, so they are not used. A handful of slight variations keep a run of
letters from sounding copied.

One background thread holds a small playback stream open during a burst of
typing and writes silence between keys. That silence is what keeps the next
key immediate. Without it the stream underruns and the following click shows
up late. The thread sleeps whenever you are not typing. Turning Sound off
drops the stream. If the output cannot be opened, typing stays silent.
"""

import array
import ctypes
import math
import queue
import random
import sys
import threading
import time

from PyQt5.QtCore import QSettings

from editing import setting_is_on

_ORG, _APP, _KEY = "humansongs", "freewrite", "soundEnabled"
_RATE = 48000
_CHUNK = 432  # 9ms. The stream stays about two chunks ahead, so a click is still quick.
_HOLD = 0.42  # how long the stream stays open after the last key, ready for the next one
_QUIET = object()
_GAIN = {"type": 0.23, "space": 0.16, "erase": 0.13, "return": 0.17}
# pitch, tick amount, seed. Tick is the noise, kept well under the knock.
_VARIANTS = {
    "type": ((1.0, 1.0, 3), (0.984, 0.82, 19), (1.016, 1.06, 41)),
    "space": ((0.90, 0.28, 7),),
    "erase": ((1.04, 0.5, 13),),
    "return": ((0.86, 0.26, 23),),
}
_simple = _pulse = None
_reported = False


def saved_sound_on():
    return setting_is_on(QSettings(_ORG, _APP).value(_KEY, True))


def remember_sound(on):
    QSettings(_ORG, _APP).setValue(_KEY, bool(on))


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


def _bump(t, at, width):
    d = t - at
    return math.exp(-(d * d) / (2 * width * width))


def _modal(n, pitch):
    """The knock. Partials sit off the harmonic series so the tone stays wooden, not electronic."""
    out = [0.0] * n
    modes = ((292.0, 0.007, 0.40), (292.0 * 2.33, 0.0042, 0.34), (292.0 * 4.15, 0.0024, 0.15))
    for i in range(n):
        t = i / _RATE
        s = 0.0
        for freq, tau, amp in modes:
            s += math.sin(math.tau * freq * pitch * t) * math.exp(-t / tau) * amp
        out[i] = s
    return out


def _ticks(n, seed):
    rng = random.Random(seed)
    out = [0.0] * n
    for at, spread, amp in ((0.0001, 2, 1.0), (0.0048, 1, 0.28)):
        center = int(at * _RATE)
        for k in range(-spread, spread + 1):
            i = center + k
            if 0 <= i < n: out[i] += amp * (1 - abs(k) / (spread + 1)) * rng.uniform(0.7, 1.0)
    return out


def _bandpass(samples, freq, q):
    w0 = math.tau * freq / _RATE
    alpha = math.sin(w0) / (2 * q)
    b0, b1, b2 = alpha, 0.0, -alpha
    a0, a1, a2 = 1 + alpha, -2 * math.cos(w0), 1 - alpha
    b0, b1, b2, a1, a2 = b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0
    x1 = x2 = y1 = y2 = 0.0
    out = []
    for x in samples:
        y = b0 * x + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1, y2, y1 = x1, x, y1, y
        out.append(y)
    return out


def _shape(pitch, tick, seed, gain):
    n = int(_RATE * 0.032)
    body, noise = _modal(n, pitch), _bandpass(_ticks(n, seed), 3400 * pitch, 0.85)
    body_peak = max((abs(s) for s in body), default=1.0) or 1.0
    noise_peak = max((abs(s) for s in noise), default=1.0) or 1.0
    scale = tick * 0.40 * body_peak / noise_peak
    mixed = [body[i] + noise[i] * scale for i in range(n)]
    _fade(mixed)
    return _pcm(_trim(mixed), gain)


def _fade(samples):
    inn, outn = 3, int(0.0022 * _RATE)
    n = len(samples)
    for i in range(min(inn, n)): samples[i] *= i / inn
    for i in range(min(outn, n)): samples[n - 1 - i] *= i / outn


def _trim(samples):
    peak = max((abs(s) for s in samples), default=1.0) or 1.0
    last = 0
    for i, s in enumerate(samples):
        if abs(s) >= peak * 0.02: last = i
    keep = min(len(samples), last + int(0.002 * _RATE))
    return samples[:max(keep, int(0.014 * _RATE))]


def _pcm(samples, gain):
    peak = max((abs(s) for s in samples), default=1.0) or 1.0
    scale = gain * 32767.0 / peak
    out = array.array("h")
    for s in samples:
        v = int(s * scale)
        if v > 32767: v = 32767
        elif v < -32768: v = -32768
        out.append(v)
    return out


def build_bank():
    bank = {}
    for kind, variants in _VARIANTS.items():
        bank[kind] = [_shape(pitch, tick, seed, _GAIN[kind]) for pitch, tick, seed in variants]
    return bank


def _render(voices, frames):
    acc = array.array("h", (0,)) * frames
    for voice in voices:
        count = min(frames, len(voice.data) - voice.pos)
        for i in range(count):
            mixed = acc[i] + voice.data[voice.pos + i]
            if mixed > 32767: mixed = 32767
            elif mixed < -32768: mixed = -32768
            acc[i] = mixed
        voice.pos += count
    if sys.byteorder != "little": acc.byteswap()
    return acc.tobytes()


class _Voice:
    __slots__ = ("data", "pos")

    def __init__(self, data):
        self.data, self.pos = data, 0

    def done(self):
        return self.pos >= len(self.data)


class KeyClicks:
    def __init__(self, on=True):
        self._on = bool(on)
        self._bank = None
        self._last = {}
        self._queue = queue.SimpleQueue()
        self._thread = None
        if self._on: self._ensure()

    def set_enabled(self, on):
        self._on = bool(on)
        if self._on:
            self._ensure()
            return
        if self._thread is not None: self._queue.put(_QUIET)

    def play(self, kind):
        if not self._on or kind not in _VARIANTS: return
        self._ensure()
        self._queue.put(kind)

    def _ensure(self):
        if self._thread is not None: return
        self._thread = threading.Thread(target=self._loop, name="freewrite-keys", daemon=True)
        self._thread.start()

    def _loop(self):
        self._prepare()
        stream, voices, quiet = None, [], 0
        while True:
            try: stream, voices, quiet = self._step(stream, voices, quiet)
            except Exception as exc:
                _report(exc)
                _close_stream(stream)
                stream, voices, quiet = None, [], 0
                time.sleep(0.2)

    def _step(self, stream, voices, quiet):
        item = self._next(stream is None and not voices)
        if item is _QUIET or not self._on:
            if not self._on: self._discard()
            return _close_stream(stream) or None, [], 0
        if item not in (_QUIET, None):
            self._add(voices, item)
        if voices: quiet = 0
        elif stream is not None:
            quiet += 1
            if quiet * _CHUNK / _RATE > _HOLD: return _close_stream(stream) or None, [], 0
        if stream is None and not voices: return None, [], 0
        if stream is None:
            stream = _open_stream()
            if stream is None: return None, [], 0
        if not _write_stream(stream, _render(voices, _CHUNK)):
            _close_stream(stream)
            return None, [], 0
        return stream, [voice for voice in voices if not voice.done()], quiet

    def _next(self, block):
        if block: return self._queue.get()
        try: return self._queue.get_nowait()
        except queue.Empty: return None

    def _discard(self):
        while True:
            try: self._queue.get_nowait()
            except queue.Empty: return

    def _prepare(self):
        if self._bank is not None: return
        try: self._bank = build_bank()
        except Exception as exc:
            _report(exc)
            self._bank = {}

    def _add(self, voices, kind):
        if len(voices) >= 4: voices.pop(0)
        options = (self._bank or {}).get(kind)
        if not options: return
        index = random.randrange(len(options))
        if len(options) > 1 and index == self._last.get(kind): index = (index + 1) % len(options)
        self._last[kind] = index
        voices.append(_Voice(options[index]))
