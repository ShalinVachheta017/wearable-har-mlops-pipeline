# Stage 1 Ingestion Refactor Notes

## What Was Simplified

- Stage 1 now has one clear job: read one selected input and write one fused 50 Hz CSV.
- The fused CSV path is dataset-specific: `data/processed/fused_<dataset_name>_50Hz.csv`.
- `DataIngestionArtifact.fused_csv_path` is the only handoff path Stage 2 should trust.
- Auto-discovery now searches only `data/raw/`.
- Direct CSV/Excel input, explicit accelerometer/gyroscope pairs, and simple auto-discovery are kept.
- Final cleanup pass on 2026-04-30 reduced the active Stage 1 file to `573` lines while restoring the required method docstring format:
  - `Method Name`
  - `Description`
  - `Output`
  - `On Failure`

## What Was Removed

- Manifest caching and skip-already-processed behavior.
- `PROCESSED_MANIFEST`, `_load_manifest`, `_save_manifest`, and `_pair_key`.
- Reuse of old fused CSVs during a normal Stage 1 run.
- `reused_existing` artifact logic.
- `sensor_fused_50Hz.csv` canonical syncing/copying.
- Decoded-folder fallback.
- Broad schema alias machinery that made the ingestion path harder to audit.

## Why Dataset-Specific Fused CSV Names Are Used

Dataset-specific names keep the evidence traceable. A file such as:

`data/processed/fused_2025_03_23_15_23_10_50Hz.csv`

shows which source recording produced the fused data. This is easier to defend in the thesis than a mutable canonical file name.

## Why Caching Was Removed

Caching made debugging difficult because a pipeline run could silently reuse old data. Stage 1 now rewrites the fused output for the selected input every time, so the downstream artifact always reflects the current run.

## How To Test Stage 1 Manually

Run explicit pair:

```bash
python run_pipeline.py --stages ingestion --accel-file data/raw/2025-03-23-15-23-10-accelerometer_data.xlsx --gyro-file data/raw/2025-03-23-15-23-10-gyroscope_data.xlsx
```

Expected output:

```text
data/processed/fused_2025_03_23_15_23_10_50Hz.csv
```

Check file:

```bash
python -c "import pandas as pd; df=pd.read_csv('data/processed/fused_2025_03_23_15_23_10_50Hz.csv'); print(df.shape); print(df.columns.tolist()); print(df.head())"
```

Check 50 Hz:

```bash
python -c "import pandas as pd; df=pd.read_csv('data/processed/fused_2025_03_23_15_23_10_50Hz.csv'); t=pd.to_datetime(df['true_time']); print(t.diff().dt.total_seconds().describe())"
```

Expected median timestamp gap:

```text
0.020
```

## Latest Verified Result

Verified on 2026-04-30 with the explicit raw sensor pair command above:

- Pipeline result: `SUCCESS (1/1 stages)`
- Output file: `data/processed/fused_2025_03_23_15_23_10_50Hz.csv`
- Output shape: `(181509, 9)`
- Output columns: `true_time, Ax, Ay, Az, Gx, Gy, Gz, timestamp_ms, timestamp_iso`
- Median timestamp gap: `0.020000` seconds
- Stage 1 artifact handoff remains `DataIngestionArtifact.fused_csv_path`

## Next Stage

Stage 1 is ready to hand off to Stage 2.

Next work item:

- Start Stage 2 Data Validation audit.
- Confirm Stage 2 reads the exact `fused_<dataset_name>_50Hz.csv` path from `DataIngestionArtifact.fused_csv_path`.
- Confirm sampling-frequency validation is not skipped because Stage 1 writes `true_time`, not a plain `timestamp` column.
