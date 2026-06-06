"""Persist and load incident records for the dashboard API."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "incidents"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _incident_path(incident_id: str) -> Path:
    return DATA_DIR / f"{incident_id}.json"


def save_incident(record: dict[str, Any]) -> dict[str, Any]:
    _ensure_data_dir()
    if "id" not in record:
        record["id"] = str(uuid.uuid4())
    path = _incident_path(record["id"])
    with path.open("w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    return record


def list_incidents() -> list[dict[str, Any]]:
    _ensure_data_dir()
    summaries: list[dict[str, Any]] = []
    for path in sorted(DATA_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            with path.open(encoding="utf-8") as f:
                record = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        root_causes = record.get("root_causes") or []
        top = root_causes[0] if root_causes else {}
        summaries.append(
            {
                "id": record.get("id", path.stem),
                "timestamp": record.get("created_at") or record.get("incident_start_iso", ""),
                "top_root_cause": top.get("service", "unknown"),
                "confidence_pct": top.get("confidence_pct", 0),
            }
        )
    return summaries


def load_incident(incident_id: str) -> dict[str, Any] | None:
    path = _incident_path(incident_id)
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)
