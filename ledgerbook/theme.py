"""Design tokens and the global Qt stylesheet.

Every colour in the interface flows from the token dictionaries below. The stylesheet only ever uses opaque
hex colours (blended here in Python), so rendering is identical across Qt styles and platforms. Nothing in this
module needs Qt except ``palette()`` / ``load_fonts()`` / ``apply()`` which import it lazily, so the contrast
rules can be unit-tested anywhere."""
import re
import tempfile
from pathlib import Path

from .icons import svg_markup

HEX = re.compile(r'^#[0-9a-fA-F]{6}$')


def _rgb(h):
    h = h.lstrip('#')
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def mix(a, b, t):
    """Blend colour ``a`` toward ``b`` by fraction ``t`` (0..1). Returns '#rrggbb'."""
    ra, ga, ba = _rgb(a)
    rb, gb, bb = _rgb(b)
    return '#%02x%02x%02x' % (round(ra + (rb - ra) * t), round(ga + (gb - ga) * t), round(ba + (bb - ba) * t))


def luminance(value):
    chans = []
    for c in _rgb(value):
        c = c / 255
        chans.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * chans[0] + 0.7152 * chans[1] + 0.0722 * chans[2]


def contrast(a, b):
    lo, hi = sorted([luminance(a), luminance(b)])
    return (hi + 0.05) / (lo + 0.05)


def valid_hex(value):
    return bool(HEX.match(str(value or '').strip()))


def _theme(name, dark, bg, side, surface, raised, border, text, muted, faint, accent, accent2, on_accent, **extra):
    t = dict(name=name, dark=dark, bg=bg, side=side, surface=surface, raised=raised, border=border,
             text=text, muted=muted, faint=faint, accent=accent, accent2=accent2, on_accent=on_accent,
             good='#34d399' if dark else '#15803d', warn='#fbbf24' if dark else '#b45309',
             bad='#f87171' if dark else '#b91c1c', serif=False)
    t.update(extra)
    t['accent_soft'] = mix(t['surface'], t['accent'], 0.17 if dark else 0.11)
    t['accent_line'] = mix(t['border'], t['accent'], 0.55)
    t['hover'] = mix(t['surface'], t['text'], 0.055)
    t['border2'] = mix(t['border'], t['text'], 0.14)
    t['zebra'] = mix(t['surface'], t['text'], 0.022)
    t['good_soft'] = mix(t['surface'], t['good'], 0.14)
    t['warn_soft'] = mix(t['surface'], t['warn'], 0.14)
    t['bad_soft'] = mix(t['surface'], t['bad'], 0.14)
    return t


THEMES = {
    'Midnight': _theme('Midnight', True, '#0b1020', '#080c18', '#111830', '#17203c', '#232f52',
                       '#e7ecf9', '#9aa8c7', '#7385ab', '#6ea8ff', '#9a8bff', '#08111f'),
    'Graphite': _theme('Graphite', True, '#121315', '#0d0e10', '#191b1e', '#202327', '#2c3035',
                       '#ececee', '#a0a6b0', '#7a828e', '#b69cff', '#e0a3ff', '#14101f'),
    'Terracotta': _theme('Terracotta', False, '#f4eee5', '#ece4d8', '#fffdf9', '#f8f2e9', '#e2d7c6',
                         '#2d2824', '#6f6458', '#83776a', '#a94f33', '#b8592f', '#ffffff', serif=True),
    'Light': _theme('Light', False, '#f3f5f9', '#ffffff', '#ffffff', '#f1f4f9', '#e1e6ee',
                    '#162033', '#566580', '#6d7b92', '#2f6be0', '#5b4be0', '#ffffff'),
}
DEFAULT_THEME = 'Midnight'
_current = dict(THEMES[DEFAULT_THEME])

# Tile colours for logbooks without a custom accent (stable per logbook id).
BOOK_COLORS = ['#5b9dff', '#34d399', '#f59e0b', '#f472b6', '#a78bfa', '#2dd4bf', '#fb7185', '#38bdf8']

SANS = ['Inter', 'Noto Sans', 'Ubuntu', 'Cantarell', 'DejaVu Sans']
SERIF = ['Source Serif 4', 'Noto Serif', 'DejaVu Serif']
MONO = ['JetBrains Mono', 'Cascadia Mono', 'Ubuntu Mono', 'DejaVu Sans Mono', 'Monospace']


def current():
    return _current


def set_current(name):
    global _current
    _current = THEMES.get(name) or THEMES[DEFAULT_THEME]
    return _current


def book_color(book_id, accent=''):
    """The colour of a logbook's tile: its own accent when valid, otherwise a stable palette pick."""
    if valid_hex(accent):
        return accent.strip()
    try:
        return BOOK_COLORS[int(book_id) % len(BOOK_COLORS)]
    except (TypeError, ValueError):
        return BOOK_COLORS[0]


def font_css(families):
    return ', '.join('"%s"' % f for f in families)


def _asset_dir():
    d = Path(tempfile.gettempdir()) / 'ledgerbook-ui-cache'
    d.mkdir(parents=True, exist_ok=True)
    return d


def _svg_file(kind, color, stroke):
    """Small SVG files used by stylesheet ``image: url()`` rules (combo arrows, check marks)."""
    path = _asset_dir() / ('%s-%s.svg' % (kind, color.lstrip('#')))
    if not path.exists():
        path.write_text(svg_markup(kind.split('-')[0] if kind != 'chev' else 'chevron_down', color, stroke=stroke))
    return path.as_posix()


def stylesheet(t):
    heading_font = font_css(SERIF if t['serif'] else SANS)
    arrow = _svg_file('chev', t['muted'], 2.2)
    check = _svg_file('check', t['on_accent'], 3.2)
    return f'''
QMainWindow, QDialog {{ background: {t['bg']}; }}
QWidget {{ color: {t['text']}; font-size: 13px; }}
QLabel {{ background: transparent; }}
QToolTip {{ background: {t['raised']}; color: {t['text']}; border: 1px solid {t['border2']};
           border-radius: 6px; padding: 5px 8px; }}

QFrame#card {{ background: {t['surface']}; border: 1px solid {t['border']}; border-radius: 14px; }}
QFrame#cardLink {{ background: {t['surface']}; border: 1px solid {t['border']}; border-radius: 14px; }}
QFrame#cardLink:hover {{ border: 1px solid {t['accent_line']}; background: {t['hover']}; }}
QFrame#tile {{ background: {t['raised']}; border: 1px solid {t['border']}; border-radius: 12px; }}
QFrame#hero {{ background: {t['accent_soft']}; border: 1px solid {t['accent_line']}; border-radius: 16px; }}
QFrame#selbar {{ background: {t['accent_soft']}; border: 1px solid {t['accent_line']}; border-radius: 12px; }}
QFrame#empty {{ background: transparent; border: 1px dashed {t['border2']}; border-radius: 16px; }}
QFrame#divider {{ background: {t['border']}; border: 0; max-height: 1px; min-height: 1px; }}
QFrame#sidebar {{ background: {t['side']}; border: 0; border-right: 1px solid {t['border']}; }}
QFrame#topbar {{ background: {t['bg']}; border: 0; border-bottom: 1px solid {t['border']}; }}
QFrame#panelHead {{ background: {t['bg']}; border: 0; }}
QFrame#panelFoot {{ background: {t['surface']}; border: 0; border-top: 1px solid {t['border']}; }}
QFrame#errorBar {{ background: {t['bad_soft']}; border: 1px solid {mix(t['border'], t['bad'], .5)}; border-radius: 10px; }}
QFrame#infoBar {{ background: {t['accent_soft']}; border: 1px solid {t['accent_line']}; border-radius: 10px; }}

QLabel#display {{ font-family: {heading_font}; font-size: 30px; font-weight: 700; }}
QLabel#h1 {{ font-family: {heading_font}; font-size: 24px; font-weight: 700; }}
QLabel#h2 {{ font-family: {heading_font}; font-size: 16px; font-weight: 600; }}
QLabel#h3 {{ font-size: 13px; font-weight: 600; }}
QLabel#muted {{ color: {t['muted']}; }}
QLabel#faint {{ color: {t['faint']}; font-size: 12px; }}
QLabel#eyebrow {{ color: {t['faint']}; font-size: 11px; font-weight: 600; }}
QLabel#statValue {{ font-family: {heading_font}; font-size: 30px; font-weight: 700; }}
QLabel#brandName {{ font-family: {heading_font}; font-size: 18px; font-weight: 700; }}
QLabel#mono {{ font-family: {font_css(MONO)}; font-size: 12px; color: {t['muted']}; }}
QLabel#pill {{ background: {t['accent_soft']}; color: {t['accent']}; border-radius: 10px; padding: 3px 10px;
              font-size: 11px; font-weight: 600; }}
QLabel#pillMuted {{ background: {t['raised']}; color: {t['muted']}; border-radius: 10px; padding: 3px 10px;
                   font-size: 11px; font-weight: 600; }}
QLabel#pillGood {{ background: {t['good_soft']}; color: {t['good']}; border-radius: 10px; padding: 3px 10px;
                  font-size: 11px; font-weight: 600; }}
QLabel#pillBad {{ background: {t['bad_soft']}; color: {t['bad']}; border-radius: 10px; padding: 3px 10px;
                 font-size: 11px; font-weight: 600; }}
QLabel#kbd {{ background: {t['raised']}; color: {t['muted']}; border: 1px solid {t['border2']};
             border-radius: 5px; padding: 1px 6px; font-size: 11px; font-weight: 600; }}

QFrame#searchbox {{ background: {t['raised']}; border: 1px solid {t['border']}; border-radius: 11px; }}
QFrame#searchbox:hover {{ border: 1px solid {t['border2']}; }}
QFrame#searchbox[focused="true"] {{ border: 1px solid {t['accent']}; }}
QFrame#searchbox QLineEdit {{ background: transparent; border: 0; padding: 0; font-size: 13px;
                              selection-background-color: {t['accent']}; selection-color: {t['on_accent']}; }}

QLineEdit, QTextEdit, QPlainTextEdit {{ background: {t['raised']}; border: 1px solid {t['border']};
    border-radius: 10px; padding: 9px 12px; selection-background-color: {t['accent']};
    selection-color: {t['on_accent']}; }}
QLineEdit:hover, QTextEdit:hover {{ border: 1px solid {t['border2']}; }}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{ border: 1px solid {t['accent']}; }}
QLineEdit:disabled {{ color: {t['faint']}; }}
QLineEdit[invalid="true"] {{ border: 1px solid {t['bad']}; }}

QComboBox, QDateEdit, QSpinBox {{ background: {t['raised']}; border: 1px solid {t['border']}; border-radius: 10px;
             padding: 0px 12px; min-height: 38px; }}
QComboBox:hover, QDateEdit:hover, QSpinBox:hover {{ border: 1px solid {t['border2']}; }}
QComboBox:focus, QComboBox:on, QDateEdit:focus, QSpinBox:focus {{ border: 1px solid {t['accent']}; }}
QComboBox::drop-down, QDateEdit::drop-down {{ border: 0; width: 28px; subcontrol-origin: padding;
    subcontrol-position: center right; }}
QComboBox::down-arrow, QDateEdit::down-arrow {{ image: url({arrow}); width: 12px; height: 12px; }}
QComboBox QAbstractItemView {{ background: {t['raised']}; border: 1px solid {t['border2']}; border-radius: 8px;
    padding: 4px; outline: 0; selection-background-color: {t['accent_soft']}; selection-color: {t['text']}; }}
QComboBox QAbstractItemView::item {{ min-height: 30px; padding: 2px 8px; border-radius: 6px; }}

QCalendarWidget QWidget {{ background: {t['raised']}; color: {t['text']}; }}
QCalendarWidget QWidget#qt_calendar_navigationbar {{ background: {t['surface']}; border-bottom: 1px solid {t['border']}; }}
QCalendarWidget QToolButton {{ background: transparent; color: {t['text']}; border: 0; border-radius: 7px;
    padding: 4px 8px; font-weight: 600; }}
QCalendarWidget QToolButton:hover {{ background: {t['hover']}; }}
QCalendarWidget QSpinBox {{ min-height: 24px; padding: 0 6px; border-radius: 7px; }}
QCalendarWidget QAbstractItemView:enabled {{ background: {t['raised']}; color: {t['text']}; outline: 0;
    selection-background-color: {t['accent']}; selection-color: {t['on_accent']}; }}
QCalendarWidget QAbstractItemView:disabled {{ color: {t['faint']}; }}

QPushButton {{ background: {t['raised']}; border: 1px solid {t['border']}; border-radius: 10px;
               padding: 8px 14px; font-weight: 500; min-height: 18px; }}
QPushButton:hover {{ background: {mix(t['raised'], t['text'], .06)}; border: 1px solid {t['border2']}; }}
QPushButton:pressed {{ background: {mix(t['raised'], t['text'], .1)}; }}
QPushButton:disabled {{ color: {t['faint']}; background: {t['surface']}; }}
QPushButton:focus {{ outline: 0; border: 1px solid {t['accent_line']}; }}
QPushButton#primary {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {t['accent']}, stop:1 {t['accent2']});
    color: {t['on_accent']}; border: 0; font-weight: 600; padding: 9px 18px; }}
QPushButton#primary:hover {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
    stop:0 {mix(t['accent'], '#ffffff', .12)}, stop:1 {mix(t['accent2'], '#ffffff', .12)}); }}
QPushButton#primary:pressed {{ background: {mix(t['accent'], '#000000', .12)}; }}
QPushButton#primary:disabled {{ background: {t['raised']}; color: {t['faint']}; }}
QPushButton#ghost {{ background: transparent; border: 1px solid transparent; color: {t['muted']}; }}
QPushButton#ghost:hover {{ background: {t['hover']}; color: {t['text']}; border: 1px solid {t['border']}; }}
QPushButton#danger {{ color: {t['bad']}; }}
QPushButton#danger:hover {{ background: {t['bad_soft']}; border: 1px solid {mix(t['border'], t['bad'], .5)}; }}
QPushButton#dangerSolid {{ background: {t['bad']}; color: #ffffff; border: 0; font-weight: 600; padding: 9px 18px; }}
QPushButton#dangerSolid:hover {{ background: {mix(t['bad'], '#ffffff', .12)}; }}
QPushButton#iconBtn {{ background: transparent; border: 1px solid transparent; border-radius: 9px; padding: 0; }}
QPushButton#iconBtn:hover {{ background: {t['hover']}; border: 1px solid {t['border']}; }}
QPushButton#iconBtn:checked {{ background: {t['accent_soft']}; border: 1px solid {t['accent_line']}; }}
QPushButton#navBtn {{ background: transparent; border: 0; border-radius: 10px; text-align: left;
    padding: 0 12px; color: {t['muted']}; font-weight: 500; }}
QPushButton#navBtn:hover {{ background: {t['hover']}; color: {t['text']}; }}
QPushButton#searchBtn {{ background: {t['raised']}; border: 1px solid {t['border']}; border-radius: 11px;
    text-align: left; padding: 0 12px; color: {t['faint']}; font-weight: 400; }}
QPushButton#searchBtn:hover {{ border: 1px solid {t['border2']}; color: {t['muted']}; }}
QPushButton#chip {{ background: {t['raised']}; border: 1px solid {t['border']}; border-radius: 14px;
    padding: 5px 12px; font-size: 12px; color: {t['muted']}; }}
QPushButton#chip:hover {{ border: 1px solid {t['accent_line']}; color: {t['text']}; }}
QPushButton#linkBtn {{ background: transparent; border: 0; color: {t['accent']}; padding: 2px 4px; font-weight: 600; }}
QPushButton#linkBtn:hover {{ color: {t['accent2']}; }}
QPushButton#menuBtn::menu-indicator {{ image: none; width: 0; }}
QPushButton#ghost::menu-indicator {{ image: none; width: 0; }}
QPushButton#iconBtn::menu-indicator {{ image: none; width: 0; }}

QToolButton#swatch {{ border: 2px solid transparent; border-radius: 14px; }}
QToolButton#swatch:checked {{ border: 2px solid {t['text']}; }}
QToolButton#glyph {{ background: {t['raised']}; border: 1px solid {t['border']}; border-radius: 10px; font-size: 18px; }}
QToolButton#glyph:hover {{ border: 1px solid {t['accent_line']}; }}
QToolButton#glyph:checked {{ background: {t['accent_soft']}; border: 2px solid {t['accent']}; }}
QToolButton {{ background: transparent; border: 0; }}

QTableWidget, QTableView {{ background: {t['surface']}; border: 1px solid {t['border']}; border-radius: 14px;
    gridline-color: {t['border']}; outline: 0; selection-background-color: {t['accent_soft']};
    selection-color: {t['text']}; alternate-background-color: {t['zebra']}; }}
QTableWidget::item {{ padding: 6px 12px; border: 0; }}
QTableWidget::item:hover {{ background: {t['hover']}; }}
QTableWidget::item:selected {{ background: {t['accent_soft']}; color: {t['text']}; }}
QHeaderView {{ background: transparent; }}
QHeaderView::section {{ background: {t['surface']}; color: {t['muted']}; border: 0;
    border-bottom: 1px solid {t['border']}; border-right: 1px solid {t['border']}; padding: 0 12px;
    font-size: 11px; font-weight: 700; }}
QHeaderView::section:hover {{ color: {t['text']}; background: {t['hover']}; }}
QTableCornerButton::section {{ background: {t['surface']}; border: 0; }}

QTreeWidget#sidebarTree {{ background: transparent; border: 0; outline: 0; }}
QTreeWidget#sidebarTree::item {{ border: 0; padding: 0; }}
QTreeWidget#sidebarTree::branch {{ image: none; border: 0; background: transparent; }}

QListWidget {{ background: transparent; border: 0; outline: 0; }}
QListWidget::item {{ border-radius: 8px; padding: 2px; }}
QListWidget::item:selected {{ background: {t['accent_soft']}; color: {t['text']}; }}
QListWidget::item:hover {{ background: {t['hover']}; }}

QScrollArea {{ background: transparent; border: 0; }}
QScrollBar:vertical {{ background: transparent; width: 12px; margin: 2px 2px 2px 0; }}
QScrollBar::handle:vertical {{ background: {t['border2']}; border-radius: 4px; min-height: 36px; margin: 0 2px; }}
QScrollBar::handle:vertical:hover {{ background: {t['faint']}; }}
QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 0 2px 2px 2px; }}
QScrollBar::handle:horizontal {{ background: {t['border2']}; border-radius: 4px; min-width: 36px; margin: 2px 0; }}
QScrollBar::handle:horizontal:hover {{ background: {t['faint']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; background: none; border: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

QMenuBar {{ background: {t['bg']}; border-bottom: 1px solid {t['border']}; padding: 3px 10px; }}
QMenuBar::item {{ background: transparent; padding: 6px 11px; border-radius: 7px; color: {t['muted']}; }}
QMenuBar::item:selected {{ background: {t['hover']}; color: {t['text']}; }}
QMenu {{ background: {t['raised']}; border: 1px solid {t['border2']}; border-radius: 10px; padding: 6px; }}
QMenu::item {{ padding: 8px 18px 8px 12px; border-radius: 6px; margin: 1px 0; }}
QMenu::item:selected {{ background: {t['accent_soft']}; }}
QMenu::item:disabled {{ color: {t['faint']}; }}
QMenu::separator {{ height: 1px; background: {t['border']}; margin: 5px 8px; }}

QStatusBar {{ background: {t['bg']}; color: {t['faint']}; border-top: 1px solid {t['border']}; }}
QStatusBar::item {{ border: 0; }}
QProgressBar {{ background: {t['raised']}; border: 0; border-radius: 3px; max-height: 6px; }}
QProgressBar::chunk {{ background: {t['accent']}; border-radius: 3px; }}

QDialog#sheet {{ background: {t['surface']}; border: 1px solid {t['border2']}; }}
QDialog#palette {{ background: {t['surface']}; border: 1px solid {t['border2']}; }}
QDialog#palette QLineEdit {{ background: transparent; border: 0; border-radius: 0; padding: 4px 2px; font-size: 16px; }}
QDialog#palette QListWidget {{ background: transparent; border: 0; outline: 0; }}
QDialog#palette QListWidget::item {{ border-radius: 9px; margin: 1px 6px; }}
QFrame#paletteInput {{ background: transparent; border: 0; border-bottom: 1px solid {t['border']}; }}
QFrame#paletteFoot {{ background: {t['raised']}; border: 0; border-top: 1px solid {t['border']}; }}

QCheckBox {{ spacing: 10px; background: transparent; }}
QCheckBox:disabled {{ color: {t['faint']}; }}
QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 6px; border: 1.5px solid {t['border2']};
    background: {t['raised']}; }}
QCheckBox::indicator:hover {{ border: 1.5px solid {t['accent_line']}; }}
QCheckBox::indicator:checked {{ background: {t['accent']}; border: 1.5px solid {t['accent']}; image: url({check}); }}
QTextBrowser {{ background: {t['raised']}; border: 1px solid {t['border']}; border-radius: 10px; padding: 8px; }}
'''


def palette(t):
    """A QPalette matching the theme so any widget we do not style explicitly still follows it."""
    from PySide6.QtGui import QColor, QPalette
    p = QPalette()
    role = QPalette.ColorRole
    pairs = {role.Window: t['bg'], role.WindowText: t['text'], role.Base: t['raised'], role.AlternateBase: t['surface'],
             role.Text: t['text'], role.Button: t['raised'], role.ButtonText: t['text'], role.ToolTipBase: t['raised'],
             role.ToolTipText: t['text'], role.Highlight: t['accent'], role.HighlightedText: t['on_accent'],
             role.PlaceholderText: t['faint'], role.Link: t['accent']}
    for r, c in pairs.items():
        p.setColor(r, QColor(c))
    return p


def load_fonts(resource_dir):
    """Register the bundled Inter weights so the UI looks identical on every distribution."""
    from PySide6.QtGui import QFontDatabase
    ok = False
    for f in sorted(Path(resource_dir).glob('fonts/*.otf')):
        ok = QFontDatabase.addApplicationFont(str(f)) >= 0 or ok
    return ok


def apply(app, name):
    """Install a theme on the whole application: base style, palette, default font and stylesheet."""
    from PySide6.QtGui import QFont
    t = set_current(name)
    app.setStyle('Fusion')
    app.setPalette(palette(t))
    font = QFont('Inter')
    font.setPixelSize(13)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)
    app.setStyleSheet(stylesheet(t))
    return t
