"""
Batch runner: evaluate all models across all compatible datasets.

This script wraps scripts/test_all_models_full.py and runs it once per dataset,
then merges all per-dataset outputs into two consolidated CSV files:

1) reports/model_comparison_all_datasets_matrix.csv
2) reports/model_comparison_all_datasets_per_class.csv

Compatibility rule for auto-discovery:
  - CSV must contain Ax, Ay, Az, Gx, Gy, Gz, activity columns
"""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "data"
RUNNER = PROJECT_ROOT / "scripts" / "test_all_models_full.py"

REQUIRED_COLUMNS = {"Ax", "Ay", "Az", "Gx", "Gy", "Gz", "activity"}


def _read_header_columns(path: Path) -> List[str]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader, [])
    return [c.strip().strip('"') for c in header]


def _is_compatible_dataset(path: Path) -> bool:
    try:
        cols = set(_read_header_columns(path))
    except Exception:
        return False
    return REQUIRED_COLUMNS.issubset(cols)


def discover_datasets(data_root: Path) -> List[Path]:
    datasets = []
    for p in data_root.rglob("*.csv"):
        # Skip noisy/generated temp folders quickly
        lowered = str(p).lower()
        if any(x in lowered for x in ["\\tmp\\", "/tmp/", "pytest"]):
            continue
        if _is_compatible_dataset(p):
            datasets.append(p)
    datasets = sorted(set(datasets))
    return datasets


def dataset_tag(path: Path) -> str:
    p = str(path).lower()
    if "synthetic" in p:
        return "synthetic"
    if "processed" in p or "fused" in p:
        return "production_like"
    if "all_users_data_labeled" in p:
        return "training_like"
    return "other"


def run_one_dataset(
    dataset_csv: Path,
    scaler_config: Path,
    mode: str,
    out_root: Path,
) -> tuple[int, Path, Path, Path]:
    stem = dataset_csv.stem.replace(" ", "_")
    run_dir = out_root / stem
    run_dir.mkdir(parents=True, exist_ok=True)

    matrix_csv = run_dir / "model_comparison_full_matrix.csv"
    per_class_csv = run_dir / "model_comparison_per_class.csv"
    run_log = run_dir / "run.log"

    cmd = [
        sys.executable,
        str(RUNNER),
        "--data-csv",
        str(dataset_csv),
        "--scaler-config",
        str(scaler_config),
        "--results-csv",
        str(matrix_csv),
        "--per-class-csv",
        str(per_class_csv),
    ]
    if mode == "norm":
        cmd.append("--normalize")
    elif mode == "raw":
        cmd.append("--no-normalize")

    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"

    proc = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        text=True,
        capture_output=True,
        env=env,
    )
    run_log.write_text(
        f"COMMAND: {' '.join(cmd)}\n\nSTDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}\n",
        encoding="utf-8",
    )

    return proc.returncode, matrix_csv, per_class_csv, run_log


def merge_outputs(
    results: Iterable[dict],
    out_matrix: Path,
    out_per_class: Path,
) -> None:
    matrix_frames = []
    per_class_frames = []

    for r in results:
        ds = r["dataset"]
        tag = r["dataset_tag"]
        rc = r["return_code"]

        if r["matrix_csv"].exists():
            df = pd.read_csv(r["matrix_csv"])
            df.insert(0, "dataset_tag", tag)
            df.insert(0, "dataset_csv", str(ds))
            df.insert(0, "run_return_code", rc)
            matrix_frames.append(df)

        if r["per_class_csv"].exists():
            dfc = pd.read_csv(r["per_class_csv"])
            dfc.insert(0, "dataset_tag", tag)
            dfc.insert(0, "dataset_csv", str(ds))
            dfc.insert(0, "run_return_code", rc)
            per_class_frames.append(dfc)

    out_matrix.parent.mkdir(parents=True, exist_ok=True)

    if matrix_frames:
        pd.concat(matrix_frames, ignore_index=True).to_csv(out_matrix, index=False, encoding="utf-8")
    else:
        pd.DataFrame().to_csv(out_matrix, index=False, encoding="utf-8")

    if per_class_frames:
        pd.concat(per_class_frames, ignore_index=True).to_csv(out_per_class, index=False, encoding="utf-8")
    else:
        pd.DataFrame().to_csv(out_per_class, index=False, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run all models on all compatible datasets.")
    p.add_argument(
        "--data-root",
        type=str,
        default=str(DATA_ROOT),
        help="Root folder for dataset discovery.",
    )
    p.add_argument(
        "--scaler-config",
        type=str,
        default=str(PROJECT_ROOT / "data" / "prepared" / "config.json"),
        help="Scaler config path for normalized mode.",
    )
    p.add_argument(
        "--mode",
        choices=["both", "norm", "raw"],
        default="both",
        help="Normalization mode passed to test_all_models_full.py.",
    )
    p.add_argument(
        "--output-root",
        type=str,
        default=str(PROJECT_ROOT / "reports" / "all_datasets_runs"),
        help="Per-dataset run outputs directory.",
    )
    p.add_argument(
        "--summary-matrix",
        type=str,
        default=str(PROJECT_ROOT / "reports" / "model_comparison_all_datasets_matrix.csv"),
        help="Merged matrix CSV output.",
    )
    p.add_argument(
        "--summary-per-class",
        type=str,
        default=str(PROJECT_ROOT / "reports" / "model_comparison_all_datasets_per_class.csv"),
        help="Merged per-class CSV output.",
    )
    p.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="Optional explicit dataset CSV paths (skip auto-discovery).",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    data_root = Path(args.data_root)
    scaler_config = Path(args.scaler_config)
    output_root = Path(args.output_root)

    if args.only:
        datasets = [Path(x) for x in args.only]
    else:
        datasets = discover_datasets(data_root)

    if not datasets:
        print("No compatible datasets found.")
        return 2

    print(f"Discovered {len(datasets)} compatible datasets.")
    for ds in datasets:
        print(f"  - {ds}")

    results = []
    for i, ds in enumerate(datasets, 1):
        print(f"\n[{i}/{len(datasets)}] Running dataset: {ds}")
        rc, matrix_csv, per_class_csv, log_path = run_one_dataset(
            dataset_csv=ds,
            scaler_config=scaler_config,
            mode=args.mode,
            out_root=output_root,
        )
        print(f"  return_code={rc}")
        print(f"  matrix={matrix_csv}")
        print(f"  per_class={per_class_csv}")
        print(f"  log={log_path}")
        results.append(
            {
                "dataset": ds,
                "dataset_tag": dataset_tag(ds),
                "return_code": rc,
                "matrix_csv": matrix_csv,
                "per_class_csv": per_class_csv,
                "log_path": log_path,
            }
        )

    merge_outputs(
        results=results,
        out_matrix=Path(args.summary_matrix),
        out_per_class=Path(args.summary_per_class),
    )

    print("\nMerged outputs:")
    print(f"  matrix   : {args.summary_matrix}")
    print(f"  per-class: {args.summary_per_class}")

    failed = [r for r in results if r["return_code"] != 0]
    if failed:
        print(f"\nWARNING: {len(failed)} dataset runs failed. Check per-dataset run.log files.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
