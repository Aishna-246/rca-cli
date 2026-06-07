# Network Fault (Packet Loss) — Online Boutique (RCAEval RE2)

## Fault Type

**Network packet loss fault** injected on the `paymentservice` container.
The fault introduces packet loss on the target service's network interface,
causing intermittent request failures and elevated latency that propagate
through the checkout flow.

## Ground Truth Root Cause

- **Root cause service:** `paymentservice`
- **Root cause indicator:** `paymentservice_latency` (service latency metric)
- **Dataset case:** `re2-ob_paymentservice_loss_0`

## What the Data Contains

- `metrics.csv` — time-series metrics for all Online Boutique services
  (CPU, memory, latency per service), sampled at 1-minute intervals
- `inject_time.txt` — Unix timestamp when the fault was injected

## RCA Command

Once the data is downloaded, run:

```bash
rca --logs examples/re2_real_failure/network_fault/metrics.csv \
    --explain
```

## Expected Output

- **#1 Root cause:** paymentservice (latency anomaly from packet loss is the origin)
- **Evidence:** paymentservice latency spike precedes checkoutservice failures and
  frontend error rate increase
- **Confidence:** High — network-induced latency on paymentservice is the injected
  fault per ground truth annotation

## Citation

Source: RCAEval benchmark (Pham et al., 2024) arXiv:2305.15374  
Dataset hosted at: https://figshare.com/articles/dataset/RCAEval_A_Benchmark_for_Root_Cause_Analysis_of_Microservice_Systems/31048672
