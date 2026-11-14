"""Move one file, including when the notes folder and its destination are on different disks."""

import errno
import os
import shutil
import uuid


def move_file(src, dst):
    """Rename when the disk allows it. Across disks, copy to a hidden temp so a crash never leaves a half-written note under its real name."""
    if os.path.lexists(dst): raise FileExistsError(dst)
    try:
        os.rename(src, dst)
        return
    except OSError as error:
        if error.errno != errno.EXDEV: raise
    tmp = os.path.join(os.path.dirname(dst), ".freewrite-%s.tmp" % uuid.uuid4().hex)
    try:
        shutil.copy2(src, tmp)
        if os.path.lexists(dst): raise FileExistsError(dst)
        os.replace(tmp, dst)
    except Exception:
        if os.path.exists(tmp):
            try: os.remove(tmp)
            except OSError: pass
        raise
    try:
        os.remove(src)
    except OSError:
        if not os.path.exists(src): return
        try: os.remove(dst)
        except OSError: pass
        raise
