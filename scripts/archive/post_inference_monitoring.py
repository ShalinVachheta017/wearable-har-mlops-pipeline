#!/usr/bin/env python3
"""
CLI wrapper for post-inference monitoring.
Logic lives in src/monitoring/post_inference_monitor.py — do not add logic here.

Usage:
    python scripts/post_inference_monitoring.py --predictions outputs/predictions.csv
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.monitoring.post_inference_monitor import PostInferenceMonitor  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 3-layer post-inference monitoring")
    parser.add_argument("--predictions", type=Path, required=True, help="Path to predictions CSV")
    parser.add_argument("--production-data", type=Path, default=None, help="Path to production .npy")
    parser.add_argument("--baseline", type=Path, default=None, help="Path to baseline JSON")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/monitoring"))
    args = parser.parse_args()

    monitor = PostInferenceMonitor()
    report = monitor.run(
        predictions_path=args.predictions,
        production_data_path=args.production_data,
        baseline_path=args.baseline,
        output_dir=args.output_dir,
    )
    print(f"Result: {report.overall_status}")
    return 0 if report.overall_status == "HEALTHY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
