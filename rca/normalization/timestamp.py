"""Normalize timestamps across heterogeneous log formats."""

import re
import time
from datetime import datetime, timezone

from dateutil import parser


def normalize_timestamp(ts_raw: str) -> float:
    """Convert a heterogeneous timestamp string to a UTC unix epoch float."""
    if ts_raw is None:
        return 0.0

    ts_raw = str(ts_raw).strip()
    if not ts_raw:
        return 0.0

    try:
        if re.match(r"^\d{10}(\.\d+)?$", ts_raw):
            return float(ts_raw)
    except ValueError:
        pass

    syslog_match = re.match(r"^[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}$", ts_raw)
    if syslog_match:
        try:
            year = datetime.now().year
            dt = datetime.strptime(f"{year} {ts_raw}", "%Y %b %d %H:%M:%S")
            return dt.replace(tzinfo=timezone.utc).timestamp()
        except ValueError:
            pass

    try:
        ts_trans = re.sub(r",(\d{1,6})$", r".\1", ts_raw)
        dt = parser.parse(ts_trans)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.timestamp()
    except (ValueError, TypeError, parser.ParserError):
        return 0.0


def normalize_events(events: list[dict]) -> list[dict]:
    """Add a normalized `ts` field to each event and sort ascending."""
    for event in events:
        event["ts"] = normalize_timestamp(event.get("ts_raw"))
    return sorted(events, key=lambda e: e["ts"])
