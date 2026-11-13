"""One click, and how far through it playback has read."""

class _Voice:
    __slots__ = ("data", "pos")

    def __init__(self, data):
        self.data, self.pos = data, 0

    def done(self):
        return self.pos >= len(self.data)
