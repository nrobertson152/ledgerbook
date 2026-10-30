#!/usr/bin/env python3
"""Seeds a throw-away profile and saves screenshots of every main screen in every theme to ./screenshots.
Run:  python3 tests_gui.py        (needs PySide6; works offscreen)"""
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
tmp = tempfile.mkdtemp()
os.environ['XDG_DATA_HOME'] = tmp + '/data'
os.environ['XDG_CONFIG_HOME'] = tmp + '/config'
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication  # noqa: E402

from ledgerbook import app as A  # noqa: E402

qt = QApplication.instance() or QApplication([])
w = A.Main()
w.resize(1360, 860)
w.show()
out = Path(__file__).parent / 'screenshots'
out.mkdir(exist_ok=True)
fid = w.store.add_folder('Workshop')
seed = [('Vehicle maintenance', '🚗'), ('3D printer', '▤'), ('Garden', '✿')]
for i, (name, _icon) in enumerate(seed):
    bid = w.store.add_book(name, 'Sample logbook %d' % (i + 1))
    if i == 0:
        w.store.configure_book(bid, folder_id=fid)
    for n in range(14):
        w.store.save_entry(bid, {'entry_date': '2026-10-%02d' % (n + 1), 'title': '%s task %d' % (name, n + 1),
                                 'notes': 'Replaced part and checked everything.\nSecond line of notes.' * (n % 3 + 1)})
w.reload_tree(fresh=True)


def shot(name):
    qt.processEvents()
    w.grab().save(str(out / (name + '.png')))


for theme_name in ('Midnight', 'Graphite', 'Terracotta', 'Light'):
    w.change_theme(theme_name)
    w.go_home(); shot('%s-home' % theme_name)
    first = w.store.books()[0]['id']
    w.select_book(first); shot('%s-logbook' % theme_name)
    w.view.search.edit.setText('zzzz'); qt.processEvents(); shot('%s-no-results' % theme_name)
    w.view.search.edit.setText('')
print('Saved screenshots to', out)
