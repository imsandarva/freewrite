# Workflows

The bottom bar is the whole interface. On the left: font size, one face control (it opens on Lato), Backspace, Sound, and a 15:00 timer. On the right: Chat, Fullscreen(F11), New Entry, the paper name (it opens on White), and History.

Backspace and Sound are pills, with no On or Off written on them. The knob on the left, on a neutral track, is off. The knob on the right, on the warm fill, is on. Sound, when on, makes a quiet click as you type. When it is off, the keys are silent. Backspace, when off, neither erases nor clicks.

## Launch

`NoteLibrary.load()` reads the remembered notes folder (`~/freewrite_notes` until you choose another), migrates legacy names, and returns entries newest first.

- No notes: create one and, because it is the only note, fill it from `assets/default.md`.
- Notes exist, none of them is an empty note dated today, and the folder is not a single welcome file: create an empty note and select it. The welcome check looks for the words `Welcome to Freewrite` in the only file.
- Otherwise: open today’s empty note, or that welcome note.

`date` on an entry is `created` formatted as `Nov 12`, so “today” follows the catalog time, not the file mtime.

## Saving

Two timers call the same save. `textChanged` saves immediately, and a one-second timer saves again. Both no-op until a note is selected. `NoteLibrary.save` skips the write when the filename and body are unchanged, then refreshes the history row only if the preview string changed.

New Entry inserts a `HumanEntry` (new uuid, `created` = now, no filename yet) at the front of the list and saves it. The editor cursor is moved to the end after a load or a new note. Selecting another note saves the current one first.

Delete removes the markdown file and the catalog row. If the deleted note was open, the newest remaining note is loaded. If none remain, a new note is created.

## History, export, chat

History toggles the sheet. It also closes on Escape (the shortcut is enabled only while the sheet is open), on the corner X, and on a click in the shaded area to the left of the sheet. Focus returns to the editor when the sheet finishes closing.

The bottom of the sheet is where notes are saved. Change picks a folder. With notes already saved, the prompt offers to bring them or leave them. Esc, Cancel, or a click outside the card keeps the current folder. Leave them points History at the new folder and opens a note from it. Move them brings the old notes along, then keeps the open note on the page. The folder is remembered for the next launch.

The arrow on a row saves a PDF. The open note is saved to disk first. A save dialog starts in the home directory. The suggested name is the first four words of the body, lowercased, with surrounding punctuation stripped, joined by hyphens, plus `.pdf`. Shorter notes use the words they have. An empty note uses `Entry <Mon DD>.pdf`. `QPrinter` writes plain text with 72 pt margins in the font and size currently selected. The PDF is not a markdown render.

Chat builds a prompt plus the trimmed note and opens it in the browser.

| Note length | Menu |
| --- | --- |
| Unencoded ChatGPT or Claude URL longer than 6000 characters | Copy Prompt only |
| Under 350 characters | “Write more first”, which has no handler |
| Otherwise | ChatGPT, Claude, and Copy Prompt |

ChatGPT uses `https://chat.openai.com/?m=`. Claude uses `https://claude.ai/new?q=`. Copy Prompt copies the ChatGPT prompt and the note. Nothing is sent until the user submits it in that site.

## Timer, type, theme

The timer is a one-second `QTimer` that is always running. The clock starts a 900-second countdown and shows `MM:SS` in fixed cells, so the digits do not shift. Pressing it again resets to `15:00`. At zero the countdown stops and the mark fades; the next press starts a fresh fifteen minutes. The bar does not hide.

Font size cycles 16, 18, 20, 22, 24, 26. The face control cycles Lato, Arial, System, and Serif. Arial resolves to Arial or Liberation Sans. System is the desktop interface face. Serif resolves to the first installed book face, preferring Gentium Book Basic. The label is drawn in that face and crossfades on each click, with no line under the word. Size and face apply to the words already on the page. They are not written to settings.

The paper name cycles White, Warm White, Sepia, Charcoal, and Black. The first launch is White. Each press steps once and is remembered. The page, the bar, History, and the folder prompt all follow that paper.

Fullscreen(F11), and the F11 key, ask the window to fill the screen. The bar hides with it. A small note at the bottom reads “Press esc to exit fullscreen” and leaves after two seconds. Escape leaves fullscreen. While History is open, Escape closes the sheet first and the next Escape leaves fullscreen. F11 does not leave.
