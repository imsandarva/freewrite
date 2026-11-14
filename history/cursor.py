"""Where the keyboard mark goes next. It stops at the ends of the list."""


def moved(index, count, delta):
    if count <= 0: return -1
    if index < 0 or index >= count: return 0
    nxt = index + (1 if delta > 0 else -1)
    if nxt < 0 or nxt >= count: return index
    return nxt
