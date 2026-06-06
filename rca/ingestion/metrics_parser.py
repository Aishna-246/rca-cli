"""Parse Prometheus metrics JSON exports and CSV time series."""

import os
import json
import pandas as pd

def parse_prometheus_json(filepath: str) -> pd.DataFrame:
    """
    Parse Prometheus query_range JSON or metric CSV export into a flat DataFrame.

    Supports two formats:
    - query_range JSON (columns: metric_name, service, timestamp, value)
    - CSV (columns: metric_name, [service], timestamp, value)

    Auto-detects format from file extension.
    Returns: pd.DataFrame or empty DataFrame on error.
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
                            "value": float(val)
                        })
                    except Exception:
                        continue
            return pd.DataFrame(rows, columns=["metric_name", "service", "timestamp", "value"])
        elif ext == ".csv":
            df = pd.read_csv(filepath)
            # Required columns: metric_name, timestamp, value. Optional: service.
            # Normalize columns present.
            req_cols = {"metric_name", "timestamp", "value"}
            has_service = "service" in df.columns
            if not req_cols.issubset(df.columns):
                return pd.DataFrame(columns=["metric_name", "service", "timestamp", "value"])
            # Ensure types
            df = df.copy()
            df["timestamp"] = pd.to_numeric(df["timestamp"], errors="coerce")
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            if not has_service:
                df["service"] = None
            # Only keep relevant columns
            return df[["metric_name", "service", "timestamp", "value"]].dropna(subset=["metric_name", "timestamp", "value"])
        else:
            return pd.DataFrame(columns=["metric_name", "service", "timestamp", "value"])
    except Exception:
        return pd.DataFrame(columns=["metric_name", "service", "timestamp", "value"])
