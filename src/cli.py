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
    import importlib.util, sys

    spec = importlib.util.spec_from_file_location(
        "run_pipeline", PROJECT_ROOT / "run_pipeline.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_pipeline"] = mod
    spec.loader.exec_module(mod)
    mod.main()


if __name__ == "__main__":
    main()
