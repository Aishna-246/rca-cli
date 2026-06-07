# CPU Fault — Online Boutique (RCAEval RE2)

## Fault Type

**CPU stress fault** injected into the `recommendationservice` container.
The fault artificially saturates CPU on the target service, causing latency
spikes that cascade downstream to dependent services.

## Ground Truth Root Cause

- **Root cause service:** `recommendationservice`
- **Root cause indicator:** `recommendationservice_cpu` (CPU utilization metric)
- **Dataset case:** `re2-ob_recommendationservice_cpu_0`

## What the Data Contains

- `metrics.csv` — time-series metrics for all Online Boutique services
  (CPU, memory, latency per service), sampled at 1-minute intervals
- `inject_time.txt` — Unix timestamp when the fault was injected

## RCA Command

Once the data is downloaded, run:

```bash
rca --logs examples/re2_real_failure/cpu_fault/metrics.csv \
    --explain
```

Or with a timestamp window (read from inject_time.txt and convert):

```bash
rca --logs examples/re2_real_failure/cpu_fault/metrics.csv \
    --since "$(python -c \"import datetime; print(datetime.datetime.fromtimestamp($(cat examples/re2_real_failure/cpu_fault/inject_time.txt)).strftime('%Y-%m-%dT%H:%M:%S'))\")" \
    --explain
```

## Expected Output

- **#1 Root cause:** recommendationservice (CPU anomaly precedes all downstream effects)
- **Evidence:** CPU utilization spike on recommendationservice, followed by latency
  increases on checkoutservice and frontend
- **Confidence:** High — CPU metric anomaly is the earliest signal in the causal chain

## Citation

Source: RCAEval benchmark (Pham et al., 2024) arXiv:2305.15374  
Dataset hosted at: https://figshare.com/articles/dataset/RCAEval_A_Benchmark_for_Root_Cause_Analysis_of_Microservice_Systems/31048672
