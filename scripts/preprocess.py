#!/usr/bin/env python3
"""
scripts/preprocess.py — Standalone preprocessing entry point
=============================================================

Runs the data pipeline stages (ingestion → validation → transformation)
without the full production pipeline orchestrator.

DEPRECATION NOTICE:
This wrapper is retained for backward compatibility, but the canonical
entrypoint is run_pipeline.py. Prefer:
    python run_pipeline.py --stages ingestion validation transformation

Usage:
    python scripts/preprocess.py
    python scripts/preprocess.py --input data/raw/my_recording.csv
    python scripts/preprocess.py --skip-ingestion
    python scripts/preprocess.py --gravity-removal --calibrate
"""

import argparse
import logging
import sys
from pathlib import Path

# Ensure project root on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.entity.config_entity import (
    PipelineConfig,
    DataIngestionConfig,
    DataTransformationConfig,
)
from src.entity.artifact_entity import DataIngestionArtifact

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("preprocess")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run data preprocessing stages (ingestion → validation → transformation)",
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to input CSV/Excel file (default: auto-detect in data/raw/)",
    )
    parser.add_argument(
        "--skip-ingestion",
        action="store_true",
        help="Skip ingestion — use existing sensor_fused_50Hz.csv",
    )
    parser.add_argument(
        "--gravity-removal",
        action="store_true",
        help="Enable gravity removal during preprocessing",
    )
    parser.add_argument(
        "--calibrate",
        action="store_true",
        help="Enable domain calibration during preprocessing",
    )
    return parser.parse_args()


def main():
    logger.warning(
        "DEPRECATED wrapper: use 'python run_pipeline.py --stages ingestion validation transformation' "
        "for canonical preprocessing orchestration."
    )
    args = parse_args()
    pipeline_cfg = PipelineConfig()

    # ── Stage 1: Data Ingestion ───────────────────────────────────────
    if not args.skip_ingestion:
        logger.info("=" * 60)
        logger.info("STAGE 1: Data Ingestion")
        logger.info("=" * 60)
        from src.components.data_ingestion import DataIngestion

        ingestion_cfg = DataIngestionConfig(
            input_csv=Path(args.input) if args.input else None,
        )
        ingestion = DataIngestion(config=ingestion_cfg)
        ingestion_artifact = ingestion.initiate_data_ingestion()
        logger.info("Ingestion complete: %s", ingestion_artifact)
    else:
        logger.info("Skipping ingestion — using existing CSV")
        ingestion_artifact = None

    # ── Stage 2: Data Validation ──────────────────────────────────────
    logger.info("=" * 60)
    logger.info("STAGE 2: Data Validation")
    logger.info("=" * 60)
    from src.components.data_validation import DataValidation
    from src.entity.config_entity import DataValidationConfig

    validation_cfg = DataValidationConfig()
    validation = DataValidation(config=validation_cfg, prev_artifact=ingestion_artifact)
    validation_artifact = validation.initiate_data_validation()
    logger.info("Validation complete: %s", validation_artifact)

    # ── Stage 3: Data Transformation ──────────────────────────────────
    logger.info("=" * 60)
    logger.info("STAGE 3: Data Transformation")
    logger.info("=" * 60)
    from src.components.data_transformation import DataTransformation

    transformation_cfg = DataTransformationConfig(
        enable_gravity_removal=args.gravity_removal,
        enable_calibration=args.calibrate,
    )
    transformation = DataTransformation(
        config=transformation_cfg, prev_artifact=validation_artifact,
    )
    transformation_artifact = transformation.initiate_data_transformation()
    logger.info("Transformation complete: %s", transformation_artifact)

    logger.info("=" * 60)
    logger.info("PREPROCESSING DONE — data ready for inference")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
