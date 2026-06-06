# Manual Test Cases

## MTC-01: Happy Path — Full Pipeline
**Setup:** Use tests/sample_logs/ files
**Command:** rca --since "02:10" --logs tests/sample_logs/orders.log tests/sample_logs/payment.log --metrics tests/sample_logs/prom.json
**Expected:** 
- Exit code 0
- Report shows orders-service as #1 root cause with >70% confidence
- payment-service appears as affected downstream
- report.json created in current directory
**Pass/Fail:** ___

## MTC-02: Missing Metrics File
**Command:** rca --since "02:10" --logs tests/sample_logs/orders.log
**Expected:** 
- Runs without crashing
- Report shows log-based analysis only
- Warning printed: "No metrics provided — skipping metric anomaly detection"
**Pass/Fail:** ___

## MTC-03: Single Log File
**Command:** rca --logs tests/sample_logs/orders.log
**Expected:** Report generated with just orders-service data. No crash.
**Pass/Fail:** ___

## MTC-04: Invalid Log File Path
**Command:** rca --logs ./nonexistent.log
**Expected:** Warning printed, file skipped. If all files invalid: exit 1.
**Pass/Fail:** ___

## MTC-05: --explain Flag (requires ANTHROPIC_API_KEY)
**Command:** rca --since "02:10" --logs tests/sample_logs/orders.log --explain
**Expected:** 
- Report includes "AI EXPLANATION" section
- Explanation mentions orders-service
- No API key in output
**Pass/Fail:** ___

## MTC-06: --explain Flag Without API Key
**Setup:** Unset ANTHROPIC_API_KEY
**Expected:** Warning: "ANTHROPIC_API_KEY not set. Skipping explanation." No crash.
**Pass/Fail:** ___

## MTC-07: Large Log File Performance
**Setup:** Generate a 100,000-line log file
**Expected:** Completes in under 10 seconds
**Pass/Fail:** ___

## MTC-08: Logs With No Anomalies
**Setup:** Create a log file with only INFO lines
**Expected:** Report says "No anomaly events found. System appears healthy."
**Pass/Fail:** ___