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
| Self-recorded Garmin external evaluation | reports/self_recorded_eval_2026_05_05/EVALUATION_REPORT.md | Chapters 5-7 | Parser fixed, labels fixed, units fixed, frozen model evaluated on User 7 |
| Self-recorded domain-shift comparison | reports/self_recorded_eval_2026_05_05/DISTRIBUTION_COMPARISON_REPORT.md | Chapters 7-8 | Self-recorded data closest to training but still shifted; retraining remains gated |
| Self-recorded claim-evidence table | reports/self_recorded_eval_2026_05_05/CLAIM_EVIDENCE_TABLE.md | Appendix / defense | Compact evidence map for parser, labels, units, metrics, distribution, governance |

## Current Wave Evidence

| Wave | Report | Verdict |
|---|---|---|
| Wave 1 | ../../reports/repo_audit/WAVE1_STAGE5_STAGE7_LABELMAP_FIXES.md | PASS |
| Wave 2 Step 1 | ../../reports/repo_audit/WAVE2_BASELINE_SPACE_VERIFICATION.md | FAIL |
| Wave 2 Step 2 | ../../reports/repo_audit/WAVE2_STAGE6_BASELINE_SPACE_FIX_VALIDATION.md | PASS |
| Wave 3 (unit-fix + abstain, 26 sessions) | ../../thesis/chapters/before_vs_after_26datasets.md | FAIL |
| Self-recorded Garmin external evaluation | ../../reports/self_recorded_eval_2026_05_05/EVALUATION_REPORT.md | PASS as external evaluation evidence; FAIL as retraining justification |

## Current Defense Evidence Summary

| Claim | Primary artifact | Status |
|---|---|---|
| Parser timestamp issue fixed | `recording/labels/2026-05-05-15-11-15/LABELING_REPORT.md` | PASS |
| Training-style User 7 labels produced | `recording/labels/2026-05-05-15-11-15/2026-05-05-15-11-15_labeled_50Hz_user7_ms2.csv` | PASS |
| Unit contract aligned | `reports/self_recorded_eval_2026_05_05/schema_unit_checks.json` | PASS |
| Frozen model weak on external session | `reports/self_recorded_eval_2026_05_05/evaluation_metrics.json` | PASS |
| Distribution shift measured | `reports/self_recorded_eval_2026_05_05/distribution_pair_summary.csv` | PASS |
| Review-gate retraining policy justified | `reports/self_recorded_eval_2026_05_05/CLAIM_EVIDENCE_TABLE.md` | PASS |
