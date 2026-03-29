# WAVE 1 CLEANUP PLAN (EXECUTED)

## A) Delete Now (Executed)

Observability stack files were removed as requested:

- `src/prometheus_metrics.py`
- `scripts/verify_prometheus_metrics.py`
- `config/prometheus.yml`
- `config/alertmanager.yml`
- `config/alerts/har_alerts.yml`
- `config/alerts/har_alerts_pending.yml`
- `config/grafana/dashboard-provider.yaml`
- `config/grafana/dashboards/dashboard-provider.yaml`
- `config/grafana/dashboards/har_dashboard.json`
- `config/grafana/datasource-prometheus.yaml`
- `config/grafana/datasources/datasource-prometheus.yaml`
- `config/grafana/har_dashboard.json`

Cache noise cleanup executed:

- root `__pycache__/` removed
- no `__pycache__` directories remain
- no `*.pyc` / `*.pyo` files remain

## B) Archive Now (Executed)

Lower-priority utility scripts were archived under `scripts/_wave1_archive/`.

Archived files:

- `scripts/_wave1_archive/benchmark_latency.py`
- `scripts/_wave1_archive/benchmark_throughput.py`
- `scripts/_wave1_archive/export_mlflow_runs.py`
- `scripts/_wave1_archive/extract_papers_to_text.py`
- `scripts/_wave1_archive/fetch_foundation_papers.py`
- `scripts/_wave1_archive/find_duplicate_papers.py`
- `scripts/_wave1_archive/generate_repo_structure.py`
- `scripts/_wave1_archive/generate_summary_report.py`
- `scripts/_wave1_archive/regenerate_support_map.py`
- `scripts/_wave1_archive/update_progress_dashboard.py`
- `scripts/_wave1_archive/verify_repository.py`
- `scripts/_wave1_archive/maintenance/cleanup_repo.ps1`
- `scripts/_wave1_archive/maintenance/fix_fstrings.py`
- `scripts/_wave1_archive/maintenance/fix_imports.py`
- `scripts/_wave1_archive/maintenance/generate_repo_summary.ps1`

## C) Keep Now (Protected and Verified)

Critical runtime and thesis-pipeline files were kept intact and verified present:

- `run_pipeline.py`
- `src/pipeline/production_pipeline.py`
- `src/api/app.py`
- `src/pipeline/inference_pipeline.py`
- `src/core/logger.py`
- `src/core/exception.py`
- `scripts/post_inference_monitoring.py`
- `scripts/build_training_baseline.py`
- `scripts/build_normalized_baseline.py`
- `scripts/preprocess.py`
- `scripts/train.py`
- `src/domain_adaptation/`
- `src/entity/`
- `src/utils/config_loader.py`
- `src/utils/artifacts_manager.py`
- `src/exceptions.py`
- `src/logger/`

## D) Decide Later (Wave 2)

These were intentionally left for a separate, lower-risk Wave 2 decision pass:

- evaluate keeping vs archiving `scripts/generate_thesis_figures.py`
- evaluate keeping vs archiving `scripts/inference_smoke.py`
- evaluate keeping vs archiving `scripts/per_dataset_inference.py`
- evaluate keeping vs archiving `scripts/preprocess_qc.py`
- evaluate keeping vs archiving `scripts/run_ab_comparison.py`
- evaluate keeping vs archiving `scripts/threshold_sweep.py`
- evaluate keeping vs archiving `scripts/trigger_policy_eval.py`
- evaluate keeping vs archiving `scripts/windowing_ablation.py`
- evaluate wrapper strategy under `src/components/` vs direct imports (no change in Wave 1)

## E) Exact Changed Files (Current Git State)

Modified:

- `docker-compose.yml`

Deleted:

- `config/alertmanager.yml`
- `config/alerts/har_alerts.yml`
- `config/alerts/har_alerts_pending.yml`
- `config/grafana/dashboard-provider.yaml`
- `config/grafana/dashboards/dashboard-provider.yaml`
- `config/grafana/dashboards/har_dashboard.json`
- `config/grafana/datasource-prometheus.yaml`
- `config/grafana/datasources/datasource-prometheus.yaml`
- `config/grafana/har_dashboard.json`
- `config/prometheus.yml`
- `scripts/benchmark_latency.py`
- `scripts/benchmark_throughput.py`
- `scripts/export_mlflow_runs.py`
- `scripts/extract_papers_to_text.py`
- `scripts/fetch_foundation_papers.py`
- `scripts/find_duplicate_papers.py`
- `scripts/maintenance/cleanup_repo.ps1`
- `scripts/maintenance/fix_fstrings.py`
- `scripts/maintenance/fix_imports.py`
- `scripts/maintenance/generate_repo_summary.ps1`
- `scripts/regenerate_support_map.py`
- `scripts/update_progress_dashboard.py`
- `scripts/verify_prometheus_metrics.py`
- `scripts/verify_repository.py`
- `src/prometheus_metrics.py`

Added (new archive path):

- `scripts/_wave1_archive/` (contains archived utility and maintenance scripts)

## F) Docker Changes Made

`docker-compose.yml` was updated to remove observability stack definitions and their persistence volumes:

- removed service `prometheus`
- removed service `alertmanager`
- removed service `grafana`
- removed volume `prometheus_data`
- removed volume `grafana_data`
- removed volume `alertmanager_data`

Preserved services:

- `mlflow`
- `inference`
- `training`
- `preprocessing`

## G) Risky / Manual-Review Items

- Git currently shows archived script moves as delete + new archive directory, not as rename pairs. Before commit, review staged content to ensure each intended archive file is included under `scripts/_wave1_archive/`.
- Existing unrelated repository changes (especially under `internal/`) are outside Wave 1 scope and should remain untouched in this cleanup commit.
- If any CI or local jobs still reference old script paths, update invocations to the new archive location only if those jobs must be preserved.
