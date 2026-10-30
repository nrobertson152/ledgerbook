"""Left navigation: brand, logbook filter, the custom-painted logbook/folder tree and quick links."""
from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QFrame, QPushButton, QStyle, QStyledItemDelegate, QTreeWidget

from . import __version__, icons, theme
from .widgets import BrandMark, Pill, SearchBox, button, hbox, icon_button, icon_label, label, vbox

T = theme.current

R_KIND = Qt.ItemDataRole.UserRole           # ('book' | 'folder', id): unchanged from earlier releases
R_NAME = Qt.ItemDataRole.UserRole + 1
R_GLYPH = Qt.ItemDataRole.UserRole + 2
R_COLOR = Qt.ItemDataRole.UserRole + 3
R_COUNT = Qt.ItemDataRole.UserRole + 4
R_PIN = Qt.ItemDataRole.UserRole + 5
ROW_HEIGHT = 42


class TreeDelegate(QStyledItemDelegate):
    """Paints folders (chevron + icon) and logbooks (coloured symbol tile) with count badges."""

    def __init__(self, tree):
        super().__init__(tree)
        self.tree = tree

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), ROW_HEIGHT)

    def paint(self, painter, option, index):
        t = T()
        data = index.data(R_KIND)
        if not data:
            return
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = option.rect.adjusted(4, 2, -4, -2)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        if selected or hovered:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(t['accent_soft'] if selected else t['hover']))
            painter.drawRoundedRect(QRectF(rect), 10, 10)
        if selected:
            painter.setBrush(QColor(t['accent']))
            painter.drawRoundedRect(QRectF(rect.left(), rect.top() + 9, 3, rect.height() - 18), 1.5, 1.5)
        cy = rect.center().y()
        x = rect.left() + 12
        name = str(index.data(R_NAME) or '')
        count = index.data(R_COUNT)
        pinned = bool(index.data(R_PIN))
        # right-hand badges first, so the name can use the remaining width
        right = rect.right() - 10
        font = QFont(painter.font())
        font.setPixelSize(11)
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        fm = QFontMetrics(font)
        if count is not None:
            txt = str(count)
            w = fm.horizontalAdvance(txt)
            painter.setPen(QColor(t['faint']))
            painter.drawText(right - w, cy + fm.ascent() // 2 - 1, txt)
            right -= w + 8
        if pinned:
            painter.drawPixmap(right - 12, cy - 6, icons.pixmap('pin', t['accent'], 12, filled=True))
            right -= 18
        if data[0] == 'folder':
            opened = self.tree.isExpanded(index)
            painter.drawPixmap(x, cy - 7, icons.pixmap('chevron_down' if opened else 'chevron_right', t['faint'], 14))
            x += 20
            painter.drawPixmap(x, cy - 9, icons.pixmap('folder', t['muted'], 18))
            x += 28
            weight = QFont.Weight.DemiBold
        else:
            x += 6
            base = QColor(index.data(R_COLOR) or t['accent'])
            fill = QColor(base)
            fill.setAlpha(52 if t['dark'] else 40)
            edge = QColor(base)
            edge.setAlpha(110)
            painter.setBrush(fill)
            painter.setPen(QPen(edge, 1))
            painter.drawRoundedRect(QRectF(x, cy - 14, 28, 28), 8, 8)
            glyph_font = QFont(painter.font())
            glyph_font.setPixelSize(14)
            painter.setFont(glyph_font)
            painter.setPen(QColor(t['text']))
            painter.drawText(QRectF(x, cy - 14, 28, 28), Qt.AlignmentFlag.AlignCenter, str(index.data(R_GLYPH) or ''))
            x += 38
            weight = QFont.Weight.DemiBold if selected else QFont.Weight.Medium
        name_font = QFont(painter.font())
        name_font.setPixelSize(13)
        name_font.setWeight(weight)
        painter.setFont(name_font)
        strong = selected or hovered or data[0] == 'folder'
        painter.setPen(QColor(t['text'] if strong else t['muted']))
        room = max(10, right - x - 6)
        text = QFontMetrics(name_font).elidedText(name, Qt.TextElideMode.ElideRight, room)
        painter.drawText(x, cy + QFontMetrics(name_font).ascent() // 2 - 1, text)
        painter.restore()


class LogbookTree(QTreeWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName('sidebarTree')
        self.setHeaderHidden(True)
        self.setRootIsDecorated(False)
        self.setIndentation(16)
        self.setUniformRowHeights(True)
        self.setMouseTracking(True)
        self.setExpandsOnDoubleClick(False)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setEditTriggers(QTreeWidget.EditTrigger.NoEditTriggers)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setItemDelegate(TreeDelegate(self))

    def theme_changed(self):
        self.viewport().update()


class NavRow(QPushButton):
    """Quick-link row (icon, text and a count badge)."""

    def __init__(self, icon_name, text, callback):
        super().__init__()
        self.setObjectName('navBtn')
        self.setFixedHeight(38)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        lay = hbox(self, (12, 0, 10, 0), 10)
        self.icon = icon_label(icon_name, 'muted', 16)
        self.text = label(text)
        self.badge = Pill('0', 'pillMuted')
        for w in (self.icon, self.text, self.badge):
            w.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lay.addWidget(self.icon)
        lay.addWidget(self.text, 1)
        lay.addWidget(self.badge)
        self.badge.hide()
        self.clicked.connect(lambda checked=False: callback())

    def set_count(self, n):
        self.badge.setText(str(n))
        self.badge.setVisible(n > 0)


class Sidebar(QFrame):
    """Composite sidebar. All behaviour lives in callbacks supplied by the main window."""
    WIDTH = 296

    def __init__(self, on_new_logbook, on_new_folder, on_collapse, on_filter, on_archive, on_recycle, on_settings):
        super().__init__()
        self.setObjectName('sidebar')
        self.setFixedWidth(self.WIDTH)
        lay = vbox(self, (14, 16, 14, 14), 12)
        head = hbox(None, (4, 0, 0, 0), 10)
        head.addWidget(BrandMark(34))
        names = vbox(None, (0, 0, 0, 0), 0)
        names.addWidget(label('Ledgerbook', 'brandName'))
        names.addWidget(label('Version %s' % __version__, 'faint'))
        head.addLayout(names, 1)
        head.addWidget(icon_button('sidebar', 'Hide sidebar  (Ctrl+B)', on_collapse, 34, 18))
        lay.addLayout(head)
        self.filter = SearchBox('Filter logbooks…', 38)
        self.filter.textChanged.connect(on_filter)
        lay.addWidget(self.filter)
        actions = hbox(None, (0, 0, 0, 0), 8)
        self.new_btn = button('New logbook', 'primary', 'book_plus', on_new_logbook)
        self.new_btn.setMinimumHeight(40)
        actions.addWidget(self.new_btn, 1)
        actions.addWidget(icon_button('folder_plus', 'New folder', on_new_folder, 40, 18, 'text'))
        lay.addLayout(actions)
        lay.addWidget(label('LIBRARY', 'eyebrow'))
        self.tree = LogbookTree()
        lay.addWidget(self.tree, 1)
        self.archive_row = NavRow('archive', 'Archived logbooks', on_archive)
        self.recycle_row = NavRow('trash', 'Recycle Bin', on_recycle)
        self.settings_row = NavRow('sliders', 'Settings', on_settings)
        for row in (self.archive_row, self.recycle_row, self.settings_row):
            lay.addWidget(row)

    def set_counts(self, archived, recycled):
        self.archive_row.set_count(archived)
        self.recycle_row.set_count(recycled)
