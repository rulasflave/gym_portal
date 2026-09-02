from datetime import datetime, timezone
from zoneinfo import ZoneInfo

TZ_LOCAL = ZoneInfo('America/Mexico_City')


def to_local(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(TZ_LOCAL)


def local_now():
    return datetime.now(TZ_LOCAL)