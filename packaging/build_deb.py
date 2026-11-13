"""Build an installable Freewrite package.

The result is dist/freewrite_<version>_all.deb. It then asks whether to put
that installer on this computer. Yes installs or updates Freewrite. Anything
else leaves the installer where it is. Run it from the project root.
"""

import os
import shutil
import subprocess
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPainter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = "1.1.0"
STAMP = "Thu, 12 Nov 2026 16:30:00 +0545"
MAINTAINER = "Sandarva Paudel <sandarvapoudel182@gmail.com>"
SIZES = (16, 24, 32, 48, 64, 128, 256, 512)
ENTRIES = ("main.py", "freewriteApp.py")
PACKAGES = (
    "app", "utils", "session", "editing", "typeface", "clock", "switch",
    "sound", "notes", "history", "place", "choice", "papers",
)
ASSETS = ("style.qss", "default.md", "pencil_icon.png", "app-icon.png")

DESKTOP = """[Desktop Entry]
Version=1.0
Type=Application
Name=Freewrite
GenericName=Writing
Comment=A quiet place to write
Exec=freewrite
TryExec=freewrite
Icon=freewrite
Terminal=false
StartupNotify=true
StartupWMClass=freewrite
Categories=Office;WordProcessor;
Keywords=write;writing;journal;notes;editor;text;freewrite;
"""

CONTROL = """Package: freewrite
Version: %s
Architecture: all
Maintainer: %s
Installed-Size: %s
Depends: python3, python3-pyqt5, libpulse0
Section: editors
Priority: optional
Description: A quiet place to write
 Freewrite is a single window for uninterrupted writing.
 Notes are plain files on this computer. There is no account.
"""

POSTINST = """#!/bin/sh
set -e
if [ "$1" = "configure" ]; then
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database -q /usr/share/applications || true
    fi
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
    fi
fi
"""

POSTRM = """#!/bin/sh
set -e
if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database -q /usr/share/applications || true
    fi
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
    fi
fi
"""


def _channel(value):
    return value[0]


def _near_backdrop(color, backdrop):
    return abs(color[0] - backdrop[0]) + abs(color[1] - backdrop[1]) + abs(color[2] - backdrop[2]) < 36


def _load_icon(path):
    image = QImage(path).convertToFormat(QImage.Format_RGBA8888)
    if image.isNull(): raise SystemExit("The pencil icon could not be read.")
    return image.copy()


def _bytes(image):
    view = image.bits()
    view.setsize(image.byteCount())
    return view


def _clear_backdrop(image):
    """Drop the flat gray around the pencil, and leave the whites drawn inside it."""
    width, height, stride = image.width(), image.height(), image.bytesPerLine()
    pixels = _bytes(image)
    backdrop = (_channel(pixels[0]), _channel(pixels[1]), _channel(pixels[2]))
    seen = bytearray(width * height)
    stack = [(0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)]
    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= width or y >= height: continue
        index = y * width + x
        if seen[index]: continue
        seen[index] = 1
        offset = y * stride + x * 4
        color = (_channel(pixels[offset]), _channel(pixels[offset + 1]), _channel(pixels[offset + 2]))
        if not _near_backdrop(color, backdrop): continue
        pixels[offset + 3] = b"\x00"
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return _pad_content(image)


def _content_box(image):
    width, height, stride = image.width(), image.height(), image.bytesPerLine()
    pixels = _bytes(image)
    min_x, min_y, max_x, max_y = width, height, -1, -1
    for y in range(height):
        row = y * stride
        for x in range(width):
            if _channel(pixels[row + x * 4 + 3]) == 0: continue
            if x < min_x: min_x = x
            if y < min_y: min_y = y
            if x > max_x: max_x = x
            if y > max_y: max_y = y
    if max_x < 0: raise SystemExit("The pencil icon has nothing left to draw.")
    return min_x, min_y, max_x - min_x + 1, max_y - min_y + 1


def _pad_content(image):
    x, y, width, height = _content_box(image)
    content = max(width, height)
    pad = int(content * 0.16)
    side = content + pad * 2
    canvas = QImage(side, side, QImage.Format_RGBA8888)
    canvas.fill(0)
    painter = QPainter(canvas)
    painter.drawImage((side - width) // 2, (side - height) // 2, image.copy(x, y, width, height))
    painter.end()
    return canvas


def _save_square(image, path, size):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    scaled = image.scaled(size, size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    if not scaled.save(path, "PNG"): raise SystemExit("The icon could not be written.")


def _write(path, text, executable=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle: handle.write(text)
    mode = 0o755 if executable else 0o644
    os.chmod(path, mode)


def _copy(src, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(src, dest)
    os.chmod(dest, 0o644)


def _icons(stage, master):
    for size in SIZES:
        dest = os.path.join(stage, "usr", "share", "icons", "hicolor", "%dx%d" % (size, size), "apps", "freewrite.png")
        _save_square(master, dest, size)
    _save_square(master, os.path.join(stage, "usr", "share", "pixmaps", "freewrite.png"), 256)


def _copy_package(name, program):
    source = os.path.join(ROOT, name)
    for dirpath, dirnames, filenames in os.walk(source):
        dirnames[:] = [item for item in dirnames if item != "__pycache__"]
        for filename in filenames:
            if not filename.endswith(".py"): continue
            full = os.path.join(dirpath, filename)
            _copy(full, os.path.join(program, os.path.relpath(full, ROOT)))


def _stage(stage, master):
    if os.path.isdir(stage): shutil.rmtree(stage)
    program = os.path.join(stage, "usr", "share", "freewrite")
    for name in ENTRIES:
        _copy(os.path.join(ROOT, name), os.path.join(program, name))
    for name in PACKAGES:
        _copy_package(name, program)
    for name in ASSETS:
        _copy(os.path.join(ROOT, "assets", name), os.path.join(program, "assets", name))
    font_dir = os.path.join(ROOT, "fonts")
    for name in os.listdir(font_dir):
        path = os.path.join(font_dir, name)
        if os.path.isfile(path): _copy(path, os.path.join(program, "fonts", name))
    _write(os.path.join(stage, "usr", "bin", "freewrite"), "#!/bin/sh\nexec python3 /usr/share/freewrite/main.py \"$@\"\n", True)
    _write(os.path.join(stage, "usr", "share", "applications", "freewrite.desktop"), DESKTOP)
    _icons(stage, master)
    installed = subprocess.check_output(["du", "-sk", os.path.join(stage, "usr")], text=True).split()[0]
    debian = os.path.join(stage, "DEBIAN")
    _write(os.path.join(debian, "control"), CONTROL % (VERSION, MAINTAINER, installed))
    _write(os.path.join(debian, "postinst"), POSTINST, True)
    _write(os.path.join(debian, "postrm"), POSTRM, True)


def build():
    source = _load_icon(os.path.join(ROOT, "assets", "pencil_icon.png"))
    master = _clear_backdrop(source)
    _save_square(master, os.path.join(ROOT, "assets", "app-icon.png"), 512)
    stage = os.path.join(ROOT, "packaging", "stage")
    _stage(stage, master)
    desktop = os.path.join(stage, "usr", "share", "applications", "freewrite.desktop")
    subprocess.check_call(["desktop-file-validate", desktop])
    dist = os.path.join(ROOT, "dist")
    os.makedirs(dist, exist_ok=True)
    package = os.path.join(dist, "freewrite_%s_all.deb" % VERSION)
    if os.path.isfile(package): os.remove(package)
    subprocess.check_call(["dpkg-deb", "--root-owner-group", "--build", stage, package])
    shutil.rmtree(stage)
    return package


def _wants_install():
    """Only a real terminal is asked. A pipe just builds, so nothing sits waiting."""
    if not sys.stdin.isatty(): return False
    try: answer = input("Install or update Freewrite on this computer as well? [y/N] ")
    except EOFError: return False
    return answer.strip().lower() in ("y", "yes")


def _as_root(command):
    return command if os.geteuid() == 0 else ["sudo", *command]


def _require_installer():
    if shutil.which("dpkg") is None or shutil.which("apt-get") is None:
        raise SystemExit("The installer is ready, but this computer cannot put it on from here.")
    if os.geteuid() != 0 and shutil.which("sudo") is None:
        raise SystemExit("The installer is ready. It needs an administrator password to go on this computer.")


def install(package):
    """Replace the installed copy even when the version number has not changed.

    apt treats the same version as already current and leaves the old files.
    dpkg puts these files in place, then apt finishes anything still missing.
    """
    _require_installer()
    try:
        subprocess.check_call(_as_root(["dpkg", "-i", package]))
        subprocess.check_call(_as_root(["apt-get", "install", "-f", "-y"]))
    except subprocess.CalledProcessError as error:
        print("The installer is ready, but it could not be put on this computer.")
        raise SystemExit(error.returncode) from None


def main():
    package = build()
    print(package, flush=True)
    if _wants_install(): install(package)


if __name__ == "__main__":
    main()
