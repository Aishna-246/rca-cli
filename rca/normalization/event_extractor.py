"""Extract anomaly events from normalized log records."""

import re

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    _model = SentenceTransformer("all-MiniLM-L6-v2")
    _SEMANTIC_DEDUP_AVAILABLE = True
except ImportError:
    _SEMANTIC_DEDUP_AVAILABLE = False


def deduplicate_events(events: list[dict]) -> list[dict]:
    """Deduplicate events by semantic similarity of their 'msg' field.

    If sentence-transformers is available:
      - Embeds each event message with all-MiniLM-L6-v2
      - Computes cosine similarity against all previously kept embeddings
      - If similarity > 0.85 with any kept embedding, the event is a
        duplicate: its cluster's 'count' is incremented and it is dropped
      - Otherwise the event is kept with count=1

    Falls back to exact string match on 'msg' when the model is unavailable.
    """
    if not events:
        return []

    if _SEMANTIC_DEDUP_AVAILABLE and len(events) > 1:
        messages = [e.get("msg", "") for e in events]
        embeddings = _model.encode(messages)  # shape: (n, dim)

        kept: list[dict] = []
        kept_embeddings: list = []

        for idx, event in enumerate(events):
            emb = embeddings[idx]
            norm_emb = emb / (float(np.linalg.norm(emb)) or 1.0)

            matched_cluster = None
            for ki, kept_emb in enumerate(kept_embeddings):
                sim = float(np.dot(norm_emb, kept_emb))
                if sim > 0.85:
                    matched_cluster = ki
                    break

            if matched_cluster is not None:
                # Increment count on the existing representative event
                kept[matched_cluster]["count"] = kept[matched_cluster].get("count", 1) + 1
            else:
                # New cluster — keep this event
                new_event = dict(event)
                new_event["count"] = 1
                kept.append(new_event)
                kept_embeddings.append(norm_emb)

        return kept

    else:
        # Fallback: exact string match on msg
        seen_msgs: set[str] = set()
        kept = []
        for event in events:
            msg = event.get("msg", "")
            if msg not in seen_msgs:
                seen_msgs.add(msg)
                new_event = dict(event)
                new_event["count"] = 1
                kept.append(new_event)
            else:
                # Find the existing event and increment its count
                for kept_event in kept:
                    if kept_event.get("msg") == msg:
                        kept_event["count"] = kept_event.get("count", 1) + 1
                        break
        return kept


def extract_anomaly_events(events: list[dict], since: float = 0.0) -> list[dict]:
    """Return ERROR/WARN and keyword-matched events after `since`, deduplicated."""
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

    sorted_events = sorted(filtered, key=lambda e: e.get("ts", 0))
    return deduplicate_events(sorted_events)
