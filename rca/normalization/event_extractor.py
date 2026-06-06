"""Extract anomaly events from normalized log records."""

import re


def extract_anomaly_events(events: list[dict], since: float = 0.0) -> list[dict]:
    """Return ERROR/WARN and keyword-matched events after `since`."""
    keywords = [
        "timeout",
        "exhausted",
        "failed",
        "exception",
        "critical",
        "refused",
        "unavailable",
        "spike",
        "saturated",
        "killed",
        "oom",
    ]
    pattern = re.compile(r"\b(" + "|".join(map(re.escape, keywords)) + r")\b", re.IGNORECASE)

    filtered: list[dict] = []
    for event in events:
        level = event.get("level", "").upper()
        msg = event.get("msg", "")
        ts = event.get("ts", 0)
        level_match = level in {"ERROR", "WARN"}
        keyword_match = bool(pattern.search(msg))
        since_match = since <= 0 or ts >= since
        if (level_match or keyword_match) and since_match:
            filtered.append(event)

    return sorted(filtered, key=lambda e: e.get("ts", 0))
