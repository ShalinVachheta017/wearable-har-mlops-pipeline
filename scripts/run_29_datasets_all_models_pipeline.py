"""
Run full pipeline for:
  - 26 production raw datasets (accel+gyro pairs from batch_28 manifest)
  - 2 synthetic CSV datasets
  - 1 training CSV dataset
across all configured models.

Outputs:
  reports/pipeline_model_matrix_29xN.csv
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "reports" / "pipeline_runs" / "batch_28_full" / "all_runs_metrics_live.csv"
PIPELINE_RESULTS_DIR = ROOT / "logs" / "pipeline"
OUTPUT_CSV_DEFAULT = ROOT / "reports" / "pipeline_model_matrix_29xN.csv"
STAGES = [
    "ingestion",
    "validation",
    "transformation",
    "inference",
    "evaluation",
    "monitoring",
    "trigger",
]


MODELS: Dict[str, Path] = {
    "pretrained/fine_tuned_1dcnnbilstm": ROOT / "models/pretrained/fine_tuned_model_1dcnnbilstm.keras",
    "pretrained/current_model": ROOT / "models/pretrained/current_model.keras",
    "actual_model/fine_tuned_1dcnnbilstm": ROOT / "models/actual model/fine_tuned_model_1dcnnbilstm.keras",
    "registry/har_model_vauto": ROOT / "models/registry/har_model_vauto.keras",
    "retrained/har_20260327_223917": ROOT / "models/retrained/har_model_20260327_223917.keras",
    "retrained/har_20260327_213930": ROOT / "models/retrained/har_model_20260327_213930.keras",
    "retrained/har_20260219_124914": ROOT / "models/retrained/har_model_20260219_124914.keras",
    "retrained/har_20260219_123616": ROOT / "models/retrained/har_model_20260219_123616.keras",
    "retrained/best_model": ROOT / "models/retrained/best_model.keras",
    "retrained/har_model_latest": ROOT / "models/retrained/har_model_latest.keras",
    "retrained/retrained_model": ROOT / "models/retrained/retrained_model.keras",
    "retrained/pseudo_label_model": ROOT / "models/retrained/pseudo_label_model.keras",
    "retrained/adabn_configA": ROOT / "models/retrained/adabn_adapted_model_configA_20260329_002340.keras",
    "retrained/adabn_configB": ROOT / "models/retrained/adabn_adapted_model_configB_20260329_002515.keras",
    "retrained/adabn_configC": ROOT / "models/retrained/adabn_adapted_model_configC_20260329_002638.keras",
    "retrained/adabn_configD": ROOT / "models/retrained/adabn_adapted_model_configD_20260328_232204.keras",
    "retrained/adabn_tent_adapted": ROOT / "models/retrained/adabn_tent_adapted_model.keras",
}


@dataclass
class DatasetSpec:
    dataset_id: str
    dataset_group: str  # production_raw | synthetic | training
    source_accel: Optional[Path] = None
    source_gyro: Optional[Path] = None
    source_csv: Optional[Path] = None


def _safe_path(p: object) -> Optional[Path]:
    if p is None:
        return None
    s = str(p).strip()
    if not s or s.lower() in {"nan", "none"}:
        return None
    return Path(s)


def load_29_specs(manifest_path: Path) -> List[DatasetSpec]:
    df = pd.read_csv(manifest_path)
    # 26 production raw pairs
    raw = df[df["dataset_type"].astype(str).str.lower() == "raw"].copy()
    raw = raw.sort_values("dataset_id")
    specs: List[DatasetSpec] = []
    for _, r in raw.iterrows():
        accel = _safe_path(r.get("source_accel"))
        gyro = _safe_path(r.get("source_gyro"))
        if accel is None or gyro is None:
            continue
        specs.append(
            DatasetSpec(
                dataset_id=str(r["dataset_id"]),
                dataset_group="production_raw",
                source_accel=accel,
                source_gyro=gyro,
            )
        )

    # 2 synthetic CSVs
    synth = df[df["dataset_type"].astype(str).str.lower() == "synthetic"].copy()
    synth = synth.sort_values("dataset_id")
    for _, r in synth.iterrows():
        csvp = _safe_path(r.get("source_csv"))
        if csvp is None:
            continue
        specs.append(
            DatasetSpec(
                dataset_id=str(r["dataset_id"]),
                dataset_group="synthetic",
                source_csv=csvp,
            )
        )

    # +1 training dataset
    specs.append(
        DatasetSpec(
            dataset_id="all_users_data_labeled",
            dataset_group="training",
            source_csv=ROOT / "data" / "all_users_data_labeled.csv",
        )
    )

    return specs


def build_command(python_bin: str, spec: DatasetSpec, model_path: Path) -> List[str]:
    cmd = [python_bin, "run_pipeline.py", "--stages", *STAGES]
    if spec.source_csv is not None:
        cmd += ["--input-csv", str(spec.source_csv)]
    else:
        cmd += ["--accel-file", str(spec.source_accel), "--gyro-file", str(spec.source_gyro)]
    cmd += ["--model", str(model_path)]
    return cmd


def newest_pipeline_result(before: set[Path]) -> Optional[Path]:
    all_now = set(PIPELINE_RESULTS_DIR.glob("pipeline_result_*.json"))
    new_files = [p for p in all_now - before if p.is_file()]
    if new_files:
        return max(new_files, key=lambda p: p.stat().st_mtime)
    if not all_now:
        return None
    return max(all_now, key=lambda p: p.stat().st_mtime)


def parse_run_id_from_stdout(stdout: str) -> Optional[str]:
    # Example line: "✅ Pipeline run summary saved: ...\\pipeline_result_20260423_165251.json"
    if not stdout:
        return None
    marker = "pipeline_result_"
    idx = stdout.rfind(marker)
    if idx < 0:
        return None
    tail = stdout[idx:]
    # expected token ends with .json
    end = tail.find(".json")
    if end < 0:
        return None
    name = tail[: end + 5]
    # name now "pipeline_result_<run_id>.json"
    prefix = "pipeline_result_"
    suffix = ".json"
    if not (name.startswith(prefix) and name.endswith(suffix)):
        return None
    return name[len(prefix) : -len(suffix)]


def parse_pipeline_json(path: Optional[Path]) -> Dict[str, object]:
    if path is None or not path.exists():
        return {"pipeline_result_json": None}
    try:
        j = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"pipeline_result_json": str(path)}

    out: Dict[str, object] = {"pipeline_result_json": str(path)}
    out["run_id"] = j.get("run_id")
    out["overall_status"] = j.get("overall_status")
    out["dataset_has_labels"] = j.get("dataset_has_labels")

    inf = j.get("inference") or {}
    ev = j.get("evaluation") or {}
    mon = j.get("monitoring") or {}
    trg = j.get("trigger") or {}

    out["active_model_path"] = inf.get("active_model_path")
    out["n_predictions"] = inf.get("n_predictions")
    conf = inf.get("confidence_stats") or {}
    out["mean_confidence"] = conf.get("mean")
    out["std_confidence"] = conf.get("std")

    out["dominant_class"] = ev.get("dominant_class")
    out["dominant_pct"] = ev.get("dominant_pct")
    out["eval_accuracy"] = (ev.get("classification_metrics") or {}).get("accuracy")
    out["eval_f1_macro"] = (ev.get("classification_metrics") or {}).get("f1_macro")

    out["monitoring_status"] = mon.get("overall_status")
    out["trigger_should_retrain"] = trg.get("should_retrain")
    out["trigger_action"] = trg.get("action")
    out["trigger_alert_level"] = trg.get("alert_level")
    return out


def run_one(
    python_bin: str,
    spec: DatasetSpec,
    model_name: str,
    model_path: Path,
    timeout_sec: int,
) -> Dict[str, object]:
    row: Dict[str, object] = {
        "dataset_id": spec.dataset_id,
        "dataset_group": spec.dataset_group,
        "source_accel": str(spec.source_accel) if spec.source_accel else None,
        "source_gyro": str(spec.source_gyro) if spec.source_gyro else None,
        "source_csv": str(spec.source_csv) if spec.source_csv else None,
        "model_name": model_name,
        "model_path": str(model_path),
    }
    if not model_path.exists():
        row.update({"return_code": -10, "error": "model_file_missing"})
        return row

    before = set(PIPELINE_RESULTS_DIR.glob("pipeline_result_*.json"))
    cmd = build_command(python_bin=python_bin, spec=spec, model_path=model_path)
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            env=env,
            timeout=timeout_sec,
        )
        row["return_code"] = proc.returncode
        row["stderr_tail"] = proc.stderr[-1200:] if proc.stderr else ""
        row["stdout_tail"] = proc.stdout[-800:] if proc.stdout else ""
    except subprocess.TimeoutExpired:
        row.update({"return_code": -9, "error": f"timeout>{timeout_sec}s"})
        return row

    # Only trust parsed pipeline JSON when command succeeded.
    if int(row.get("return_code", -1)) == 0:
        run_id_from_out = parse_run_id_from_stdout(str(row.get("stdout_tail", "")))
        if run_id_from_out:
            explicit = PIPELINE_RESULTS_DIR / f"pipeline_result_{run_id_from_out}.json"
            if explicit.exists():
                pj = explicit
            else:
                pj = newest_pipeline_result(before)
        else:
            pj = newest_pipeline_result(before)
        row.update(parse_pipeline_json(pj))
    else:
        row.update(
            {
                "pipeline_result_json": None,
                "run_id": None,
                "overall_status": None,
                "dataset_has_labels": None,
                "active_model_path": None,
                "n_predictions": None,
                "mean_confidence": None,
                "std_confidence": None,
                "dominant_class": None,
                "dominant_pct": None,
                "eval_accuracy": None,
                "eval_f1_macro": None,
                "monitoring_status": None,
                "trigger_should_retrain": None,
                "trigger_action": None,
                "trigger_alert_level": None,
            }
        )
    return row


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", default=str(MANIFEST))
    p.add_argument("--python-bin", default=sys.executable)
    p.add_argument("--output-csv", default=str(OUTPUT_CSV_DEFAULT))
    p.add_argument("--timeout-sec", type=int, default=1800)
    p.add_argument("--only-models", nargs="*", default=None, help="Optional subset of model keys.")
    p.add_argument("--limit-datasets", type=int, default=0, help="Debug only.")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    specs = load_29_specs(Path(args.manifest))

    # enforce target set size expectation where possible
    prod_n = sum(1 for s in specs if s.dataset_group == "production_raw")
    synth_n = sum(1 for s in specs if s.dataset_group == "synthetic")
    train_n = sum(1 for s in specs if s.dataset_group == "training")
    print(f"Dataset counts -> production_raw={prod_n}, synthetic={synth_n}, training={train_n}, total={len(specs)}")

    if args.limit_datasets > 0:
        specs = specs[: args.limit_datasets]

    model_items = list(MODELS.items())
    if args.only_models:
        keep = set(args.only_models)
        model_items = [(k, v) for (k, v) in model_items if k in keep]

    total = len(specs) * len(model_items)
    print(f"Planned runs: {len(specs)} datasets x {len(model_items)} models = {total}")

    rows: List[Dict[str, object]] = []
    run_i = 0
    out_csv = Path(args.output_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    for spec in specs:
        for model_name, model_path in model_items:
            run_i += 1
            print(f"[{run_i}/{total}] {spec.dataset_id} :: {model_name}")
            row = run_one(
                python_bin=args.python_bin,
                spec=spec,
                model_name=model_name,
                model_path=model_path,
                timeout_sec=args.timeout_sec,
            )
            rows.append(row)
            # checkpoint write
            pd.DataFrame(rows).to_csv(out_csv, index=False, encoding="utf-8")

    print(f"Saved: {out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
