"""Generate plain-English explanations via optional LLM integration."""
import os

def generate_explanation(ranked_causes: list[dict], log_events: list[dict]) -> str:
    """
    Generate a plain-English summary of incident root cause, cascade, and fix.
    Uses Anthropic Claude (Haiku 3) via API key in ANTHROPIC_API_KEY.
    Fails gracefully (returns '') if no key or other error.
    """
    try:
        # Try to load .env if present
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass  # dot-ent is optional; doc required adding python-dotenv for best results

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("[yellow]No ANTHROPIC_API_KEY set: skipping LLM explanation.[/yellow]")
            return ""

        # Select top 3 root causes with evidence
        causes_top = ranked_causes[:3] if ranked_causes else []
        causes_fmt = []
        for c in causes_top:
            service = c.get("service", "-")
            metric = c.get("metric", "-")
            conf = c.get("confidence_pct", "?")
            evid = c.get("evidence", {}) or {}
            evid_lines = []
            if "causal_edges" in evid:
                evid_lines.append(f"{evid['causal_edges']} causal edges")
            if (evid.get("log_errors_before", 0)):
                evid_lines.append(f"{evid['log_errors_before']} log errors before incident")
            if evid.get("anomaly_at") is not None:
                evid_lines.append(f"anomaly at {evid['anomaly_at']}")
            evidence = ", ".join([el for el in evid_lines if el])
            causes_fmt.append(
                f"- [{service}.{metric}] (confidence: {conf}%){': ' + evidence if evidence else ''}"
            )
        ranked_causes_formatted = "\n".join(causes_fmt) if causes_fmt else "None detected."

        # Pick 5 most relevant error logs (just top 5 by time or severity)
        # Simple: take first 5; could later sort by importance if present
        log_lines_fmt = []
        for log in log_events[:5]:
            # Seek error, service, message, time
            msg = log.get("message") or log.get("msg") or ""
            time = log.get("timestamp") or log.get("time") or ""
            svc = log.get("service") or ""
            severity = log.get("level") or log.get("severity") or ""
            details = []
            if time:
                details.append(f"[{time}]")
            if svc:
                details.append(f"{svc}")
            if severity:
                details.append(f"{severity.upper()}")
            line = " ".join(details) + (": " if details else "") + msg
            # Truncate for sanity
            if len(line) > 200:
                line = line[:197] + "..."
            log_lines_fmt.append(line)
        log_lines_formatted = "\n".join(f"- {l}" for l in log_lines_fmt) if log_lines_fmt else "No log evidence available."

        # Prompt template
        prompt = f"""
You are an SRE analyzing a production incident. 

Here are the automated root cause findings:

ROOT CAUSES:
{ranked_causes_formatted}

KEY LOG EVIDENCE:
{log_lines_formatted}

Write a 3-sentence plain English explanation of:
1. What was the root cause
2. How it cascaded
3. What to do to fix it

Be specific. Use service names. No jargon.
"""

        # Call Anthropic Claude via REST API
        import requests

        payload = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 300,
            "temperature": 0.3,
            "messages": [
                {
                    "role": "user",
                    "content": prompt.strip(),
                }
            ]
        }
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        url = "https://api.anthropic.com/v1/messages"
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        js = resp.json()
        # Claude-3 returns completions in .content as a list of dicts of type="text"
        content = ""
        completions = js.get("content")
        if completions and isinstance(completions, list):
            content = "".join([p.get("text","") for p in completions if p.get("type")=="text"])
        elif js.get("completion"):  # fallback
            content = js["completion"]
        return content.strip()
    except Exception as e:
        print(f"[yellow]LLM explanation API error: {e}[/yellow]")
        return ""