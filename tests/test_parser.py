"""Tests for log and metrics parsers."""

import json

import pytest

from rca.ingestion.log_parser import parse_log_file


@pytest.fixture
def standard_log_line() -> str:
    return "2024-01-01 02:11:34,221 ERROR [orders] Thread pool exhausted"


@pytest.fixture
def syslog_log_line() -> str:
    return "Jan  1 02:11:34 orders[1234]: ERROR DB connection timeout"


@pytest.fixture
def json_log_line() -> str:
    return json.dumps(
        {
            "timestamp": "2024-01-01T02:11:34Z",
            "level": "error",
            "service": "orders",
            "message": "Payment failed",
        }
    )


@pytest.fixture
def all_levels_log_content() -> str:
    return "\n".join(
        [
            "2024-01-01 02:11:34,100 ERROR [orders-service] error event",
            "2024-01-01 02:11:35,200 WARN [orders-service] warn event",
            "2024-01-01 02:11:36,300 INFO [orders-service] info event",
            "2024-01-01 02:11:37,400 DEBUG [orders-service] debug event",
        ]
    )


def _write_log(tmp_path, name: str, content: str) -> str:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return str(path)


def test_parse_standard_format(tmp_path, standard_log_line):
    path = _write_log(tmp_path, "orders.log", standard_log_line + "\n")
    records = parse_log_file(path)

    assert len(records) == 1
    record = records[0]
    assert record["ts_raw"] == "2024-01-01 02:11:34,221"
    assert record["level"] == "ERROR"
    assert record["service"] == "orders"
    assert record["msg"] == "Thread pool exhausted"


def test_parse_syslog_format(tmp_path, syslog_log_line):
    path = _write_log(tmp_path, "orders.log", syslog_log_line + "\n")
    records = parse_log_file(path)

    assert len(records) == 1
    record = records[0]
    assert record["ts_raw"] == "Jan  1 02:11:34"
    assert record["level"] == "ERROR"
    assert record["service"] == "orders"
    assert record["msg"] == "DB connection timeout"


def test_parse_json_log(tmp_path, json_log_line):
    path = _write_log(tmp_path, "orders.log", json_log_line + "\n")
    records = parse_log_file(path)

    assert len(records) == 1
    record = records[0]
    assert record["ts_raw"] == "2024-01-01T02:11:34Z"
    assert record["level"] == "ERROR"
    assert record["service"] == "orders"
    assert record["msg"] == "Payment failed"


def test_skip_unparseable_line(tmp_path):
    content = "not a log line\n!!! garbage @@@\n"
    path = _write_log(tmp_path, "garbage.log", content)
    records = parse_log_file(path)

    assert records == []


def test_empty_file(tmp_path):
    path = _write_log(tmp_path, "empty.log", "")
    records = parse_log_file(path)

    assert records == []


def test_missing_file():
    records = parse_log_file("/nonexistent/path/does-not-exist.log")

    assert records == []


def test_level_extraction(tmp_path, all_levels_log_content):
    path = _write_log(tmp_path, "levels.log", all_levels_log_content + "\n")
    records = parse_log_file(path)

    assert len(records) == 4
    assert [r["level"] for r in records] == ["ERROR", "WARN", "INFO", "DEBUG"]


def test_service_extracted_from_brackets(tmp_path):
    line = "2024-01-01 02:11:34,500 ERROR [orders-service] pool exhausted"
    path = _write_log(tmp_path, "orders.log", line + "\n")
    records = parse_log_file(path)

    assert len(records) == 1
    assert records[0]["service"] == "orders-service"
