"""End-to-end integration tests for the RCA CLI pipeline."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from rca.cli import app

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_LOGS = PROJECT_ROOT / "tests" / "sample_logs"


def _cli_path(path: Path) -> str:
    """Format a path for Typer CLI args (forward slashes on Windows)."""
    return path.as_posix()


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def sample_orders() -> Path:
    return SAMPLE_LOGS / "orders.log"


@pytest.fixture
def sample_payment() -> Path:
    return SAMPLE_LOGS / "payment.log"


@pytest.fixture
def sample_metrics() -> Path:
    return SAMPLE_LOGS / "prom.json"


def test_full_pipeline_happy_path(
    runner: CliRunner,
    tmp_path: Path,
    sample_orders: Path,
    sample_payment: Path,
    sample_metrics: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    report_path = tmp_path / "report.json"
    monkeypatch.chdir(PROJECT_ROOT)

    result = runner.invoke(
        app,
        [
            "--logs",
            _cli_path(sample_orders),
            "--logs",
            _cli_path(sample_payment),
            "--metrics",
            _cli_path(sample_metrics),
            "--since",
            "2024-01-01T02:11:00",
            "--output",
            _cli_path(report_path),
        ],
    )

    assert result.exit_code == 0, result.output

    assert report_path.exists()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    root_causes = report["root_causes"]
    assert len(root_causes) >= 1

    top = root_causes[0]
    # payment-service is the correct root cause: its metrics spike at 1704075180
    # (payment_request_duration_p99 and db_connection_pool_used), which precedes
    # the orders-service thread pool spike at 1704075240.
    assert top["service"] == "payment-service"
    assert top["confidence_pct"] > 50


def test_no_metrics_path(
    runner: CliRunner,
    tmp_path: Path,
    sample_orders: Path,
    sample_payment: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    report_path = tmp_path / "report.json"
    monkeypatch.chdir(PROJECT_ROOT)

    result = runner.invoke(
        app,
        [
            "--logs",
            _cli_path(sample_orders),
            "--logs",
            _cli_path(sample_payment),
            "--since",
            "2024-01-01T02:11:00",
            "--output",
            _cli_path(report_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert result.exception is None

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert len(report["root_causes"]) >= 1


def test_empty_log_path(
    runner: CliRunner,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    empty_log = tmp_path / "empty.log"
    empty_log.write_text("", encoding="utf-8")
    report_path = tmp_path / "report.json"
    monkeypatch.chdir(PROJECT_ROOT)

    result = runner.invoke(
        app,
        [
            "--logs",
            _cli_path(empty_log),
            "--output",
            _cli_path(report_path),
        ],
    )

    assert result.exit_code == 1
    assert not report_path.exists()
