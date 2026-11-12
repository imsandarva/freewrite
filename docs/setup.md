# Setup

The app is PyQt5. On Debian or Ubuntu, `python3-pyqt5` is enough, including `QtPrintSupport` for PDF export. A pip install of `PyQt5` works the same way. Key clicks use the PulseAudio library that is already part of the desktop (PipeWire included). No extra audio package is installed.

## Run from the source tree

From the project root, so relative paths resolve:

```bash
python3 freewriteApp.py
```

That entry loads `assets/style.qss`, registers the Lato files beside the app, and uses `app_icons/1024-mac.png`. `main.py` is the installed entry point. It always reads the stylesheet from `/usr/share/freewrite/assets/style.qss`, so it only works after the package is installed.

The first launch creates `~/freewrite_notes` and, when the folder is empty, writes the welcome text from `assets/default.md` as the first note.

## Installed package

`/usr/bin/freewrite` runs `python3 /usr/share/freewrite/main.py`. The desktop file is `freewrite.desktop` (`Office`, `WordProcessor`). Runtime dependency is `python3-pyqt5`.

`main.py` forces the process locale to English (United States) so the writing surface stays left to right. Theme changes still reload `assets/style.qss` from the current working directory, which is the source tree during development and is not the install path. After a theme toggle in an installed build, the stylesheet only reloads if that relative file is visible.

`create_deb_structure.py` regenerates the packaging skeleton under `freewrite-package/`. Edit the modules at the project root, then refresh the package tree. Do not treat the copies under `usr/share/freewrite/` as the source.

## Settings

`QSettings("humansongs", "freewrite")` stores three values:

| Key | Meaning |
| --- | --- |
| `colorScheme` | `"light"` or `"dark"`. Missing means light. |
| `backspaceEnabled` | Whether Backspace deletes. Missing means on. |
| `soundEnabled` | Whether typing makes a soft click. Missing means on. |

For the two switches, stored booleans and the strings `0`, `false`, `no`, and `off` count as off.

Notes themselves are not in settings. They are files, described in [Architecture](architecture.md).
