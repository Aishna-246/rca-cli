"""Typer CLI entry point for the rca command."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console

from rca.api.analysis import run_incident_analysis
from rca.output.report import print_report

app = typer.Typer()
console = Console()


@app.command()
def main(
    logs: Optional[List[Path]] = typer.Option(
        None, "--logs", help="Log files to analyze (optional if --metrics provided)"
    ),
    metrics: Optional[Path] = typer.Option(
        None, "--metrics", help="Metrics file in Prometheus JSON or RCAEval CSV format"
    ),
    since: Optional[str] = typer.Option(None, "--since", help="Start of incident window"),
    explain: bool = typer.Option(False, "--explain", help="Generate LLM plain-English explanation"),
    output_json: Optional[Path] = typer.Option(None, "--output", help="Save JSON report to file"),
) -> None:
    """Analyze logs and metrics to detect root causes."""
    try:
        log_paths = list(logs) if logs else []

        if not log_paths and not metrics:
            console.print("[bold red]Error: Provide at least one --logs file or a --metrics file.[/bold red]")
            raise typer.Exit(code=1)

        if not log_paths and metrics:
            console.print("[yellow]Running in metrics-only mode — no log files provided[/yellow]")

        result = run_incident_analysis(
            log_paths=log_paths,
            metrics_path=metrics,
            since=since,
            explain=explain,
        )

        print_report(
            ranked_causes=result["root_causes"],
            log_files=[str(p) for p in log_paths],
            metrics_file=str(metrics) if metrics else None,
            event_count=result["event_count"],
            incident_start=result["incident_start"],
            llm_explanation=result.get("llm_explanation"),
            output_file=str(output_json) if output_json else "report.json",
        )

        raise typer.Exit(code=0)
    except typer.Exit:
        raise
    except ValueError as exc:
        console.print(f"[bold red]Error: {exc}[/bold red]")
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        console.print(f"[bold red]Error: {exc}[/bold red]")
        raise typer.Exit(code=1) from exc


def run() -> None:
    app()


if __name__ == "__main__":
    run()
