"""Reusable, theme-aware building blocks: layout helpers, buttons, tiles, search box and toast."""
from PySide6.QtCore import QEvent, QPropertyAnimation, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import (QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSizePolicy,
                               QVBoxLayout, QWidget)

from . import icons, theme

T = theme.current


# --------------------------------------------------------------------------------------- layout helpers
def hbox(parent=None, margins=(0, 0, 0, 0), spacing=8):
    lay = QHBoxLayout(parent) if parent is not None else QHBoxLayout()
    lay.setContentsMargins(*margins)
    lay.setSpacing(spacing)
    return lay


def vbox(parent=None, margins=(0, 0, 0, 0), spacing=8):
    lay = QVBoxLayout(parent) if parent is not None else QVBoxLayout()
    lay.setContentsMargins(*margins)
    lay.setSpacing(spacing)
    return lay


def label(text='', kind=None, wrap=False, selectable=False):
    lab = QLabel(text)
    if kind:
        lab.setObjectName(kind)
    lab.setWordWrap(wrap)
    if selectable:
        lab.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return lab


def divider():
    d = QFrame()
    d.setObjectName('divider')
    d.setFrameShape(QFrame.Shape.NoFrame)
    return d


# --------------------------------------------------------------------------------------- icons on buttons
_ROLE_BY_KIND = {'': 'text', 'primary': 'on_accent', 'ghost': 'muted', 'danger': 'bad', 'dangerSolid': 'on_accent',
                 'navBtn': 'muted', 'iconBtn': 'muted'}


def _apply_icon(btn):
    name, role = btn.property('iconName'), btn.property('iconRole') or 'text'
    if name:
        color = '#ffffff' if role == 'white' else T().get(role, T()['text'])
        btn.setIcon(icons.icon(name, color, int(btn.property('iconPx') or 16)))


def set_button_icon(btn, name, role=None, px=16):
    btn.setProperty('iconName', name)
    btn.setProperty('iconRole', role or _ROLE_BY_KIND.get(btn.objectName(), 'text'))
    btn.setProperty('iconPx', px)
    btn.setIconSize(QSize(px, px))
    _apply_icon(btn)


def button(text='', kind='', icon=None, cb=None, tip=None):
    """kind: '' | 'primary' | 'ghost' | 'danger' | 'dangerSolid'."""
    b = QPushButton(text)
    if kind:
        b.setObjectName(kind)
    if icon:
        set_button_icon(b, icon)
    if cb:
        b.clicked.connect(lambda checked=False: cb())
    if tip:
        b.setToolTip(tip)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setFocusPolicy(Qt.FocusPolicy.TabFocus)
    return b


def icon_button(name, tip='', cb=None, size=36, px=18, role='muted'):
    b = QPushButton()
    b.setObjectName('iconBtn')
    set_button_icon(b, name, role, px)
    b.setFixedSize(size, size)
    b.setToolTip(tip)
    b.setAccessibleName(tip or name)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setFocusPolicy(Qt.FocusPolicy.TabFocus)
    if cb:
        b.clicked.connect(lambda checked=False: cb())
    return b


def icon_label(name, role='muted', px=16):
    lab = QLabel()
    lab.setFixedSize(px + 2, px + 2)
    lab.setProperty('iconName', name)
    lab.setProperty('iconRole', role)
    lab.setProperty('iconPx', px)
    lab.setPixmap(icons.pixmap(name, T().get(role, T()['muted']), px))
    return lab


def retint(root):
    """Re-colour every icon under ``root`` after a theme change."""
    for b in root.findChildren(QPushButton):
        if b.property('iconName'):
            _apply_icon(b)
    for lab in root.findChildren(QLabel):
        name = lab.property('iconName')
        if name:
            lab.setPixmap(icons.pixmap(name, T().get(lab.property('iconRole') or 'muted', T()['muted']),
                                       int(lab.property('iconPx') or 16)))
    for w in root.findChildren(QWidget):
        if hasattr(w, 'theme_changed'):
            w.theme_changed()
        w.update()


def fade_in(widget, ms=180):
    """Fade a widget in; the effect is removed afterwards so it never interferes with painting."""
    try:
        fx = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(fx)
        anim = QPropertyAnimation(fx, b'opacity', widget)
        anim.setDuration(ms)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.finished.connect(lambda: widget.setGraphicsEffect(None))
        anim.start()
        widget._fade_anim = anim
    except RuntimeError:
        pass


# --------------------------------------------------------------------------------------- simple widgets
class Pill(QLabel):
    def __init__(self, text, kind='pill'):
        super().__init__(text)
        self.setObjectName(kind)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)


class Card(QFrame):
    """A rounded surface. ``body`` is the vertical layout to add content to."""

    def __init__(self, padding=20, spacing=12, name='card'):
        super().__init__()
        self.setObjectName(name)
        self.body = vbox(self, (padding, padding, padding, padding), spacing)


class ClickCard(QFrame):
    """A card that behaves like a button."""
    clicked = Signal()

    def __init__(self, padding=16, spacing=10):
        super().__init__()
        self.setObjectName('cardLink')
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.body = vbox(self, (padding, padding, padding, padding), spacing)

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton and self.rect().contains(ev.position().toPoint()):
            self.clicked.emit()
        super().mouseReleaseEvent(ev)

    def keyPressEvent(self, ev):
        if ev.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.clicked.emit()
        else:
            super().keyPressEvent(ev)


class IconTile(QWidget):
    """Rounded square tinted with a colour; shows an emoji/glyph or a line icon."""

    def __init__(self, size=40, glyph='', icon_name='', color=None):
        super().__init__()
        self.glyph, self.icon_name, self.color = glyph, icon_name, color
        self.px = size
        self.setFixedSize(size, size)

    def configure(self, glyph='', icon_name='', color=None):
        self.glyph, self.icon_name, self.color = glyph, icon_name, color
        self.update()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = T()
        base = QColor(self.color or t['accent'])
        fill = QColor(base)
        fill.setAlpha(52 if t['dark'] else 40)
        edge = QColor(base)
        edge.setAlpha(110)
        p.setBrush(fill)
        p.setPen(QPen(edge, 1))
        r = self.rect().adjusted(1, 1, -1, -1)
        p.drawRoundedRect(r, self.px * 0.3, self.px * 0.3)
        if self.glyph:
            font = QFont(self.font())
            font.setPixelSize(max(10, int(self.px * 0.48)))
            p.setFont(font)
            p.setPen(QColor(t['text']))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.glyph)
        elif self.icon_name:
            sz = int(self.px * 0.5)
            pm = icons.pixmap(self.icon_name, base.name(), sz)
            p.drawPixmap((self.width() - sz) // 2, (self.height() - sz) // 2, pm)
        p.end()


class BrandMark(QWidget):
    """Gradient app mark with a book glyph."""

    def __init__(self, size=34):
        super().__init__()
        self.px = size
        self.setFixedSize(size, size)

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = T()
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0, QColor(t['accent']))
        grad.setColorAt(1, QColor(t['accent2']))
        p.setBrush(grad)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(self.rect(), self.px * 0.3, self.px * 0.3)
        sz = int(self.px * 0.56)
        p.drawPixmap((self.width() - sz) // 2, (self.height() - sz) // 2,
                     icons.pixmap('book', t['on_accent'], sz, stroke=2.0))
        p.end()


class SearchBox(QFrame):
    """Search field with icon and clear button."""
    textChanged = Signal(str)

    def __init__(self, placeholder='Search…', height=40):
        super().__init__()
        self.setObjectName('searchbox')
        self.setProperty('focused', False)
        self.setFixedHeight(height)
        lay = hbox(self, (12, 0, 6, 0), 8)
        lay.addWidget(icon_label('search', 'faint', 16))
        self.edit = QLineEdit()
        self.edit.setPlaceholderText(placeholder)
        self.edit.setClearButtonEnabled(False)
        self.edit.installEventFilter(self)
        self.edit.textChanged.connect(self._changed)
        lay.addWidget(self.edit, 1)
        self.clear_btn = icon_button('x', 'Clear', self.clear, 26, 14)
        self.clear_btn.hide()
        lay.addWidget(self.clear_btn)

    def eventFilter(self, obj, ev):
        if obj is self.edit and ev.type() in (QEvent.Type.FocusIn, QEvent.Type.FocusOut):
            self.setProperty('focused', ev.type() == QEvent.Type.FocusIn)
            self.style().unpolish(self)
            self.style().polish(self)
        return super().eventFilter(obj, ev)

    def _changed(self, text):
        self.clear_btn.setVisible(bool(text))
        self.textChanged.emit(text)

    def text(self):
        return self.edit.text()

    def setText(self, text):
        self.edit.setText(text)

    def clear(self):
        self.edit.clear()

    def focus(self):
        self.edit.setFocus()
        self.edit.selectAll()


class Toast(QFrame):
    """Transient message pill anchored to the bottom centre of the window, with an optional action (e.g. Undo)."""

    def __init__(self, parent):
        super().__init__(parent)
        self._icon = QLabel()
        self._icon.setFixedSize(18, 18)
        self._text = QLabel()
        self._action = QPushButton()
        self._action.setObjectName('linkBtn')
        self._action.setCursor(Qt.CursorShape.PointingHandCursor)
        self._action.clicked.connect(self._run_action)
        self._callback = None
        lay = hbox(self, (16, 10, 12, 10), 10)
        lay.addWidget(self._icon)
        lay.addWidget(self._text)
        lay.addWidget(self._action)
        self._fx = QGraphicsOpacityEffect(self)
        self._fx.setOpacity(0.0)
        self.setGraphicsEffect(self._fx)
        self._anim = QPropertyAnimation(self._fx, b'opacity', self)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._hide)
        self.hide()

    def show_message(self, text, kind='good', action=None, callback=None):
        t = T()
        self.setStyleSheet('QFrame { background: %s; border: 1px solid %s; border-radius: 12px; } '
                           'QLabel { background: transparent; border: 0; } '
                           'QPushButton { border: 0; background: transparent; }' % (t['raised'], t['border2']))
        color = {'good': t['good'], 'bad': t['bad'], 'info': t['accent']}.get(kind, t['accent'])
        name = {'good': 'check_circle', 'bad': 'x_circle', 'info': 'info'}.get(kind, 'info')
        self._icon.setPixmap(icons.pixmap(name, color, 18))
        self._text.setText(text)
        self._callback = callback
        self._action.setVisible(bool(action))
        self._action.setText(action or '')
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, not action)
        self.adjustSize()
        self.reposition()
        self.show()
        self.raise_()
        self._anim.stop()
        self._anim.setDuration(160)
        self._anim.setStartValue(self._fx.opacity())
        self._anim.setEndValue(1.0)
        self._anim.start()
        self._timer.start(6000 if action else 2600)

    def _run_action(self):
        cb, self._callback = self._callback, None
        self._hide()
        if cb:
            cb()

    def reposition(self):
        par = self.parentWidget()
        if par is not None:
            self.move(int((par.width() - self.width()) / 2), par.height() - self.height() - 36)

    def _hide(self):
        self._anim.stop()
        self._anim.setDuration(240)
        self._anim.setStartValue(self._fx.opacity())
        self._anim.setEndValue(0.0)
        self._anim.finished.connect(self._after_hide)
        self._anim.start()

    def _after_hide(self):
        try:
            self._anim.finished.disconnect(self._after_hide)
        except (RuntimeError, TypeError):
            pass
        if self._fx.opacity() <= 0.01:
            self.hide()
