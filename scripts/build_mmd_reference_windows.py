"""Build transformed reference windows for the Stage 6 MMD drift monitor.

The MMD branch keeps z-score preprocessing as the baseline. This helper creates
the reference tensor used by runtime MMD from an existing reference CSV, using
the same preprocessor and saved scaler configuration as inference.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_thesis_ablation_experiments import (
    DatasetSpec,
    _fit_robust_scaler,
    _load_zscore_scaler,
    _prepare_windows,
    _project_path,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build MMD reference windows")
    parser.add_argument(
        "--reference-csv",
        default="data/synthetic_runs/all_users_data_labeled_actual_input.csv",
        help="Existing labeled reference replay CSV.",
    )
    parser.add_argument(
        "--output",
        default="models/mmd_reference_windows.npy",
        help="Output .npy path for transformed reference windows.",
    )
    parser.add_argument("--max-rows", type=int, default=120000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    reference_csv = _project_path(args.reference_csv)
    output_path = _project_path(args.output)
    max_rows = None if args.max_rows == 0 else args.max_rows

    import logging

    logger = logging.getLogger("mmd_reference_builder")
    zscore = _load_zscore_scaler(_project_path("data/prepared/config.json"))
    robust = _fit_robust_scaler(reference_csv, args.max_rows, logger)
    bundle = _prepare_windows(
        DatasetSpec("mmd_reference", reference_csv),
        "zscore",
        args.max_rows,
        zscore,
        robust,
        logger,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    import numpy as np

    np.save(output_path, bundle.X)
    print(f"Saved MMD reference windows: {output_path}")
    print(f"shape={bundle.X.shape}, source={reference_csv}, max_rows={args.max_rows}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
