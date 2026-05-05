"""
Thin CLI wrapper for Stage 4 model inference.

The defended runtime implementation lives in
`src.components.model_inference.ModelInference`. This module exists only for
backward-compatible command-line use.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.components.model_inference import ACTIVITY_CLASSES, run_model_inference_from_paths
from src.config import DATA_PREPARED, DEFAULT_MODEL_PATH


def parse_args() -> argparse.Namespace:
    """
    Method Name :   parse_args
    Description :   Parse command-line arguments for one-off offline inference.

    Output      :   Returns an argparse namespace.
    On Failure  :   Logs the error and raises the exception.
    """
    parser = argparse.ArgumentParser(description="Run Stage 4 offline batch inference.")
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=DATA_PREPARED / "production_X.npy",
        help="Path to prepared production_X.npy.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=DATA_PREPARED / "predictions",
        help="Directory for Stage 4 prediction artifacts.",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=Path,
        default=DEFAULT_MODEL_PATH,
        help="Path to Keras model.",
    )
    parser.add_argument("--batch-size", type=int, default=32, help="Offline batch size.")
    parser.add_argument(
        "--threshold",
        "-t",
        type=float,
        default=0.50,
        help="Maximum-softmax threshold below which a window is marked uncertain.",
    )
    return parser.parse_args()


def main() -> int:
    """
    Method Name :   main
    Description :   Execute the thin CLI wrapper around the Stage 4 component.

    Output      :   Returns process exit code 0 on success.
    On Failure  :   Logs the error and raises the exception.
    """
    args = parse_args()
    artifact = run_model_inference_from_paths(
        input_path=args.input,
        model_path=args.model,
        output_dir=args.output,
        batch_size=args.batch_size,
        confidence_threshold=args.threshold,
    )
    print(f"Predictions CSV : {artifact.predictions_csv_path}")
    print(f"Predictions NPY : {artifact.predictions_npy_path}")
    print(f"Probabilities   : {artifact.probabilities_npy_path}")
    print(f"Report          : {artifact.inference_report_path}")
    print(f"Dominant class  : {artifact.dominant_class} ({artifact.dominant_pct:.2f}%)")
    print(f"Collapse level  : {artifact.collapse_level}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

