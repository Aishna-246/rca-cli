"""FastAPI server backing the RCA-CLI dashboard."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from rca.api.analysis import run_incident_analysis
from rca.api.store import list_incidents, load_incident, save_incident

app = FastAPI(title="RCA-CLI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/incidents")
def get_incidents() -> list[dict]:
    return list_incidents()


@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id: str) -> dict:
    record = load_incident(incident_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return record


@app.get("/api/incidents/{incident_id}/graph")
def get_incident_graph(incident_id: str) -> dict:
    record = load_incident(incident_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    graph_data = record.get("graph")
    if not graph_data:
        return {"nodes": [], "links": []}
    return graph_data


@app.post("/api/analyze")
async def analyze_incident(
    logs: Annotated[list[UploadFile], File(...)],
    metrics: UploadFile | None = File(None),
    since: str | None = Form(None),
    explain: bool = Form(False),
) -> dict:
    if not logs:
        raise HTTPException(status_code=400, detail="At least one log file is required")

    tmpdir = Path(tempfile.mkdtemp(prefix="rca-upload-"))
    log_paths: list[Path] = []
    metrics_path: Path | None = None

    try:
        for upload in logs:
            dest = tmpdir / (upload.filename or "upload.log")
            with dest.open("wb") as f:
                shutil.copyfileobj(upload.file, f)
            log_paths.append(dest)

        if metrics and metrics.filename:
            metrics_path = tmpdir / metrics.filename
            with metrics_path.open("wb") as f:
                shutil.copyfileobj(metrics.file, f)

        record = run_incident_analysis(
            log_paths=log_paths,
            metrics_path=metrics_path,
            since=since,
            explain=explain,
        )
        saved = save_incident(record)
        return {"id": saved["id"]}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def main() -> None:
    import uvicorn

    uvicorn.run("rca.api.server:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
