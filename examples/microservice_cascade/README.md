# Demo: Microservice Cascade Failure — DB Autovacuum Lock

## What happened

A PostgreSQL autovacuum job held an `AccessShareLock` on the `transactions`
table for 4+ seconds, causing query timeouts in payment-service, which
exhausted its DB connection pool, which exhausted its thread pool,
which caused the API gateway to receive 503s and open its circuit breaker.

**Timeline:**
- `14:22:38` — PostgreSQL autovacuum acquires lock on `transactions` table
- `14:22:40` — 8 queries waiting for lock
- `14:22:44` — Lock wait timeouts start in payment-service (2000ms threshold)
- `14:22:58` — payment-service DB queries slow: 2341ms, 1891ms
- `14:22:59` — payment-service DB connection pool: 18 active, 4 waiting
- `14:23:00` — DB connection timeouts. payment-service thread pool starts filling
- `14:23:01` — payment-service thread pool exhausted (50/50). Rejecting requests
- `14:23:11` — api-gateway receives first 503 from payment-service
- `14:23:13` — api-gateway circuit breaker OPENS. All checkout requests fail
- `14:25:10` — DB recovered. payment-service healthy. Circuit breaker closes

**Root cause:** PostgreSQL autovacuum lock contention on `public.transactions`

## How to run this demo

```bash
rca --since "14:22:30" \
    --logs examples/microservice_cascade/db-primary.log \
            examples/microservice_cascade/payment-service.log \
            examples/microservice_cascade/api-gateway.log \
    --metrics examples/microservice_cascade/prom.json \
    --explain
```

## Expected output

RCA-CLI should identify:
- **#1 Root cause:** db-primary lock contention (earliest anomaly, causes everything downstream)
- **Cascade:** autovacuum lock → query timeouts → connection pool exhaustion → thread pool exhaustion → 503s → circuit breaker
- **AI Explanation:** Fix by tuning autovacuum settings or adding `lock_timeout` to payment-service queries

## What makes this realistic

This exact failure mode (autovacuum lock → connection pool cascade) is one of the
most common production incidents in PostgreSQL-backed microservice systems.
Documented in: Percona PostgreSQL blog, PGConf talks 2022-2024.
