#!/usr/bin/env python3
"""
CLI wrapper for building drift-detection baselines.
Logic lives in src/monitoring/baseline_builder.py — do not add logic here.

Usage:
    python scripts/build_training_baseline.py
    python scripts/build_training_baseline.py \
        --data data/raw/all_users_data_labeled.csv \
        --output models/training_baseline.json \
        --output-normalized models/normalized_baseline.json
"""
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.monitoring.baseline_builder import BaselineBuilder  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Build training baseline for drift detection (Stage 10)")
    parser.add_argument(
        "--data", type=Path,
        default=_PROJECT_ROOT / "data" / "raw" / "all_users_data_labeled.csv",
        help="Labeled training CSV",
    )
    parser.add_argument(
        "--output", type=Path,
        default=_PROJECT_ROOT / "models" / "training_baseline.json",
        help="Full training baseline output path",
    )
    parser.add_argument(
        "--output-normalized", type=Path,
        default=_PROJECT_ROOT / "models" / "normalized_baseline.json",
        help="Normalized baseline output path (used by Stage 6 drift detection)",
    )
    args = parser.parse_args()

    builder = BaselineBuilder()
    baseline = builder.build_from_csv(args.data)
    builder.save(args.output)
    builder.save_normalized(args.output_normalized)

    logger.info(
        "Done — %d windows, %d channels, %d classes",
        baseline["n_samples"],
        baseline["n_channels"],
        len(baseline["per_class"]),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
