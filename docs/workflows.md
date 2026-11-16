# Workflows

The bottom bar is the whole interface. On the left: one face control (it opens on Lato), Backspace, Sound, and a 15:00 timer. On the right: Chat, New Entry, the paper name (it opens on White), and History.

Ctrl+N starts a new note. Ctrl+H opens and closes History. Ctrl+W closes the window. A question that is open closes first, and the writing stays. In History, Up and Down move between notes and Enter opens the marked one. Ctrl++ and Ctrl+- change the type size, and so does Ctrl+=. The size steps through 16, 18, 20, 22, 24, and 26, and it does not wrap past either end.

Backspace and Sound are pills, with no On or Off written on them. The knob on the left, on a neutral track, is off. The knob on the right, on the warm fill, is on. Sound, when on, makes a quiet click as you type. When it is off, the keys are silent. Backspace, when off, neither erases nor clicks.

## Launch

The window opens in the ordinary size and place it last had, or maximized when it was closed that way. The first launch is 1100×600, centered on the screen under the cursor. Fullscreen and the taskbar are not restored. `windowGeometry` is the ordinary rectangle. `windowMaximized` is whether that launch should be maximized.

`NoteLibrary.load()` reads the remembered notes folder (`~/freewrite_notes` until you choose another), migrates legacy names, and returns entries newest first.

- No notes: create one and, because it is the only note, fill it from `assets/default.md`.
- Notes exist, and the folder is not a single welcome file: open a blank page. It is not written until there is something on it. The welcome check looks for the words `Welcome to Freewrite` in the only file.
- Otherwise: open that welcome note.

`date` on an entry is `created` formatted as `Nov 12`, so “today” follows the catalog time, not the file mtime.

## Saving

Two timers call the same save. `textChanged` saves immediately, and a one-second timer saves again. Both no-op until a note is selected. `NoteLibrary.save` skips the write when the filename and body are unchanged, then refreshes the history row only if the preview string changed.

New Entry opens a blank page. Nothing is stored, and History does not list it, until the page has something besides spaces and line breaks. Starting another new note while that page is still blank just stays there. Selecting another note saves the current one first, and leaves the blank page behind. Clearing a saved note removes its file and its History row; typing again saves it once more. The editor cursor is moved to the end after a load or a new note.

Delete moves the note into Trash. The file leaves the notes folder and waits in a hidden `.trash` folder, with the date it was written and the time it was deleted. If the deleted note was open, the newest remaining note is loaded. If none remain, a new note is created. Nothing in Trash is removed until you delete that note there, or empty Trash. Both of those ask first. Restore puts the note back in History, in the month it was written. The note you are writing stays open.

## History, export, chat

History toggles the sheet. It also closes on Escape (the shortcut is enabled only while the sheet is open), on the corner X, and on a click in the shaded area to the left of the sheet. Focus returns to the editor when the sheet finishes closing.

Trash sits on the count line in History. Opening it slides a second sheet over History. The chevron goes back. Escape closes Trash first, and the next Escape closes History. Restore, Delete forever, and Empty are on that sheet. Delete forever and Empty ask before anything is removed.

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

Ctrl++ and Ctrl+- step the type size through 16, 18, 20, 22, 24, and 26. Holding the keys keeps stepping, and the size stays put at 16 and at 26. The face control cycles Lato, Arial, System, and Serif. Arial resolves to Arial or Liberation Sans. System is the desktop interface face. Serif resolves to the first installed book face, preferring Gentium Book Basic. The label is drawn in that face and crossfades on each click, with no line under the word. Size and face apply to the words already on the page, and both are remembered for the next launch. A face that is not one of those four opens on Lato. A size outside that list opens at 18.

The paper name cycles White, Warm White, Sepia, Charcoal, and Black. The first launch is White. Each press steps once and is remembered. The page, the bar, History, and the folder prompt all follow that paper.

F11 asks the window to fill the screen. The bar has no control for it. The bar hides with it, and so does the scrollbar on the page. The writing still moves with the wheel and the keys. A small note at the bottom reads “Press esc to exit fullscreen” and leaves after two seconds. Leaving fullscreen brings the bar and the scrollbar back. Escape leaves fullscreen. While Trash is open, Escape closes Trash first. While History is open, Escape closes the sheet, and the next Escape leaves fullscreen. F11 does not leave.
