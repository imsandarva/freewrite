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

From the project root:

```bash
python3 packaging/build_deb.py
sudo apt install ./dist/freewrite_1.1.0_all.deb
```

`apt` installs `python3-pyqt5` and `libpulse0` if they are missing. After that, Freewrite is an application: search for it by name in the menu and open it from there. The command `freewrite` also starts it. The icon is the pencil in `assets/pencil_icon.png`, with the plain gray backdrop removed so it sits cleanly in the menu.

The package puts the code in `/usr/share/freewrite`, the launcher at `/usr/bin/freewrite`, the menu entry at `/usr/share/applications/freewrite.desktop`, and the icon in the `hicolor` theme as `freewrite`. `Terminal=false` in that entry is what keeps it from opening a terminal window.

`main.py` is the installed entry. It sets the locale to English (United States) so the writing surface stays left to right, and it names the window `freewrite` so the desktop can match it to that menu entry. Styles, the welcome note, and the icon are read from beside the code (`paths.py`), so a menu launch finds them no matter which folder the session started in. Theme changes reload that same stylesheet.

Edit the modules at the project root, then run the build script again. The tree under `freewrite-package/` is an older packaging sketch and is not what `build_deb.py` ships.

## Settings

`QSettings("humansongs", "freewrite")` stores four values:

| Key | Meaning |
| --- | --- |
| `colorScheme` | `"light"` or `"dark"`. Missing means light. |
| `backspaceEnabled` | Whether Backspace deletes. Missing means on. |
| `soundEnabled` | Whether typing makes a soft click. Missing means on. |
| `notesDirectory` | Folder notes are saved in. Missing means `~/freewrite_notes`. |

For the two switches, stored booleans and the strings `0`, `false`, `no`, and `off` count as off.

Notes themselves are not in settings. They are files in `notesDirectory`, described in [Architecture](architecture.md). Changing the folder from History can move those files. The setting is updated only after that choice is finished.
