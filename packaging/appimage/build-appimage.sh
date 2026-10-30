#!/usr/bin/env bash
# Build a self-contained Ledgerbook AppImage.
#
#   bash packaging/appimage/build-appimage.sh
#
# The AppImage bundles a relocatable CPython (astral-sh/python-build-standalone), PySide6-Essentials
# and Ledgerbook itself, so the target machine needs no Python at all. Requires: bash, curl, tar,
# python3 (only to read GitHub's JSON) and an internet connection. Output: dist/Ledgerbook-<ver>-<arch>.AppImage
#
# Optional environment overrides:
#   ARCH=x86_64|aarch64         target architecture (default: this machine)
#   PY_SERIES=3.12              bundled Python minor version
#   PBS_URL=<url>               exact python-build-standalone tarball to use (skips the GitHub lookup)
#   PYSIDE_SPEC='PySide6-Essentials>=6.7,<7'
#   APPIMAGETOOL=<path>         use an existing appimagetool instead of downloading it
#   TRIM=0                      keep pip, stdlib tests, tkinter and Qt's QML/Designer tooling
set -euo pipefail

HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
ROOT=$(cd -- "$HERE/../.." && pwd)
VERSION=$(sed -n "s/^__version__ = '\(.*\)'$/\1/p" "$ROOT/ledgerbook/__init__.py")
ARCH=${ARCH:-$(uname -m)}
PY_SERIES=${PY_SERIES:-3.12}
PYSIDE_SPEC=${PYSIDE_SPEC:-'PySide6-Essentials>=6.7,<7'}
TRIM=${TRIM:-1}
BUILD="$ROOT/build/appimage"
CACHE="$BUILD/cache"
APPDIR="$BUILD/Ledgerbook.AppDir"
DIST="$ROOT/dist"
OUT="$DIST/Ledgerbook-$VERSION-$ARCH.AppImage"

say() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
die() { printf '\nError: %s\n' "$*" >&2; exit 1; }

[ -n "$VERSION" ] || die "could not read __version__ from ledgerbook/__init__.py"
for tool in curl tar python3; do command -v "$tool" >/dev/null || die "'$tool' is required"; done
case "$ARCH" in x86_64|aarch64) ;; *) die "unsupported ARCH '$ARCH' (use x86_64 or aarch64)";; esac
mkdir -p "$CACHE" "$DIST"

# ------------------------------------------------------------------------------------ 1. Python runtime
if [ -z "${PBS_URL:-}" ]; then
  say "Finding the latest portable CPython $PY_SERIES for $ARCH"
  PBS_URL=$(curl -fsSL https://api.github.com/repos/astral-sh/python-build-standalone/releases/latest |
    python3 -I -c '
import json, re, sys
series, arch = sys.argv[1], sys.argv[2]
assets = {a["name"]: a["browser_download_url"] for a in json.load(sys.stdin)["assets"]}
for flavour in ("install_only_stripped", "install_only"):
    pat = re.compile(r"cpython-%s\.\d+\+\d+-%s-unknown-linux-gnu-%s\.tar\.gz$" % (re.escape(series), arch, flavour))
    hits = sorted(n for n in assets if pat.fullmatch(n))
    if hits:
        print(assets[hits[-1]]); break
' "$PY_SERIES" "$ARCH") || true
  [ -n "$PBS_URL" ] || die "no python-build-standalone build found for $PY_SERIES/$ARCH; set PBS_URL manually"
fi
PBS_TAR="$CACHE/$(basename "${PBS_URL%%\?*}" | sed 's/%2B/+/g')"
if [ ! -s "$PBS_TAR" ]; then
  say "Downloading $(basename "$PBS_TAR")"
  curl -fL --retry 3 -o "$PBS_TAR.part" "$PBS_URL" && mv "$PBS_TAR.part" "$PBS_TAR"
fi

say "Creating AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/lib" "$APPDIR/usr/share/applications" \
         "$APPDIR/usr/share/icons/hicolor/256x256/apps" "$APPDIR/usr/share/doc/ledgerbook"
tar -xzf "$PBS_TAR" -C "$APPDIR/usr"          # unpacks to usr/python/
PY="$APPDIR/usr/python/bin/python3"
[ -x "$PY" ] || die "unexpected tarball layout: $PY not found"
"$PY" -I -c 'import sys; print("Bundled Python", sys.version.split()[0])'

# ------------------------------------------------------------------------------------ 2. Qt + Ledgerbook
say "Installing $PYSIDE_SPEC"
"$PY" -I -m pip install --no-cache-dir --no-compile --disable-pip-version-check "$PYSIDE_SPEC"

SITE=$("$PY" -I -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')
say "Copying Ledgerbook $VERSION into $SITE"
"$PY" -I -c 'import shutil, sys
shutil.copytree(sys.argv[1], sys.argv[2], ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))' \
  "$ROOT/ledgerbook" "$SITE/ledgerbook"
cp "$ROOT/LICENSE" "$APPDIR/usr/share/doc/ledgerbook/LICENSE"

# ------------------------------------------------------------------------------------ 3. Trim
if [ "$TRIM" = 1 ]; then
  say "Removing parts Ledgerbook never uses"
  STDLIB=$("$PY" -I -c 'import sysconfig; print(sysconfig.get_paths()["stdlib"])')
  case "$STDLIB/" in "$APPDIR"/*) ;; *) die "refusing to trim: $STDLIB is outside the AppDir";; esac
  rm -rf "$STDLIB/test" "$STDLIB/idlelib" "$STDLIB/tkinter" "$STDLIB/turtledemo" "$STDLIB/lib2to3"
  rm -f "$STDLIB"/lib-dynload/_tkinter*.so "$APPDIR"/usr/python/lib/libtcl* "$APPDIR"/usr/python/lib/libtk*
  rm -rf "$APPDIR"/usr/python/lib/tcl* "$APPDIR"/usr/python/lib/tk* "$APPDIR"/usr/python/lib/itcl* "$APPDIR"/usr/python/lib/thread*
  # Qt developer tools and QML runtime files (Ledgerbook uses QtCore/QtGui/QtWidgets/QtSvg only).
  rm -rf "$SITE/PySide6/Qt/qml" "$SITE/PySide6/qml" "$SITE/PySide6/scripts" "$SITE/PySide6/include" "$SITE/PySide6/typesystems"
  for tool in designer assistant linguist lupdate lrelease uic rcc qmlformat qmllint qmlls qmlcachegen qmlimportscanner qmltyperegistrar balsam balsamui svgtoqml; do
    rm -f "$SITE/PySide6/$tool" "$SITE/PySide6/Qt/libexec/$tool"
  done
  "$PY" -I -m pip uninstall -y -q pip || true
fi

# ------------------------------------------------------------------------------------ 4. System libraries
# Qt 6's X11 plugin needs libxcb-cursor0, which Ubuntu/Mint often lack. These xcb-util libraries have a
# stable ABI and are safe to bundle; core X11/GL/driver libraries are deliberately left to the host.
say "Bundling xcb helper libraries"
missing=""
for lib in libxcb-cursor.so.0 libxcb-image.so.0 libxcb-render-util.so.0 libxcb-util.so.1 \
           libxcb-icccm.so.4 libxcb-keysyms.so.1 libxkbcommon-x11.so.0; do
  path=$(ldconfig -p 2>/dev/null | awk -v l="$lib" '$1 == l && /x86-64|AArch64|aarch64/ {print $NF; exit}')
  [ -n "$path" ] || path=$(ldconfig -p 2>/dev/null | awk -v l="$lib" '$1 == l {print $NF; exit}')
  if [ -n "$path" ]; then cp -L "$path" "$APPDIR/usr/lib/$lib"; echo "  + $lib"; else missing="$missing $lib"; fi
done
if [ -n "$missing" ]; then
  echo "  ! Not found on this build machine:$missing"
  echo "    The AppImage will rely on the target system for these. To bundle them, run:"
  echo "    sudo apt install libxcb-cursor0 libxcb-image0 libxcb-render-util0 libxcb-util1 libxcb-icccm4 libxcb-keysyms1 libxkbcommon-x11-0"
fi

# ------------------------------------------------------------------------------------ 5. AppDir metadata
say "Writing launcher, desktop entry and icon"
install -m 755 "$HERE/AppRun" "$APPDIR/AppRun"
cp "$HERE/ledgerbook.desktop" "$APPDIR/ledgerbook.desktop"
sed -i "s/^X-AppImage-Version=.*/X-AppImage-Version=$VERSION/" "$APPDIR/ledgerbook.desktop"
cp "$APPDIR/ledgerbook.desktop" "$APPDIR/usr/share/applications/ledgerbook.desktop"
cp "$ROOT/assets/ledgerbook.png" "$APPDIR/ledgerbook.png"
cp "$ROOT/assets/ledgerbook.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/ledgerbook.png"
ln -sf ledgerbook.png "$APPDIR/.DirIcon"

say "Pre-compiling Python bytecode (the AppImage is read-only at run time)"
"$PY" -I -m compileall -q -j 0 "$APPDIR/usr/python/lib" >/dev/null || true

# ------------------------------------------------------------------------------------ 6. Smoke test
say "Smoke-testing the bundled app (offscreen)"
tmp=$(mktemp -d)
QT_QPA_PLATFORM=offscreen XDG_DATA_HOME="$tmp/d" XDG_CONFIG_HOME="$tmp/c" \
  LD_LIBRARY_PATH="$APPDIR/usr/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
  "$PY" -I "$ROOT/tests/test_qt_smoke.py" || die "smoke test failed; see output above"
rm -rf "$tmp"

# ------------------------------------------------------------------------------------ 7. Pack
if [ -z "${APPIMAGETOOL:-}" ]; then
  APPIMAGETOOL="$CACHE/appimagetool-$ARCH.AppImage"
  if [ ! -s "$APPIMAGETOOL" ]; then
    say "Downloading appimagetool"
    curl -fL --retry 3 -o "$APPIMAGETOOL.part" \
      "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-$ARCH.AppImage"
    mv "$APPIMAGETOOL.part" "$APPIMAGETOOL"
  fi
  chmod +x "$APPIMAGETOOL"
fi

say "Packing $(basename "$OUT")"
rm -f "$OUT"
# Extract-and-run lets appimagetool work even where FUSE isn't available (containers, CI).
APPIMAGE_EXTRACT_AND_RUN=1 ARCH="$ARCH" "$APPIMAGETOOL" "$APPDIR" "$OUT"
chmod +x "$OUT"

say "Done: $OUT ($(du -h "$OUT" | cut -f1))"
echo "Run it with:  $OUT"
