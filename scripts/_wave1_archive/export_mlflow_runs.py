"""
Export MLflow experiment runs to CSV for offline review and ablation table.

Usage
-----
# Export by experiment name (most common)
python scripts/export_mlflow_runs.py --experiment har-retraining

# Export multiple experiments
python scripts/export_mlflow_runs.py --experiment har-production-pipeline har-retraining

# Custom tracking URI (if not using local mlruns/)
python scripts/export_mlflow_runs.py --experiment har-retraining \
    --tracking-uri http://127.0.0.1:5000

# Filter to specific run status
python scripts/export_mlflow_runs.py --experiment har-retraining --status FINISHED

# Limit columns (params + metrics only, no tags)
python scripts/export_mlflow_runs.py --experiment har-retraining --no-tags

Output: mlflow_export_<experiment_name>_<timestamp>.csv in outputs/ folder
"""

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

# Allow running from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _get_client(tracking_uri: str | None):
    """Return an MlflowClient pointed at the given URI."""
    import mlflow
    from mlflow.tracking import MlflowClient

    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
    else:
        # Default: look for local mlruns/ SQLite DB
        default_db = PROJECT_ROOT / "mlruns" / "mlflow.db"
        if default_db.exists():
            mlflow.set_tracking_uri(f"sqlite:///{default_db}")
        else:
            # Fall back to directory-based tracking
            mlflow.set_tracking_uri(str(PROJECT_ROOT / "mlruns"))

    return MlflowClient()


def export_experiment(
    experiment_name: str,
    client,
    output_dir: Path,
    status_filter: str | None = None,
    include_tags: bool = True,
) -> Path:
    """Export one experiment to CSV and return the output path."""

    # Resolve experiment
    exp = client.get_experiment_by_name(experiment_name)
    if exp is None:
        # Try treating it as a numeric ID
        try:
            exp = client.get_experiment(experiment_name)
        except Exception:
            pass
    if exp is None:
        print(f"  [WARN] Experiment not found: {experiment_name!r} — skipping.")
        return None

    print(f"  Experiment: {exp.name!r}  (id={exp.experiment_id})")

    # Fetch runs
    filter_str = f"attributes.status = '{status_filter}'" if status_filter else None
    runs = client.search_runs(
        experiment_ids=[exp.experiment_id],
        filter_string=filter_str,
        order_by=["start_time DESC"],
        max_results=500,
    )

    if not runs:
        print(f"  [WARN] No runs found in {experiment_name!r}.")
        return None

    print(f"  Found {len(runs)} run(s).")

    # ── Collect all column names ──────────────────────────────────────
    all_param_keys:  set[str] = set()
    all_metric_keys: set[str] = set()
    all_tag_keys:    set[str] = set()

    for run in runs:
        all_param_keys.update(run.data.params.keys())
        all_metric_keys.update(run.data.metrics.keys())
        if include_tags:
            all_tag_keys.update(run.data.tags.keys())

    base_cols = ["run_id", "run_name", "status", "start_time", "end_time",
                 "duration_s", "artifact_uri"]
    param_cols  = sorted(f"param.{k}"  for k in all_param_keys)
    metric_cols = sorted(f"metric.{k}" for k in all_metric_keys)
    tag_cols    = sorted(f"tag.{k}"    for k in all_tag_keys) if include_tags else []
    fieldnames  = base_cols + param_cols + metric_cols + tag_cols

    # ── Build rows ────────────────────────────────────────────────────
    rows = []
    for run in runs:
        start_ms = run.info.start_time
        end_ms   = run.info.end_time
        duration = ""
        if start_ms and end_ms:
            duration = f"{(end_ms - start_ms) / 1000:.1f}"

        row: dict = {
            "run_id":       run.info.run_id,
            "run_name":     run.info.run_name or "",
            "status":       run.info.status,
            "start_time":   datetime.fromtimestamp(start_ms / 1000).isoformat() if start_ms else "",
            "end_time":     datetime.fromtimestamp(end_ms   / 1000).isoformat() if end_ms   else "",
            "duration_s":   duration,
            "artifact_uri": run.info.artifact_uri,
        }
        for k, v in run.data.params.items():
            row[f"param.{k}"] = v
        for k, v in run.data.metrics.items():
            row[f"metric.{k}"] = round(v, 6) if isinstance(v, float) else v
        if include_tags:
            for k, v in run.data.tags.items():
                row[f"tag.{k}"] = v

        rows.append(row)

    # ── Save CSV ──────────────────────────────────────────────────────
    ts        = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = experiment_name.replace("/", "_").replace(" ", "_")
    out_path  = output_dir / f"mlflow_export_{safe_name}_{ts}.csv"

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Saved: {out_path}  ({len(rows)} rows, {len(fieldnames)} columns)")
    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="Export MLflow runs to CSV for review and ablation table.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--experiment", "-e",
        nargs="+",
        required=True,
        help="Experiment name(s) or numeric ID(s) to export.",
    )
    parser.add_argument(
        "--tracking-uri",
        default=None,
        help="MLflow tracking URI (default: auto-detect local mlruns/).",
    )
    parser.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / "outputs"),
        help="Directory to write CSV files (default: outputs/).",
    )
    parser.add_argument(
        "--status",
        default=None,
        choices=["RUNNING", "FINISHED", "FAILED", "KILLED"],
        help="Filter by run status (default: all).",
    )
    parser.add_argument(
        "--no-tags",
        action="store_true",
        help="Exclude tag columns from the CSV (smaller file).",
    )

    args = parser.parse_args()

    try:
        client = _get_client(args.tracking_uri)
    except Exception as exc:
        print(f"[ERROR] Could not connect to MLflow: {exc}")
        sys.exit(1)

    output_dir = Path(args.output_dir)
    print(f"\nExporting to: {output_dir}\n")

    exported = []
    for exp_name in args.experiment:
        print(f"Processing experiment: {exp_name!r}")
        out = export_experiment(
            experiment_name=exp_name,
            client=client,
            output_dir=output_dir,
            status_filter=args.status,
            include_tags=not args.no_tags,
        )
        if out:
            exported.append(out)
        print()

    if exported:
        print(f"Done. {len(exported)} file(s) exported:")
        for p in exported:
            print(f"  {p}")
    else:
        print("No files exported.")
        sys.exit(1)


if __name__ == "__main__":
    main()
