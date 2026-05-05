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

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("preprocess")


def main():
    logger.error(
        "DEPRECATED wrapper blocked. Use: "
        "python run_pipeline.py --stages ingestion validation transformation"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
