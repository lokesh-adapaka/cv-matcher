"""Simple in-memory daily rate limiter for web scrapers."""
from __future__ import annotations

import logging
import threading
from datetime import date

logger = logging.getLogger(__name__)

DAILY_LIMIT = 50

# {source_name: {"date": date, "count": int}}
_counters: dict[str, dict] = {}
_lock = threading.Lock()


class RateLimitExceeded(Exception):
    """Raised when the daily scrape limit for a source is exceeded."""

    def __init__(self, source: str, limit: int):
        self.source = source
        self.limit = limit
        super().__init__(f"{source} daily request limit ({limit}) exceeded")


def check_and_increment(source: str) -> None:
    """Check if a request is allowed for *source* today. Raises RateLimitExceeded if not."""
    today = date.today()

    with _lock:
        entry = _counters.get(source)

        # Reset counter on a new day
        if entry is None or entry["date"] != today:
            _counters[source] = {"date": today, "count": 0}
            entry = _counters[source]

        if entry["count"] >= DAILY_LIMIT:
            logger.warning(f"Rate limit reached for {source}: {entry['count']}/{DAILY_LIMIT}")
            raise RateLimitExceeded(source, DAILY_LIMIT)

        entry["count"] += 1
        logger.debug(f"{source} request {entry['count']}/{DAILY_LIMIT} today")


def remaining(source: str) -> int:
    """Return how many requests are left for *source* today."""
    today = date.today()
    with _lock:
        entry = _counters.get(source)
        if entry is None or entry["date"] != today:
            return DAILY_LIMIT
        return max(0, DAILY_LIMIT - entry["count"])
