# Freewrite

Linux port of [Farza’s Freewrite](https://www.freewrite.io/): a single writing window meant for timed, uninterrupted freewriting. Notes are plain markdown files in `~/freewrite_notes`, or another folder chosen from History. There is no account, sync, or editor beyond the page you are typing on.

The code that runs is the Python at the project root. `freewrite-package/` is a Debian packaging tree and can lag behind that source.

| Doc | What it covers |
| --- | --- |
| [Setup](setup.md) | Running from source, the installed layout, and where settings and notes live |
| [Architecture](architecture.md) | Modules, how a note is stored, and the decisions that shape the window |
| [Workflows](workflows.md) | A writing session: launch, save, history, sound, export, chat, timer, and theme |
