"""
CLI entrypoint for the installed har-pipeline command.
Delegates to run_pipeline.main() — single entry point for the full pipeline.

Usage after `pip install -e .`:
    har-pipeline
    har-pipeline --stages inference evaluation monitoring trigger
    har-pipeline --retrain --labels path/to/labels.csv
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path when invoked as an installed script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main():
    import run_pipeline

    run_pipeline.main()


if __name__ == "__main__":
    main()
