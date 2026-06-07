"""
Download representative RE2 failure cases from the RCAEval benchmark.

RCAEval is an open-source benchmark for root cause analysis of microservice
systems. This script downloads three cases from the RE2-OB (Online Boutique)
dataset — one CPU fault, one memory fault, one network (packet loss) fault —
and saves them into examples/re2_real_failure/ for use with rca-cli.

Data source:
  RCAEval benchmark (Pham et al., 2024) arXiv:2305.15374
  https://figshare.com/articles/dataset/RCAEval_A_Benchmark_for_Root_Cause_Analysis_of_Microservice_Systems/31048672

Usage:
  python scripts/download_datasets.py
"""

from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("requests is required: pip install requests")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Figshare direct download URL for RCAEval dataset (publicly available, MIT)
# This is the RE2-OB (Online Boutique) portion of the benchmark.
FIGSHARE_BASE = "https://figshare.com/ndownloader/files"

# Figshare file IDs for the RE2-OB dataset zip (from the RCAEval Figshare page)
# https://figshare.com/articles/dataset/RCAEval_.../31048672
# Each entry: (figshare_file_id, archive_subpath, local_dest_dir)
CASES = [
    {
        "name": "CPU fault (recommendationservice)",
        "fault_type": "cpu",
        "service": "recommendationservice",
        # RE2-OB naming: re2-ob_recommendationservice_cpu_0
        "archive_subdir": "re2-ob_recommendationservice_cpu_0",
        "dest": "examples/re2_real_failure/cpu_fault",
    },
    {
        "name": "Memory fault (cartservice)",
        "fault_type": "mem",
        "service": "cartservice",
        "archive_subdir": "re2-ob_cartservice_mem_0",
        "dest": "examples/re2_real_failure/memory_fault",
    },
    {
        "name": "Network fault / packet loss (paymentservice)",
        "fault_type": "loss",
        "service": "paymentservice",
        "archive_subdir": "re2-ob_paymentservice_loss_0",
        "dest": "examples/re2_real_failure/network_fault",
    },
]

# Figshare file ID for the RE2-OB zip archive.
# Retrieved from: https://figshare.com/articles/dataset/RCAEval_.../31048672
RE2_OB_FIGSHARE_FILE_ID = "57668430"
RE2_OB_DOWNLOAD_URL = f"{FIGSHARE_BASE}/{RE2_OB_FIGSHARE_FILE_ID}"

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def download_archive(url: str, desc: str) -> bytes:
    """Stream-download a URL and return its raw bytes."""
    print(f"Downloading {desc} ...")
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()

    total = int(resp.headers.get("content-length", 0))
    received = 0
    chunks = []
    for chunk in resp.iter_content(chunk_size=65536):
        chunks.append(chunk)
        received += len(chunk)
        if total:
            pct = received * 100 // total
            print(f"\r  {pct}% ({received // 1024} KB / {total // 1024} KB)", end="", flush=True)
    print()
    return b"".join(chunks)


def extract_case(zf: zipfile.ZipFile, subdir: str, dest: Path) -> bool:
    """
    Extract metrics.json (converted to metrics.csv) and inject_time.txt
    from a subdirectory inside the zip into dest/.
    Returns True if the case was found, False otherwise.
    """
    dest.mkdir(parents=True, exist_ok=True)

    # Normalise: zip may have a top-level folder or not
    all_names = zf.namelist()
    # Find the matching subdir prefix (handles optional top-level wrapper)
    prefix = next(
        (n for n in all_names if subdir in n and n.endswith("metrics.json")),
        None,
    )
    if prefix is None:
        print(f"  WARNING: '{subdir}' not found in archive. Skipping.")
        return False

    # Derive the folder prefix up to and including subdir
    folder_prefix = prefix[: prefix.index(subdir) + len(subdir) + 1]

    extracted_any = False
    for target_filename in ("metrics.json", "inject_time.txt", "logs.csv"):
        member = folder_prefix + target_filename
        if member not in all_names:
            continue
        data = zf.read(member)

        if target_filename == "metrics.json":
            # Convert JSON → CSV so rca-cli can consume it directly
            try:
                records = json.loads(data)
                if isinstance(records, list) and records:
                    import csv as csv_mod

                    csv_path = dest / "metrics.csv"
                    with csv_path.open("w", newline="", encoding="utf-8") as fh:
                        writer = csv_mod.DictWriter(fh, fieldnames=records[0].keys())
                        writer.writeheader()
                        writer.writerows(records)
                    print(f"  Saved metrics.csv ({len(records)} rows)")
                    extracted_any = True
                else:
                    # Fallback: save raw JSON
                    (dest / "metrics.json").write_bytes(data)
                    print("  Saved metrics.json (unexpected format — skipped CSV conversion)")
                    extracted_any = True
            except Exception as exc:
                print(f"  WARNING: Could not convert metrics.json: {exc}")
                (dest / "metrics.json").write_bytes(data)
                extracted_any = True
        else:
            out_path = dest / target_filename
            out_path.write_bytes(data)
            print(f"  Saved {target_filename}")
            extracted_any = True

    return extracted_any


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("RCAEval RE2 Dataset Downloader")
    print("Source: arXiv:2305.15374 / Pham et al., 2024")
    print("=" * 60)
    print()

    # Download the RE2-OB archive once
    try:
        raw = download_archive(RE2_OB_DOWNLOAD_URL, "RE2-OB dataset (Online Boutique)")
    except requests.RequestException as exc:
        sys.exit(
            f"\nFailed to download dataset: {exc}\n"
            "Check your internet connection and try again.\n"
            "Manual download: https://figshare.com/articles/dataset/"
            "RCAEval_A_Benchmark_for_Root_Cause_Analysis_of_Microservice_Systems/31048672"
        )

    # Verify it's a zip
    if not zipfile.is_zipfile(io.BytesIO(raw)):
        sys.exit(
            "Downloaded file is not a ZIP archive.\n"
            "The Figshare file ID may have changed. Check:\n"
            "https://figshare.com/articles/dataset/"
            "RCAEval_A_Benchmark_for_Root_Cause_Analysis_of_Microservice_Systems/31048672"
        )

    print()
    success_count = 0
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        for case in CASES:
            dest = PROJECT_ROOT / case["dest"]
            print(f"Extracting: {case['name']}")
            print(f"  → {dest.relative_to(PROJECT_ROOT)}")
            ok = extract_case(zf, case["archive_subdir"], dest)
            if ok:
                success_count += 1
            print()

    print("=" * 60)
    print(f"Done. {success_count}/{len(CASES)} cases extracted.")
    print()
    print("Run the demos with:")
    print()
    print("  # CPU fault")
    print("  rca --logs examples/re2_real_failure/cpu_fault/metrics.csv --explain")
    print()
    print("  # Memory fault")
    print("  rca --logs examples/re2_real_failure/memory_fault/metrics.csv --explain")
    print()
    print("  # Network fault")
    print("  rca --logs examples/re2_real_failure/network_fault/metrics.csv --explain")
    print()
    print("Citation: RCAEval (Pham et al., 2024) arXiv:2305.15374")
    print("=" * 60)


if __name__ == "__main__":
    main()
