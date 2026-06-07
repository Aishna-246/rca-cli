"""Run the RCA pipeline and shape results for the dashboard API."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from rca.analysis import anomaly, causality, graph
from rca.ingestion.log_parser import parse_log_file
from rca.ingestion.metrics_parser import parse_prometheus_json
from rca.normalization.event_extractor import extract_anomaly_events
from rca.normalization.timestamp import normalize_events
from rca.ranking.scorer import score_root_causes

try:
    from rca.output.llm_explain import generate_explanation
except ImportError:
    def generate_explanation(ranked_causes, log_events):  # type: ignore[misc]
        return ""


def _parse_since(since: str | None) -> float:
    if not since:
        return time.time() - 30 * 60
    try:
        if ":" in since and len(since) <= 8:
            parts = since.strip().split(":")
            if len(parts) == 2:
                minutes, seconds = int(parts[0]), int(parts[1])
                return time.time() - (minutes * 60 + seconds)
            if len(parts) == 3:
                hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
                return time.time() - (hours * 3600 + minutes * 60 + seconds)
        dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return float(since)


def _build_anomaly_series(metrics_df: pd.DataFrame) -> dict[str, pd.Series]:
    series: dict[str, pd.Series] = {}
    if metrics_df is None or metrics_df.empty:
        return series
    for (metric_name, service), group in metrics_df.groupby(["metric_name", "service"], dropna=False):
        svc = service if pd.notna(service) and service else "unknown"
        key = f"{svc}:{metric_name}"
        sorted_group = group.sort_values("timestamp")
        series[key] = sorted_group.set_index("timestamp")["value"]
    return series


def _service_from_key(key: str) -> str:
    if ":" in key:
        return key.split(":", 1)[0]
    if "." in key:
        return key.split(".", 1)[0]
    return key


def build_graph_payload(
    causal_edges: list[dict[str, Any]],
    ranked_causes: list[dict[str, Any]],
) -> dict[str, Any]:
    root_service = ranked_causes[0]["service"] if ranked_causes else None
    affected_services: set[str] = set()
    all_services: set[str] = set()

    for edge in causal_edges:
        cause_svc = _service_from_key(edge.get("cause", ""))
        effect_svc = _service_from_key(edge.get("effect", ""))
        all_services.add(cause_svc)
        all_services.add(effect_svc)
        if root_service and cause_svc == root_service:
            affected_services.add(effect_svc)

    for cause in ranked_causes[1:]:
        affected_services.add(cause.get("service", ""))

    nodes: list[dict[str, Any]] = []
    for service in sorted(all_services):
        if service == root_service:
            role = "root_cause"
        elif service in affected_services:
            role = "affected"
        else:
            role = "healthy"
        nodes.append({"id": service, "name": service, "role": role})

    links: list[dict[str, Any]] = []
    for edge in causal_edges:
        source = _service_from_key(edge.get("cause", ""))
        target = _service_from_key(edge.get("effect", ""))
        if source == target:
            continue
        confidence = float(edge.get("confidence", 0))
        links.append(
            {
                "source": source,
                "target": target,
                "confidence": confidence,
            }
        )

    if not nodes and ranked_causes:
        for cause in ranked_causes:
            role = "root_cause" if cause.get("rank") == 1 else "affected"
            nodes.append(
                {
                    "id": cause["service"],
                    "name": cause["service"],
                    "role": role,
                }
            )

    return {"nodes": nodes, "links": links}


def run_incident_analysis(
    log_paths: list[Path],
    metrics_path: Path | None,
    since: str | None = None,
    explain: bool = False,
) -> dict[str, Any]:
    if not log_paths and not metrics_path:
        raise ValueError("Provide at least one log file (--logs) or a metrics file (--metrics)")

    incident_start = _parse_since(since)

    # --- Parse logs ---
    log_events: list[dict] = []
    for log_path in log_paths:
        log_events.extend(parse_log_file(str(log_path)))

    # --- Parse metrics ---
    metrics_df = pd.DataFrame()
    if metrics_path:
        metrics_df = parse_prometheus_json(str(metrics_path))

    # --- Metrics-only mode: synthesise log-compatible events from metrics ---
    metrics_only = not log_events and not metrics_df.empty
    if not log_events:
        if metrics_df.empty:
            raise ValueError("No log events parsed and no usable metrics data found")
        synthetic_events = anomaly.detect_anomalies_from_metrics_only(metrics_df)
        log_anomaly_events = [e for e in synthetic_events if e["ts"] >= incident_start]
    else:
        norm_events = normalize_events(log_events)
        log_anomaly_events = extract_anomaly_events(norm_events, since=incident_start)

    # --- Metric anomaly detection ---
    metric_anomalies = []
    if not metrics_df.empty:
        metric_anomalies = anomaly.detect_metric_anomalies(metrics_df, z_threshold=2.5)

    # --- Causal analysis ---
    anomaly_series = _build_anomaly_series(metrics_df)
    causal_results = (
        causality.run_causality_analysis(anomaly_series, anomaly_list=metric_anomalies)
        if anomaly_series
        else causality.temporal_precedence_analysis(metric_anomalies) if metric_anomalies else []
    )
    causal_graph = graph.build_causal_graph(causal_results)
    root_candidates = graph.identify_root_causes(causal_graph)
    ranked_causes = score_root_causes(
        root_candidates,
        metric_anomalies,
        log_anomaly_events,
        incident_start=incident_start,
    )

    llm_explanation = None
    if explain:
        llm_explanation = generate_explanation(ranked_causes, log_anomaly_events) or None

    graph_payload = build_graph_payload(causal_results, ranked_causes)
    incident_dt = datetime.fromtimestamp(incident_start, tz=timezone.utc)

    return {
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
        "incident_start": incident_start,
        "incident_start_iso": incident_dt.isoformat(),
        "root_causes": ranked_causes,
        "causal_edges": causal_results,
        "graph": graph_payload,
        "llm_explanation": llm_explanation,
        "event_count": len(log_anomaly_events),
        "metrics_only": metrics_only,
        "log_files": [p.name for p in log_paths],
        "metrics_file": metrics_path.name if metrics_path else None,
    }
