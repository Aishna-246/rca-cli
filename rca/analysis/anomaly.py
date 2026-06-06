"""Detect metric anomalies using statistical thresholds."""

import pandas as pd


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
