"""Run Granger causality tests between anomalous metric pairs."""

import warnings

import pandas as pd
from statsmodels.tsa.stattools import adfuller, grangercausalitytests


def temporal_precedence_analysis(anomaly_list: list[dict]) -> list[dict]:
    """Simple causality based on 'happens before' temporal ordering.

    If service A's first anomaly timestamp precedes service B's first anomaly
    timestamp by 30–300 seconds, draw a directed edge A -> B.

    Not statistically rigorous like Granger but reliable on small datasets.
    Confidence decays linearly: edges with smaller time gaps score higher.
    """
    if not anomaly_list:
        return []

    # Find the earliest anomaly timestamp per service
    service_first_anomaly: dict[str, float] = {}
    for a in anomaly_list:
        service = a.get("service")
        ts = a.get("anomaly_at")
        if not service or ts is None:
            continue
        if service not in service_first_anomaly or ts < service_first_anomaly[service]:
            service_first_anomaly[service] = float(ts)

    edges: list[dict] = []
    services = list(service_first_anomaly.keys())
    for cause in services:
        for effect in services:
            if cause == effect:
                continue
            time_diff = service_first_anomaly[effect] - service_first_anomaly[cause]
            if 30 <= time_diff <= 300:
                edges.append({
                    "cause": cause,
                    "effect": effect,
                    "p_value": 0.05,  # nominal value for display
                    "confidence": round(1 - (time_diff / 300), 3),
                    "method": "temporal_precedence",
                })
    return edges


def run_causality_analysis(
    anomaly_series: dict[str, pd.Series],
    anomaly_list: list[dict] | None = None,
) -> list[dict]:
    """Run Granger causality tests on metric series pairs.

    Falls back to temporal_precedence_analysis when:
    - Granger returns 0 edges, OR
    - any series has fewer than 15 aligned points

    If both methods produce edges, results are merged and deduplicated
    by (cause, effect) pair — Granger edges take precedence.
    """
    granger_results: list[dict] = []
    keys = list(anomaly_series.keys())
    has_short_series = False

    for i, key_x in enumerate(keys):
        for j, key_y in enumerate(keys):
            if i == j:
                continue

            series_x = anomaly_series[key_x]
            series_y = anomaly_series[key_y]
            merged = pd.merge(
                series_x.rename("X"),
                series_y.rename("Y"),
                left_index=True,
                right_index=True,
                how="inner",
            )

            if len(merged) < 6:
                continue

            if len(merged) < 15:
                has_short_series = True

            try:
                adf_x = adfuller(merged["X"].values, autolag="AIC")
                x_series = merged["X"] if adf_x[1] <= 0.05 else merged["X"].diff().dropna()
                adf_y = adfuller(merged["Y"].values, autolag="AIC")
                y_series = merged["Y"] if adf_y[1] <= 0.05 else merged["Y"].diff().dropna()
                frame = pd.concat([x_series, y_series], axis=1, keys=["X", "Y"]).dropna()
                if len(frame) < 6:
                    continue

                if len(frame) < 15:
                    has_short_series = True

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", FutureWarning)
                    res_lag2 = grangercausalitytests(
                        frame[["Y", "X"]], maxlag=2, verbose=False
                    )
                    res_lag4 = grangercausalitytests(
                        frame[["Y", "X"]], maxlag=4, verbose=False
                    )
                p_lag2 = res_lag2[1][0]["ssr_ftest"][1]
                p_lag4 = res_lag4[1][0]["ssr_ftest"][1]
                p_value = min(p_lag2, p_lag4)

                threshold = 0.15 if len(frame) < 30 else 0.05
                if p_value < threshold:
                    granger_results.append(
                        {
                            "cause": key_x,
                            "effect": key_y,
                            "p_value": float(p_value),
                            "confidence": round(1 - float(p_value), 3),
                        }
                    )
            except Exception:
                continue

    # Run temporal fallback when Granger found nothing or series are short
    use_temporal = (not granger_results or has_short_series) and anomaly_list
    if not use_temporal:
        return granger_results

    temporal_results = temporal_precedence_analysis(anomaly_list)

    if not granger_results:
        return temporal_results

    # Merge: Granger edges take precedence; fill in gaps with temporal edges
    seen: set[tuple[str, str]] = {(e["cause"], e["effect"]) for e in granger_results}
    merged_results = list(granger_results)
    for edge in temporal_results:
        key = (edge["cause"], edge["effect"])
        if key not in seen:
            merged_results.append(edge)
            seen.add(key)
    return merged_results
