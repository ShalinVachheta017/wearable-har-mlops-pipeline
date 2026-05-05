# TODO

## Thesis-Critical Next Steps

- Finalize and run the planned thesis experiments (baseline, drift, retraining trigger behavior).
- Export reproducible experiment artifacts and map them to thesis chapters.
- Freeze defense-ready evidence (plots, metrics, ablations, and decision logs).

## Repo Hygiene (Follow-Up)

- Review moved legacy notes in `archive/old_planning_docs/` and prune if no longer needed.
- Decide whether `setup.py` is still required or can be retired after packaging review.
- Keep root clean: only operational entrypoints and core project metadata.
..You’re asking exactly the right thing: what sigma means in your pipeline, which dataset it is computed from, why 2-sigma or 3-sigma is used, and what alternatives/citations exist. I’ll quickly scan your codebase for the actual threshold logic so I can explain it in your project’s terms, not just generic statistics.

Search complete: Locate sigma logic

Searched for regex `sigma|std|standard deviation|z-score|threshold|drift|trigger`, 200 results

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/src/trigger_policy.py#1-1), lines 1 to 150

Searched for files matching `**/src/**/monitoring.py`, no matches

I found strong hints but the quick search output had path-resolution issues, so I’m now verifying exact files and lines directly in your workspace to give you a precise explanation tied to your implementation.

Searched for regex `sigma|z-score|zscore|std|standard deviation` (`**/src/**`), 200 results

Searched for regex `sigma|z-score|zscore|std|standard deviation` (`**/config/**`), 16 results

Searched for regex `sigma|z-score|zscore|std|standard deviation|threshold` (`**/internal/**`), 200 results

Searched for regex `TriggerThresholds|drift_z|warn|critical|retrain` (`**/src/**`), 200 results

I confirmed your repo does use explicit 2-sigma warning and 3-sigma critical drift logic, plus a baseline-vs-production z-score comparison. Next I’m reading the exact implementation blocks for baseline creation and drift computation so I can explain which dataset each sigma comes from.

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/src/trigger_policy.py#80-80), lines 80 to 170

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/src/trigger_policy.py#490-490), lines 490 to 560

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/src/components/post_inference_monitoring.py)

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/src/entity/config_entity.py#170-170), lines 170 to 230

I’ve verified the threshold definitions in code, including the explicit note that Layer 3 uses z-score of mean shift versus baseline (not PSI). I’ll now read the baseline-generation code and the monitoring script that computes the per-channel drift score formula so I can map sigma to the exact training and production datasets.

Searched for files matching `**/models/normalized_baseline.json`, no matches

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/scripts/post_inference_monitoring.py#1-1), lines 1 to 320

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/scripts/build_training_baseline.py)

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/src/components/baseline_update.py)

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/scripts/post_inference_monitoring.py#320-320), lines 320 to 431

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/src/preprocess_data.py#450-450), lines 450 to 590

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/src/entity/config_entity.py#280-280), lines 280 to 330

I now have the baseline builder and drift formula from your monitoring script; next I’m checking how Stage 7 consumes that drift score so I can explain the full flow from production stats to retraining decision.

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/src/components/trigger_evaluation.py)

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/src/trigger_policy.py#560-560), lines 560 to 760

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/internal/writing/defense_qa.md#595-595), lines 595 to 620

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/tests/test_threshold_consistency.py)

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/config/alerts/har_alerts.yml#60-60), lines 60 to 110

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/reports/THRESHOLD_CALIBRATION.csv#1-1), lines 1 to 20

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/src/api/app.py#220-220), lines 220 to 290

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/src/api/app.py#70-70), lines 70 to 180

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/src/utils/config_loader.py)

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/config/pipeline_overrides.yaml)

I’ve confirmed config and runtime sources; I’m taking one last pass through the threshold-sweep script and docs to answer your “why 2 sigma, why not 3 sigma only, and alternatives” part with evidence from your own project.

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/internal/reference/tech/monitoring.md#100-100), lines 100 to 170

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/internal/notes/product_review.md#460-460), lines 460 to 484

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/scripts/threshold_sweep.py#1-1), lines 1 to 280

Searched for regex `drift_thresholds|drift_zscore|sweetspot|best|selected|thresholds =` (`**/scripts/threshold_sweep.py`), 39 results

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/scripts/threshold_sweep.py#270-270), lines 270 to 420

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/scripts/threshold_sweep.py#420-420), lines 420 to 575

Searched for files matching `**/normalized_baseline*.json`, no matches

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/data/prepared/config.json)

Read [](file:///d%3A/study%20apply/ML%20Ops/MasterArbeit_MLops/src/wasserstein_drift.py#50-50), lines 50 to 280

Searched for regex `2.0σ|3.0σ|mean shift per channel|drift_zscore_warn|drift_zscore_critical|min_signals_for_retrain` (`**/src/trigger_policy.py`), 29 results

Searched for regex `mean_diff =|DRIFT_CHANNEL_THRESHOLD|feature_space='transformed'|Baseline feature-space mismatch` (`**/scripts/post_inference_monitoring.py`), 5 results

Searched for regex `normalization_variant|scaler_mean|scaler_scale|Loaded z-score scaler from training|data/prepared/config.json` (`**/src/preprocess_data.py`), 8 results

Searched for regex `build_from_csv|source_csv|feature_space|normalized_baseline.json|training_data_path` (`**/scripts/build_training_baseline.py`), 14 results

Searched for regex `drift_zscore_threshold|drift_zscore_warn|drift_zscore_critical` (`**/src/entity/config_entity.py`), 3 results

Searched for text `drift_zscore_threshold=2.0 std deviations from the training baseline` (`**/config/alerts/har_alerts.yml`), 1 result

Searched for regex `input_file|train_users|val_users|test_users|scaler_mean|scaler_scale|normalization_variant` (`**/data/prepared/config.json`), no results

Searched for regex `train_users|scaler_mean|input_file|scaler_scale` (`**/data/prepared/config.json`), 4 results

I now have the exact implementation details and docs to answer in project context. I’ll quickly compute the threshold calibration file size and then give you a clear, plain-language explanation of where sigma comes from, why 2 versus 3 sigma, and alternatives with citations.

Ran terminal command: Set-Location "d:\study apply\ML Ops\MasterArbeit_MLops"; (Import-Csv "reports/THRESHOLD_CALIBRATION.csv").Count

Sigma here means standard deviation, and in your pipeline it is used in two different places.

1. Sigma for preprocessing (feature scaling)
- Production data is normalized using mean and standard deviation learned from training data, not from live production data.
- This is implemented in preprocess_data.py, preprocess_data.py, preprocess_data.py.
- Those saved training statistics are in config.json.

2. Sigma for drift detection (monitoring/triggering)
- Drift is computed as how far production mean moved away from baseline mean, measured in baseline standard deviations:
- $z = \frac{|\mu_{prod} - \mu_{base}|}{\sigma_{base} + \epsilon}$
- Implementation is in post_inference_monitoring.py.
- The code also enforces that baseline must be in transformed feature space, same as production tensors (post_inference_monitoring.py).
- The baseline itself is built from training CSV windows by Stage 10 logic in build_training_baseline.py, with transformed-space metadata at build_training_baseline.py.

Why 2-sigma and 3-sigma?
- Your repo explicitly defines:
- Warning at 2 sigma and critical at 3 sigma in trigger_policy.py, trigger_policy.py, trigger_policy.py, and config_entity.py.
- Intuition under normality:
- $P(|Z| > 2) \approx 4.55\%$ (more sensitive, earlier warning)
- $P(|Z| > 3) \approx 0.27\%$ (stricter, stronger evidence)
- So 2 sigma is early detection, 3 sigma is high-confidence alert.
- Your trigger also reduces false alarms by requiring multi-signal voting (2-of-3 style) via trigger_policy.py and trigger_policy.py.

How this helps detect problems
- It makes drift across channels comparable even if raw units differ.
- It is explainable to stakeholders: “this channel moved 2.7 standard deviations from baseline.”
- It supports tiered operations: monitor at warning level, escalate at critical level.
- Alert text in ops config also reflects this logic at har_alerts.yml.

Is there any other way?
- Yes, and your repo already includes one:
- Wasserstein distance + change-point z-score style detector in wasserstein_drift.py and wasserstein_drift.py.
- Common alternatives you can combine with sigma:
1. Robust z-score using median/MAD (better under heavy outliers).
2. KS test / AD test (distribution-shape shifts, not only mean shift).
3. PSI (often used in industry scorecards, but binning-dependent).
4. CUSUM/Page-Hinkley or ADWIN/DDM for online drift streams.
5. Multivariate distance (Mahalanobis, MMD) when channel correlations matter.

Citation basis behind your current sigma rule
- Your code comments cite concept-drift and sequential detection lineage in trigger_policy.py.
- Good references to cite in thesis:
1. Gama et al., 2014, ACM Computing Surveys, concept drift survey, DOI 10.1145/2523813.
2. Page, 1954, Biometrika, CUSUM, DOI 10.2307/2333009.
3. Wald, 1947, Sequential Analysis (SPRT foundation).
4. For classic 3-sigma control-chart rationale: Shewhart SPC tradition (also summarized in standard SPC texts such as Montgomery).

Project-specific evidence for threshold tuning
- Threshold sweep script: threshold_sweep.py, sweet-spot logic at threshold_sweep.py.
- Current calibration table file is THRESHOLD_CALIBRATION.csv, and it has 52 rows in your workspace.

If you want, I can next give you a very simple decision rule for your defense slide:
- when to say “2 sigma warning only,”
- when to say “3 sigma retrain candidate,”
- and when to ignore as noise.