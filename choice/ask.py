"""The question asked when the notes folder changes."""

from choice.prompt import _Prompt
from choice.sentence import _sentence


def ask_move(parent, path, paper, count, crowded):
    """'move', 'leave', or 'cancel'. Cancel keeps the folder that was already in use."""
    title = "Bring this note with you?" if count == 1 else "Bring your notes with you?"
    leave, move = ("Leave it", "Move it") if count == 1 else ("Leave them", "Move them")
    return _Prompt.open(parent, paper, title, _sentence(count, crowded), path, ((leave, "leave", False), (move, "move", True)), True)


def tell(parent, title, body, paper):
    _Prompt.open(parent, paper, title, body, "", (("Okay", "okay", True),), False)


def ask_delete(parent, paper):
    """'delete' or 'cancel'. Cancel leaves the note in Trash."""
    return _Prompt.open(
        parent, paper, "Delete this note forever?",
        "This takes it out of Trash. You won't be able to bring it back.",
        "", (("Delete", "delete", True),), True,
    )


def ask_empty(parent, paper, count):
    """'empty' or 'cancel'. Cancel leaves Trash as it is."""
    body = "The note waiting in Trash will be deleted forever." if count == 1 else "Every note waiting in Trash will be deleted forever."
    return _Prompt.open(parent, paper, "Empty Trash?", body, "", (("Empty Trash", "empty", True),), True)
