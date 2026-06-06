"""Score and rank root cause candidates by confidence."""


def score_root_causes(
    graph_candidates: list[dict],
    anomaly_events: list[dict],
    log_events: list[dict],
    incident_start: float,
) -> list[dict]:
    """Rank root cause candidates using causal confidence, logs, and timing."""
    def extract_service_metric(service_metric: str) -> tuple[str, str]:
        if ":" in service_metric:
            parts = service_metric.split(":", 1)
        elif "." in service_metric:
            parts = service_metric.split(".", 1)
        else:
            return service_metric, "unknown"
        return parts[0], parts[1] if len(parts) > 1 else "unknown"

    anomalies_by_key: dict[tuple, dict] = {}
    for anomaly in anomaly_events:
        key = (anomaly.get("service"), anomaly.get("metric"))
        prev = anomalies_by_key.get(key)
        if prev is None or anomaly.get("anomaly_at", float("inf")) < prev.get("anomaly_at", float("inf")):
            anomalies_by_key[key] = anomaly

    log_errors_by_service: dict[str, list] = {}
    for event in log_events:
        level = event.get("level", "").upper()
        service = event.get("service")
        ts = event.get("ts", 0)
        if level == "ERROR" and service and incident_start - 60 <= ts < incident_start + 300:
            log_errors_by_service.setdefault(service, []).append(event)

    raw_scores: list[dict] = []
    min_score = None
    max_score = None

    for candidate in graph_candidates:
        service_metric = candidate.get("service_metric", "")
        base_score = float(candidate.get("score", 0))
        service, metric = extract_service_metric(service_metric)
        log_errors = log_errors_by_service.get(service, [])
        log_bonus = 0.5 * len(log_errors)
        anomaly = anomalies_by_key.get((service, metric))
        anomaly_at = anomaly.get("anomaly_at") if anomaly else None
        temporal_bonus = 1.0 if anomaly_at is not None and anomaly_at <= incident_start + 300 else 0.0
        raw = base_score + log_bonus + temporal_bonus

        min_score = raw if min_score is None else min(min_score, raw)
        max_score = raw if max_score is None else max(max_score, raw)
        raw_scores.append(
            {
                "service": service,
                "metric": metric,
                "raw_score": raw,
                "log_errors_before": len(log_errors),
                "anomaly_at": float(anomaly_at) if anomaly_at is not None else None,
                "causal_edges": len(candidate.get("causes", [])),
            }
        )

    if not raw_scores:
        services: dict[str, int] = {}
        for event in log_events:
            if event.get("level", "").upper() == "ERROR":
                svc = event.get("service", "unknown")
                services[svc] = services.get(svc, 0) + 1
        for idx, (service, count) in enumerate(sorted(services.items(), key=lambda x: x[1], reverse=True), start=1):
            return [
                {
                    "rank": idx,
                    "service": service,
                    "metric": "error_logs",
                    "confidence_pct": min(95, 40 + count * 5),
                    "evidence": {
                        "causal_edges": 0,
                        "log_errors_before": count,
                        "anomaly_at": None,
                    },
                }
            ]

    span = (max_score - min_score) if max_score is not None and min_score is not None else 1.0
    if span == 0:
        span = 1.0

    output: list[dict] = []
    for item in raw_scores:
        confidence_pct = int(round(((item["raw_score"] - min_score) / span) * 100))
        output.append(
            {
                "service": item["service"],
                "metric": item["metric"],
                "confidence_pct": confidence_pct,
                "evidence": {
                    "causal_edges": item["causal_edges"],
                    "log_errors_before": item["log_errors_before"],
                    "anomaly_at": item["anomaly_at"],
                },
            }
        )

    output.sort(key=lambda x: x["confidence_pct"], reverse=True)
    for idx, item in enumerate(output, start=1):
        item["rank"] = idx

    return output
