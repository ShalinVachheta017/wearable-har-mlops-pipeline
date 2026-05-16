"""Stage 9 & 10 — Model Registration, Rollback, and Baseline Update Tests"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from src.components.model_registration import ModelRegistration
from src.entity.artifact_entity import (
    BaselineUpdateArtifact,
    ModelRegistrationArtifact,
    ModelRetrainingArtifact,
)
from src.entity.config_entity import (
    BaselineUpdateConfig,
    ModelRegistrationConfig,
    PipelineConfig,
)


# ── Model Registration Gate ───────────────────────────────────────────────────

_CURRENT_ACC = 0.90


def _fake_registry_patch(current_acc: float = _CURRENT_ACC):
    return (
        patch("src.model_rollback.ModelRegistry.get_current_version", return_value="v1.0.0"),
        patch("src.model_rollback.ModelRegistry.list_versions",
              return_value=[{"version": "v1.0.0", "metrics": {"val_accuracy": current_acc}}]),
        patch("src.model_rollback.ModelRegistry.register_model",
              return_value=MagicMock(version="v1.0.1")),
        patch("src.model_rollback.ModelRegistry.deploy_model", return_value=False),
    )


def _make_comp(tmp_path, new_accuracy, degradation_tolerance=0.005,
               block_if_no_metrics=False, metrics_override=None):
    fake_model = tmp_path / "model.keras"
    fake_model.write_text("fake")
    metrics = {"val_accuracy": new_accuracy} if new_accuracy is not None else {}
    if metrics_override is not None:
        metrics = metrics_override
    retrain = ModelRetrainingArtifact(
        retrained_model_path=fake_model,
        training_report={},
        metrics=metrics,
        n_source_samples=100,
        retraining_timestamp="2026-02-26T00:00:00",
    )
    cfg = ModelRegistrationConfig(
        proxy_validation=True,
        auto_deploy=False,
        degradation_tolerance=degradation_tolerance,
        block_if_no_metrics=block_if_no_metrics,
    )
    return ModelRegistration(PipelineConfig(project_root=tmp_path), cfg, retrain)


def _run(comp):
    patches = _fake_registry_patch()
    with patches[0], patches[1], patches[2], patches[3]:
        return comp.initiate_model_registration()


def test_improved_model_is_accepted(tmp_path):
    assert _run(_make_comp(tmp_path, new_accuracy=0.92)).is_better_than_current is True


def test_large_regression_outside_tolerance_is_blocked(tmp_path):
    assert _run(_make_comp(tmp_path, new_accuracy=0.88, degradation_tolerance=0.005)).is_better_than_current is False


def test_zero_tolerance_blocks_any_drop(tmp_path):
    assert _run(_make_comp(tmp_path, new_accuracy=0.899, degradation_tolerance=0.0)).is_better_than_current is False


def test_tta_model_with_block_if_no_metrics_is_blocked(tmp_path):
    result = _run(_make_comp(tmp_path, new_accuracy=None, block_if_no_metrics=True,
                             metrics_override={"after_mean_confidence": 0.85}))
    assert result.is_better_than_current is False


# ── Baseline Update (stage 10) ────────────────────────────────────────────────

@pytest.fixture
def pipeline_config_bu(tmp_path):
    cfg = PipelineConfig()
    cfg.project_root = tmp_path
    cfg.models_dir = tmp_path / "models"
    cfg.data_raw_dir = tmp_path / "data" / "raw"
    cfg.logs_dir = tmp_path / "logs"
    cfg.models_dir.mkdir(parents=True, exist_ok=True)
    cfg.data_raw_dir.mkdir(parents=True, exist_ok=True)
    return cfg


def test_baseline_update_defaults():
    cfg = BaselineUpdateConfig()
    assert cfg.training_data_path is None
    assert cfg.rebuild_embeddings is False


def test_baseline_update_initiate_with_mock_builder(pipeline_config_bu, tmp_path):
    csv_path = pipeline_config_bu.data_raw_dir / "all_users_data_labeled.csv"
    pd.DataFrame({
        "timestamp": range(100),
        "Ax_w": np.random.randn(100), "Ay_w": np.random.randn(100), "Az_w": np.random.randn(100),
        "Gx_w": np.random.randn(100), "Gy_w": np.random.randn(100), "Gz_w": np.random.randn(100),
        "activity": ["sitting"] * 50 + ["standing"] * 50,
        "User": [1] * 100,
    }).to_csv(csv_path, index=False)

    mock_builder = MagicMock()
    mock_builder.build_from_csv.return_value = {"n_channels": 6, "n_samples": 100, "per_class": {}}

    config = BaselineUpdateConfig(
        output_baseline_path=tmp_path / "baseline.json",
        output_normalized_path=tmp_path / "normalized.json",
    )

    with patch("src.monitoring.baseline_builder.BaselineBuilder", return_value=mock_builder):
        from src.components.baseline_update import BaselineUpdate
        artifact = BaselineUpdate(pipeline_config_bu, config).initiate_baseline_update()

    assert isinstance(artifact, BaselineUpdateArtifact)
    assert artifact.n_channels == 6
    assert artifact.update_timestamp != ""
