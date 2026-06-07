"""Parse Prometheus metrics JSON exports and CSV time series."""

import os
import json
import pandas as pd


def parse_prometheus_json(filepath: str) -> pd.DataFrame:
    """
    Parse metrics data into a flat DataFrame with columns:
        metric_name, service, timestamp, value

    Supports three formats (auto-detected):

    1. Prometheus query_range JSON
       { "data": { "result": [ { "metric": {...}, "values": [[ts, val], ...] } ] } }

    2. Standard CSV
       Required columns: metric_name, timestamp, value
       Optional column:  service

    3. RCAEval CSV
       Columns: timestamp, service_name, metric_name, value
       (column order/names as produced by the RCAEval benchmark download utility)

    Returns an empty DataFrame on error or unrecognised format.
    """
    if not filepath or not os.path.exists(filepath) or not os.path.isfile(filepath):
        return pd.DataFrame(columns=["metric_name", "service", "timestamp", "value"])

    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == ".json":
            with open(filepath, "r", encoding="utf-8") as f:
                content = json.load(f)
            rows = []
            for series in content.get("data", {}).get("result", []):
                metric = series.get("metric", {})
                metric_name = metric.get("__name__", None)
                service = metric.get("service") or metric.get("job")
                for value_pair in series.get("values", []):
                    if len(value_pair) != 2:
                        continue
                    timestamp, val = value_pair
                    try:
                        rows.append({
                            "metric_name": metric_name,
                            "service": service,
                            "timestamp": float(timestamp),
                            "value": float(val),
                        })
                    except Exception:
                        continue
            return pd.DataFrame(rows, columns=["metric_name", "service", "timestamp", "value"])

        elif ext == ".csv":
            df = pd.read_csv(filepath)
            cols = set(df.columns)

            # --- RCAEval format: timestamp, service_name, metric_name, value ---
            rcaeval_cols = {"timestamp", "service_name", "metric_name", "value"}
            if rcaeval_cols.issubset(cols):
                df = df.copy()
                df = df.rename(columns={"service_name": "service"})
                df["timestamp"] = pd.to_numeric(df["timestamp"], errors="coerce")
                df["value"] = pd.to_numeric(df["value"], errors="coerce")
                return (
                    df[["metric_name", "service", "timestamp", "value"]]
                    .dropna(subset=["metric_name", "timestamp", "value"])
                    .reset_index(drop=True)
                )

            # --- Standard CSV format: metric_name, timestamp, value[, service] ---
            req_cols = {"metric_name", "timestamp", "value"}
            if req_cols.issubset(cols):
                df = df.copy()
                df["timestamp"] = pd.to_numeric(df["timestamp"], errors="coerce")
                df["value"] = pd.to_numeric(df["value"], errors="coerce")
                if "service" not in cols:
                    df["service"] = None
                return (
                    df[["metric_name", "service", "timestamp", "value"]]
                    .dropna(subset=["metric_name", "timestamp", "value"])
                    .reset_index(drop=True)
                )

            # Unrecognised CSV schema
            return pd.DataFrame(columns=["metric_name", "service", "timestamp", "value"])

        else:
            return pd.DataFrame(columns=["metric_name", "service", "timestamp", "value"])

    except Exception:
        return pd.DataFrame(columns=["metric_name", "service", "timestamp", "value"])
