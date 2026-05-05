"""Build models/raw_physical_baseline.json for Stage 6 drift monitoring.

PURPOSE
-------
The raw physical baseline defines what "normal" sensor data looks like in
production-unit space (m/s² + deg/s), so Stage 6 can measure z-score
mean-shift drift against it.

SOURCE DATA REQUIREMENT — CRITICAL
-----------------------------------
The baseline MUST be built from labeled TRAINING / REFERENCE data, NOT from
production monitoring sessions.  Using production sessions as the reference
makes drift detection circular: the baseline will always match the data being
monitored, and genuine drift will be invisible.

Correct source:  data/all_users_data_labeled.csv  (training split)
Wrong source:    data/raw/2025-08-19-08-58-40/    (production session)

PREPROCESSING CONTRACT
----------------------
Only the steps active in production inference are applied:

  1. milliG → m/s²  (accelerometer unit conversion, factor = 0.00980665)
  2. Windowing       (window_size=200, stride=100, 50 % overlap)
  3. NO normalization / NO scaler
  4. NO gravity removal
  5. NO calibration

The output JSON carries  metadata.feature_space = "raw_physical_units"
so Stage 6's mismatch guard can detect if the wrong baseline is loaded.

Usage
-----
  python scripts/build_raw_physical_baseline.py --input-csv <path>

  --input-csv   Path to the labeled training CSV (must have columns
                Ax, Ay, Az, Gx, Gy, Gz at 50 Hz).
                Default: data/all_users_data_labeled.csv
                WARNING: do NOT point this at production session files.

  --output      Path for the output JSON.
                Default: models/raw_physical_baseline.json

  --window-size Number of timesteps per window.  Default: 200
  --stride      Stride between windows.          Default: 100
  --hz          Sampling rate in Hz.             Default: 50
  --no-convert  Skip milliG → m/s² conversion (use when input is already m/s²).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SENSOR_COLS = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
UNIT_FACTOR = 0.00980665  # milliG → m/s²
ALREADY_CONVERTED_THRESHOLD = 2.0  # m/s²; if abs(mean_Az) > this, assume already converted


def _detect_unit_conversion_needed(df) -> bool:
    """Return True when accelerometer data looks like milliG (mean |Az| >> 1)."""
    import pandas as pd
    az_abs_mean = float(df["Az"].abs().mean()) if "Az" in df.columns else 0.0
    # milliG gravity ≈ 1000 milliG ≈ 9.8 m/s²; raw milliG gravity ≈ 1000
    return az_abs_mean > 500  # heuristic: >500 milliG suggests milliG input


def build_baseline(
    input_csv: Path,
    output_path: Path,
    window_size: int = 200,
    stride: int = 100,
    hz: int = 50,
    force_convert: bool = True,
) -> None:
    import pandas as pd

    print(f"Loading: {input_csv}")
    df = pd.read_csv(input_csv)

    # Accept both canonical names (Ax, Ay, …) and the _w-suffixed variants
    # used in the merged training CSVs (Ax_w, Ay_w, …).
    _w_renames = {f"{c}_w": c for c in SENSOR_COLS if f"{c}_w" in df.columns and c not in df.columns}
    if _w_renames:
        df = df.rename(columns=_w_renames)
        print(f"  Renamed columns: {_w_renames}")

    missing = [c for c in SENSOR_COLS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Input CSV is missing required sensor columns: {missing}. "
            f"Available columns: {list(df.columns)}"
        )

    # Accelerometer unit conversion.
    if force_convert:
        # Detect whether data is already in m/s² to avoid double-conversion.
        auto_detect = _detect_unit_conversion_needed(df)
        if auto_detect:
            print(f"  Applying milliG → m/s² conversion (factor {UNIT_FACTOR})")
            for col in ["Ax", "Ay", "Az"]:
                df[col] = df[col] * UNIT_FACTOR
        else:
            print(
                f"  Skipping unit conversion — mean |Az|={df['Az'].abs().mean():.3f} "
                "suggests data is already in m/s²."
            )
    else:
        print("  Unit conversion skipped (--no-convert flag set).")

    sensor_data = df[SENSOR_COLS].values.astype(np.float32)
    n_samples = len(sensor_data)
    n_windows = max(0, (n_samples - window_size) // stride + 1)

    if n_windows == 0:
        raise ValueError(
            f"Not enough samples to build even one window: "
            f"n_samples={n_samples}, window_size={window_size}, stride={stride}"
        )

    windows = np.stack(
        [sensor_data[i * stride: i * stride + window_size] for i in range(n_windows)]
    )
    print(f"  Windows: {windows.shape}  (n={n_windows}, size={window_size}, stride={stride})")

    # Per-channel statistics computed over all timesteps across all windows.
    flat = windows.reshape(-1, 6)  # (n_windows * window_size, 6)

    channel_means = flat.mean(axis=0).tolist()
    channel_stds = flat.std(axis=0).tolist()
    channel_mins = flat.min(axis=0).tolist()
    channel_maxs = flat.max(axis=0).tolist()

    percentiles = {}
    for pct in [5, 25, 50, 75, 95]:
        percentiles[f"p{pct}"] = np.percentile(flat, pct, axis=0).tolist()

    per_channel = {}
    for i, name in enumerate(SENSOR_COLS):
        per_channel[name] = {
            "mean": float(channel_means[i]),
            "std": float(channel_stds[i]),
            "min": float(channel_mins[i]),
            "max": float(channel_maxs[i]),
            **{k: float(v[i]) for k, v in percentiles.items()},
        }

    baseline = {
        "schema_version": 1,
        "mean": channel_means,
        "std": channel_stds,
        "min": channel_mins,
        "max": channel_maxs,
        "percentiles": {k: v for k, v in percentiles.items()},
        "per_channel": per_channel,
        "channel_names": SENSOR_COLS,
        "n_channels": 6,
        "n_samples": int(n_windows),
        "metadata": {
            "n_windows": int(n_windows),
            "window_size": window_size,
            "step_size": stride,
            "n_channels": 6,
            "source_csv": str(input_csv),
            "created_at": datetime.now().isoformat(),
            "sensor_columns": SENSOR_COLS,
            # feature_space is the critical field Stage 6 uses for mismatch detection.
            "feature_space": "raw_physical_units",
            "preprocessing_contract": {
                "unit_conversion": "milliG_to_ms2",
                "unit_factor": UNIT_FACTOR,
                "normalization": "none",
                "gravity_removal": False,
                "calibration": False,
                "sampling_hz": hz,
                "window_size": window_size,
                "stride": stride,
            },
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(baseline, indent=2), encoding="utf-8")
    print(f"Baseline saved -> {output_path}")
    print(f"  Az mean: {per_channel['Az']['mean']:.4f} m/s2  (expected ~+-9.8 for wrist-down)")
    print(f"  Gx mean: {per_channel['Gx']['mean']:.4f} deg/s")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build raw physical baseline for Stage 6 drift monitoring.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=PROJECT_ROOT / "data" / "all_users_data_labeled.csv",
        help="Path to labeled training CSV with Ax,Ay,Az,Gx,Gy,Gz columns at 50 Hz.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "models" / "raw_physical_baseline.json",
        help="Output path for baseline JSON. Default: models/raw_physical_baseline.json",
    )
    parser.add_argument("--window-size", type=int, default=200)
    parser.add_argument("--stride", type=int, default=100)
    parser.add_argument("--hz", type=int, default=50)
    parser.add_argument(
        "--no-convert",
        action="store_true",
        help="Skip milliG → m/s² conversion (use when input is already in m/s²).",
    )
    parser.add_argument(
        "--force-production-input",
        action="store_true",
        help="Bypass the production-session path guard (use only for debugging).",
    )
    args = parser.parse_args()

    if not args.input_csv.exists():
        print(f"ERROR: Input CSV not found: {args.input_csv}")
        print(
            "Provide --input-csv pointing to the labeled training CSV used for model evaluation."
        )
        return 1

    # Heuristic guard: production session folders are typically named with a
    # timestamp pattern (YYYY-MM-DD-HH-MM-SS).  Warn loudly if the input path
    # looks like a raw production session rather than the training dataset.
    import re as _re
    _session_pattern = _re.compile(r"\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}")
    if _session_pattern.search(str(args.input_csv)):
        print(
            "WARNING: The --input-csv path looks like a production session "
            f"({args.input_csv}).\n"
            "The baseline MUST be built from TRAINING/REFERENCE data, not from "
            "the same production sessions that Stage 6 will monitor.\n"
            "Using a production session makes drift detection circular.\n"
            "Pass --force-production-input to override this guard if you are "
            "absolutely sure."
        )
        if not getattr(args, "force_production_input", False):
            return 1

    build_baseline(
        input_csv=args.input_csv,
        output_path=args.output,
        window_size=args.window_size,
        stride=args.stride,
        hz=args.hz,
        force_convert=not args.no_convert,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
