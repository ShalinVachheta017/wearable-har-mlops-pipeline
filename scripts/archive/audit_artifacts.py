#!/usr/bin/env python3
"""
Audit Artifacts — verify pipeline outputs exist per run.

Usage:
    python scripts/audit_artifacts.py                        # latest run, stages 1-7
    python scripts/audit_artifacts.py --retrain              # include stages 8-10
    python scripts/audit_artifacts.py --run-id 20260219_104537
    python scripts/audit_artifacts.py --run-id 20260219_104537 --retrain
"""

import argparse
import glob
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── Check definitions ──────────────────────────────────────────────────
# Each entry: (glob_pattern_relative_to_project_root, human_label)
# Patterns use forward slashes; resolved at runtime.

CHECKS_INFERENCE = {
    "1_ingestion": [
        ("data/processed/sensor_fused_50Hz.csv", "Fused CSV"),
    ],
    "2_validation": [],  # checked via pipeline_result JSON below
    "3_transformation": [
        ("data/prepared/production_X.npy", "Windowed numpy array"),
    ],
    "4_inference": [
        ("data/prepared/predictions/predictions_*.csv", "Predictions CSV"),
        ("data/prepared/predictions/predictions_*.npy", "Predictions NPY"),
    ],
    "5_evaluation": [
        ("outputs/evaluation/evaluation_*.json", "Evaluation report JSON"),
    ],
    "6_monitoring": [
        ("outputs/evaluation/monitoring_report.json", "Monitoring report JSON"),
    ],
    "7_trigger": [
        ("logs/pipeline/pipeline_result_*.json", "Pipeline result JSON"),
    ],
}

CHECKS_RETRAIN = {
    "8_retraining": [
        ("models/retrained/*.keras", "Retrained model"),
    ],
    "9_registration": [],  # checked via pipeline_result JSON
    "10_baseline": [
        ("models/training_baseline.json", "Training baseline JSON"),
        ("models/normalized_baseline.json", "Normalized baseline JSON"),
    ],
}

# Stages whose pass/fail is verified by checking stages_completed in result JSON
JSON_VERIFIED_STAGES = {"validation", "registration"}


def find_latest_run_id(artifacts_dir: Path) -> str | None:
    """Return the newest run_id folder name in artifacts/."""
    dirs = sorted(
        [d.name for d in artifacts_dir.iterdir() if d.is_dir()],
        reverse=True,
    )
    return dirs[0] if dirs else None


def find_pipeline_result(root: Path) -> Path | None:
    """Return the most recent pipeline_result_*.json."""
    pattern = str(root / "logs" / "pipeline" / "pipeline_result_*.json")
    matches = sorted(glob.glob(pattern), reverse=True)
    return Path(matches[0]) if matches else None


def check_stages_in_result(result_path: Path, stages: set[str]) -> dict[str, bool]:
    """Return {stage: True/False} by parsing stages_completed in result JSON."""
    try:
        with open(result_path) as f:
            data = json.load(f)
        completed = set(data.get("stages_completed", []))
        return {s: (s in completed) for s in stages}
    except Exception:
        return {s: False for s in stages}


def check_file_pattern(root: Path, pattern: str) -> tuple[bool, str]:
    """
    Check a glob pattern relative to project root.
    Returns (passed, detail_string).
    """
    full = str(root / pattern)
    matches = glob.glob(full)
    if not matches:
        return False, "not found"
    # Check at least one match has size > 0
    non_empty = [m for m in matches if os.path.getsize(m) > 0]
    if not non_empty:
        return False, f"{len(matches)} match(es) but all 0 bytes"
    total_bytes = sum(os.path.getsize(m) for m in non_empty)
    if total_bytes > 1_048_576:
        detail = f"{len(non_empty)} match(es), {total_bytes / 1_048_576:.1f} MB"
    else:
        detail = f"{len(non_empty)} match(es), {total_bytes:,} bytes"
    return True, detail


def run_audit(root: Path, include_retrain: bool, run_id: str | None) -> int:
    """Run the audit and return number of failures."""
    checks = dict(CHECKS_INFERENCE)
    if include_retrain:
        checks.update(CHECKS_RETRAIN)

    # Header
    print()
    print(f"  HAR MLOps Artifact Audit")
    print(f"  Project root : {root}")
    if run_id:
        print(f"  Run ID       : {run_id}")
    print(f"  Retrain check: {'YES' if include_retrain else 'NO (stages 1-7 only)'}")
    print()
    print(f"  {'Stage':<18} {'Check':<28} {'Status'}")
    print(f"  {'─' * 18} {'─' * 28} {'─' * 30}")

    n_pass = 0
    n_fail = 0

    for stage, file_checks in checks.items():
        if not file_checks:
            # JSON-verified stage — skip file check row, handled separately
            continue
        for pattern, label in file_checks:
            passed, detail = check_file_pattern(root, pattern)
            status = f"PASS ({detail})" if passed else f"FAIL ({detail})"
            icon = "+" if passed else "X"
            print(f"  {stage:<18} {label:<28} [{icon}] {status}")
            if passed:
                n_pass += 1
            else:
                n_fail += 1

    # JSON-verified stages
    result_path = find_pipeline_result(root)
    stages_to_verify = {"validation"}
    if include_retrain:
        stages_to_verify.add("registration")

    if result_path:
        json_results = check_stages_in_result(result_path, stages_to_verify)
        for stage_name, passed in json_results.items():
            stage_key = {"validation": "2_validation", "registration": "9_registration"}[stage_name]
            detail = "in stages_completed" if passed else "NOT in stages_completed"
            icon = "+" if passed else "X"
            status = f"PASS ({detail})" if passed else f"FAIL ({detail})"
            print(f"  {stage_key:<18} {'Stage completed (JSON)':<28} [{icon}] {status}")
            if passed:
                n_pass += 1
            else:
                n_fail += 1
    else:
        for stage_name in stages_to_verify:
            stage_key = {"validation": "2_validation", "registration": "9_registration"}[stage_name]
            print(f"  {stage_key:<18} {'Stage completed (JSON)':<28} [X] FAIL (no pipeline_result JSON found)")
            n_fail += 1

    # Artifact dir check (bonus traceability)
    if run_id:
        art_dir = root / "artifacts" / run_id
        if art_dir.exists():
            n_art_files = sum(1 for _ in art_dir.rglob("*") if _.is_file())
            print(f"\n  Artifact dir   : {art_dir}  ({n_art_files} files)")
        else:
            print(f"\n  Artifact dir   : {art_dir}  (NOT FOUND)")

    # Summary
    total = n_pass + n_fail
    print(f"\n  {'─' * 76}")
    print(f"  Result: {n_pass}/{total} PASS, {n_fail}/{total} FAIL")
    print()

    return n_fail


def main():
    parser = argparse.ArgumentParser(description="Audit pipeline artifacts for a given run.")
    parser.add_argument("--run-id", type=str, default=None,
                        help="Run ID (timestamp folder name). Default: auto-pick latest.")
    parser.add_argument("--retrain", action="store_true",
                        help="Include stages 8-10 checks (retraining/registration/baseline).")
    parser.add_argument("--root", type=str, default=None,
                        help="Project root directory. Default: auto-detect from script location.")
    args = parser.parse_args()

    root = Path(args.root) if args.root else PROJECT_ROOT

    run_id = args.run_id
    if not run_id:
        run_id = find_latest_run_id(root / "artifacts")
        if run_id:
            print(f"  Auto-detected latest run: {run_id}")

    n_failures = run_audit(root, args.retrain, run_id)
    sys.exit(n_failures)


if __name__ == "__main__":
    main()
