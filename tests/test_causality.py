"""Tests for causality analysis and graph construction."""

import numpy as np
import pandas as pd
import pytest

from rca.analysis.causality import run_causality_analysis

REQUIRED_KEYS = {"cause", "effect", "p_value", "confidence"}


@pytest.fixture
def lagged_cause_series() -> dict[str, pd.Series]:
    """X leads Y by 2 steps: Y[t] = sin(t-2), X[t] = sin(t).

    Granger requires stochastic variation; negligible noise avoids a perfect-fit error.
    """
    rng = np.random.default_rng(0)
    t = np.arange(100, dtype=float)
    noise = rng.normal(0, 1e-6, size=len(t))
    x = pd.Series(np.sin(t) + noise, index=t, name="metric_x")
    y = pd.Series(np.sin(t - 2) + noise, index=t, name="metric_y")
    return {"service_x:metric_x": x, "service_y:metric_y": y}


@pytest.fixture
def independent_series() -> dict[str, pd.Series]:
    rng = np.random.default_rng(42)
    t = np.arange(100, dtype=float)
    x = pd.Series(rng.normal(size=100), index=t, name="metric_a")
    y = pd.Series(rng.normal(size=100), index=t, name="metric_b")
    return {"service_a:metric_a": x, "service_b:metric_b": y}


@pytest.fixture
def short_series() -> dict[str, pd.Series]:
    t = np.arange(5, dtype=float)
    x = pd.Series(np.sin(t), index=t)
    y = pd.Series(np.cos(t), index=t)
    return {"short_x:metric": x, "short_y:metric": y}


def test_granger_detects_known_cause(lagged_cause_series):
    results = run_causality_analysis(lagged_cause_series)

    x_causes_y = [
        r for r in results if r["cause"] == "service_x:metric_x" and r["effect"] == "service_y:metric_y"
    ]
    assert len(x_causes_y) >= 1
    assert x_causes_y[0]["p_value"] < 0.05


def test_granger_no_spurious_cause(independent_series):
    results = run_causality_analysis(independent_series)

    assert results == []


def test_insufficient_data(short_series):
    results = run_causality_analysis(short_series)

    assert results == []


def test_output_schema(lagged_cause_series):
    results = run_causality_analysis(lagged_cause_series)

    assert len(results) >= 1
    for entry in results:
        assert set(entry.keys()) == REQUIRED_KEYS
        assert isinstance(entry["cause"], str)
        assert isinstance(entry["effect"], str)
        assert isinstance(entry["p_value"], float)
        assert isinstance(entry["confidence"], float)
        assert entry["confidence"] == round(1 - entry["p_value"], 3)
