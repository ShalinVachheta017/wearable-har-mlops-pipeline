#!/usr/bin/env python3
"""
scripts/train.py — Standalone training / retraining entry point
================================================================

DEPRECATION NOTICE:
This wrapper is retained for backward compatibility, but the canonical
entrypoint is run_pipeline.py. Prefer:
    python run_pipeline.py --retrain

Usage:
    python scripts/train.py
"""

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("train")


def main():
    logger.error("DEPRECATED wrapper blocked. Use: python run_pipeline.py --retrain")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
