"""Stage 8 — Model Retraining Tests (supervised retraining only)"""
from __future__ import annotations

import pytest

from src.entity.config_entity import PipelineConfig, ModelRetrainingConfig


@pytest.fixture
def pipeline_config(tmp_path):
    cfg = PipelineConfig()
    cfg.project_root = tmp_path
    cfg.models_dir = tmp_path / "models"
    cfg.models_pretrained_dir = tmp_path / "models" / "pretrained"
    cfg.data_raw_dir = tmp_path / "data" / "raw"
    cfg.data_prepared_dir = tmp_path / "data" / "prepared"
    cfg.logs_dir = tmp_path / "logs"
    for d in [cfg.models_dir, cfg.models_pretrained_dir, cfg.data_raw_dir, cfg.data_prepared_dir]:
        d.mkdir(parents=True, exist_ok=True)
    return cfg


def test_creates_instance(pipeline_config):
    from src.components.model_retraining import ModelRetraining
    comp = ModelRetraining(pipeline_config, ModelRetrainingConfig())
    assert comp is not None


def test_retraining_config_defaults():
    cfg = ModelRetrainingConfig()
    # Defended runtime: supervised retraining only — no unsupervised hooks.
    assert not hasattr(cfg, "enable_adaptation") or cfg.enable_adaptation is False
