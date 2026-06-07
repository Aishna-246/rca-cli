# Memory Fault — Online Boutique (RCAEval RE2)

## Fault Type

**Memory stress fault** injected into the `cartservice` container.
The fault forces memory pressure on the target service, causing OOM-like
conditions, increased GC pressure, and elevated latency for cart operations.

## Ground Truth Root Cause

- **Root cause service:** `cartservice`
- **Root cause indicator:** `cartservice_mem` (memory utilization metric)
- **Dataset case:** `re2-ob_cartservice_mem_0`

## What the Data Contains

- `metrics.csv` — time-series metrics for all Online Boutique services
  (CPU, memory, latency per service), sampled at 1-minute intervals
- `inject_time.txt` — Unix timestamp when the fault was injected

## RCA Command

Once the data is downloaded, run:

```bash
rca --logs examples/re2_real_failure/memory_fault/metrics.csv \
    --explain
```

## Expected Output

- **#1 Root cause:** cartservice (memory anomaly is the earliest and strongest signal)
- **Evidence:** Memory utilization spike on cartservice, latency increase on
  checkoutservice (depends on cartservice for cart operations)
- **Confidence:** High — memory metric is the injected fault indicator per ground truth

## Citation

Source: RCAEval benchmark (Pham et al., 2024) arXiv:2305.15374  
Dataset hosted at: https://figshare.com/articles/dataset/RCAEval_A_Benchmark_for_Root_Cause_Analysis_of_Microservice_Systems/31048672
