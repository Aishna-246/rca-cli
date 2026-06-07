"""Detect metric anomalies using statistical thresholds."""

import warnings

import pandas as pd
import numpy as np


def detect_metric_anomalies(df: pd.DataFrame, z_threshold: float = 2.0) -> list[dict]:
    """Detect anomalies using Z-score outlier detection per metric series."""
    if df is None or df.empty:
        return []

    required = {"metric_name", "service", "timestamp", "value"}
    if not required.issubset(df.columns):
        return []

    anomalies: list[dict] = []
    grouped = df.groupby(["metric_name", "service"], dropna=False)

    for (metric_name, service), group in grouped:
        group_sorted = group.sort_values("timestamp").reset_index(drop=True)
        values = group_sorted["value"]

        if len(group_sorted) < 5:
            mean = values.mean()
            std = values.std()
            if std == 0 or pd.isna(std):
                continue
            z_scores = (values - mean) / std
        else:
            rolling_mean = values.rolling(window=5, min_periods=1).mean()
            rolling_std = values.rolling(window=5, min_periods=1).std(ddof=0).replace(0, pd.NA)
            z_scores = (values - rolling_mean) / rolling_std

        for idx, z in enumerate(z_scores):
            try:
                z_val = float(z)
            except (TypeError, ValueError):
                continue
            if pd.isna(z_val) or abs(z_val) <= z_threshold:
                continue
            anomalies.append(
                {
                    "metric": metric_name,
                    "service": service,
                    "anomaly_at": float(group_sorted.iloc[idx]["timestamp"]),
                    "value": float(values.iloc[idx]),
                    "z_score": z_val,
                    "direction": "spike" if z_val > 0 else "drop",
                }
            )

    return anomalies


def detect_anomalies_from_metrics_only(df: pd.DataFrame) -> list[dict]:
    """
    Detect anomalies from a metrics DataFrame and return them as log-compatible
    event dicts that flow through the same pipeline as parsed log events.

    Three detection methods per series:
    - Spike: rolling Z-score > 2.0
    - Gradual degradation: linear trend slope exceeds 1% of mean per step
    - Sustained elevation: value > mean + 1.5*std for 5+ consecutive points

    Returns a list of dicts with keys:
        ts, level, service, msg, source
    """
    if df is None or df.empty:
        return []

    required = {"metric_name", "service", "timestamp", "value"}
    if not required.issubset(df.columns):
        return []

    events: list[dict] = []
    grouped = df.groupby(["metric_name", "service"], dropna=False)

    for (metric_name, service), group in grouped:
        svc = str(service) if pd.notna(service) and service else "unknown"
        group_sorted = group.sort_values("timestamp").reset_index(drop=True)
        values = group_sorted["value"].astype(float)
        timestamps = group_sorted["timestamp"].astype(float)
        n = len(values)

        if n < 3:
            continue

        mean = values.mean()
        std = values.std(ddof=0)
        if pd.isna(std) or std == 0:
            std = 1.0

        # --- 1. Spike detection (rolling Z-score > 2.0) ---
        window = min(5, n)
        rolling_mean = values.rolling(window=window, min_periods=1).mean()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            rolling_std = (
                values.rolling(window=window, min_periods=1)
                .std(ddof=0)
                .replace(0, pd.NA)
                .fillna(std)
            )
        z_scores = (values - rolling_mean) / rolling_std

        for idx, z in enumerate(z_scores):
            try:
                z_val = float(z)
            except (TypeError, ValueError):
                continue
            if pd.isna(z_val) or abs(z_val) <= 2.0:
                continue
            direction = "spike" if z_val > 0 else "drop"
            events.append({
                "ts": float(timestamps.iloc[idx]),
                "level": "ERROR",
                "service": svc,
                "msg": (
                    f"Metric anomaly: {metric_name} {direction} "
                    f"(value={values.iloc[idx]:.3g}, z={z_val:.2f})"
                ),
                "source": "metrics",
            })

        # --- 2. Gradual degradation (linear trend slope) ---
        if n >= 5:
            x = np.arange(n, dtype=float)
            # Fit a line: slope via least-squares
            x_mean = x.mean()
            y_mean = float(values.mean())
            numerator = float(((x - x_mean) * (values - y_mean)).sum())
            denominator = float(((x - x_mean) ** 2).sum())
            slope = numerator / denominator if denominator != 0 else 0.0
            # Threshold: slope > 1% of mean per step (or 0.01 absolute if mean~0)
            threshold = max(abs(mean) * 0.01, 0.01)
            if abs(slope) > threshold:
                # Emit one event at the midpoint of the series
                mid_idx = n // 2
                direction = "increasing" if slope > 0 else "decreasing"
                events.append({
                    "ts": float(timestamps.iloc[mid_idx]),
                    "level": "WARN",
                    "service": svc,
                    "msg": (
                        f"Gradual degradation: {metric_name} steadily {direction} "
                        f"(slope={slope:.4g} per step)"
                    ),
                    "source": "metrics",
                })

        # --- 3. Sustained elevation (> mean + 1.5*std for 5+ consecutive points) ---
        elevation_threshold = mean + 1.5 * std
        run_start: int | None = None
        for idx in range(n):
            above = float(values.iloc[idx]) > elevation_threshold
            if above:
                if run_start is None:
                    run_start = idx
            else:
                if run_start is not None and (idx - run_start) >= 5:
                    events.append({
                        "ts": float(timestamps.iloc[run_start]),
                        "level": "WARN",
                        "service": svc,
                        "msg": (
                            f"Sustained elevation: {metric_name} stayed above "
                            f"{elevation_threshold:.3g} for {idx - run_start} consecutive points"
                        ),
                        "source": "metrics",
                    })
                run_start = None
        # Catch a run that extends to the end of the series
        if run_start is not None and (n - run_start) >= 5:
            events.append({
                "ts": float(timestamps.iloc[run_start]),
                "level": "WARN",
                "service": svc,
                "msg": (
                    f"Sustained elevation: {metric_name} stayed above "
                    f"{elevation_threshold:.3g} for {n - run_start} consecutive points"
                ),
                "source": "metrics",
            })

    return sorted(events, key=lambda e: e["ts"])
