"""Run Granger causality tests between anomalous metric pairs."""

import warnings

import pandas as pd
from statsmodels.tsa.stattools import adfuller, grangercausalitytests


def run_causality_analysis(anomaly_series: dict[str, pd.Series]) -> list[dict]:
    """Run Granger causality tests on metric series pairs."""
    results: list[dict] = []
    keys = list(anomaly_series.keys())

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

            try:
                adf_x = adfuller(merged["X"].values, autolag="AIC")
                x_series = merged["X"] if adf_x[1] <= 0.05 else merged["X"].diff().dropna()
                adf_y = adfuller(merged["Y"].values, autolag="AIC")
                y_series = merged["Y"] if adf_y[1] <= 0.05 else merged["Y"].diff().dropna()
                frame = pd.concat([x_series, y_series], axis=1, keys=["X", "Y"]).dropna()
                if len(frame) < 6:
                    continue

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
                    results.append(
                        {
                            "cause": key_x,
                            "effect": key_y,
                            "p_value": float(p_value),
                            "confidence": round(1 - float(p_value), 3),
                        }
                    )
            except Exception:
                continue

    return results
