# Demo: JVM Memory Leak — Recommendation Service OOM

## What happened

A recommendation service's `UserProfileCache` had a memory leak —
user profile objects were being added to the cache but the LRU
eviction policy wasn't working correctly, causing heap to grow
steadily over 2.75 hours until OOM.

**Timeline:**
- `10:00` — Service starts. Heap: 134MB
- `10:00–11:00` — Normal operation. Heap grows slowly: 134MB → 221MB
- `11:00–12:00` — Heap growth accelerates: 221MB → 367MB. GC pressure increases
- `12:00–12:45` — Critical phase. Major GC runs every 15 minutes, recovers less each time
- `12:45:00` — Heap at 489MB/512MB (95%). GC overhead limit exceeded
- `12:45:10` — OutOfMemoryError thrown. All requests fail
- `12:45:11` — Process terminates

**Root cause:** Memory leak in `UserProfileCache.put()` at line 89 —
HashMap unbounded growth due to broken LRU eviction logic.

## How to run this demo

```bash
rca --since "12:30:00" \
    --logs examples/memory_leak/recommendation-service.log \
    --explain
```

## Expected output

- **#1 Root cause:** recommendation-service heap memory leak
- **Evidence:** Progressive heap growth over 2.75 hours, GC recovery
  decreasing each cycle, OOM at UserProfileCache line 89
- **AI Explanation:** Fix the LRU eviction logic in UserProfileCache,
  or add `-XX:+HeapDumpOnOutOfMemoryError` to capture the leak on next OOM
