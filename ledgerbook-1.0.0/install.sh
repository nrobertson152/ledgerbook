#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ENV="$HOME/.local/share/ledgerbook/installer-venv"
if ! command -v python3 >/dev/null 2>&1; then
 echo 'Python 3 is required. On Linux Mint: sudo apt install python3 python3-venv' >&2
 exit 1
fi
# Linux Mint / Ubuntu: Qt needs the xcb cursor library even when the Python wheel is installed.
if command -v dpkg-query >/dev/null 2>&1 && ! dpkg-query -W -f='${Status}' libxcb-cursor0 2>/dev/null | grep -q 'install ok installed'; then
 echo 'Ledgerbook requires the Qt XCB cursor system library.'
 echo 'Installing libxcb-cursor0 using apt (administrator permission required).'
 sudo apt-get update
 sudo apt-get install -y libxcb-cursor0 libxkbcommon-x11-0 libxcb-xinerama0
fi
if [ ! -x "$ENV/bin/python" ]; then
 python3 -m venv "$ENV" || { echo 'Install python3-venv: sudo apt install python3-venv' >&2; exit 1; }
fi
"$ENV/bin/python" -m pip install --disable-pip-version-check 'PySide6-Essentials>=6.7,<7'
exec "$ENV/bin/python" "$HERE/installer.py"
