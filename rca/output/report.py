"""Format terminal reports and write report.json."""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import BarColumn
from rich.align import Align
from rich import box
from datetime import datetime, timedelta
import json
import os

def format_confidence_bar(confidence_pct: int) -> str:
    """
    Returns a unicode bar visualization for confidence, length 10.
    """
    full_blocks = confidence_pct // 10
    partial = confidence_pct % 10
    bar = "█" * full_blocks
    if partial >= 5 and full_blocks < 10:
        bar += "▌"
        full_blocks += 1
    bar = bar.ljust(10, "░")
    return bar

def format_seconds_to_time(seconds: float) -> str:
    """Converts seconds since epoch or float to hh:mm:ss."""
    try:
        dt = datetime.utcfromtimestamp(seconds)
        return dt.strftime("%H:%M:%S")
    except Exception:
        # fallback
        return str(seconds)

def write_json_report(
    ranked_causes: list[dict],
    log_files: list[str],
    metrics_file: str | None,
    event_count: int,
    incident_start: float,
    llm_explanation: str | None = None,
    output_file: str = "report.json",
) -> None:
    """Write analysis results to a JSON report file."""
    report_data = {
        "root_causes": ranked_causes,
        "log_files": log_files,
        "metrics_file": metrics_file,
        "event_count": event_count,
        "incident_start": incident_start,
        "llm_explanation": llm_explanation,
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

def print_report(
    ranked_causes: list[dict],
    log_files: list[str],
    metrics_file: str | None,
    event_count: int,
    incident_start: float,
    llm_explanation: str | None = None,
    output_file: str = "report.json",
) -> None:
    console = Console()
    # HEADER PANEL
    header_text = Text(" RCA-CLI  •  Incident Analysis ", style="bold white on blue", justify="center")
    console.print(Panel(header_text, box=box.DOUBLE, padding=(0,1), expand=False))

    # PARSED INPUT SECTION
    def file_with_lines(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                lines = sum(1 for _ in f)
            return f"{os.path.basename(filename)} ({lines} lines)"
        except Exception:
            return os.path.basename(filename)
    log_files_str = ", ".join([file_with_lines(f) for f in log_files])
    metrics_file_str = os.path.basename(metrics_file) if metrics_file else "none"
    events_str = f"{event_count} anomaly event{'s' if event_count != 1 else ''}"
    parsed_table = Table(show_header=False, box=None, show_edge=False, pad_edge=False, style="cyan")
    parsed_table.add_row("Log files", f": {log_files_str}")
    parsed_table.add_row("Metrics",   f": {metrics_file_str}")
    parsed_table.add_row("Events",    f": {events_str}")

    panel_input = Panel(
        Align.left(parsed_table),
        title="PARSED INPUT",
        border_style="cyan",
        padding=(0,1)
    )
    console.print(panel_input)

    # ROOT CAUSES
    if ranked_causes:
        rc_panel_lines = []
        for d in ranked_causes:
            rank = d.get("rank", "?")
            service = d.get("service", "unknown")
            metric = d.get("metric", "unknown")
            confidence_pct = d.get("confidence_pct", 0)
            conf_bar = format_confidence_bar(confidence_pct)
            evidence = d.get("evidence", {})
            causal_edges = evidence.get("causal_edges")
            log_errors_before = evidence.get("log_errors_before")
            anomaly_at = evidence.get("anomaly_at")
            root_line = f"#{rank}  {service}  [bold][{metric}][/bold]".ljust(40)
            root_line += f"{str(confidence_pct).rjust(3)}%  {conf_bar}"
            rc_panel_lines.append(root_line)
            # Caused/Downstream
            caused = None
            if "causal_edges" in evidence and hasattr(d.get("evidence"), "get"):
                caused = evidence.get("caused")  # For forward compatibility
            if "causes" in d and d["causes"]:
                caused = ", ".join(d["causes"])
            if caused:
                rc_panel_lines.append(f"    Caused: [cyan]{caused}[/cyan]")
            elif rank > 1:
                rc_panel_lines.append(f"    (likely downstream effect of #{rank-1})")
            # Evidence
            details = []
            if isinstance(log_errors_before, int) and log_errors_before > 0:
                details.append(f"{log_errors_before} error log{'s' if log_errors_before != 1 else ''} before incident")
            if anomaly_at is not None:
                tstr = format_seconds_to_time(anomaly_at)
                details.append(f"anomaly at {tstr}")
            if details:
                rc_panel_lines.append("    Evidence: " + ", ".join(details))
            rc_panel_lines.append("")
        rc_panel_body = "\n".join(rc_panel_lines).rstrip()
    else:
        rc_panel_body = "\n[yellow]No root causes identified.[/yellow]\n"

    rc_panel = Panel(
        rc_panel_body,
        title="ROOT CAUSES",
        border_style="magenta",
        padding=(0,1)
    )
    console.print(rc_panel)

    # AI EXPLANATION
    if llm_explanation:
        explain_panel = Panel(
            Align.left(llm_explanation),
            title="AI EXPLANATION",
            border_style="green",
            padding=(1,1)
        )
        console.print(explain_panel)

    # Write JSON report
    write_json_report(
        ranked_causes=ranked_causes,
        log_files=log_files,
        metrics_file=metrics_file,
        event_count=event_count,
        incident_start=incident_start,
        llm_explanation=llm_explanation,
        output_file=output_file,
    )