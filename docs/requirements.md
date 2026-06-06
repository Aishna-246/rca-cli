## Functional Requirements

FR-01: Accept multiple log files as CLI arguments
FR-02: Accept Prometheus metrics JSON as CLI argument
FR-03: Accept a --since timestamp to filter the incident window
FR-04: Parse log files with heterogeneous timestamp formats
FR-05: Extract anomaly events (ERROR/WARN lines, keyword matches)
FR-06: Detect metric anomalies using Z-score threshold
FR-07: Run Granger causality test between anomalous metric pairs
FR-08: Build a directed causal graph from test results
FR-09: Rank root cause candidates by confidence score
FR-10: Output a formatted terminal report with Rich
FR-11: Optionally generate a plain-English explanation via LLM (--explain flag)
FR-12: Write report.json for programmatic consumption
FR-13: Exit with code 0 on success, 1 on error

## Non-Functional Requirements

NFR-01: Parse 10,000 log lines in under 5 seconds
NFR-02: No external network calls unless --explain flag is used
NFR-03: Works fully offline (except Phase 5)
NFR-04: CLI must work on Linux, macOS, and Windows
NFR-05: All secrets (API keys) via environment variables only — never hardcoded
NFR-06: Test coverage >= 80%