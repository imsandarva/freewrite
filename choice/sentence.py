"""The sentence that asks whether the notes should come along."""

def _sentence(count, crowded):
    if count == 1:
        opening = "Your note can move into this folder and sit alongside the notes already there" if crowded else "Your note can move into this folder"
        return "%s, or it can stay where it is. Anything you write from now on will be saved here." % opening
    opening = "Your %d notes can move into this folder and sit alongside the notes already there" if crowded else "Your %d notes can move into this folder"
    return "%s, or they can stay where they are. Anything you write from now on will be saved here." % (opening % count)
