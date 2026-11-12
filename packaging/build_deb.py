"""Build an installable Freewrite package.

The result is dist/freewrite_<version>_all.deb. Installing it puts a Freewrite
entry in the application menu, with the pencil as its icon, and a freewrite
command on the path. Run it from the project root.
"""

import os
import shutil
import subprocess
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = "1.1.0"
STAMP = "Thu, 12 Nov 2026 16:30:00 +0545"
MAINTAINER = "Sandarva Paudel <sandarvapoudel182@gmail.com>"
SIZES = (16, 24, 32, 48, 64, 128, 256, 512)
MODULES = (
    "main.py", "freewriteApp.py", "ContentView.py", "editing.py", "typeface.py",
    "clock.py", "switch.py", "sound.py", "notes.py", "history.py", "paths.py",
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


def _near_backdrop(color, backdrop):
    return abs(color[0] - backdrop[0]) + abs(color[1] - backdrop[1]) + abs(color[2] - backdrop[2]) < 36


def _clear_backdrop(image):
    """Drop the flat gray around the pencil, and leave the whites drawn inside it."""
    image = image.convert("RGBA")
    width, height = image.size
    pixels = image.load()
    backdrop = pixels[0, 0][:3]
    seen = bytearray(width * height)
    stack = [(0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)]
    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= width or y >= height: continue
        index = y * width + x
        if seen[index]: continue
        seen[index] = 1
        red, green, blue, _alpha = pixels[x, y]
        if not _near_backdrop((red, green, blue), backdrop): continue
        pixels[x, y] = (red, green, blue, 0)
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    cropped = image.crop(image.getbbox())
    pad = int(max(cropped.size) * 0.16)
    side = max(cropped.size) + pad * 2
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(cropped, ((side - cropped.width) // 2, (side - cropped.height) // 2), cropped)
    return canvas


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
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        master.resize((size, size), Image.Resampling.LANCZOS).save(dest, "PNG")
    pixmap = os.path.join(stage, "usr", "share", "pixmaps", "freewrite.png")
    os.makedirs(os.path.dirname(pixmap), exist_ok=True)
    master.resize((256, 256), Image.Resampling.LANCZOS).save(pixmap, "PNG")


def _stage(stage, master):
    if os.path.isdir(stage): shutil.rmtree(stage)
    program = os.path.join(stage, "usr", "share", "freewrite")
    for name in MODULES:
        _copy(os.path.join(ROOT, name), os.path.join(program, name))
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
    source = Image.open(os.path.join(ROOT, "assets", "pencil_icon.png"))
    master = _clear_backdrop(source)
    icon_path = os.path.join(ROOT, "assets", "app-icon.png")
    master.resize((512, 512), Image.Resampling.LANCZOS).save(icon_path, "PNG")
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


if __name__ == "__main__":
    print(build())
