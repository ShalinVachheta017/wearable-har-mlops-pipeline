#!/usr/bin/env python3
"""
=============================================================================
HAR MLOps — Production Pipeline  (Single Entry Point)
=============================================================================

Run the ENTIRE 14-stage production pipeline with one command:

    python run_pipeline.py                                      # stages 1-7
    python run_pipeline.py --retrain --adapt adabn_tent         # + two-stage TTA (recommended)
    python run_pipeline.py --retrain --adapt adabn              # + AdaBN only
    python run_pipeline.py --retrain --adapt tent               # + TENT entropy-min
    python run_pipeline.py --retrain --adapt pseudo_label       # + calibrated pseudo-labels
    python run_pipeline.py --advanced                  # + calibration, drift, etc.
    python run_pipeline.py --stages inference evaluation  # specific stages
    python run_pipeline.py --input-csv my_recording.csv   # your own data

Pipeline stages (in order):
     1  ingestion         →  raw Garmin Excel / CSV → sensor_fused_50Hz.csv
     2  validation        →  schema + value-range checks
     3  transformation    →  CSV → normalised, windowed production_X.npy
     4  inference         →  .npy + pretrained model → predictions CSV/NPY
     5  evaluation        →  confidence / distribution / ECE analysis
     6  monitoring        →  3-layer (confidence, temporal, drift)
     7  trigger           →  automated retraining decision
  ── retraining cycle (--retrain) ──
     8  retraining        →  standard / AdaBN / pseudo-label
     9  registration      →  version, deploy, rollback
    10  baseline_update   →  rebuild drift baselines
  ── advanced analytics (--advanced) ──
    11  calibration       →  temperature scaling, MC Dropout, ECE
    12  wasserstein_drift →  Wasserstein distance, change-point detection
    13  curriculum_pseudo_labeling → progressive self-training with EWC
    14  sensor_placement  →  hand detection, axis mirroring augmentation

Result LOG → logs/pipeline/pipeline_result_<timestamp>.log
Result JSON → logs/pipeline/pipeline_result_<timestamp>.json

=============================================================================
"""

import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Import centralized logger
from src.logger import CURRENT_LOG_FILE, logging

logger = logging.getLogger(__name__)

from src.entity.config_entity import (
    DataIngestionConfig,
    DataTransformationConfig,
    ModelInferenceConfig,
    ModelRetrainingConfig,
    PipelineConfig,
)
from src.pipeline.production_pipeline import ProductionPipeline
from src.utils.config_loader import (
    apply_overrides,
    load_monitoring_config,
    load_trigger_config,
    load_yaml_overrides,
)

# Logging is already configured in src.logger module - no need for basicConfig here


def parse_args():
    parser = argparse.ArgumentParser(
        description="HAR MLOps Production Pipeline — run all stages with one command",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full inference cycle (stages 1-7)
  python run_pipeline.py

  # Skip ingestion — CSV already exists
  python run_pipeline.py --skip-ingestion

  # Inference onward (stages 4-7)
  python run_pipeline.py --stages inference evaluation monitoring trigger

  # Your own recording — CSV input
  python run_pipeline.py --input-csv data/raw/my_recording.csv

  # Full cycle + two-stage TTA (recommended for moderate drift)
  python run_pipeline.py --retrain --adapt adabn_tent

  # Full cycle + AdaBN only (fastest)
  python run_pipeline.py --retrain --adapt adabn

  # Full cycle + TENT entropy minimisation
  python run_pipeline.py --retrain --adapt tent

  # Retrain with calibrated pseudo-labeling
  python run_pipeline.py --retrain --adapt pseudo_label

  # Advanced analytics (calibration, Wasserstein drift, etc.)
  python run_pipeline.py --advanced

  # Curriculum pseudo-labeling only
  python run_pipeline.py --stages curriculum_pseudo_labeling --curriculum-iterations 10

  # Run specific advanced stages
  python run_pipeline.py --stages calibration wasserstein_drift sensor_placement

  # Continue past errors
  python run_pipeline.py --continue-on-failure
        """,
    )

    parser.add_argument(
        "--stages",
        nargs="+",
        choices=[
            "ingestion",
            "validation",
            "transformation",
            "inference",
            "evaluation",
            "monitoring",
            "trigger",
            "retraining",
            "registration",
            "baseline_update",
            "calibration",
            "wasserstein_drift",
            "curriculum_pseudo_labeling",
            "sensor_placement",
        ],
        default=None,
        help="Run only these stages (default: 1-7; use --retrain for 8-10, --advanced for 11-14)",
    )
    parser.add_argument(
        "--skip-ingestion",
        action="store_true",
        help="Skip data ingestion — use existing sensor_fused_50Hz.csv",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip data validation",
    )
    parser.add_argument(
        "--continue-on-failure",
        action="store_true",
        help="Log errors and continue to next stage instead of aborting",
    )

    # ── Input overrides ───────────────────────────────────────────────
    parser.add_argument(
        "--input-csv",
        type=str,
        default=None,
        help="Path to fused CSV (your own recording, ABCD cases)",
    )
    parser.add_argument(
        "--accel-file",
        type=str,
        default=None,
        help="Path to raw accelerometer CSV/XLSX (targets one specific session)",
    )
    parser.add_argument(
        "--gyro-file",
        type=str,
        default=None,
        help="Path to raw gyroscope CSV/XLSX (targets one specific session)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Path to .keras model for inference",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/pipeline_config.yaml",
        help="Path to YAML config file (default: config/pipeline_config.yaml)",
    )
    parser.add_argument(
        "--gravity-removal",
        action="store_true",
        default=None,
        help="Enable gravity removal (overrides config file)",
    )
    parser.add_argument(
        "--no-unit-conversion",
        action="store_true",
        help="Disable unit conversion milliG→m/s² (overrides config file)",
    )
    parser.add_argument(
        "--no-normalization",
        action="store_true",
        help="Disable data normalization (overrides config file) — for comparison experiments",
    )
    parser.add_argument(
        "--normalization-variant",
        type=str,
        default=None,
        choices=["zscore", "robust", "none"],
        help="Normalization variant to use (overrides config file): zscore | robust | none",
    )
    parser.add_argument(
        "--calibrate",
        action="store_true",
        default=None,
        help="Enable domain calibration (overrides config file)",
    )

    # ── Retraining flags ──────────────────────────────────────────────
    parser.add_argument(
        "--retrain",
        action="store_true",
        help="Include stages 8-10 (retraining → registration → baseline)",
    )
    parser.add_argument(
        "--adapt",
        type=str,
        choices=["adabn", "tent", "adabn_tent", "pseudo_label", "none"],
        default="none",
        help="Domain adaptation method for retraining (default: none)",
    )
    parser.add_argument(
        "--labels",
        type=str,
        default=None,
        help="Path to ground-truth labels for supervised retraining",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=100,
        help="Training epochs for retraining (default: 100)",
    )
    parser.add_argument(
        "--skip-cv",
        action="store_true",
        help="Skip cross-validation during retraining (faster audit runs)",
    )
    parser.add_argument(
        "--auto-deploy",
        action="store_true",
        help="Automatically deploy retrained model if proxy validation passes",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        default=False,
        help=(
            "Promote rebuilt baseline to the shared models/ path that monitoring reads. "
            "Default: False — baseline is saved only as an MLflow artifact (safe). "
            "Only set this when you are confident the new baseline reflects production reality."
        ),
    )

    # ── Advanced analytics flags ──────────────────────────────────────
    parser.add_argument(
        "--advanced",
        action="store_true",
        help="Include stages 11-14 (calibration, Wasserstein drift, "
        "curriculum pseudo-labeling, sensor placement)",
    )
    parser.add_argument(
        "--curriculum-iterations",
        type=int,
        default=5,
        help="Number of curriculum pseudo-labeling iterations (default: 5)",
    )
    parser.add_argument(
        "--ewc-lambda",
        type=float,
        default=1000.0,
        help="EWC regularization strength (default: 1000.0)",
    )
    parser.add_argument(
        "--mc-dropout-passes",
        type=int,
        default=30,
        help="Number of MC Dropout forward passes (default: 30)",
    )

    return parser.parse_args()


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
                    pass  # memory growth must be set before GPUs are initialized
            names = ", ".join(g.name for g in gpus)
            print(f"  Device : GPU ({names}) — memory growth enabled")
            logger.info("Device: GPU available — %s (memory growth enabled)", names)
            return "gpu"
        else:
            tf_ver = getattr(tf, "__version__", "?")
            if tf_ver >= "2.11":
                msg = (
                    f"CPU — TF {tf_ver} on Windows-native has no CUDA GPU support "
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


def load_preprocessing_config(config_path: str) -> dict:
    """Load preprocessing toggles from YAML config file."""
    import yaml

    path = Path(config_path)
    if not path.exists():
        print(f"Config file not found: {path}, using defaults")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    return cfg.get("preprocessing", {})


def main():
    # Display startup banner with log file location
    print("=" * 80)
    print("HAR MLOps Production Pipeline")
    print("=" * 80)
    print(f"  Log file: {CURRENT_LOG_FILE}")
    device = _detect_gpu()
    print("=" * 80)
    print()
    logger.info("Pipeline starting... (device=%s)", device)

    args = parse_args()

    # ── Load config from YAML ─────────────────────────────────────────
    yaml_preproc = load_preprocessing_config(args.config)

    # Resolve preprocessing toggles: CLI flags override YAML config
    enable_unit_conversion = yaml_preproc.get("enable_unit_conversion", True)
    enable_gravity_removal = yaml_preproc.get("enable_gravity_removal", False)
    enable_calibration = yaml_preproc.get("enable_calibration", False)
    enable_normalization = yaml_preproc.get("enable_normalization", True)
    normalization_variant = yaml_preproc.get("normalization_variant", "zscore")

    # CLI overrides
    if args.no_unit_conversion:
        enable_unit_conversion = False
    if args.gravity_removal:
        enable_gravity_removal = True
    if args.calibrate:
        enable_calibration = True
    if args.no_normalization:
        enable_normalization = False
    if args.normalization_variant:
        normalization_variant = args.normalization_variant

    # Show what's active using logger
    logger.info("Preprocessing configuration (from %s):", args.config)
    logger.info(
        "  Unit Conversion (milliG\u2192m/s\u00b2): %s", "ON" if enable_unit_conversion else "OFF"
    )
    logger.info("  Gravity Removal:               %s", "ON" if enable_gravity_removal else "OFF")
    logger.info("  Domain Calibration:            %s", "ON" if enable_calibration else "OFF")
    logger.info(
        "  Normalization:                 %s  (variant=%s)",
        "ON" if enable_normalization else "OFF",
        normalization_variant,
    )

    # ── Build configs ─────────────────────────────────────────────────
    pipeline_cfg = PipelineConfig()

    # Load runtime threshold overrides from YAML (or HAR_PIPELINE_OVERRIDES env var)
    _overrides = load_yaml_overrides()

    ingestion_cfg = DataIngestionConfig(
        input_csv=Path(args.input_csv) if args.input_csv else None,
        accel_file=Path(args.accel_file) if args.accel_file else None,
        gyro_file=Path(args.gyro_file) if args.gyro_file else None,
    )

    transformation_cfg = DataTransformationConfig(
        enable_unit_conversion=enable_unit_conversion,
        enable_gravity_removal=enable_gravity_removal,
        enable_calibration=enable_calibration,
        enable_normalization=enable_normalization,
        normalization_variant=normalization_variant,
    )

    inference_cfg = ModelInferenceConfig(
        model_path=Path(args.model) if args.model else None,
    )

    retraining_cfg = ModelRetrainingConfig(
        enable_adaptation=(args.adapt != "none"),
        adaptation_method=args.adapt,
        epochs=args.epochs,
        skip_cv=args.skip_cv,
        labels_path=Path(args.labels) if args.labels else None,
    )

    from src.entity.config_entity import ModelRegistrationConfig

    registration_cfg = ModelRegistrationConfig(
        auto_deploy=args.auto_deploy,
    )

    # Advanced configs
    from src.entity.config_entity import (
        CalibrationUncertaintyConfig,
        CurriculumPseudoLabelingConfig,
        SensorPlacementConfig,
        WassersteinDriftConfig,
    )

    calibration_cfg = CalibrationUncertaintyConfig(
        mc_forward_passes=args.mc_dropout_passes,
    )
    wasserstein_cfg = WassersteinDriftConfig()
    curriculum_cfg = CurriculumPseudoLabelingConfig(
        n_iterations=args.curriculum_iterations,
        ewc_lambda=args.ewc_lambda,
    )
    sensor_cfg = SensorPlacementConfig()

    # ── Apply YAML overrides to all threshold-bearing configs ─────────
    monitoring_cfg = load_monitoring_config()
    trigger_cfg = load_trigger_config()
    if _overrides:
        apply_overrides(registration_cfg, _overrides.get("registration", {}))
        apply_overrides(calibration_cfg, _overrides.get("calibration", {}))
        apply_overrides(curriculum_cfg, _overrides.get("curriculum", {}))
        logger.info("YAML overrides applied from config/pipeline_overrides.yaml")

    # ── Print planned stages ──────────────────────────────────────────
    _print_planned_stages(args)

    # ── Build and run pipeline ────────────────────────────────────────
    pipeline = ProductionPipeline(
        pipeline_config=pipeline_cfg,
        ingestion_config=ingestion_cfg,
        transformation_config=transformation_cfg,
        inference_config=inference_cfg,
        retraining_config=retraining_cfg,
        registration_config=registration_cfg,
        monitoring_config=monitoring_cfg,
        trigger_config=trigger_cfg,
        calibration_config=calibration_cfg,
        wasserstein_config=wasserstein_cfg,
        curriculum_config=curriculum_cfg,
        sensor_placement_config=sensor_cfg,
    )

    result = pipeline.run(
        stages=args.stages,
        skip_ingestion=args.skip_ingestion,
        skip_validation=args.skip_validation,
        continue_on_failure=args.continue_on_failure,
        enable_retrain=args.retrain,
        enable_advanced=args.advanced,
        update_baseline=args.update_baseline,
    )

    # ── Print Summary ─────────────────────────────────────────────────
    _print_pipeline_summary(result)

    # ── Exit code ─────────────────────────────────────────────────────
    if result.overall_status == "SUCCESS":
        sys.exit(0)
    else:
        sys.exit(1)


def _print_planned_stages(args):
    """Print a clear stage manifest so the user (and thesis logs) know exactly
    which stages are scheduled to run before execution begins."""
    P = _safe_print

    # Determine which stage groups are active
    core_stages = [
        ("1", "ingestion", "Raw Garmin CSV/XLSX → sensor_fused_50Hz.csv"),
        ("2", "validation", "Schema + value-range checks on fused data"),
        ("3", "transformation", "CSV → normalised, windowed production_X.npy"),
        ("4", "inference", ".npy + pretrained model → predictions CSV/NPY"),
        ("5", "evaluation", "Confidence / distribution / ECE analysis"),
        ("6", "monitoring", "3-layer (confidence, temporal, z-score drift)"),
        ("7", "trigger", "Automated retraining decision (PASS/WARN/ALERT)"),
    ]
    retrain_stages = [
        ("8", "retraining", f"Domain adaptation: {args.adapt} → retrained .keras"),
        ("9", "registration", "Version, validate proxy metrics, deploy or rollback"),
        ("10", "baseline_update", "Rebuild drift + calibration baselines from new data"),
    ]
    advanced_stages = [
        ("11", "calibration", "Temperature scaling + MC Dropout uncertainty"),
        ("12", "wasserstein_drift", "Wasserstein distance + change-point detection"),
        ("13", "curriculum_pseudo_labeling", "Progressive self-training with EWC"),
        ("14", "sensor_placement", "Hand detection + axis-mirroring augmentation"),
    ]

    # Filter to explicitly requested stages when --stages is used
    explicit = set(args.stages) if args.stages else None

    def _will_run(name: str) -> bool:
        if explicit:
            return name in explicit
        return True  # default: all applicable groups run

    P("\n" + "=" * 70)
    P("  PLANNED PIPELINE STAGES")
    P("=" * 70)

    P("\n  ── Training Pipeline (stages 1-7, always included) ──────────")
    skipped = {"ingestion"} if args.skip_ingestion else set()
    skipped |= {"validation"} if args.skip_validation else set()
    for num, name, desc in core_stages:
        if explicit and name not in explicit:
            status = "  skip  "
        elif name in skipped:
            status = " --skip "
        else:
            status = "  queue "
        P(f"    [{status}] Stage {num:>2}: {name:<30}  {desc}")

    if args.retrain or (explicit and any(n in explicit for _, n, _ in retrain_stages)):
        P("\n  ── Retraining Cycle (stages 8-10, --retrain) ────────────────")
        for num, name, desc in retrain_stages:
            if explicit and name not in explicit:
                status = "  skip  "
            else:
                status = "  queue "
            P(f"    [{status}] Stage {num:>2}: {name:<30}  {desc}")

    if args.advanced or (explicit and any(n in explicit for _, n, _ in advanced_stages)):
        P("\n  ── Advanced Analytics (stages 11-14, --advanced) ────────────")
        for num, name, desc in advanced_stages:
            if explicit and name not in explicit:
                status = "  skip  "
            else:
                status = "  queue "
            P(f"    [{status}] Stage {num:>2}: {name:<30}  {desc}")

    P("\n  ── Runtime components (not pipeline stages) ─────────────────")
    P("    [ always ]        inference/     FastAPI service  (docker/ or src/api/)")
    P("    [ always ]        monitoring/    Post-prediction monitoring layer")
    P("    [ on demand ]     deployment/    Model deploy / rollback manager")
    P("    [ retraining ]    domain_adaptation/  AdaBN / TENT / pseudo-label")

    P("\n" + "=" * 70)
    P("  Starting execution …")
    P("=" * 70 + "\n")


def _safe_print(text: str):
    """Print text, replacing characters that can't be encoded on Windows cp1252."""
    import sys as _sys

    try:
        print(text)
    except UnicodeEncodeError:
        print(
            text.encode(_sys.stdout.encoding or "utf-8", errors="replace").decode(
                _sys.stdout.encoding or "utf-8", errors="replace"
            )
        )


def _print_pipeline_summary(result):
    """Print a clean summary of key pipeline metrics."""
    P = _safe_print  # shorthand
    P("\n" + "=" * 70)
    P("  PIPELINE SUMMARY")
    P("=" * 70)

    # Overall status
    status_icon = (
        "[OK]"
        if result.overall_status == "SUCCESS"
        else "[!!]" if result.overall_status == "PARTIAL" else "[FAIL]"
    )
    P(f"\n{status_icon} Overall Status: {result.overall_status}")
    P(f"   Completed: {len(result.stages_completed)} stages")
    P(f"   Failed: {len(result.stages_failed)} stages")

    # Key metrics
    P("\n  KEY METRICS")
    P("-" * 70)

    # Inference metrics
    if result.inference:
        P(f"\n  Inference:")
        P(f"    - Predictions: {result.inference.n_predictions:,}")
        P(f"    - Duration: {result.inference.inference_time_seconds:.2f}s")
        if result.inference.confidence_stats:
            conf = result.inference.confidence_stats
            P(f"    - Mean Confidence: {conf.get('mean', 0)*100:.1f}%")
            P(
                f"    - Uncertain: {conf.get('n_uncertain', 0)} ({conf.get('n_uncertain', 0)/max(result.inference.n_predictions, 1)*100:.1f}%)"
            )

    # Monitoring metrics
    if result.monitoring:
        P(f"\n  Monitoring:")
        P(f"    - Overall: {result.monitoring.overall_status}")

        if result.monitoring.layer3_drift:
            drift = result.monitoring.layer3_drift
            drift_score = drift.get("max_drift", 0)
            P(f"    - Drift Score: {drift_score:.4f}")

            if drift_score > 1.50:
                P(f"      [!] HIGH DRIFT ({drift_score:.3f}) - Retraining recommended")
            elif drift_score > 0.75:
                P(f"      [~] Moderate drift ({drift_score:.3f}) - Monitor closely")
            else:
                P(f"      [ok] Drift within acceptable range")

    # Trigger decision
    if result.trigger:
        P(f"\n  Retraining Decision:")
        retrain_icon = "[retrain]" if result.trigger.should_retrain else "[ok]"
        P(f"    {retrain_icon} Should Retrain: {'YES' if result.trigger.should_retrain else 'NO'}")
        P(f"    - Alert Level: {result.trigger.alert_level}")
        if result.trigger.reasons:
            P(f"    - Reasons:")
            for reason in result.trigger.reasons[:3]:
                P(f"      - {reason}")

    # Retraining metrics (if retrain ran)
    if result.retraining:
        P(f"\n  Retraining:")
        for k, v in result.retraining.metrics.items():
            if isinstance(v, float):
                P(f"    - {k}: {v:.4f}")
            else:
                P(f"    - {k}: {v}")
        P(f"    - Source samples: {result.retraining.n_source_samples}")
        P(f"    - Target samples: {result.retraining.n_target_samples}")

    # Activity distribution
    if result.inference and result.inference.activity_distribution:
        P(f"\n  Top 3 Activities Detected:")
        sorted_activities = sorted(
            result.inference.activity_distribution.items(), key=lambda x: x[1], reverse=True
        )[:3]
        for activity, count in sorted_activities:
            pct = count / max(result.inference.n_predictions, 1) * 100
            P(f"    - {activity}: {count} ({pct:.1f}%)")

    P("\n" + "=" * 70)
    P(f"  Artifacts saved to: artifacts/{result.run_id}")
    P(f"  Log file: {CURRENT_LOG_FILE}")
    P("=" * 70 + "\n")


if __name__ == "__main__":
    main()
