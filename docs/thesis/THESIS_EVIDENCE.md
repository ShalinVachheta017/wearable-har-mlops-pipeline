# THESIS EVIDENCE

Track every thesis claim with a reproducible artifact.

## Mapping Table

| Experiment | Artifact | Chapter | Notes |
|---|---|---|---|
| Baseline evaluation | mlruns/<run_id> | Chapter 7 | Accuracy/F1 summary |
| Drift experiment | artifacts/<run_id>/monitoring/monitoring_summary.json | Chapter 6 | Include max_drift and channel counts |
| Trigger evaluation | artifacts/<run_id>/trigger/trigger_decision.json | Chapter 6 | Include alert level + should_retrain |
| Runtime benchmark | outputs/evaluation/* or custom benchmark outputs | Chapter 7 | Include throughput and latency |
| Unit-fix + abstain comparison (26 sessions) | thesis/tables/before_vs_after_26datasets.csv + thesis/chapters/before_vs_after_26datasets.md | Chapter 7 | Negative-result ablation; confidence unchanged, review routing increased |

## Current Wave Evidence

| Wave | Report | Verdict |
|---|---|---|
| Wave 1 | ../../reports/repo_audit/WAVE1_STAGE5_STAGE7_LABELMAP_FIXES.md | PASS |
| Wave 2 Step 1 | ../../reports/repo_audit/WAVE2_BASELINE_SPACE_VERIFICATION.md | FAIL |
| Wave 2 Step 2 | ../../reports/repo_audit/WAVE2_STAGE6_BASELINE_SPACE_FIX_VALIDATION.md | PASS |
| Wave 3 (unit-fix + abstain, 26 sessions) | ../../thesis/chapters/before_vs_after_26datasets.md | FAIL |
