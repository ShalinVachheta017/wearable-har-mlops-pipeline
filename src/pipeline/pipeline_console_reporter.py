"""Console reporting helpers for the production pipeline CLI."""

from __future__ import annotations

from src.entity.artifact_entity import PipelineResult
from src.logger import CURRENT_LOG_FILE, logging

logger = logging.getLogger(__name__)


def print_startup_banner() -> str:
    """
    Method Name :   print_startup_banner
    Description :   Print startup information and detect the runtime device.

    Output      :   Returns "gpu" or "cpu".
    On Failure  :   Logs the error and continues with CPU.
    """
    print("=" * 80)
    print("HAR MLOps Production Pipeline")
    print("=" * 80)
    print(f"  Log file: {CURRENT_LOG_FILE}")
    device = _detect_gpu()
    print("=" * 80)
    print()
    return device


def _detect_gpu() -> str:
    """Detect GPU availability, enable memory growth, and return 'gpu' or 'cpu'."""
    try:
        import tensorflow as tf

        gpus = tf.config.list_physical_devices("GPU")
        if gpus:
            for gpu in gpus:
                try:
                    tf.config.experimental.set_memory_growth(gpu, True)
                except RuntimeError:
                    pass
            names = ", ".join(g.name for g in gpus)
            print(f"  Device : GPU ({names}) - memory growth enabled")
            logger.info("Device: GPU available - %s (memory growth enabled)", names)
            return "gpu"

        tf_ver = getattr(tf, "__version__", "?")
        try:
            parts = tf_ver.split(".")
            tf_major = int(parts[0])
            tf_minor = int(parts[1]) if len(parts) > 1 else 0
        except (ValueError, IndexError):
            tf_major, tf_minor = 0, 0
        if (tf_major, tf_minor) >= (2, 11):
            msg = (
                f"CPU - TF {tf_ver} on Windows-native has no CUDA GPU support "
                "(last native-Windows GPU build was TF 2.10). "
                "Use WSL2 for GPU: tensorflow.org/install/pip"
            )
        else:
            msg = "CPU (no GPU detected)"
        print(f"  Device : {msg}")
        logger.info("Device: %s", msg)
        return "cpu"
    except Exception as exc:
        print(f"  Device : CPU (GPU detection failed: {exc})")
        logger.warning("GPU detection failed: %s", exc)
        return "cpu"


def print_planned_stages(args) -> None:
    """
    Method Name :   print_planned_stages
    Description :   Print the stage manifest before pipeline execution.

    Output      :   Writes the planned stages to stdout.
    On Failure  :   Logs the error and raises the exception.
    """
    core_stages = [
        ("1", "ingestion", "Raw Garmin CSV/XLSX -> fused_<dataset>_50Hz.csv"),
        ("2", "validation", "Schema + value-range checks on fused data"),
        ("3", "transformation", "CSV -> audited, windowed production_X.npy"),
        ("4", "inference", ".npy + pretrained model -> predictions CSV/NPY"),
        ("5", "evaluation", "Confidence / distribution / ECE analysis"),
        ("6", "monitoring", "3-layer (confidence, temporal, z-score drift)"),
        ("7", "trigger", "Automated retraining decision (HEALTHY/WARNING/CRITICAL)"),
    ]
    retrain_stages = [
        (
            "8",
            "retraining",
            "Supervised retraining on labeled data -> retrained .keras",
        ),
        ("9", "registration", "Version, validate proxy metrics, deploy or rollback"),
        (
            "10",
            "baseline_update",
            "Rebuild drift + calibration baselines from new data",
        ),
    ]
    advanced_stages = [
        ("11", "calibration", "Temperature scaling + MC Dropout uncertainty"),
    ]
    explicit = set(args.stages) if args.stages else None

    _safe_print("\n" + "=" * 70)
    _safe_print("  PLANNED PIPELINE STAGES")
    _safe_print("=" * 70)

    _safe_print("\n  -- Training Pipeline (stages 1-7, always included) ----------")
    skipped = {"ingestion"} if args.skip_ingestion else set()
    skipped |= {"validation"} if args.skip_validation else set()
    for num, name, desc in core_stages:
        if explicit and name not in explicit:
            status = "  skip  "
        elif name in skipped:
            status = " --skip "
        else:
            status = "  queue "
        _safe_print(f"    [{status}] Stage {num:>2}: {name:<30}  {desc}")

    if args.retrain or (explicit and any(n in explicit for _, n, _ in retrain_stages)):
        _safe_print("\n  -- Retraining Cycle (stages 8-10, --retrain) ----------------")
        for num, name, desc in retrain_stages:
            status = "  skip  " if explicit and name not in explicit else "  queue "
            _safe_print(f"    [{status}] Stage {num:>2}: {name:<30}  {desc}")

    if args.advanced or (
        explicit and any(n in explicit for _, n, _ in advanced_stages)
    ):
        _safe_print("\n  -- Advanced Analytics (stage 11, --advanced) ----------------")
        for num, name, desc in advanced_stages:
            status = "  skip  " if explicit and name not in explicit else "  queue "
            _safe_print(f"    [{status}] Stage {num:>2}: {name:<30}  {desc}")

    _safe_print("\n  -- Runtime components (not pipeline stages) -----------------")
    _safe_print(
        "    [ always ]        inference/     FastAPI service  (docker/ or src/api/)"
    )
    _safe_print("    [ always ]        monitoring/    Post-prediction monitoring layer")
    _safe_print("    [ on demand ]     deployment/    Model deploy / rollback manager")

    _safe_print("\n" + "=" * 70)
    _safe_print("  Starting execution ...")
    _safe_print("=" * 70 + "\n")


def print_pipeline_summary(result: PipelineResult) -> None:
    """
    Method Name :   print_pipeline_summary
    Description :   Print final pipeline metrics after execution.

    Output      :   Writes summary text to stdout.
    On Failure  :   Logs the error and raises the exception.
    """
    _print_compact_run_summary(result)
    _safe_print("\n" + "=" * 70)
    _safe_print("  PIPELINE SUMMARY")
    _safe_print("=" * 70)

    status_icon = (
        "[OK]"
        if result.overall_status == "SUCCESS"
        else "[!!]" if result.overall_status == "PARTIAL" else "[FAIL]"
    )
    _safe_print(f"\n{status_icon} Overall Status: {result.overall_status}")
    _safe_print(f"   Completed: {len(result.stages_completed)} stages")
    _safe_print(f"   Failed: {len(result.stages_failed)} stages")

    _safe_print("\n  KEY METRICS")
    _safe_print("-" * 70)
    _print_inference_metrics(result)
    _print_monitoring_metrics(result)
    _print_trigger_metrics(result)
    _print_retraining_metrics(result)
    _print_activity_distribution(result)

    _safe_print("\n" + "=" * 70)
    _safe_print(f"  Artifacts saved to: artifacts/{result.run_id}")
    _safe_print(f"  Log file: {CURRENT_LOG_FILE}")
    _safe_print("=" * 70 + "\n")


def _safe_print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        import sys as _sys

        encoding = _sys.stdout.encoding or "utf-8"
        print(
            text.encode(encoding, errors="replace").decode(encoding, errors="replace")
        )


def _print_compact_run_summary(result: PipelineResult) -> None:
    run_id = result.run_id or "-"
    input_src = _input_source_line(result)
    windows = (
        f"{result.transformation.n_windows:,}"
        if result.transformation and result.transformation.n_windows
        else "-"
    )
    infer_line = _inference_line(result)
    conf_line = _confidence_line(result)
    dom_line, dom_flag = _dominant_class_line(result)
    label_line = _label_status_line(result)
    drift_line = _drift_line(result)
    trigger_line = _trigger_line(result)
    mlflow_line = "run logged" if result.mlflow_tracked else "init failed - not tracked"
    total_stages = len(result.stages_completed) + len(result.stages_failed)
    overall_line = f"{result.overall_status or 'UNKNOWN'}  ({len(result.stages_completed)}/{total_stages} stages)"

    width = 64
    _safe_print("\n+" + "=" * width + "+")
    _safe_print("|" + "RUN SUMMARY".center(width) + "|")
    _safe_print("+" + "-" * width + "+")
    for label, value, warn in (
        ("Run ID", run_id, False),
        ("Input source", input_src, False),
        ("Windows", windows, False),
        ("Inference", infer_line, False),
        ("Mean confidence", conf_line, False),
        ("Label status", label_line, False),
        ("Dominant class", dom_line, dom_flag),
        ("Drift status", drift_line, False),
        ("Trigger", trigger_line, False),
        ("MLflow", mlflow_line, False),
        ("Overall", overall_line, False),
    ):
        _safe_print(_box_row(label, value, warn, width))
    _safe_print("+" + "=" * width + "+\n")


def _box_row(label: str, value: str, warn: bool, width: int) -> str:
    marker = " [!]" if warn else "    "
    cell = f"  {label:<18}{marker}{value}"
    if len(cell) > width - 1:
        cell = cell[: width - 4] + "..."
    return "|" + cell.ljust(width) + "|"


def _input_source_line(result: PipelineResult) -> str:
    if not result.ingestion or not getattr(result.ingestion, "fused_csv_path", None):
        return "-"
    import os

    fused_name = os.path.basename(str(result.ingestion.fused_csv_path))
    source_path = getattr(result.ingestion, "source_path", None)
    source_type = getattr(result.ingestion, "source_type", "")
    source_name = os.path.basename(str(source_path)) if source_path else ""
    line = (
        f"{source_name} -> {fused_name}"
        if source_name and source_name != fused_name
        else fused_name
    )
    return f"{line} [{source_type}]" if source_type else line


def _inference_line(result: PipelineResult) -> str:
    if not result.inference:
        return "-"
    duration = getattr(result.inference, "inference_time_seconds", None)
    n_windows = getattr(result.inference, "n_predictions", None)
    if not duration or not n_windows:
        return "-"
    rate = int(n_windows / duration) if duration > 0 else 0
    return f"{duration:.2f}s  ({rate:,} win/sec)"


def _confidence_line(result: PipelineResult) -> str:
    if result.inference and result.inference.confidence_stats:
        return f"{result.inference.confidence_stats.get('mean', 0) * 100:.1f}%"
    return "-"


def _dominant_class_line(result: PipelineResult) -> tuple[str, bool]:
    if not result.inference or not result.inference.activity_distribution:
        return "-", False
    dist = result.inference.activity_distribution
    dominant = max(dist, key=lambda k: dist[k])
    count = dist[dominant]
    total = max(result.inference.n_predictions, 1)
    pct = count / total * 100
    warn = (
        result.evaluation.distribution_dominance_warning
        if result.evaluation
        else pct > 95.0
    )
    suffix = "  [!] dominance flag" if warn else ""
    return f"{dominant} ({pct:.1f}%){suffix}", bool(warn)


def _label_status_line(result: PipelineResult) -> str:
    has_labels = getattr(result, "dataset_has_labels", None)
    source = getattr(result, "dataset_label_source", None)
    if has_labels is True:
        return f"LABELED ({source})" if source else "LABELED"
    if has_labels is False:
        return f"UNLABELED ({source})" if source else "UNLABELED"
    return "unknown"


def _drift_line(result: PipelineResult) -> str:
    if not result.monitoring or not result.monitoring.layer3_drift:
        return "-"
    drift = result.monitoring.layer3_drift
    return f"{drift.get('status', result.monitoring.overall_status)}  (max={drift.get('max_drift', 0):.3f})"


def _trigger_line(result: PipelineResult) -> str:
    if not result.trigger:
        return "-"
    reasons = result.trigger.reasons or []
    return f"{result.trigger.action or 'NONE'}  ({reasons[0] if reasons else 'all metrics normal'})"


def _print_inference_metrics(result: PipelineResult) -> None:
    if not result.inference:
        return
    _safe_print("\n  Inference:")
    _safe_print(f"    - Predictions: {result.inference.n_predictions:,}")
    _safe_print(f"    - Duration: {result.inference.inference_time_seconds:.2f}s")
    if result.inference.confidence_stats:
        conf = result.inference.confidence_stats
        n_uncertain = conf.get("n_uncertain", 0)
        pct = n_uncertain / max(result.inference.n_predictions, 1) * 100
        _safe_print(f"    - Mean Confidence: {conf.get('mean', 0) * 100:.1f}%")
        _safe_print(f"    - Uncertain: {n_uncertain} ({pct:.1f}%)")


def _print_monitoring_metrics(result: PipelineResult) -> None:
    if not result.monitoring:
        return
    _safe_print("\n  Monitoring:")
    _safe_print(f"    - Overall: {result.monitoring.overall_status}")
    if result.monitoring.layer3_drift:
        drift = result.monitoring.layer3_drift
        score = drift.get("max_drift", 0)
        status = drift.get("status", result.monitoring.overall_status)
        _safe_print(f"    - Drift Score: {score:.4f}")
        if status == "CRITICAL":
            _safe_print(
                f"      [!] CRITICAL DRIFT ({score:.3f}) - Manual review required"
            )
        elif status == "WARNING":
            _safe_print(f"      [~] WARNING drift ({score:.3f}) - Monitor closely")
        else:
            _safe_print("      [ok] Drift within acceptable range")


def _print_trigger_metrics(result: PipelineResult) -> None:
    if not result.trigger:
        return
    _safe_print("\n  Retraining Decision:")
    icon = "[retrain]" if result.trigger.should_retrain else "[ok]"
    _safe_print(
        f"    {icon} Should Retrain: {'YES' if result.trigger.should_retrain else 'NO'}"
    )
    _safe_print(f"    - Alert Level: {result.trigger.alert_level}")
    if result.trigger.reasons:
        _safe_print("    - Reasons:")
        for reason in result.trigger.reasons[:3]:
            _safe_print(f"      - {reason}")


def _print_retraining_metrics(result: PipelineResult) -> None:
    if not result.retraining:
        return
    _safe_print("\n  Retraining:")
    for key, value in result.retraining.metrics.items():
        _safe_print(
            f"    - {key}: {value:.4f}"
            if isinstance(value, float)
            else f"    - {key}: {value}"
        )
    _safe_print(f"    - Source samples: {result.retraining.n_source_samples}")
    _safe_print(f"    - Target samples: {result.retraining.n_target_samples}")


def _print_activity_distribution(result: PipelineResult) -> None:
    if not result.inference or not result.inference.activity_distribution:
        return
    _safe_print("\n  Top 3 Activities Detected:")
    top = sorted(
        result.inference.activity_distribution.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:3]
    for activity, count in top:
        pct = count / max(result.inference.n_predictions, 1) * 100
        _safe_print(f"    - {activity}: {count} ({pct:.1f}%)")
