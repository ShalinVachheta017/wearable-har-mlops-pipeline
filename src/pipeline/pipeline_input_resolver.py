"""Input, label, and resume-artifact resolution for ProductionPipeline."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.entity.artifact_entity import DataIngestionArtifact, DataTransformationArtifact
from src.logger import logging
from src.utils.label_detection import LABEL_COLUMN_CANDIDATES, NON_GROUND_TRUTH_COLUMNS

logger = logging.getLogger(__name__)


class PipelineInputResolver:
    """Resolve pipeline inputs when earlier stages are skipped."""

    def __init__(self, pipeline_config, ingestion_config, retraining_config):
        self.pipeline_config = pipeline_config
        self.ingestion_config = ingestion_config
        self.retraining_config = retraining_config

    def detect_dataset_labels(self):
        """
        Method Name :   detect_dataset_labels
        Description :   Detect labels from configured labels file or CSV headers.

        Output      :   Returns has_labels, label_column, and label_source.
        On Failure  :   Logs the error and raises the exception.
        """
        if self.retraining_config.labels_path:
            labels_path = Path(self.retraining_config.labels_path)
            if labels_path.exists():
                return True, None, f"labels file: {labels_path}"
            logger.warning("Configured labels path does not exist: %s", labels_path)

        csv_candidates = []
        if self.ingestion_config.input_csv:
            csv_candidates.append(Path(self.ingestion_config.input_csv))
        csv_candidates.append(self.resolve_existing_fused_csv())

        for candidate in csv_candidates:
            label_col = self.detect_label_column_from_csv(candidate)
            if label_col:
                return True, label_col, f"CSV column '{label_col}' in {candidate}"
        return False, None, None

    def resolve_existing_fused_csv(self) -> Path:
        """
        Method Name :   resolve_existing_fused_csv
        Description :   Resolve the best existing fused CSV for resume/skip-stage flows.

        Output      :   Returns a CSV path.
        On Failure  :   Logs the error and raises the exception.
        """
        candidates = sorted(
            self.pipeline_config.data_processed_dir.glob("fused_*_*.csv"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if candidates:
            return candidates[0]
        if self.ingestion_config.input_csv:
            return Path(self.ingestion_config.input_csv)
        return self.pipeline_config.data_processed_dir / "fused_dataset_50Hz.csv"

    def make_fallback_ingestion_artifact(self) -> DataIngestionArtifact:
        """
        Method Name :   make_fallback_ingestion_artifact
        Description :   Build an ingestion artifact for an already-existing fused CSV.

        Output      :   Returns DataIngestionArtifact.
        On Failure  :   Logs the error and raises the exception.
        """
        csv_path = self.resolve_existing_fused_csv()
        label_column = self.detect_label_column_from_csv(csv_path)
        return DataIngestionArtifact(
            fused_csv_path=Path(csv_path),
            n_rows=0,
            n_columns=0,
            sampling_hz=50,
            ingestion_timestamp=datetime.now().isoformat(),
            source_type="fallback",
            source_path=Path(csv_path),
            has_labels=bool(label_column),
            label_column=label_column,
        )

    def make_fallback_transformation_artifact(self) -> DataTransformationArtifact:
        """
        Method Name :   make_fallback_transformation_artifact
        Description :   Build a transformation artifact for existing prepared .npy data.

        Output      :   Returns DataTransformationArtifact.
        On Failure  :   Logs the error and raises the exception.
        """
        prepared = self.pipeline_config.data_prepared_dir
        report = prepared / "transformation_report.json"
        return DataTransformationArtifact(
            production_X_path=prepared / "production_X.npy",
            metadata_path=prepared / "production_metadata.json",
            n_windows=0,
            window_size=200,
            unit_conversion_applied=False,
            preprocessing_timestamp=datetime.now().isoformat(),
            transformation_report_path=report if report.exists() else None,
            channel_order=["Ax", "Ay", "Az", "Gx", "Gy", "Gz"],
            has_labels=False,
            normalization_applied=False,
            model_input_space="fallback_existing_X",
            production_y_path=None,
        )

    @staticmethod
    def label_column_from_headers(headers: List[str]) -> Optional[str]:
        """
        Method Name :   label_column_from_headers
        Description :   Find a ground-truth label column from CSV headers.

        Output      :   Returns the matching column name or None.
        On Failure  :   Logs the error and raises the exception.
        """
        normalized = {str(col).strip().lower(): str(col) for col in headers}
        for candidate in LABEL_COLUMN_CANDIDATES:
            if candidate in normalized and candidate not in NON_GROUND_TRUTH_COLUMNS:
                return normalized[candidate]
        return None

    def detect_label_column_from_csv(self, csv_path: Optional[Path]) -> Optional[str]:
        """
        Method Name :   detect_label_column_from_csv
        Description :   Read only the CSV header and detect a label column.

        Output      :   Returns the label column name or None.
        On Failure  :   Logs the error and raises the exception.
        """
        if not csv_path:
            return None
        csv_path = Path(csv_path)
        if not csv_path.exists() or not csv_path.is_file():
            return None
        try:
            with csv_path.open("r", encoding="utf-8", newline="") as f:
                headers = next(csv.reader(f), [])
        except UnicodeDecodeError:
            try:
                with csv_path.open("r", encoding="latin-1", newline="") as f:
                    headers = next(csv.reader(f), [])
            except Exception as exc:
                logger.debug("Could not inspect CSV headers for %s: %s", csv_path, exc)
                return None
        except Exception as exc:
            logger.debug("Could not inspect CSV headers for %s: %s", csv_path, exc)
            return None
        return self.label_column_from_headers(headers)
