# Ledgerbook 1.0.0 — Qt 6

Copyright (C) 2026 Nate Robertson. GPL-3.0-only. See LICENSE.

Ledgerbook is an offline, customizable logbook manager for Linux. Ledgerbook 1.0.0 is the first stable release. It continues from the Beta 3.0.0 redesign, keeps every Beta 2.5.2 feature, and leaves the SQLite schema, `.ledgerbook` files and `settings.json` keys unchanged, so your existing data opens as-is.

## What's in 1.0.0

- **Four redesigned themes** (Midnight, Graphite, Terracotta, Light) with a bundled Inter typeface, checked for readable contrast.
- **Home dashboard** with totals, recently opened logbooks and quick actions.
- **Command palette** (Ctrl+K): jump to any logbook or run any action by typing.
- **New sidebar**: coloured logbook tiles, count badges, folders, pinning, quick links to Archive, Recycle Bin and Settings.
- **Cleaner logbook view**: header with symbol and description, search, sort chip, selection bar, friendly empty and no-results states.
- **Undo instead of confirmation** when deleting entries (Ctrl+Z, or the toast button). Everything still goes to the Recycle Bin.
- **Redesigned dialogs** for entries, columns, logbook settings, PDF export, recovery and About, with inline validation.
- **Richer PDF reports** with shaded header band, banded rows, page numbers, landscape option.
- Toast feedback with Open / Show-in-folder actions after exports.

## Kept from earlier releases

Configurable fields, folders, pinning, recent logbooks, collapsible sidebar, sorting, column widths, row selection, entry duplication, archiving, Recycle Bin recovery, CSV / `.ledgerbook` import and export, PDF report columns and ranges, backups, restore, integrity checks, auto-backup, release notes, settings and About.

## Shortcuts

| Key | Action |
|---|---|
| Ctrl+K | Command palette |
| Ctrl+N / Ctrl+Shift+N | New entry / new logbook |
| Ctrl+F | Search entries |
| Ctrl+D | Duplicate selected entries |
| Ctrl+Z | Undo last delete |
| Ctrl+B | Show or hide the sidebar |
| Ctrl+Return | Save in the entry dialog |
| Delete / Return | Delete / edit selected entries |

## Installation on Linux Mint (installer)

Extract the archive and run `bash install.sh`. It installs Qt's `libxcb-cursor0` with apt if missing, creates an isolated installer environment and downloads PySide6-Essentials. The wizard then installs the app and creates a desktop launcher. The first installation needs an internet connection; normal use does not.

If virtual environments are missing: `sudo apt install python3-venv`.

Data lives in `~/.local/share/ledgerbook/ledgerbook.sqlite3` (or `$XDG_DATA_HOME/ledgerbook/`). The installer never replaces it. **Back up your database before upgrading.**

## Portable AppImage

`packaging/appimage/build-appimage.sh` builds a single-file `Ledgerbook-1.0.0-x86_64.AppImage`. It bundles its own Python and Qt, so the target machine needs no Python, pip or venv.

```bash
bash packaging/appimage/build-appimage.sh      # needs internet and curl; output goes to dist/
chmod +x dist/Ledgerbook-1.0.0-x86_64.AppImage
./dist/Ledgerbook-1.0.0-x86_64.AppImage
```

Build on the oldest distribution you want to support, because the AppImage won't run on systems older than the one that built it. Linux Mint 21 or newer is fine for Mint users. The AppImage uses the same data folder as the installed app, so both see the same logbooks. See `packaging/appimage/README.md` for details and options.

## Validation limits

Storage, preferences, helpers and theme-contrast tests run without Qt (`PYTHONPATH=. python3 -m unittest discover -s tests`). The interface was exercised headlessly against a stand-in Qt layer, but not on real Qt. Run `python3 tests_gui.py` on a desktop with PySide6 to produce screenshots of every screen in every theme, and check your own screen scaling before relying on this release for critical data.
