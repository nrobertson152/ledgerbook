"""Small formatting helpers (Qt-free, unit-tested)."""
from datetime import date, datetime, timezone


def plural(n, one, many=None):
    return '%d %s' % (n, one if n == 1 else (many or one + 's'))


def parse_date(text):
    try:
        return datetime.strptime(str(text)[:10], '%Y-%m-%d').date()
    except ValueError:
        return None


def fmt_date(text, today=None):
    """'2026-10-30' -> 'Oct 30, 2026'. Unparseable input is returned unchanged."""
    d = parse_date(text)
    if d is None:
        return str(text or '')
    return '%s %d, %d' % (d.strftime('%b'), d.day, d.year)


def relative_day(text, today=None):
    """'Today', 'Yesterday', '3 days ago', or the formatted date for older entries."""
    d = parse_date(text)
    if d is None:
        return str(text or '')
    today = today or date.today()
    delta = (today - d).days
    if delta == 0:
        return 'Today'
    if delta == 1:
        return 'Yesterday'
    if 1 < delta < 7:
        return '%d days ago' % delta
    if delta == -1:
        return 'Tomorrow'
    return fmt_date(text)


def fmt_timestamp(text):
    """SQLite CURRENT_TIMESTAMP (UTC) -> local 'Oct 30, 2:05 PM'."""
    try:
        moment = datetime.strptime(str(text)[:19], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc).astimezone()
    except ValueError:
        return str(text or '')
    hour = moment.hour % 12 or 12
    return '%s %d, %d:%02d %s' % (moment.strftime('%b'), moment.day, hour, moment.minute,
                                  'AM' if moment.hour < 12 else 'PM')


def greeting(now=None):
    hour = (now or datetime.now()).hour
    if hour < 5:
        return 'Working late'
    if hour < 12:
        return 'Good morning'
    if hour < 18:
        return 'Good afternoon'
    return 'Good evening'


def human_size(num_bytes):
    size = float(num_bytes)
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024 or unit == 'GB':
            return ('%d %s' % (size, unit)) if unit == 'B' else ('%.1f %s' % (size, unit))
        size /= 1024


def is_true(value):
    from .constants import TRUE_VALUES
    return str(value or '').strip().lower() in TRUE_VALUES
