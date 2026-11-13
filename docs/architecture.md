# Architecture

`FreewriteApp` is a `QMainWindow` (1100×600, centered on the screen under the cursor). Its only content widget is `ContentView`, which owns the editor, the bottom bar, and a history sheet drawn on top of the page.

```text
main.py                       installed entry: locale, then the window
freewriteApp.py               source entry
app/                          the window, and where assets and fonts are found
utils/                        the settings identity, and how an on/off value is read
papers/                       the five writing papers, and the name that steps through them
session/                      the page: bar, timer, theme, notes, chat, PDF, folder
editing/                      the editor, and which keys count as typing
typeface/                     the face, the size, applying a face
clock/                        the 15:00 countdown
switch/                       the pill used for Backspace and Sound
sound/                        key clicks
notes/                        names, catalog, atomic writes
place/                        which folder notes use, and moving them
history/                      sheet that slides over the writing
choice/                       the prompt that asks whether old notes come along
assets/                       style.qss, default.md
fonts/                        Lato (OFL)
```

`main.py` and `freewriteApp.py` only wire those packages together. Each package's `__init__.py` re-exports the names other code asks for. The folder that contains the packages is where `assets/` and `fonts/` live, both in the source tree and under `/usr/share/freewrite`.

`assets/style.qss` holds the shared layout. The colors come from the current paper and are appended when the paper changes. The file does not set a font on the editor. History, the pills, the face control, the size control, the paper name, and the clock paint themselves. A widget palette would be wiped the next time the stylesheet is applied, so those surfaces keep their own colors.

## The bar

The left side is the writing setup, in this order: size, face, a short rule, Backspace, Sound, the clock. The right side is the rest of the session: Chat, Fullscreen(F11), New Entry, the paper name, History.

Size steps 16, 18, 20, 22, 24, 26. The face starts at Lato and steps through Arial, System, and Serif, then back to Lato. Arial is Liberation Sans when Arial is not installed. System is the desktop’s interface face. Serif prefers Gentium Book Basic, then Gentium, Liberation Serif, and a few other book faces. The word is drawn in the face it names and crossfades into the next one. Nothing is drawn under it. The page, including words already written, changes on the click.

The paper starts on White. Each press on its name steps to Warm White, Sepia, Charcoal, then Black, then back to White. White is pure white. Warm White is ivory. Sepia is a muted beige. Charcoal is a soft dark gray. Black is true black. The choice is remembered as `colorScheme`. An older `light` value is White, and an older `dark` value is Black. The name crossfades the same way the face does. History, the pills, the clock, and the fullscreen note all take their colors from that paper.

`apply_face` sets the widget font, the document default, and the characters already on the page, and it puts the caret back. Theme reload polishes the editor and would otherwise drop the widget font to the application default. The characters keep the face.

The clock reads 15:00 until it is started. Digits sit in fixed cells. While it runs they warm and a small mark shows beside them. Stopping early returns to 15:00. Reaching zero stops the clock; the next start begins a fresh fifteen minutes. A pointer click on the size, the face, a pill, or the clock returns focus to the page.

Fullscreen(F11) and the F11 key set the fullscreen bit on the window. The window’s state is what shows or hides the bar, so a desktop that leaves fullscreen on its own cannot leave the bar hidden. Escape clears that bit. While History is open, Escape still closes the sheet, and the next Escape leaves fullscreen. F11 does not leave. Entering shows a capsule at the bottom, “Press esc to exit fullscreen”, for two seconds. It is not in the layout, so the writing does not move when it appears.

## A note on disk

`NoteLibrary` in `notes/library.py` owns one folder. That folder starts as `~/freewrite_notes` and can be changed from the bottom of History. The choice is remembered as `notesDirectory`. Each note is one `.md` file plus a row in a hidden `.entries.json` catalog:

```json
{ "entries": [ { "id": "<uuid>", "created": "<iso seconds>", "filename": "the morning was slow.md" } ] }
```

The catalog is how History keeps the original date after a rename. Deleting `.entries.json` does not delete writing. Dates then fall back to the file’s mtime, and missing ids are new uuids. Files that do not end in `.md`, or that start with a dot, are ignored.

Identity is resolved in this order: a catalog row with both `created` and `id`, then a legacy filename, then mtime plus a new uuid.

### Names

History and the filename share the first 30 characters of the note, flattened to one line (newlines and tabs become spaces). History appends `...` when the note is longer. That ellipsis is only in the list.

Before the stem is used as a filename, `/`, `\`, and control characters become spaces, and leading dots are stripped so a name cannot be a path or a hidden file. An empty stem is `Untitled`. If `stem.md` is already another note, the next file is `stem 2.md`, then `stem 3.md`. The note’s own current name is not treated as a collision.

The name follows the opening while those 30 characters are still changing. Once the stem is stable, later saves do not rename the file. A save whose filename and body both match what is already on disk returns without rewriting.

### Writes

`write_atomic` writes `.freewrite-<uuid>.tmp` in the notes folder, then `os.replace`s it onto the target. The previous file stays until the new copy is complete. Temps left by a crash are removed the next time the library loads.

A rename writes the new text onto the current filename first, then `os.rename`s that file to the new name, so the note is never stored in two places. If the destination already exists, the rename raises and the current file still holds the new text.

### Older notes

Previous builds used `[uuid]-[YYYY-MM-DD-HH-MM-SS].md`. On load, those files are renamed from their opening words. The catalog is written with the planned names before any rename, and the body is not edited. The uuid and timestamp from the old name become the catalog id and `created` time.

Opening a note drops a leading `\n\n`. Older builds stored two blank lines so the cursor sat lower. New writing starts on the first line, and the stripped gap is what gets saved next.

## History sheet

`HistoryDrawer` is not in the page layout. It is a child of `ContentView`, fitted to the top and right of the window and stopped at the bottom bar, so opening it does not reflow the writing. In fullscreen the bar is hidden, so the sheet uses the whole window.

One `progress` value drives the motion: `0` parks the sheet past the right edge, `1` docks it. Open runs 340 ms, close 260 ms, both on the same ease-out curve, and both start from the current progress. A second click therefore reverses the sheet instead of restarting the animation. Width is `min(400, window − 72)`, or the full width when the window is under 300 px. A scrim and a short shadow fade with the same progress.

The list is newest first, with a month heading whenever the month changes. The current year is just the month name. The open note is marked. Rows are rebuilt only when the set of ids, previews, dates, selection, or sheet color changes, and the scroll position is restored after a rebuild.

Under the list, a pinned row shows where notes are saved. A path inside the home folder is shown as `~/...`. The full path is the tooltip. Change opens the system folder picker.

If the current folder has no notes, the new folder is used immediately. If it has notes, a prompt asks whether they should come along. Dismissing it, or Cancel, leaves the folder unchanged. Leaving them keeps every old file where it is, and History then shows the new folder. An empty new folder starts a blank note, not the welcome text.

Moving them transfers the markdown files and merges the catalogs. A name that already exists in the new folder becomes `stem 2.md`, so nothing is overwritten. The note that was open stays open. If the move fails, files already transferred are put back and the new folder's catalog is restored before the setting changes. A move that cannot be fully undone says so, and names both folders.

## Backspace and Sound

`WritingEdit` drops the Backspace key when that pill is off, including when the whole note is selected. Other keys are unchanged. Both pills remember their state, `backspaceEnabled` and `soundEnabled`. A pointer toggle returns focus to the editor. Space or Enter, while the pill itself is focused, does not.

Backspace and Sound are the same control (`QuietSwitch`). The knob sits on the left when off and on the right when on. Off is a neutral track. On uses the same warm accent as History, so the filled side is the one that is on. Neither pill writes the words On or Off. A screen reader still hears the state.

Sound plays a short click for keys that write: letters and punctuation, Space, Return, and Backspace or Delete. Shortcuts and arrows stay silent. Backspace makes no click when that key is turned off, because the key does nothing. A few slight variations keep a run of letters from sounding identical. The click is generated in the app. Nothing is downloaded, and no audio package is added.

Playback uses the PulseAudio library already on the machine, which PipeWire provides too. One thread writes the clicks and sleeps when you are not typing. It keeps the stream open for a brief moment between keys and writes silence in that gap, so the next key is not late. Turning Sound off drops the stream. If the output cannot be opened, typing continues without sound.
