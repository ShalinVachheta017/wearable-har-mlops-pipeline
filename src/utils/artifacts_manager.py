"""
Artifacts Manager for HAR MLOps Production Pipeline

Manages creation and organization of experiment artifacts.
Each run creates a timestamped artifacts folder containing all stage outputs.

Structure:
artifacts/
  20260214_153045/
    data_ingestion/
    data_transformation/
    validation/
    inference/
    evaluation/
    run_info.json
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from src.utils.common import get_timestamp

logger = logging.getLogger(__name__)


def _serialize_for_json(obj: Any) -> Any:
    """Convert non-JSON-native objects to serializable representations."""
    if isinstance(obj, Path):
        return str(obj)
    if hasattr(obj, "item"):  # numpy scalar types
        return obj.item()
    if hasattr(obj, "__dict__"):
        return str(obj)
    return str(obj)


class ArtifactsManager:
    """Manages experiment artifacts for each pipeline run."""

    def __init__(
        self,
        base_dir: Union[str, Path] = "artifacts",
        run_id: Optional[str] = None,
        start_time: Optional[str] = None,
    ):
        """
        Initialize artifacts manager.

        Args:
            base_dir: Base directory for all artifacts
            run_id: Optional externally generated run id for strict run-folder alignment
            start_time: Optional externally generated start timestamp (ISO)
        """
        self.base_dir = Path(base_dir)
        self.run_id = run_id or get_timestamp()
        self.timestamp = self.run_id  # backward-compatible alias
        self.run_dir = self.base_dir / self.run_id

        # Stage directories
        self.dirs: Dict[str, Path] = {
            "data_ingestion": self.run_dir / "data_ingestion",
            "data_transformation": self.run_dir / "data_transformation",
            "validation": self.run_dir / "validation",
            "inference": self.run_dir / "inference",
            "evaluation": self.run_dir / "evaluation",
            "monitoring": self.run_dir / "monitoring",
            "trigger": self.run_dir / "trigger",
        }

        self.metadata: Dict[str, Any] = {
            "run_id": self.run_id,
            "start_time": start_time or datetime.now().isoformat(),
            "stages": {},
        }

    def initialize(self) -> Path:
        """Create all artifact directories for this run."""
        logger.info(f"Initializing artifacts directory: {self.run_dir}")

        for stage_name, stage_dir in self.dirs.items():
            stage_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created {stage_name} directory: {stage_dir}")

        return self.run_dir

    def get_stage_dir(self, stage_name: str) -> Path:
        """Get directory for a specific stage."""
        if stage_name not in self.dirs:
            raise ValueError(f"Unknown stage: {stage_name}. Available: {list(self.dirs.keys())}")
        return self.dirs[stage_name]

    def save_file(
        self, source_path: Path, stage_name: str, dest_name: Optional[str] = None
    ) -> Optional[Path]:
        """
        Copy a file to the appropriate stage directory.

        Args:
            source_path: Path to source file
            stage_name: Name of the stage (data_ingestion, etc.)
            dest_name: Optional custom destination filename
        """
        if not Path(source_path).exists():
            logger.warning(f"Source file not found: {source_path}")
            return None

        stage_dir = self.get_stage_dir(stage_name)
        dest_name = dest_name or Path(source_path).name
        dest_path = stage_dir / dest_name

        shutil.copy2(source_path, dest_path)
        logger.debug(f"Saved {source_path.name} to {stage_name}/")
        return dest_path

    def save_json(self, data: Dict[str, Any], stage_name: str, filename: str) -> Path:
        """
        Save JSON data to stage directory.

        Args:
            data: Dictionary to save as JSON
            stage_name: Name of the stage
            filename: Output filename
        """
        stage_dir = self.get_stage_dir(stage_name)
        filepath = stage_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=_serialize_for_json)

        logger.debug(f"Saved JSON to {stage_name}/{filename}")
        return filepath

    def log_stage_completion(
        self, stage_name: str, status: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log completion of a pipeline stage.

        Args:
            stage_name: Name of the stage
            status: Status (SUCCESS, FAILED, PARTIAL)
            details: Additional details about the stage
        """
        self.metadata["stages"][stage_name] = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
        }

    def finalize(self) -> Path:
        """Save final run metadata."""
        self.metadata["end_time"] = datetime.now().isoformat()

        metadata_path = self.run_dir / "run_info.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2, default=_serialize_for_json)

        logger.info(f"Artifacts saved to: {self.run_dir}")
        logger.info(f"Run metadata saved to: {metadata_path}")
        return metadata_path

    def get_latest_run_dir(self) -> Optional[Path]:
        """Get the most recent run directory."""
        if not self.base_dir.exists():
            return None

        run_dirs = sorted([d for d in self.base_dir.iterdir() if d.is_dir()])
        return run_dirs[-1] if run_dirs else None
