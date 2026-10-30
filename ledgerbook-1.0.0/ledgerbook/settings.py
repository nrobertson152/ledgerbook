"""Settings (non-modal) and About dialogs."""
from pathlib import Path

from PySide6.QtCore import QRectF, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QFont, QPainter, QPen
from PySide6.QtWidgets import QGridLayout, QTextBrowser, QWidget

from . import VERSION, theme
from .constants import LICENSE_NOTICE, LICENSE_URL
from .dialogs import Panel, size_button
from .util import human_size
from .widgets import BrandMark, ClickCard, IconTile, button, hbox, label, retint, vbox

T = theme.current


class ThemeCard(QWidget):
    """Clickable miniature preview of a theme."""
    clicked = Signal(str)

    def __init__(self, name):
        super().__init__()
        self.name, self.selected = name, False
        self.setFixedSize(138, 112)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(name)

    def set_selected(self, on):
        self.selected = on
        self.update()

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.name)

    def paintEvent(self, ev):
        t = theme.THEMES[self.name]
        cur = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        box = QRectF(2, 2, self.width() - 4, 84)
        p.setPen(QPen(QColor(cur['accent'] if self.selected else cur['border']), 2 if self.selected else 1))
        p.setBrush(QColor(t['bg']))
        p.drawRoundedRect(box, 12, 12)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(t['side']))
        p.drawRoundedRect(QRectF(8, 8, 34, 72), 8, 8)
        for i in range(3):
            p.setBrush(QColor(t['border2']))
            p.drawRoundedRect(QRectF(14, 18 + i * 14, 22, 6), 3, 3)
        p.setBrush(QColor(t['surface']))
        p.drawRoundedRect(QRectF(50, 8, box.width() - 56, 72), 8, 8)
        p.setBrush(QColor(t['accent']))
        p.drawRoundedRect(QRectF(58, 17, 40, 8), 4, 4)
        p.setBrush(QColor(t['border']))
        for i in range(3):
            p.drawRoundedRect(QRectF(58, 34 + i * 12, box.width() - 72, 6), 3, 3)
        font = QFont(self.font())
        font.setPixelSize(12)
        font.setWeight(QFont.Weight.DemiBold)
        p.setFont(font)
        p.setPen(QColor(cur['text']))
        p.drawText(QRectF(0, 90, self.width(), 20), Qt.AlignmentFlag.AlignCenter, self.name)
        p.end()


class SettingsDialog(Panel):
    def __init__(self, win):
        super().__init__(win, 'Settings', 'Appearance, your data, and everything in between.', 720, 740,
                         modal=False, scrolling=True)
        self.win = win
        self.setObjectName('settings')
        # ---- appearance
        self.body.addWidget(label('Appearance', 'h2'))
        row = hbox(None, (0, 0, 0, 0), 14)
        self.cards = {}
        for name in theme.THEMES:
            card = ThemeCard(name)
            card.set_selected(name == win.theme)
            card.clicked.connect(self._pick_theme)
            self.cards[name] = card
            row.addWidget(card)
        row.addStretch(1)
        self.body.addLayout(row)
        # ---- data
        self.body.addSpacing(6)
        self.body.addWidget(label('Data and portability', 'h2'))
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        actions = [
            ('upload', 'Import logbook', 'Add a logbook from a .ledgerbook file', win.import_book),
            ('download', 'Export logbook', 'Save the open logbook as a .ledgerbook file', win.export_book),
            ('inbox', 'Import CSV', 'Add rows to the open logbook', win.import_csv),
            ('table', 'Export CSV', 'Spreadsheet-friendly copy of the open logbook', win.export_csv),
            ('file', 'PDF report', 'Choose columns and rows for a printable report', win.export_pdf),
            ('database', 'Back up database', 'Save a complete copy of everything', win.backup),
            ('reset', 'Restore backup', 'Replace the library with a saved backup', win.restore_backup),
            ('shield', 'Integrity check', 'Verify the database is healthy', win.integrity_check),
            ('archive', 'Archived logbooks', 'Bring hidden logbooks back', win.archived_books),
            ('trash', 'Recycle Bin', 'Restore deleted entries and logbooks', win.recycle_bin),
        ]
        for n, (icon_name, title, text, cb) in enumerate(actions):
            grid.addWidget(self._tile(icon_name, title, text, cb), n // 2, n % 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        self.body.addLayout(grid)
        # ---- storage
        self.body.addSpacing(6)
        self.body.addWidget(label('Storage', 'h2'))
        store_path = Path(win.store.path)
        size = human_size(store_path.stat().st_size) if store_path.exists() else '—'
        self.body.addWidget(label('Database  ·  %s' % size, 'h3'))
        self.body.addWidget(label(str(store_path), 'mono', wrap=True, selectable=True))
        folder = store_path.parent
        links = hbox(None, (0, 4, 0, 0), 10)
        links.addWidget(button('Open data folder', '', 'folder',
                               lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))))
        links.addWidget(button('Open backups folder', '', 'folder',
                               lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder / 'backups')))))
        links.addStretch(1)
        self.body.addLayout(links)
        self.body.addWidget(label('A backup is also saved automatically once a day; the newest seven are kept.',
                                  'faint', wrap=True))
        # ---- about
        self.body.addSpacing(6)
        self.body.addWidget(label('About', 'h2'))
        about = hbox(None, (0, 0, 0, 0), 10)
        about.addWidget(button('About Ledgerbook', '', 'info', win.about))
        about.addWidget(button('What’s new', '', 'sparkle', win.show_whats_new_now))
        about.addStretch(1)
        self.body.addLayout(about)
        self.body.addStretch(1)
        self.foot.addStretch(1)
        self.foot.addWidget(label(VERSION, 'faint'))
        self.foot.addWidget(size_button(button('Close', 'primary', None, self.close)))

    def _tile(self, icon_name, title, text, cb):
        card = ClickCard(14, 8)
        row = hbox(None, (0, 0, 0, 0), 12)
        row.addWidget(IconTile(36, '', icon_name), 0, Qt.AlignmentFlag.AlignTop)
        col = vbox(None, (0, 0, 0, 0), 2)
        col.addWidget(label(title, 'h3'))
        col.addWidget(label(text, 'faint', wrap=True))
        row.addLayout(col, 1)
        card.body.addLayout(row)
        card.clicked.connect(cb)
        return card

    def _pick_theme(self, name):
        self.win.change_theme(name)
        for key, card in self.cards.items():
            card.set_selected(key == name)
        retint(self)


class AboutDialog(Panel):
    def __init__(self, parent):
        super().__init__(parent, 'About Ledgerbook', '', 640, 620)
        head = hbox(None, (0, 0, 0, 0), 16)
        head.addWidget(BrandMark(64), 0, Qt.AlignmentFlag.AlignTop)
        col = vbox(None, (0, 0, 0, 0), 3)
        col.addWidget(label('Ledgerbook', 'display'))
        col.addWidget(label('%s  ·  Qt 6 Desktop Edition' % VERSION, 'muted'))
        col.addWidget(label('A private, offline workspace for logbooks, records and maintenance history.', 'muted',
                            wrap=True))
        head.addLayout(col, 1)
        self.body.addLayout(head)
        self.body.addWidget(label('Created and maintained by Nate Robertson  ·  Copyright © 2026', 'h3', wrap=True))
        self.body.addWidget(label('Free and open-source software under the GNU General Public License, version 3 '
                                  '(GPL-3.0-only).', 'muted', wrap=True))
        notice = QTextBrowser()
        notice.setOpenExternalLinks(True)
        notice.setPlainText(LICENSE_NOTICE)
        self.body.addWidget(notice, 1)
        link = button('Read the full GPL-3.0 license', '', 'external',
                      lambda: QDesktopServices.openUrl(QUrl(LICENSE_URL)))
        self.add_buttons('Close', None, None, left=[link])
