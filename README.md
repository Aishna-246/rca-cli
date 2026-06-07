When a microservice system breaks, an on-call engineer manually opens
6+ browser tabs, reads logs from multiple services with different formats,
and manually correlates timestamps to find the root cause.

Average time: 47 minutes (source: IJETCSIT Dec 2024).

RCA-CLI automates this. You give it your log files and metrics.
It gives you a ranked, evidence-backed root cause in under 30 seconds.

## Validated Against Real Data

RCA-CLI has been tested against the **RCAEval benchmark** — 735 real production
failures across microservice systems (Online Boutique, Sock Shop, Train Ticket),
each with documented ground truth root causes and multi-source telemetry
(metrics, logs, traces).

Three representative cases (CPU fault, memory fault, network fault) are
available as runnable demos in [`examples/re2_real_failure/`](examples/re2_real_failure/).

**Download and run:**
```bash
python scripts/download_datasets.py
rca --logs examples/re2_real_failure/cpu_fault/metrics.csv --explain
```

> RCAEval: Pham et al., 2024 — arXiv:2305.15374  
> https://github.com/phamquiluan/RCAEval