"""Verify that a 3-service cascade (A → B → C) ranks serviceA as root cause.

serviceA: strong causal graph score, few log errors (actual root)
serviceB: medium score, medium errors (intermediate)
serviceC: weak score, many log errors (downstream leaf, should NOT win)
"""
from rca.ranking.scorer import score_root_causes

graph_candidates = [
    {"service_metric": "serviceA:cpu", "score": 1.5, "out_degree": 2,
     "causes": ["serviceB:latency", "serviceC:errors"]},
    {"service_metric": "serviceB:latency", "score": 1.2, "out_degree": 1,
     "causes": ["serviceC:errors"]},
    {"service_metric": "serviceC:errors", "score": 0.8, "out_degree": 0,
     "causes": []},
]

# serviceC has most log errors (downstream leaf accumulates errors)
log_events = (
    [{"level": "ERROR", "service": "serviceA", "ts": 1.0}] * 3 +
    [{"level": "ERROR", "service": "serviceB", "ts": 2.0}] * 8 +
    [{"level": "ERROR", "service": "serviceC", "ts": 3.0}] * 15
)

# serviceA anomaly fires first
anomaly_events = [
    {"service": "serviceA", "metric": "cpu",     "anomaly_at": 1.0},
    {"service": "serviceB", "metric": "latency", "anomaly_at": 60.0},
    {"service": "serviceC", "metric": "errors",  "anomaly_at": 120.0},
]

results = score_root_causes(
    graph_candidates=graph_candidates,
    anomaly_events=anomaly_events,
    log_events=log_events,
    incident_start=0.0,
)

print("Ranked root causes:")
for r in results:
    print(f"  #{r['rank']} {r['service']:12s}  confidence={r['confidence_pct']:3d}%"
          f"  log_errors={r['evidence']['log_errors_before']}")

top = results[0]
assert top["service"] == "serviceA", (
    f"Expected serviceA as #1 root cause, got {top['service']}"
)
assert top["confidence_pct"] > results[1]["confidence_pct"], (
    "serviceA confidence should be strictly higher than serviceB"
)
print("\nPASS: serviceA correctly identified as #1 root cause")
