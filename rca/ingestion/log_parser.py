"""Parse heterogeneous log files into structured records."""

import json
import os
import re


def parse_log_file(filepath: str) -> list[dict]:
    """Parse a heterogeneous log file into structured records."""
    levels = {
        "ERROR": "ERROR",
        "ERR": "ERROR",
        "error": "ERROR",
        "WARN": "WARN",
        "WARNING": "WARN",
        "warn": "WARN",
        "INFO": "INFO",
        "info": "INFO",
        "DEBUG": "DEBUG",
        "debug": "DEBUG",
    }
    patterns = [
        re.compile(
            r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+)\s+"
            r"(?P<level>[A-Z]+)\s+\[(?P<service>[^\]]+)\]\s+(?P<msg>.+)$"
        ),
        re.compile(
            r"^(?P<timestamp>[A-Z][a-z]{2}\s+\d{1,2} \d{2}:\d{2}:\d{2})\s+"
            r"(?P<service>[^\s\[]+)(?:\[\d+\])?:\s+(?P<level>[A-Z]+)\s+(?P<msg>.+)$"
        ),
        re.compile(
            r"^(?P<timestamp>\d+\.\d+)\s+(?P<level>[A-Z]+)\s+"
            r"\[(?P<service>[^\]]+)\]\s+(?P<msg>.+)$"
        ),
    ]
    level_choices = {"ERROR", "WARN", "INFO", "DEBUG"}

    if not filepath or not os.path.exists(filepath) or not os.path.isfile(filepath):
        return []

    filename_stem = os.path.splitext(os.path.basename(filepath))[0]
    records: list[dict] = []

    try:
        with open(filepath, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                if line.startswith("{") and line.endswith("}"):
                    try:
                        record = json.loads(line)
                        level = levels.get(str(record.get("level", "")).upper(), "UNKNOWN")
                        records.append(
                            {
                                "ts_raw": record.get("timestamp", ""),
                                "level": level if level in level_choices else "UNKNOWN",
                                "service": record.get("service") or filename_stem,
                                "msg": record.get("message", ""),
                            }
                        )
                        continue
                    except json.JSONDecodeError:
                        continue

                matched = False
                for pat in patterns:
                    match = pat.match(line)
                    if not match:
                        continue
                    data = match.groupdict()
                    level = levels.get(data.get("level", "").upper(), "UNKNOWN")
                    records.append(
                        {
                            "ts_raw": data.get("timestamp", ""),
                            "level": level if level in level_choices else "UNKNOWN",
                            "service": data.get("service") or filename_stem,
                            "msg": data.get("msg", ""),
                        }
                    )
                    matched = True
                    break
                if not matched:
                    continue
    except OSError:
        return []

    return records
