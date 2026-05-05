#!/usr/bin/env python3
"""
HAR MLOps production pipeline entrypoint.

This file intentionally stays thin: it parses CLI arguments, builds config
dataclasses, calls `ProductionPipeline`, and prints the final run summary.
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.logger import logging
from src.pipeline.pipeline_config_factory import (
    build_runtime_configs,
    load_preprocessing_config,
    load_validation_config,
)
from src.pipeline.pipeline_console_reporter import (
    print_pipeline_summary,
    print_planned_stages,
    print_startup_banner,
)
from src.pipeline.production_pipeline import ProductionPipeline

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description="HAR MLOps Production Pipeline - run all stages with one command",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_pipeline.py
  python run_pipeline.py --skip-ingestion
  python run_pipeline.py --stages inference evaluation monitoring trigger
  python run_pipeline.py --input-csv data/raw/my_recording.csv
  python run_pipeline.py --retrain --adapt adabn_tent
  python run_pipeline.py --advanced
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
        ],
        default=None,
        help="Run only these stages (default: 1-7; use --retrain for 8-10, --advanced for 11)",
    )
    parser.add_argument(
        "--skip-ingestion",
        action="store_true",
        help="Skip data ingestion - use newest existing fused_<dataset>_50Hz.csv",
    )
    parser.add_argument("--skip-validation", action="store_true", help="Skip data validation")
    parser.add_argument(
        "--continue-on-failure",
        action="store_true",
        help="Log errors and continue to next stage instead of aborting",
    )

    parser.add_argument(
        "--input-csv",
        type=str,
        default=None,
        help="Path to input file - CSV or Excel (.xlsx/.xls).",
    )
    parser.add_argument(
        "--accel-file",
        type=str,
        default=None,
        help="Path to raw accelerometer CSV/XLSX for one specific session.",
    )
    parser.add_argument(
        "--gyro-file",
        type=str,
        default=None,
        help="Path to raw gyroscope CSV/XLSX for one specific session.",
    )
    parser.add_argument("--model", type=str, default=None, help="Path to .keras model for inference")
    parser.add_argument(
        "--config",
        type=str,
        default="config/pipeline_config.yaml",
        help=(
            "Path to YAML config for preprocessing and Stage 2 validation settings. "
            "Monitoring/trigger/registration thresholds are read from "
            "config/pipeline_overrides.yaml or $HAR_PIPELINE_OVERRIDES."
        ),
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
        help="Disable unit conversion milliG->m/s^2 (overrides config file)",
    )
    parser.add_argument(
        "--enable-normalization",
        action="store_true",
        help="Enable saved-scaler normalization for A/B testing.",
    )
    parser.add_argument(
        "--no-normalization",
        action="store_true",
        help="Disable saved-scaler normalization (overrides config file)",
    )
    parser.add_argument(
        "--normalization-variant",
        type=str,
        default=None,
        choices=["zscore", "robust", "none"],
        help="Normalization variant to use: zscore | robust | none",
    )
    parser.add_argument(
        "--calibrate",
        action="store_true",
        default=None,
        help="Enable domain calibration (overrides config file)",
    )

    parser.add_argument(
        "--retrain",
        action="store_true",
        help="Include stages 8-10 (retraining -> registration -> baseline)",
    )
    parser.add_argument(
        "--adapt",
        type=str,
        choices=["adabn", "tent", "adabn_tent", "pseudo_label", "none"],
        default="none",
        help="Domain adaptation method for retraining (default: none).",
    )
    parser.add_argument(
        "--labels",
        type=str,
        default=None,
        help="Path to ground-truth labels for supervised retraining/evaluation",
    )
    parser.add_argument("--epochs", type=int, default=100, help="Training epochs for retraining")
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
            "Promote rebuilt baseline to the shared models/ path. "
            "Default is safe: save baseline only as an MLflow artifact."
        ),
    )

    parser.add_argument(
        "--advanced",
        action="store_true",
        help="Include stage 11 (calibration: temperature scaling, MC Dropout)",
    )
    parser.add_argument(
        "--mc-dropout-passes",
        type=int,
        default=30,
        help="Number of MC Dropout forward passes",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    device = print_startup_banner()
    logger.info("Pipeline starting... (device=%s)", device)

    configs = build_runtime_configs(args)
    print_planned_stages(args)

    pipeline = ProductionPipeline(
        pipeline_config=configs.pipeline,
        ingestion_config=configs.ingestion,
        validation_config=configs.validation,
        transformation_config=configs.transformation,
        inference_config=configs.inference,
        evaluation_config=configs.evaluation,
        retraining_config=configs.retraining,
        registration_config=configs.registration,
        monitoring_config=configs.monitoring,
        trigger_config=configs.trigger,
        calibration_config=configs.calibration,
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

    print_pipeline_summary(result)
    sys.exit(0 if result.overall_status == "SUCCESS" else 1)


if __name__ == "__main__":
    main()
