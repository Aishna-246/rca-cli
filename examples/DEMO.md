# RCA-CLI Demo Scenarios

Three real-world incident scenarios you can run immediately to see RCA-CLI in action.
Each tells a complete causal story — from root cause to cascade to recovery.

---

## Setup (one time)

```bash
git clone https://github.com/Aishna-246/rca-cli
cd rca-cli
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

---

## Demo 1 — HDFS Block Replication Failure
**Scenario:** A disk fails on a Hadoop datanode, triggering block under-replication
and forcing the NameNode into Safe Mode, blocking all writes cluster-wide.

**Based on:** Loghub HDFS dataset (Wei Xu et al., SOSP 2009)

```bash
rca --since "14:22:00" \
    --logs examples/hdfs_failure/namenode.log \
            examples/hdfs_failure/datanode02.log \
    --metrics examples/hdfs_failure/prom.json \
    --explain
```

**What to expect:**
- Root cause: `datanode02` disk failure (disk I/O latency spike at 14:22:10)
- Cascade: dead node → 3,821 under-replicated blocks → Safe Mode → write failures
- Recovery detected at 14:25:00 when replication completes

---

## Demo 2 — Microservice Cascade: DB Lock → Payment Outage
**Scenario:** A PostgreSQL autovacuum lock causes query timeouts in payment-service,
exhausting its connection pool and thread pool, triggering the API gateway
circuit breaker and causing checkout failures for 2 minutes.

**Based on:** Real PostgreSQL autovacuum cascade failure pattern (PGConf 2023)

```bash
rca --since "14:22:30" \
    --logs examples/microservice_cascade/db-primary.log \
            examples/microservice_cascade/payment-service.log \
            examples/microservice_cascade/api-gateway.log \
    --metrics examples/microservice_cascade/prom.json \
    --explain
```

**What to expect:**
- Root cause: `db-primary` lock contention (autovacuum at 14:22:38 — earliest anomaly)
- Cascade: lock → query timeouts → connection exhaustion → thread exhaustion → 503s → circuit breaker
- api-gateway is the last affected service, not the cause

---

## Demo 3 — JVM Memory Leak: OOM After 2.75 Hours
**Scenario:** A recommendation service's LRU cache has a memory leak.
Heap grows steadily for 2 hours 45 minutes before the JVM runs out of memory.

```bash
rca --since "12:30:00" \
    --logs examples/memory_leak/recommendation-service.log \
    --explain
```

**What to expect:**
- Root cause: `recommendation-service` heap memory leak in UserProfileCache
- Evidence: progressive heap growth 134MB → 489MB over 2.75 hours
- OOM at line 89 of UserProfileCache.java

---

## Live Dashboard Demo

1. Start the API: `python -m rca.api.server`
2. Start the dashboard: `cd dashboard && npm start`
3. Open http://localhost:3000
4. Click **Run New Analysis**
5. Upload any log files from the `examples/` folder
6. See the causal graph render in real time

Or visit the live deployment: **https://rca-cli.vercel.app**

---

## Demo 4 — Real Production Failures (RCAEval Benchmark)

**What is RCAEval?**  
RCAEval is a peer-reviewed open-source benchmark for root cause analysis of
microservice systems, published at ASE 2024 and WWW 2025. It contains **735 real
failure cases** across nine datasets, each with multi-source telemetry (metrics,
logs, traces) and a documented ground truth root cause service and indicator.

These are not synthetic scenarios — they are real faults injected into running
microservice deployments (Online Boutique, Sock Shop, Train Ticket) with verified
outcomes.

**Download the data first (one time):**

```bash
python scripts/download_datasets.py
```

---

### Demo 4a — CPU Fault (recommendationservice)

A CPU stress fault is injected into `recommendationservice`, saturating its CPU
and causing latency spikes that cascade to `checkoutservice` and `frontend`.

**Ground truth root cause:** `recommendationservice` (CPU metric)

```bash
rca --logs examples/re2_real_failure/cpu_fault/metrics.csv \
    --explain
```

**What to expect:**
- Root cause: `recommendationservice` CPU utilization anomaly
- Cascade: recommendation latency → checkout latency → frontend errors
- Confidence ranked highest for the injected service

---

### Demo 4b — Memory Fault (cartservice)

A memory stress fault is injected into `cartservice`, forcing memory pressure
and elevated GC activity that degrades cart operation latency downstream.

**Ground truth root cause:** `cartservice` (memory metric)

```bash
rca --logs examples/re2_real_failure/memory_fault/metrics.csv \
    --explain
```

**What to expect:**
- Root cause: `cartservice` memory utilization spike
- Cascade: cart latency → checkout failures
- Memory metric anomaly is the earliest signal in the causal chain

---

### Demo 4c — Network Fault / Packet Loss (paymentservice)

A packet loss fault is injected on `paymentservice`'s network interface, causing
intermittent request failures and elevated latency through the checkout flow.

**Ground truth root cause:** `paymentservice` (latency metric from packet loss)

```bash
rca --logs examples/re2_real_failure/network_fault/metrics.csv \
    --explain
```

**What to expect:**
- Root cause: `paymentservice` latency spike (packet loss origin)
- Cascade: payment failures → checkout errors → frontend error rate increase
- Network-induced latency precedes all other downstream anomalies

---

### Research Citation

These cases are drawn directly from the RCAEval benchmark:

> Pham, L., Ha, H., & Zhang, H. (2024). Root Cause Analysis for Microservice
> System based on Causal Inference: How Far Are We? *Proceedings of the 39th
> IEEE/ACM International Conference on Automated Software Engineering (ASE)*, 706–715.
> arXiv:2305.15374

Dataset: https://figshare.com/articles/dataset/RCAEval_A_Benchmark_for_Root_Cause_Analysis_of_Microservice_Systems/31048672

---

## Research Citations

These demo scenarios are grounded in published research:

- Wei Xu et al., "Detecting Large-Scale System Problems by Mining Console Logs", SOSP 2009
- Jieming Zhu et al., "Tools and Benchmarks for Automated Log Parsing", ICSE 2019  
- He et al., "An Evaluation Study on Log Parsing and Its Use in Log Mining", DSN 2016
- arXiv:2408.00803 — "Root Cause Analysis in Microservice Architectures: A Survey" (2024)
- IJETCSIT Dec 2024 — "AI-Driven Log Analysis Reduces MTTR from 47min to 8min"
