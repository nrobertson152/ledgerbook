# Building the Ledgerbook AppImage

```bash
bash packaging/appimage/build-appimage.sh
```

Output: `dist/Ledgerbook-<version>-<arch>.AppImage`. The version is read from `ledgerbook/__init__.py`.

## Files

| File | Purpose |
|---|---|
| `build-appimage.sh` | Builds the AppDir, smoke-tests it and packs it with appimagetool |
| `AppRun` | Entry point: runs the bundled Python in isolated mode (`-I -m ledgerbook`) |
| `ledgerbook.desktop` | Desktop entry (the version field is filled in at build time) |

The icon comes from `assets/ledgerbook.png` (256×256).

## What the script does

1. Downloads a relocatable CPython 3.12 from `astral-sh/python-build-standalone`, using the latest release and cached in `build/appimage/cache/`.
2. Runs `pip install PySide6-Essentials>=6.7,<7` into that Python and copies the `ledgerbook` package into its site-packages.
3. Trims files the app never uses: pip, stdlib tests, tkinter/Tcl, and Qt's QML and Designer tooling. Set `TRIM=0` to skip this.
4. Bundles Qt's xcb helper libraries, such as `libxcb-cursor0`, from the build machine. Mint and Ubuntu often don't ship these. Core X11, GL and driver libraries are left to the host.
5. Pre-compiles the bytecode, because an AppImage is read-only when it runs.
6. Runs `tests/test_qt_smoke.py` offscreen against the bundled copy and stops if it fails.
7. Packs everything with the current `appimagetool` (continuous build).

## Build machine

- Needs internet, `curl`, `tar` and `python3`.
- To bundle the xcb helpers, first run:
  `sudo apt install libxcb-cursor0 libxcb-image0 libxcb-render-util0 libxcb-util1 libxcb-icccm4 libxcb-keysyms1 libxkbcommon-x11-0`
- The AppImage only runs on systems with the same or a newer glibc than the build machine. Build on the oldest distribution you support; Linux Mint 21 / Ubuntu 22.04 is a good baseline.
- For an ARM build, run the script on an aarch64 machine with `ARCH=aarch64`.

## Options

`ARCH`, `PY_SERIES`, `PBS_URL`, `PYSIDE_SPEC`, `APPIMAGETOOL` and `TRIM`. The comments at the top of the script describe each one.

## Data

The AppImage uses the same locations as the installed app: `~/.local/share/ledgerbook/` for data and `~/.config/ledgerbook/settings.json` for settings. Installed and portable copies therefore share the same logbooks.
