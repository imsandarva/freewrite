"""Play a click for each writing key, on a thread that sleeps when you are not typing."""

import queue
import random
import threading
import time

from sound.constants import _CHUNK, _HOLD, _QUIET, _RATE, _VARIANTS
from sound.pulse import _close_stream, _open_stream, _report, _write_stream
from sound.render import _render
from sound.synthesis import build_bank
from sound.voice import _Voice


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
