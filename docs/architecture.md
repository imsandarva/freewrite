# Architecture

`FreewriteApp` is a `QMainWindow` (1100×600, centered on the screen under the cursor). Its only content widget is `ContentView`, which owns the editor, the bottom bar, and a history sheet drawn on top of the page.

```text
main.py / freewriteApp.py     window, stylesheet, locale, Lato
        ContentView.py        session: editor, bar, save loop, chat, PDF
            editing.py        the editor, and which keys count as typing
            switch.py         the pill used for Backspace and Sound
            sound.py          key clicks
            notes.py          names, catalog, atomic writes
            history.py        sheet that slides over the writing
        assets/               style.qss, default.md
        fonts/                Lato (OFL)
```

The stylesheet in `assets/style.qss` keys off a `dark` property on the window, the editor, the bar, and the buttons. History and the pills paint themselves. A widget palette would be wiped the next time the stylesheet is applied, so those surfaces keep their own colors.

## A note on disk

`NoteLibrary` in `notes.py` owns `~/freewrite_notes`. Each note is one `.md` file plus a row in a hidden `.entries.json` catalog:

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

`HistoryDrawer` is not in the page layout. It is a child of `ContentView`, fitted to the top and right of the window and stopped at the bottom bar, so opening it does not reflow the writing.

One `progress` value drives the motion: `0` parks the sheet past the right edge, `1` docks it. Open runs 340 ms, close 260 ms, both on the same ease-out curve, and both start from the current progress. A second click therefore reverses the sheet instead of restarting the animation. Width is `min(400, window − 72)`, or the full width when the window is under 300 px. A scrim and a short shadow fade with the same progress.

The list is newest first, with a month heading whenever the month changes. The current year is just the month name. The open note is marked. Rows are rebuilt only when the set of ids, previews, dates, selection, or sheet color changes, and the scroll position is restored after a rebuild.

## Backspace and Sound

`WritingEdit` drops the Backspace key when that pill is off, including when the whole note is selected. Other keys are unchanged. Both pills remember their state, `backspaceEnabled` and `soundEnabled`. A pointer toggle returns focus to the editor. Space or Enter, while the pill itself is focused, does not.

Backspace and Sound are the same control (`QuietSwitch`). The knob sits on the left when off and on the right when on. Off is a neutral track. On uses the same warm accent as History, so the filled side is the one that is on. Neither pill writes the words On or Off. A screen reader still hears the state.

Sound plays a short click for keys that write: letters and punctuation, Space, Return, and Backspace or Delete. Shortcuts and arrows stay silent. Backspace makes no click when that key is turned off, because the key does nothing. A few slight variations keep a run of letters from sounding identical. The click is generated in the app. Nothing is downloaded, and no audio package is added.

Playback uses the PulseAudio library already on the machine, which PipeWire provides too. One thread writes the clicks and sleeps when you are not typing. It keeps the stream open for a brief moment between keys and writes silence in that gap, so the next key is not late. Turning Sound off drops the stream. If the output cannot be opened, typing continues without sound.
