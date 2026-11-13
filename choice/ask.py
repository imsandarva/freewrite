"""The question asked when the notes folder changes."""

from choice.prompt import _Prompt
from choice.sentence import _sentence


def ask_move(parent, path, dark, count, crowded):
    """'move', 'leave', or 'cancel'. Cancel keeps the folder that was already in use."""
    title = "Bring this note with you?" if count == 1 else "Bring your notes with you?"
    leave, move = ("Leave it", "Move it") if count == 1 else ("Leave them", "Move them")
    return _Prompt.open(parent, dark, title, _sentence(count, crowded), path, ((leave, "leave", False), (move, "move", True)), True)


def tell(parent, title, body, dark):
    _Prompt.open(parent, dark, title, body, "", (("Okay", "okay", True),), False)
