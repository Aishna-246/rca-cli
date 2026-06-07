# RE2 Real Production Failures (RCAEval Benchmark)

This folder contains three representative failure cases extracted from the
**RCAEval RE2 dataset** — a publicly available benchmark of real microservice
failures with documented ground truth root causes.

## About RE2

RE2 is one of three benchmark suites in RCAEval. It covers **270 failure cases**
across three microservice systems (Online Boutique, Sock Shop, Train Ticket),
each with multi-source telemetry: metrics, logs, and traces.

**Fault types covered:** cpu, mem, disk, delay, loss, socket  
**Services per system:** 5  
**Repetitions per fault/service pair:** 3  
**Ground truth:** Each case has an annotated root cause service and root cause indicator

## Folder Structure

```
re2_real_failure/
├── README.md               ← this file
├── cpu_fault/
│   ├── metrics.csv         ← time-series metrics (downloaded by script)
│   └── README.md           ← fault details + rca command
├── memory_fault/
│   ├── metrics.csv
│   └── README.md
└── network_fault/
    ├── metrics.csv
    └── README.md
```

## How to Get the Data

Run the download script from the project root:

```bash
python scripts/download_datasets.py
```

This downloads and extracts the three representative cases from the
RCAEval RE2 Online Boutique dataset hosted on Figshare.

## Citation

Source: RCAEval benchmark (Pham et al., 2024) arXiv:2305.15374

```bibtex
@inproceedings{pham2024root,
  title={Root Cause Analysis for Microservice System based on Causal Inference: How Far Are We?},
  author={Pham, Luan and Ha, Huong and Zhang, Hongyu},
  booktitle={Proceedings of the 39th IEEE/ACM International Conference on Automated Software Engineering},
  pages={706--715},
  year={2024}
}
```
