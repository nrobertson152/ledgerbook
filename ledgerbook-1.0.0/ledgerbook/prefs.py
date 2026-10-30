"""User preferences: the same ``settings.json`` file and keys as earlier releases (Qt-free)."""
import json
import os
from pathlib import Path


def pref_path():
    base = os.environ.get('XDG_CONFIG_HOME') or str(Path.home() / '.config')
    return Path(base) / 'ledgerbook' / 'settings.json'


class Prefs:
    """Tiny JSON-backed key/value store. Unknown keys written by older versions are preserved."""

    def __init__(self, path=None):
        self.path = Path(path) if path else pref_path()
        self.data = self._read()

    def _read(self):
        try:
            loaded = json.loads(self.path.read_text(encoding='utf-8'))
            return loaded if isinstance(loaded, dict) else {}
        except (OSError, ValueError):
            return {}

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value, save=True):
        self.data[key] = value
        if save:
            self.save()

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix('.tmp')
            tmp.write_text(json.dumps(self.data, indent=2), encoding='utf-8')
            tmp.replace(self.path)
        except OSError:
            pass

    # list helpers -----------------------------------------------------------------------------
    def id_list(self, key):
        return [str(x) for x in self.data.get(key, [])]

    def toggle_in(self, key, ident):
        """Add/remove `ident` at the front of a list preference. Returns True when it is now present."""
        items = self.id_list(key)
        ident = str(ident)
        if ident in items:
            items.remove(ident)
            present = False
        else:
            items.insert(0, ident)
            present = True
        self.set(key, items)
        return present

    def touch_recent(self, book_id, limit=200):
        recent = [int(x) for x in self.data.get('recent_books', []) if str(x).isdigit()]
        self.set('recent_books', [int(book_id)] + [i for i in recent if i != int(book_id)][:limit - 1])
