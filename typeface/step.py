"""The writing sizes, one step at a time. The ends stay put."""

SIZES = (16, 18, 20, 22, 24, 26)


def step_size(sizes, current, direction):
    sizes = [int(size) for size in sizes]
    if not sizes: return int(current)
    current = int(current)
    index = sizes.index(current) if current in sizes else 0
    nxt = index + (1 if direction > 0 else -1)
    if nxt < 0 or nxt >= len(sizes): return sizes[index]
    return sizes[nxt]
