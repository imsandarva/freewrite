"""Rates, gains, and the handful of click variations."""

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
