"""Mix the clicks that are still ringing into one chunk of audio."""

import array
import sys


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
