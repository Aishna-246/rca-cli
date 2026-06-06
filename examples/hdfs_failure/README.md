# Demo: HDFS Block Replication Failure

## What happened

A real-world style incident based on HDFS failure patterns documented in
the Loghub dataset (Wei Xu et al., SOSP 2009).

**Timeline:**
- `14:22:10` — datanode02 disk I/O latency spikes from 15ms → 5,221ms
- `14:22:13` — datanode02 disk fails completely, DataNode process shuts down
- `14:22:45` — NameNode declares datanode02 dead after heartbeat timeout (30s)
- `14:22:45` — 3,821 blocks added to replication queue (all blocks that were on datanode02)
- `14:22:55` — NameNode enters Safe Mode, blocking all write operations
- `14:23:00` — Client write RPCs start failing across the cluster
- `14:25:00` — Replication complete across remaining 4 datanodes, Safe Mode exits

**Root cause:** Disk failure on datanode02 caused heartbeat timeout,
triggering Safe Mode and write unavailability across the cluster.

## How to run this demo

```bash
rca --since "14:22:00" \
    --logs examples/hdfs_failure/namenode.log \
            examples/hdfs_failure/datanode02.log \
    --metrics examples/hdfs_failure/prom.json \
    --explain
```

## Expected output

RCA-CLI should identify:
- **#1 Root cause:** datanode02 disk failure (disk I/O latency spike precedes all other anomalies)
- **Cascade:** datanode02 death → under-replicated blocks → NameNode safe mode → write failures
- **AI Explanation:** Plain English summary of what to do (replace the failed disk on datanode02)

## Data source

Log format based on Apache Hadoop HDFS logs.
Incident pattern based on: Wei Xu et al., "Detecting Large-Scale System Problems
by Mining Console Logs", SOSP 2009.
Dataset reference: https://github.com/logpai/loghub
