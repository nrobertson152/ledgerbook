"""Ctrl+K command palette: jump to a logbook or run any action."""
from PySide6.QtCore import QEvent, QSize, Qt, QTimer
from PySide6.QtWidgets import QDialog, QFrame, QLineEdit, QListWidget, QListWidgetItem

from . import icons, theme
from .widgets import hbox, icon_label, label, vbox

T = theme.current


class CommandPalette(QDialog):
    """``items`` is a list of dicts: title, subtitle, icon (icon name), action (callable)."""

    def __init__(self, parent, items):
        super().__init__(parent)
        self.setObjectName('palette')
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setModal(True)
        self.setFixedSize(640, 460)
        self.items = items
        self.chosen = None
        lay = vbox(self, (0, 0, 0, 0), 0)
        bar = QFrame()
        bar.setObjectName('paletteInput')
        bl = hbox(bar, (20, 14, 20, 14), 12)
        bl.addWidget(icon_label('search', 'faint', 18))
        self.edit = QLineEdit()
        self.edit.setPlaceholderText('Search logbooks and actions…')
        self.edit.textChanged.connect(self.populate)
        self.edit.installEventFilter(self)
        bl.addWidget(self.edit, 1)
        lay.addWidget(bar)
        self.list = QListWidget()
        self.list.setIconSize(QSize(20, 20))
        self.list.itemActivated.connect(self._pick)
        self.list.itemClicked.connect(self._pick)
        lay.addWidget(self.list, 1)
        foot = QFrame()
        foot.setObjectName('paletteFoot')
        fl = hbox(foot, (18, 9, 18, 9), 8)
        for key, text in (('↑↓', 'navigate'), ('↵', 'open'), ('Esc', 'close')):
            fl.addWidget(label(key, 'kbd'))
            fl.addWidget(label(text, 'faint'))
            fl.addSpacing(10)
        fl.addStretch(1)
        lay.addWidget(foot)
        self.populate('')
        QTimer.singleShot(0, self.edit.setFocus)

    def populate(self, query):
        self.list.clear()
        tokens = query.casefold().split()
        t = T()
        shown = 0
        for it in self.items:
            hay = (it['title'] + ' ' + it.get('subtitle', '')).casefold()
            if all(tok in hay for tok in tokens):
                text = it['title'] + (('\n' + it['subtitle']) if it.get('subtitle') else '')
                row = QListWidgetItem(icons.icon(it.get('icon', 'search'), t['accent'], 20), text)
                row.setData(Qt.ItemDataRole.UserRole, it)
                row.setSizeHint(QSize(0, 52 if it.get('subtitle') else 42))
                self.list.addItem(row)
                shown += 1
                if shown >= 60:
                    break
        if self.list.count():
            self.list.setCurrentRow(0)

    def eventFilter(self, obj, ev):
        if obj is self.edit and ev.type() == QEvent.Type.KeyPress:
            key = ev.key()
            if key in (Qt.Key.Key_Down, Qt.Key.Key_Up) and self.list.count():
                step = 1 if key == Qt.Key.Key_Down else -1
                self.list.setCurrentRow(max(0, min(self.list.count() - 1, self.list.currentRow() + step)))
                return True
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if self.list.currentItem() is not None:
                    self._pick(self.list.currentItem())
                return True
        return super().eventFilter(obj, ev)

    def _pick(self, row):
        self.chosen = row.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def showEvent(self, ev):
        super().showEvent(ev)
        par = self.parentWidget()
        if par is not None:
            win = par.window()
            c = win.mapToGlobal(win.rect().center())
            self.move(c.x() - self.width() // 2, c.y() - self.height() // 2 - 70)

    def run(self):
        self.exec()
        return self.chosen['action'] if self.chosen else None
