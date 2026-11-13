"""Build the short wooden knock each writing key plays."""

import array
import math
import random

from sound.constants import _GAIN, _RATE, _VARIANTS


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
