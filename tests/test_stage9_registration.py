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
        adaptation_method="standard",
        metrics=metrics,
        n_target_samples=100,
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


def test_equal_accuracy_is_accepted(tmp_path):
    assert _run(_make_comp(tmp_path, new_accuracy=0.90)).is_better_than_current is True


def test_small_regression_within_tolerance_is_accepted(tmp_path):
    assert _run(_make_comp(tmp_path, new_accuracy=0.897, degradation_tolerance=0.005)).is_better_than_current is True


def test_large_regression_outside_tolerance_is_blocked(tmp_path):
    assert _run(_make_comp(tmp_path, new_accuracy=0.88, degradation_tolerance=0.005)).is_better_than_current is False


def test_zero_tolerance_blocks_any_drop(tmp_path):
    assert _run(_make_comp(tmp_path, new_accuracy=0.899, degradation_tolerance=0.0)).is_better_than_current is False


def test_tta_model_without_metrics_defaults_to_true(tmp_path):
    result = _run(_make_comp(tmp_path, new_accuracy=None, block_if_no_metrics=False,
                             metrics_override={"after_mean_confidence": 0.85}))
    assert result.is_better_than_current is True
    assert result.is_deployed is False


def test_tta_model_with_block_if_no_metrics_is_blocked(tmp_path):
    result = _run(_make_comp(tmp_path, new_accuracy=None, block_if_no_metrics=True,
                             metrics_override={"after_mean_confidence": 0.85}))
    assert result.is_better_than_current is False


# ── Model Rollback / Registry ─────────────────────────────────────────────────

class TestModelVersion:
    def test_creation(self):
        from model_rollback import ModelVersion
        version = ModelVersion(
            version='1.0.0', path='/models/v1/model.keras',
            created_at=datetime.now().isoformat(), deployed_at=None,
            metrics={'f1': 0.89, 'accuracy': 0.91}, config_hash='abc123',
            data_version=None, status='archived',
        )
        assert version.version == '1.0.0'
        assert version.metrics['f1'] == 0.89

    def test_to_dict(self):
        from model_rollback import ModelVersion
        version = ModelVersion(
            version='1.0.0', path='/models/v1/model.keras',
            created_at='2026-01-30T10:00:00', deployed_at=None,
            metrics={'f1': 0.89}, config_hash='abc123', data_version=None, status='archived',
        )
        d = version.to_dict()
        assert isinstance(d, dict)
        assert d['version'] == '1.0.0'

    def test_from_dict_roundtrip(self):
        from model_rollback import ModelVersion
        original = ModelVersion(
            version='2.0.0', path='/models/v2/model.keras',
            created_at='2026-02-01T12:00:00', deployed_at='2026-02-01T13:00:00',
            metrics={'accuracy': 0.92}, config_hash='def456', data_version='v3', status='deployed',
        )
        restored = ModelVersion.from_dict(original.to_dict())
        assert restored.version == original.version
        assert restored.metrics == original.metrics
        assert restored.status == original.status


class TestModelRegistry:
    def test_registry_initialization(self):
        from model_rollback import ModelRegistry
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ModelRegistry(registry_dir=Path(tmpdir) / 'registry')
            assert registry.registry_dir.exists()
            assert registry.registry['current_version'] is None

    def test_register_model(self):
        from model_rollback import ModelRegistry
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ModelRegistry(registry_dir=Path(tmpdir) / 'registry')
            model_path = Path(tmpdir) / 'new_model.keras'
            model_path.write_text('mock model data')
            version = registry.register_model(model_path=model_path, version='1.0.0', metrics={'f1': 0.90})
            assert version.version == '1.0.0'
            assert '1.0.0' in registry.registry['models']

    def test_deploy_model(self):
        from model_rollback import ModelRegistry
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ModelRegistry(registry_dir=Path(tmpdir) / 'registry')
            model_path = Path(tmpdir) / 'model.keras'
            model_path.write_text('mock')
            registry.register_model(model_path=model_path, version='1.0.0', metrics={'f1': 0.85})
            assert registry.deploy_model('1.0.0') is True
            assert registry.get_current_version() == '1.0.0'

    def test_deploy_nonexistent_version(self):
        from model_rollback import ModelRegistry
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ModelRegistry(registry_dir=Path(tmpdir) / 'registry')
            assert registry.deploy_model('999.0.0') is False

    def test_list_versions(self):
        from model_rollback import ModelRegistry
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ModelRegistry(registry_dir=Path(tmpdir) / 'registry')
            for i in range(3):
                mp = Path(tmpdir) / f'model_{i}.keras'
                mp.write_text(f'mock {i}')
                registry.register_model(model_path=mp, version=f'{i+1}.0.0', metrics={'f1': 0.80 + i * 0.05})
            assert len(registry.list_versions()) == 3

    def test_get_current_version_none(self):
        from model_rollback import ModelRegistry
        with tempfile.TemporaryDirectory() as tmpdir:
            assert ModelRegistry(registry_dir=Path(tmpdir) / 'registry').get_current_version() is None

    def test_register_with_deploy(self):
        from model_rollback import ModelRegistry
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ModelRegistry(registry_dir=Path(tmpdir) / 'registry')
            mp = Path(tmpdir) / 'model.keras'
            mp.write_text('mock model')
            registry.register_model(model_path=mp, version='1.0.0', metrics={'accuracy': 0.90}, deploy=True)
            assert registry.get_current_version() == '1.0.0'

    def test_deployment_history(self):
        from model_rollback import ModelRegistry
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ModelRegistry(registry_dir=Path(tmpdir) / 'registry')
            for v in ['1.0.0', '2.0.0']:
                mp = Path(tmpdir) / f'model_{v}.keras'
                mp.write_text(f'mock {v}')
                registry.register_model(model_path=mp, version=v, metrics={'f1': 0.85}, deploy=True)
            history = registry.get_deployment_history()
            assert len(history) >= 2
            assert history[-1]['action'] == 'deploy'


class TestRollbackIntegration:
    def test_full_rollback_workflow(self):
        from model_rollback import ModelRegistry
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ModelRegistry(registry_dir=Path(tmpdir) / 'registry')
            for v, f1 in [('1.0.0', 0.88), ('2.0.0', 0.82)]:
                mp = Path(tmpdir) / f'model_{v}.keras'
                mp.write_text(f'{v} data')
                registry.register_model(model_path=mp, version=v, metrics={'f1': f1}, deploy=True)
            assert registry.get_current_version() == '2.0.0'
            assert registry.rollback(target_version='1.0.0') is True
            assert registry.get_current_version() == '1.0.0'

    def test_rollback_to_previous(self):
        from model_rollback import ModelRegistry
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ModelRegistry(registry_dir=Path(tmpdir) / 'registry')
            for v in ['1.0.0', '2.0.0']:
                mp = Path(tmpdir) / f'model_{v}.keras'
                mp.write_text(f'{v} data')
                registry.register_model(model_path=mp, version=v, metrics={'f1': 0.85}, deploy=True)
            assert registry.rollback() is True
            assert registry.get_current_version() == '1.0.0'

    def test_rollback_records_history(self):
        from model_rollback import ModelRegistry
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ModelRegistry(registry_dir=Path(tmpdir) / 'registry')
            for v in ['1.0.0', '2.0.0']:
                mp = Path(tmpdir) / f'model_{v}.keras'
                mp.write_text(f'{v} data')
                registry.register_model(model_path=mp, version=v, metrics={'f1': 0.85}, deploy=True)
            registry.rollback(target_version='1.0.0')
            rollbacks = [h for h in registry.get_deployment_history() if h['action'] == 'rollback']
            assert len(rollbacks) >= 1


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


class TestBaselineUpdateConfig:
    def test_defaults(self):
        cfg = BaselineUpdateConfig()
        assert cfg.training_data_path is None
        assert cfg.rebuild_embeddings is False


class TestBaselineUpdateComponent:
    def test_initiate_with_mock_builder(self, pipeline_config_bu, tmp_path):
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
