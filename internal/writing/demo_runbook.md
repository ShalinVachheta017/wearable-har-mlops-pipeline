# Defense Demo Runbook

## 1. Demo Goal

Demonstrate that the defended thesis runtime can be executed reproducibly through the Stage 1-7 operational path, that it writes auditable artifacts, and that the governance layer routes weak evidence to review rather than unsafe automatic retraining.

## 2. What the Demo Proves

- `run_pipeline.py` handles orchestration of the defended Stage 1-7 path.
- Model A is the defended proof-of-concept runtime candidate used by the pipeline.
- The pipeline emits run-scoped artifacts that can be inspected after execution.
- Monitoring severity and governance action are separated.
- `CRITICAL` is a monitoring severity label, while `REVIEW` is the governance action.
- `auto_retrain=false` prevents automatic mutation from live monitoring output alone.

## 3. What the Demo Does NOT Prove

- It does not prove clinical validity.
- It does not prove population-level generalization.
- It does not prove production-grade deployment readiness.
- It does not prove that Stage 8-10 should run automatically.
- It does not prove that low accuracy means the pipeline is broken.
- It does not prove that monitoring alerts alone justify retraining.

## 4. Pre-Demo Checklist

- Repository root is `D:\study apply\ML Ops\MasterArbeit_MLops`.
- The Python environment used for the thesis is available.
- `python run_pipeline.py --help` works without import errors.
- The committed fallback evidence folders exist:
  - `artifacts/20260508_235323/`
  - `artifacts/20260508_235356/`
- The User 7 labeled input file exists:
  - `data/raw/2026-05-05-15-11-15_labeled_50Hz_user7.csv`
- Optional API check is attempted only if the local service is already running.
- Stage 8-10 are not used in the live demo.

## 5. Exact Commands

### 5.1 Environment Check

```powershell
Set-Location "D:\study apply\ML Ops\MasterArbeit_MLops"
python --version
python run_pipeline.py --help
```

If the thesis environment is managed by Conda and activation is needed:

```powershell
conda activate thesis-mlops
python --version
python run_pipeline.py --help
```

### 5.2 Safe Live Run: Defended Stage 1-7 Path

Preferred live-demo command on the labeled User 7 session:

```powershell
python run_pipeline.py --stages ingestion validation transformation inference evaluation monitoring trigger --input-csv data/raw/2026-05-05-15-11-15_labeled_50Hz_user7.csv
```

If Conda activation is unreliable but the environment exists:

```powershell
conda run -n thesis-mlops python run_pipeline.py --stages ingestion validation transformation inference evaluation monitoring trigger --input-csv data/raw/2026-05-05-15-11-15_labeled_50Hz_user7.csv
```

### 5.3 Inspect the Most Important Generated Artifacts

After the run completes, inspect the newest run folder under `artifacts/`, then open:

```powershell
Get-Content artifacts\<NEW_RUN_ID>\run_info.json
Get-Content artifacts\<NEW_RUN_ID>\monitoring\monitoring_report.json
Get-Content artifacts\<NEW_RUN_ID>\trigger\trigger_decision.json
```

### 5.4 Optional API Health Check

Only use this if the FastAPI service is already running:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/health | Select-Object -ExpandProperty Content
Invoke-WebRequest http://127.0.0.1:8000/api/model/info | Select-Object -ExpandProperty Content
```

## 6. Expected Output

For a successful Stage 1-7 run on the User 7 labeled session, the expected pattern is:

- Ingestion: `SUCCESS`
- Validation: `SUCCESS`
- Transformation: `SUCCESS`
- Inference: `SUCCESS`
- Evaluation: `SUCCESS`
- Monitoring: overall status in the critical band
- Trigger: `SUCCESS`

Expected evidence pattern from the defended User 7 run (`artifacts/20260508_235356/`):

- rows: `99017`
- windows: `989`
- transformation: `normalization=true`, `gravity_removal=false`
- inference: `989` predictions, about `0.73 ms/window`
- evaluation mean confidence: about `0.359`
- monitoring:
  - `overall_status = CRITICAL`
  - `confidence_status = CRITICAL`
  - `temporal_status = HEALTHY`
  - `drift_status = HEALTHY`
- trigger:
  - `action = review`
  - `should_retrain = false`
  - `auto_retrain = false`
  - `alert_level = CRITICAL`

This is the key sentence to keep straight:

`CRITICAL` is monitoring severity. `REVIEW` is the governance action.

## 7. Where Artifacts Are Saved

Live-run artifacts are written under:

```text
artifacts/<run_id>/
```

The files to inspect first are:

- `artifacts/<run_id>/run_info.json`
- `artifacts/<run_id>/monitoring/monitoring_report.json`
- `artifacts/<run_id>/trigger/trigger_decision.json`

Additional comparison evidence already committed in the repository:

- `reports/abc_comparison/abc_results.csv`
- `reports/abc_comparison/comparison_summary.json`

## 8. What to Say While the Command Runs

Use short, thesis-safe narration:

- "This command runs only the defended operational path: Stages 1 through 7."
- "Model A is the defended proof-of-concept runtime candidate for this thesis."
- "Stages 8 through 10 are the gated mutation path, and they are not part of the live demo."
- "The point of the demo is reproducible execution and governed routing, not clinical accuracy."
- "If monitoring enters a critical band, that does not mean retraining happens automatically."
- "The trigger layer is separate from monitoring, and `auto_retrain=false` is a deliberate policy."

When the monitoring output appears:

- "Here the monitoring severity is `CRITICAL`, which indicates low-confidence risk."
- "The governance action is `REVIEW`, and `should_retrain=false`, so the system does not mutate the model automatically."

## 9. Backup Plan If the Demo Fails

If the environment is slow, imports fail, or the live run stalls, stop the rerun and switch immediately to committed evidence.

Say:

`The thesis claim depends on archived reproducible artifacts as well as the command path, so I will open the committed evidence directly.`

Then open the existing evidence JSON files instead of rerunning:

```powershell
Get-Content artifacts\20260508_235323\run_info.json
Get-Content artifacts\20260508_235323\monitoring\monitoring_report.json
Get-Content artifacts\20260508_235323\trigger\trigger_decision.json
Get-Content artifacts\20260508_235356\run_info.json
Get-Content artifacts\20260508_235356\monitoring\monitoring_report.json
Get-Content artifacts\20260508_235356\trigger\trigger_decision.json
Get-Content reports\abc_comparison\abc_results.csv -TotalCount 12
Get-Content reports\abc_comparison\comparison_summary.json
```

## 10. Existing Evidence Files to Show Instead of Rerunning

Primary fallback evidence files:

- `artifacts/20260508_235323/run_info.json`
- `artifacts/20260508_235323/monitoring/monitoring_report.json`
- `artifacts/20260508_235323/trigger/trigger_decision.json`
- `artifacts/20260508_235356/run_info.json`
- `artifacts/20260508_235356/monitoring/monitoring_report.json`
- `artifacts/20260508_235356/trigger/trigger_decision.json`
- `reports/abc_comparison/abc_results.csv`
- `reports/abc_comparison/comparison_summary.json`

How to use them:

- Use `20260508_235323` to show an unlabeled Garmin production-style session.
- Use `20260508_235356` to show the labeled User 7 external session.
- Use `abc_results.csv` and `comparison_summary.json` to explain why Model A is the defended runtime candidate instead of Model B or Model C.

## 11. Common Examiner Questions

### Why are Stages 8-10 not shown live?

Because the defended live runtime claim is the Stage 1-7 operational path. Stage 8-10 are gated mutation stages and are intentionally not run automatically in the demo.

### Why is `auto_retrain=false`?

Because the thesis defends governance-first operation. Unlabeled or weak evidence can justify review, but not automatic model mutation.

### Does `CRITICAL` mean the model failed?

No. `CRITICAL` is a monitoring severity label. The separate governance action is `REVIEW`, which means the system detected risk and correctly avoided unsafe automatic retraining.

### Why is low confidence important here?

Because the thesis is about monitored operation under uncertainty. The system is supposed to surface risky behavior explicitly instead of silently overclaiming.

### Does the demo prove clinical usefulness?

No. The demo proves reproducible execution, artifact persistence, and governance routing. It does not prove clinical validity.

### Why use Model A if Model B had stronger legacy metrics in some comparisons?

Because Model A has the defended clean runtime contract. Model B depends on a legacy diagnostic setup with a non-persisted full-evaluation scaler, so it is not the defended reproducible runtime contract.

### What is the main thesis-safe conclusion from the live demo?

The pipeline can execute reproducibly through Stage 1-7, persist auditable artifacts, and route uncertain evidence to `REVIEW` with `auto_retrain=false`. That demonstrates governed operation, not automatic adaptation.

## Recommended Demo Order

1. Run the environment check.
2. Attempt the Stage 1-7 live run on the User 7 labeled session.
3. Open `run_info.json`.
4. Open `monitoring_report.json`.
5. Open `trigger_decision.json`.
6. If asked, show `comparison_summary.json` and `abc_results.csv`.
7. If the live run is slow or fails, switch immediately to the committed evidence files above.
