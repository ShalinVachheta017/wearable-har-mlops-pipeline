# Before vs After on 26 Production Datasets

Generated: 2026-03-29 21:29:11

## Summary

- Sessions compared: 26
- Baseline successful runs: 25/26
- Modified successful runs: 25/26
- Dominance >=95% (baseline): 3
- Dominance >=95% (modified): 3
- Mean confidence (baseline): 0.8578
- Mean confidence (modified): 0.8578
- Mean delta dominant_pct (after-before): -13.8282
- Mean delta review_pct (after-before): 63.5510

## Honest interpretation for thesis writing

- This was not a successful performance improvement attempt.
- Mean confidence did not improve; it stayed effectively unchanged across successful pairs.
- Lower class dominance came mostly from abstain/review routing, not better class discrimination.
- Trigger behavior became much stricter (many sessions moved from none to queue_retrain or trigger).
- g-unit fix did not activate in this 26-session set, so it did not explain the observed shifts.
- Stream-reuse guard did not fire because explicit accel/gyro inputs were provided each run.
- One session failed in both variants due to empty accelerometer data (2025-08-13-04-18-52).
- Practical takeaway: keep this as a negative-result ablation and baseline-monitoring evidence.

## Per-session table

| session_id | before dominant | after dominant | before dom% | after dom% | before conf | after conf | before review% | after review% | trigger before | trigger after |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| 2025-03-23-15-23-10 | hand_tapping | REVIEW | 99.94 | 99.61 | 0.9345 | 0.9345 | 0.00 | 99.61 | review | review |
| 2025-07-16-21-03-13 | hand_tapping | hand_tapping | 85.58 | 51.76 | 0.8714 | 0.8714 | 0.00 | 40.26 | none | trigger |
| 2025-07-16-21-46-56 | hand_tapping | REVIEW | 77.92 | 73.04 | 0.8441 | 0.8441 | 0.00 | 73.04 | none | queue_retrain |
| 2025-07-16-22-29-04 | hand_tapping | REVIEW | 84.39 | 78.68 | 0.8596 | 0.8596 | 0.00 | 78.68 | none | queue_retrain |
| 2025-07-16-23-13-09 | hand_tapping | REVIEW | 78.92 | 75.00 | 0.8591 | 0.8591 | 0.00 | 75.00 | none | queue_retrain |
| 2025-07-17-01-48-33 | hand_tapping | REVIEW | 99.50 | 98.13 | 0.9305 | 0.9305 | 0.00 | 98.13 | review | review |
| 2025-07-17-13-49-10 | hand_tapping | hand_tapping | 92.88 | 58.58 | 0.9218 | 0.9218 | 0.00 | 38.79 | none | queue_retrain |
| 2025-07-17-14-16-20 | hand_tapping | REVIEW | 77.68 | 76.84 | 0.8261 | 0.8261 | 0.00 | 76.84 | none | queue_retrain |
| 2025-07-17-15-05-26 | hand_tapping | REVIEW | 79.03 | 66.54 | 0.8507 | 0.8507 | 0.00 | 66.54 | none | queue_retrain |
| 2025-07-17-15-59-12 | hand_tapping | REVIEW | 78.48 | 60.57 | 0.8562 | 0.8562 | 0.00 | 60.57 | none | queue_retrain |
| 2025-07-17-17-39-05 | hand_tapping | REVIEW | 90.70 | 79.07 | 0.8995 | 0.8995 | 0.00 | 79.07 | none | queue_retrain |
| 2025-07-17-18-53-05 | hand_tapping | REVIEW | 56.70 | 42.86 | 0.7770 | 0.7770 | 0.00 | 42.86 | monitor | trigger |
| 2025-07-17-19-27-18 | hand_tapping | REVIEW | 84.89 | 65.55 | 0.8760 | 0.8760 | 0.00 | 65.55 | none | queue_retrain |
| 2025-07-17-21-42-30 | hand_tapping | REVIEW | 78.68 | 67.48 | 0.8455 | 0.8455 | 0.00 | 67.48 | none | queue_retrain |
| 2025-07-19-11-24-04 | ear_rubbing | REVIEW | 84.65 | 87.58 | 0.9347 | 0.9347 | 0.00 | 87.58 | queue_retrain | trigger |
| 2025-07-21-13-58-56 | hand_tapping | REVIEW | 77.35 | 50.90 | 0.8670 | 0.8670 | 0.00 | 50.90 | none | queue_retrain |
| 2025-07-21-16-30-24 | hand_tapping | REVIEW | 71.70 | 58.33 | 0.8200 | 0.8200 | 0.00 | 58.33 | none | queue_retrain |
| 2025-07-25-12-15-48 | hand_tapping | REVIEW | 72.39 | 56.67 | 0.8243 | 0.8243 | 0.00 | 56.67 | none | queue_retrain |
| 2025-07-25-22-11-22 | hand_tapping | REVIEW | 77.07 | 47.93 | 0.8404 | 0.8404 | 0.00 | 47.93 | none | queue_retrain |
| 2025-08-01-12-52-49 | hand_tapping | REVIEW | 67.41 | 55.57 | 0.8126 | 0.8126 | 0.00 | 55.57 | none | queue_retrain |
| 2025-08-11-12-33-33 | hand_tapping | REVIEW | 99.91 | 99.56 | 0.8762 | 0.8762 | 0.00 | 99.56 | review | review |
| 2025-08-11-13-19-03 | hand_tapping | REVIEW | 71.92 | 58.29 | 0.8095 | 0.8095 | 0.00 | 58.29 | none | queue_retrain |
| 2025-08-12-12-09-08 | hand_tapping | REVIEW | 78.58 | 56.13 | 0.8240 | 0.8240 | 0.00 | 56.13 | none | queue_retrain |
| 2025-08-12-17-01-38 | hand_tapping | REVIEW | 77.40 | 66.56 | 0.8081 | 0.8081 | 0.00 | 66.56 | none | queue_retrain |
| 2025-08-13-04-18-52 |  |  | nan | nan | nan | nan | 0.00 | 0.00 |  |  |
| 2025-08-19-08-58-40 | hand_tapping | REVIEW | 85.64 | 52.40 | 0.8762 | 0.8762 | 0.00 | 52.40 | none | queue_retrain |
