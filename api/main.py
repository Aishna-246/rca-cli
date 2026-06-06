"""FastAPI server for the RCA-CLI dashboard and programmatic access."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from rca.api.analysis import run_incident_analysis

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"

app = FastAPI(title="RCA-CLI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    log_paths: list[str] = Field(..., min_length=1)
    metrics_path: str | None = None
    since: str | None = None
    explain: bool = False


def _ensure_reports_dir() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _report_path(report_id: str) -> Path:
    safe_id = Path(report_id).name
    return REPORTS_DIR / f"{safe_id}.json"


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    resolved = path.resolve()
    if not str(resolved).startswith(str(PROJECT_ROOT.resolve())):
        raise HTTPException(status_code=400, detail=f"Path outside project root: {path_str}")
    if not resolved.exists():
        raise HTTPException(status_code=400, detail=f"File not found: {path_str}")
    return resolved


def _timestamp_filename() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def save_report(record: dict[str, Any]) -> dict[str, Any]:
    _ensure_reports_dir()
    report_id = record.get("id") or _timestamp_filename()
    base = report_id
    suffix = 0
    while _report_path(report_id).exists():
        suffix += 1
        report_id = f"{base}_{suffix}"

    record["id"] = report_id
    path = _report_path(report_id)
    with path.open("w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    return record


def load_report(report_id: str) -> dict[str, Any] | None:
    path = _report_path(report_id)
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def list_report_summaries() -> list[dict[str, Any]]:
    _ensure_reports_dir()
    summaries: list[dict[str, Any]] = []
    for path in sorted(REPORTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
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


@app.get("/api/incidents")
def get_incidents() -> list[dict[str, Any]]:
    """List all saved reports from ./reports/."""
    return list_report_summaries()


@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id: str) -> dict[str, Any]:
    """Return a specific report JSON by id (filename stem)."""
    record = load_report(incident_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return record


@app.get("/api/incidents/{incident_id}/graph")
def get_incident_graph(incident_id: str) -> dict[str, Any]:
    """Return graph nodes and edges for react-force-graph-2d."""
    record = load_report(incident_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    graph = record.get("graph") or {}
    nodes = graph.get("nodes", [])
    links = graph.get("links", graph.get("edges", []))
    return {"nodes": nodes, "links": links, "edges": links}


@app.post("/api/run")
def run_analysis(request: RunRequest) -> dict[str, Any]:
    """Run the RCA pipeline on server-side paths and save the report."""
    log_paths = [_resolve_path(path) for path in request.log_paths]
    metrics_path = _resolve_path(request.metrics_path) if request.metrics_path else None

    try:
        record = run_incident_analysis(
            log_paths=log_paths,
            metrics_path=metrics_path,
            since=request.since,
            explain=request.explain,
        )
        saved = save_report(record)
        return saved
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc


def main() -> None:
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
