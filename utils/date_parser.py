"""utils/date_parser.py — Date/time parsing with validation."""

from datetime import datetime


FORMATS = ["%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y"]
TIME_FORMATS = ["%H:%M", "%H.%M"]


def parse_date(text: str) -> datetime | None:
    for fmt in FORMATS:
        try:
            return datetime.strptime(text.strip(), fmt)
        except ValueError:
            continue
    return None


def parse_time(text: str) -> tuple[int, int] | None:
    for fmt in TIME_FORMATS:
        try:
            t = datetime.strptime(text.strip(), fmt)
            return t.hour, t.minute
        except ValueError:
            continue
    return None


def combine_datetime(date: datetime, hour: int, minute: int) -> datetime:
    return date.replace(hour=hour, minute=minute, second=0, microsecond=0)
