"""Month-transition scheduler logic."""

from __future__ import annotations

import logging
from datetime import datetime

from zoneinfo import ZoneInfo

from config import config

logger = logging.getLogger(__name__)


def current_month(tz: ZoneInfo | None = None) -> tuple[int, int]:
    """Return (year, month) in the configured timezone."""
    tz = tz or config.TZ
    now = datetime.now(tz)
    return now.year, now.month


def current_date(tz: ZoneInfo | None = None):
    """Return today's date in the configured timezone."""
    from datetime import date
    tz = tz or config.TZ
    return datetime.now(tz).date()


def month_label(year: int, month: int) -> str:
    """Human-readable month label, e.g. 'MAY 2026'."""
    month_names = [
        "JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE",
        "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER",
    ]
    return f"{month_names[month - 1]} {year}"
