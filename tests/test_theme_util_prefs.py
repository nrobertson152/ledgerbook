"""Qt-free tests: theme contrast, helpers, preferences, version consistency, overview queries."""
import re
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from ledgerbook import VERSION, __version__, prefs, theme, util
from ledgerbook.store import Store


class ThemeContrast(unittest.TestCase):
    def test_all_themes_readable(self):
        self.assertEqual(sorted(theme.THEMES), sorted(['Midnight', 'Graphite', 'Terracotta', 'Light']))
        for name, t in theme.THEMES.items():
            with self.subTest(theme=name):
                self.assertGreaterEqual(theme.contrast(t['text'], t['bg']), 7)
                self.assertGreaterEqual(theme.contrast(t['text'], t['surface']), 7)
                self.assertGreaterEqual(theme.contrast(t['muted'], t['surface']), 4.5)
                self.assertGreaterEqual(theme.contrast(t['faint'], t['surface']), 3.4)
                self.assertGreaterEqual(theme.contrast(t['on_accent'], t['accent']), 4.5)

    def test_hex_helpers(self):
        self.assertTrue(theme.valid_hex('#4f8cff'))
        self.assertFalse(theme.valid_hex('blue'))
        self.assertTrue(theme.valid_hex(theme.book_color(3, '')))


class Helpers(unittest.TestCase):
    def test_plural_and_dates(self):
        self.assertEqual(util.plural(1, 'entry', 'entries'), '1 entry')
        self.assertEqual(util.plural(2, 'entry', 'entries'), '2 entries')
        today = date.today()
        self.assertEqual(util.relative_day(today.isoformat()), 'Today')
        self.assertEqual(util.relative_day((today - timedelta(days=1)).isoformat()), 'Yesterday')
        self.assertTrue(util.is_true('true') and not util.is_true('false'))
        self.assertIn('KB', util.human_size(2048))


class Prefs(unittest.TestCase):
    def test_roundtrip_and_recent(self):
        with tempfile.TemporaryDirectory() as d:
            p = prefs.Prefs(Path(d) / 's.json')
            p.set('theme', 'Light')
            self.assertTrue(p.toggle_in('pinned_books', 4))
            self.assertFalse(p.toggle_in('pinned_books', 4))
            p.touch_recent(2); p.touch_recent(5); p.touch_recent(2)
            q = prefs.Prefs(Path(d) / 's.json')
            self.assertEqual(q.get('theme'), 'Light')
            self.assertEqual(q.data['recent_books'][:2], [2, 5])


class Overview(unittest.TestCase):
    def test_overview_counts(self):
        with tempfile.TemporaryDirectory() as d:
            s = Store(Path(d) / 'db.sqlite3')
            b = s.add_book('Car')
            s.save_entry(b, {'title': 'Oil'})
            o = s.overview()
            self.assertIsNotNone(o)
            s.close()


class Versions(unittest.TestCase):
    def test_everything_says_1_0_0(self):
        self.assertEqual((__version__, VERSION), ('1.0.0', '1.0.0'))
        self.assertIn("VERSION = '1.0.0'", (ROOT / 'installer.py').read_text())
        self.assertIn('Ledgerbook 1.0.0', (ROOT / 'README.md').read_text())
        for py in (ROOT / 'ledgerbook').glob('*.py'):
            self.assertNotRegex(py.read_text(), r'Beta \d\.\d', py.name)


if __name__ == '__main__':
    unittest.main()
