"""Built-in line icon set (24x24 grid, stroked). Drawn in code so Ledgerbook needs no icon files
and icons can be tinted to any theme colour."""
from functools import lru_cache

try:  # Qt is only needed to rasterise icons; the SVG markup itself (and the theme) work without it
    from PySide6.QtCore import QByteArray, QRectF, Qt
    from PySide6.QtGui import QIcon, QPainter, QPixmap
    from PySide6.QtSvg import QSvgRenderer
except ImportError:  # pragma: no cover - exercised only in Qt-free test environments
    QByteArray = QRectF = Qt = QIcon = QPainter = QPixmap = QSvgRenderer = None

# name -> inner SVG markup (stroke = currentColor). Names ending in "_fill" are filled shapes.
PATHS = {
    'home': '<path d="M3 11l9-8 9 8"/><path d="M5 10v10h5v-6h4v6h5V10"/>',
    'search': '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>',
    'star': '<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"/>',
    'sliders': '<path d="M4 7h10M18 7h2M4 17h2M10 17h10"/><circle cx="16" cy="7" r="2"/><circle cx="8" cy="17" r="2"/>',
    'info': '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8v.01"/>',
    'folder': '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    'history': '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l3 2"/>',
    'layout': '<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>',
    'calculator': '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8 7h8M8 12h.01M12 12h.01M16 12h.01M8 16h.01M12 16h.01M16 16h.01"/>',
    'gauge': '<path d="M3.5 17a9.5 9.5 0 1 1 17 0"/><path d="M12 13l4-5"/><circle cx="12" cy="14" r="1"/>',
    'droplet': '<path d="M12 3c3.5 4.5 6 7.5 6 11a6 6 0 0 1-12 0c0-3.5 2.5-6.5 6-11z"/>',
    'wind': '<path d="M3 8h10a3 3 0 1 0-3-3"/><path d="M3 12h15a3 3 0 1 1-3 3"/><path d="M3 16h7a2.5 2.5 0 1 1-2.5 2.5"/>',
    'zap': '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
    'cog': '<circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="6.5"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3M5.3 5.3l2.1 2.1M16.6 16.6l2.1 2.1M5.3 18.7l2.1-2.1M16.6 7.4l2.1-2.1"/>',
    'ruler': '<rect x="2" y="8" width="20" height="8" rx="1.5"/><path d="M6 8v3M10 8v4M14 8v3M18 8v4"/>',
    'cylinder': '<rect x="3" y="8" width="12" height="8" rx="1.5"/><path d="M15 12h6M7 8v8M21 9v6"/>',
    'thermometer': '<path d="M10 14V5a2 2 0 0 1 4 0v9a4 4 0 1 1-4 0z"/>',
    'waves': '<path d="M3 7c2 0 2-1.5 4.5-1.5S10 7 12 7s2.5-1.5 4.5-1.5S19 7 21 7"/><path d="M3 12c2 0 2-1.5 4.5-1.5S10 12 12 12s2.5-1.5 4.5-1.5S19 12 21 12"/><path d="M3 17c2 0 2-1.5 4.5-1.5S10 17 12 17s2.5-1.5 4.5-1.5S19 17 21 17"/>',
    'tank': '<rect x="4" y="4" width="16" height="16" rx="3"/><path d="M4 12c2.5-2 4-2 5.3 0s3.2 2 5.3 0 3-2 5.4 0"/>',
    'cable': '<circle cx="5" cy="5" r="2"/><circle cx="19" cy="19" r="2"/><path d="M7 5h4a4 4 0 0 1 4 4v2a4 4 0 0 0 4 4v2"/>',
    'plug': '<path d="M9 3v5M15 3v5"/><path d="M6 8h12v4a6 6 0 0 1-12 0z"/><path d="M12 18v3"/>',
    'swap': '<path d="M7 4L3 8l4 4"/><path d="M3 8h14"/><path d="M17 20l4-4-4-4"/><path d="M21 16H7"/>',
    'file': '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>',
    'table': '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M3 15h18M9 4v16"/>',
    'download': '<path d="M12 4v11M7 11l5 5 5-5"/><path d="M4 20h16"/>',
    'upload': '<path d="M12 16V5M7 9l5-5 5 5"/><path d="M4 20h16"/>',
    'copy': '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2"/>',
    'bookmark': '<path d="M6 3h12v18l-6-4-6 4z"/>',
    'reset': '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/>',
    'plus': '<path d="M12 5v14M5 12h14"/>',
    'trash': '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/>',
    'archive': '<rect x="3" y="4" width="18" height="4" rx="1"/><path d="M5 8v11a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8M10 12h4"/>',
    'check': '<path d="M5 12.5l4.5 4.5L19 7"/>',
    'alert': '<path d="M12 4L2.5 20h19z"/><path d="M12 10v4M12 17v.01"/>',
    'x_circle': '<circle cx="12" cy="12" r="9"/><path d="M9 9l6 6M15 9l-6 6"/>',
    'check_circle': '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l3 3 5-6"/>',
    'x': '<path d="M6 6l12 12M18 6L6 18"/>',
    'chevron_left': '<path d="M15 5l-7 7 7 7"/>',
    'chevron_right': '<path d="M9 5l7 7-7 7"/>',
    'chevron_down': '<path d="M5 9l7 7 7-7"/>',
    'chevrons_left': '<path d="M11 6l-6 6 6 6M18 6l-6 6 6 6"/>',
    'chevrons_right': '<path d="M6 6l6 6-6 6M13 6l6 6-6 6"/>',
    'command': '<path d="M15 6v12a3 3 0 1 0 3-3H6a3 3 0 1 0 3 3V6a3 3 0 1 0-3 3h12a3 3 0 1 0-3-3"/>',
    'sun': '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5L19 19M5 19l1.5-1.5M17.5 6.5L19 5"/>',
    'moon': '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/>',
    'clipboard': '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4h6v3H9zM9 12h6M9 16h4"/>',
    'book': '<path d="M3 5c3-1 6-1 9 1v14c-3-2-6-2-9-1zM21 5c-3-1-6-1-9 1v14c3-2 6-2 9-1z"/>',
    'compare': '<rect x="3" y="4" width="8" height="16" rx="2"/><rect x="13" y="4" width="8" height="16" rx="2"/>',
    'shield': '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
    'timer': '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2.5 2M9 2h6"/>',
    'conduit': '<circle cx="12" cy="12" r="9"/><circle cx="9" cy="10" r="1.6"/><circle cx="15" cy="10" r="1.6"/><circle cx="12" cy="15" r="1.6"/>',
    'activity': '<path d="M3 12h4l3-8 4 16 3-8h4"/>',
    'funnel': '<path d="M3 4h18l-7 9v6l-4 2v-8z"/>',
    'flow': '<path d="M3 12h15M13 6l6 6-6 6"/>',
    'motor': '<rect x="5" y="7" width="12" height="10" rx="2"/><path d="M17 10h3v4h-3M5 12H3M9 7V5h4v2"/>',
    'pump': '<circle cx="12" cy="12" r="7"/><path d="M5 12H2M19 12h3M12 5V2"/><path d="M9.5 9l5.5 3-5.5 3z"/>',
    'pin': '<path d="M12 17v5M8 3h8l-1 6 3 3v2H6v-2l3-3z"/>',
    'flame': '<path d="M12 3c1 4 5 5.5 5 10a5 5 0 0 1-10 0c0-2 1-3 2-4 0 2 1 3 2 3 0-3-1-5 1-9z"/>',
    'sigma': '<path d="M18 5H6l6 7-6 7h12"/>',
    'pencil': '<path d="M4 20l1-4L16.5 4.5a2 2 0 0 1 3 3L8 19z"/>',
    'sparkle': '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/>',
    'more': '<path d="M5 12h.01M12 12h.01M19 12h.01"/>',
    'undo': '<path d="M9 14L4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/>',
    'sidebar': '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16"/>',
    'columns': '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16M15 4v16"/>',
    'sort_up': '<path d="M12 19V5M5 12l7-7 7 7"/>',
    'sort_down': '<path d="M12 5v14M19 12l-7 7-7-7"/>',
    'folder_plus': '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M12 11v5M9.5 13.5h5"/>',
    'book_plus': '<path d="M5 4.5A1.5 1.5 0 0 1 6.5 3H19v16H6.5A1.5 1.5 0 0 0 5 20.5z"/><path d="M5 20.5A1.5 1.5 0 0 0 6.5 22H19v-3"/><path d="M12 7v6M9 10h6"/>',
    'database': '<ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
    'external': '<path d="M14 4h6v6M20 4l-9 9"/><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
    'eye': '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    'eye_off': '<path d="M3 3l18 18"/><path d="M10.6 5.1A9.8 9.8 0 0 1 12 5c6.5 0 10 7 10 7a17 17 0 0 1-3.2 4.2M6.6 6.7A17 17 0 0 0 2 12s3.5 7 10 7a9.7 9.7 0 0 0 4.2-.9"/><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2"/>',
    'arrow_up': '<path d="M12 19V5M6 11l6-6 6 6"/>',
    'arrow_down': '<path d="M12 5v14M6 13l6 6 6-6"/>',
    'lock': '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    'inbox': '<path d="M3 13l3-8h12l3 8v6a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z"/><path d="M3 13h5l1 3h6l1-3h5"/>',
    'palette': '<path d="M12 3a9 9 0 1 0 0 18c1.2 0 2-.8 2-1.8 0-.5-.2-.9-.5-1.2-.3-.3-.5-.7-.5-1.2 0-1 .8-1.8 1.8-1.8H17a4 4 0 0 0 4-4C21 6.5 17 3 12 3z"/><path d="M7.5 11.5h.01M10 7.5h.01M14.5 7.5h.01"/>',
    'heart': '<path d="M12 20s-7-4.4-9-9a5 5 0 0 1 9-3 5 5 0 0 1 9 3c-2 4.6-9 9-9 9z"/>',
    'list': '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
}
FILLED = {'star', 'pin', 'heart'}  # icons that can be drawn filled (pinned state)


def svg_markup(name, color, filled=False, stroke=1.75):
    inner = PATHS.get(name, PATHS['info'])
    fill = color if (filled and name in FILLED) else 'none'
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%s" stroke="%s" '
            'stroke-width="%s" stroke-linecap="round" stroke-linejoin="round">%s</svg>'
            % (fill, color, stroke, inner))


@lru_cache(maxsize=1024)
def _pixmap(name, color, size, dpr, filled, stroke):
    pm = QPixmap(int(size * dpr), int(size * dpr))
    pm.setDevicePixelRatio(dpr)
    pm.fill(Qt.GlobalColor.transparent)
    renderer = QSvgRenderer(QByteArray(svg_markup(name, color, filled, stroke).encode('utf-8')))
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(p, QRectF(0, 0, size, size))
    p.end()
    return pm


def pixmap(name, color, size=18, dpr=2.0, filled=False, stroke=1.75):
    """Tinted pixmap of a named icon. `color` is a '#rrggbb' string."""
    return _pixmap(name, color, int(size), float(dpr), bool(filled), stroke)


def icon(name, color, size=18, filled=False, stroke=1.75):
    return QIcon(pixmap(name, color, size, 2.0, filled, stroke))
