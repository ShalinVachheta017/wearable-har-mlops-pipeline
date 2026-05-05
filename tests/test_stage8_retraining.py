"""Stage 8 — Model Retraining Tests (AdaBN domain adaptation)"""
from __future__ import annotations

import numpy as np
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

pytestmark = pytest.mark.slow  # requires TensorFlow

from src.entity.config_entity import PipelineConfig, ModelRetrainingConfig
from src.entity.artifact_entity import (
    ModelRetrainingArtifact,
    DataTransformationArtifact,
    TriggerEvaluationArtifact,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

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


@pytest.fixture
def dummy_npy(tmp_path):
    path = tmp_path / "data" / "prepared" / "production_X.npy"
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, np.random.randn(50, 200, 6).astype(np.float32))
    return path


@pytest.fixture
def transformation_artifact(dummy_npy):
    return DataTransformationArtifact(
        production_X_path=dummy_npy,
        metadata_path=dummy_npy.parent / "meta.json",
        n_windows=50,
        window_size=200,
        unit_conversion_applied=False,
        preprocessing_timestamp=datetime.now().isoformat(),
    )


@pytest.fixture
def dummy_model():
    tf = pytest.importorskip("tensorflow")
    keras = tf.keras
    inputs = keras.Input(shape=(200, 6))
    x = keras.layers.Conv1D(16, 3, padding="same")(inputs)
    x = keras.layers.BatchNormalization()(x)
    x = keras.layers.ReLU()(x)
    x = keras.layers.GlobalAveragePooling1D()(x)
    x = keras.layers.Dense(11, activation="softmax")(x)
    model = keras.Model(inputs, x)
    model.compile(optimizer="adam", loss="categorical_crossentropy")
    return model


@pytest.fixture
def target_data():
    np.random.seed(42)
    return np.random.randn(100, 200, 6).astype(np.float32)


# ── ModelRetraining component ─────────────────────────────────────────────────

class TestModelRetrainingInit:
    def test_creates_instance(self, pipeline_config):
        from src.components.model_retraining import ModelRetraining
        comp = ModelRetraining(pipeline_config, ModelRetrainingConfig())
        assert comp.config.adaptation_method == "none"

    def test_adaptation_disabled_by_default(self, pipeline_config):
        assert ModelRetrainingConfig().enable_adaptation is False


class TestModelRetrainingAdaBN:
    @pytest.mark.skipif(
        not pytest.importorskip("tensorflow", reason="TF not installed"),
        reason="TF required",
    )
    def test_adabn_retraining(self, pipeline_config, transformation_artifact):
        tf = pytest.importorskip("tensorflow")
        keras = tf.keras
        pretrained_dir = pipeline_config.models_pretrained_dir
        inputs = keras.Input(shape=(200, 6))
        x = keras.layers.Conv1D(8, 3, padding="same")(inputs)
        x = keras.layers.BatchNormalization()(x)
        x = keras.layers.ReLU()(x)
        x = keras.layers.GlobalAveragePooling1D()(x)
        x = keras.layers.Dense(11, activation="softmax")(x)
        model = keras.Model(inputs, x)
        model.compile(optimizer="adam", loss="categorical_crossentropy")
        model.save(pretrained_dir / "fine_tuned_model_1dcnnbilstm.keras")

        from src.components.model_retraining import ModelRetraining
        comp = ModelRetraining(
            pipeline_config,
            ModelRetrainingConfig(enable_adaptation=True, adaptation_method="adabn", adabn_n_batches=2, batch_size=16),
            transformation_artifact=transformation_artifact,
        )
        artifact = comp.initiate_model_retraining()
        assert isinstance(artifact, ModelRetrainingArtifact)
        assert artifact.adaptation_method == "adabn"
        assert artifact.retrained_model_path.exists()
        assert "after_mean_confidence" in artifact.metrics


# ── AdaBN unit tests ──────────────────────────────────────────────────────────

class TestFindBNLayers:
    def test_finds_bn_layers(self, dummy_model):
        from src.domain_adaptation.adabn import _find_bn_layers
        layers = _find_bn_layers(dummy_model)
        assert len(layers) >= 1
        assert "batch_normalization" in layers[0].name.lower() or "bn" in layers[0].name.lower()

    def test_returns_empty_for_none(self):
        from src.domain_adaptation.adabn import _find_bn_layers
        assert _find_bn_layers(None) == []


class TestAdaptBNStatistics:
    def test_model_unchanged_weights(self, dummy_model, target_data):
        from src.domain_adaptation.adabn import adapt_bn_statistics
        pytest.importorskip("tensorflow")
        conv_weights_before = dummy_model.layers[1].get_weights()[0].copy()
        adapt_bn_statistics(dummy_model, target_data, n_batches=3, batch_size=32)
        conv_weights_after = dummy_model.layers[1].get_weights()[0]
        np.testing.assert_array_equal(conv_weights_before, conv_weights_after)

    def test_bn_stats_change(self, dummy_model, target_data):
        from src.domain_adaptation.adabn import adapt_bn_statistics, _find_bn_layers
        bn_layers = _find_bn_layers(dummy_model)
        before_var = bn_layers[0].get_weights()[3].copy()
        adapt_bn_statistics(dummy_model, target_data, n_batches=20, batch_size=32, reset_stats=False)
        after_var = bn_layers[0].get_weights()[3]
        assert not np.allclose(before_var, after_var, atol=1e-4)

    def test_returns_model(self, dummy_model, target_data):
        from src.domain_adaptation.adabn import adapt_bn_statistics
        assert adapt_bn_statistics(dummy_model, target_data, n_batches=2) is dummy_model


class TestAdaBNScoreConfidence:
    def test_returns_dict(self, dummy_model, target_data):
        from src.domain_adaptation.adabn import adabn_score_confidence
        result = adabn_score_confidence(dummy_model, target_data)
        assert isinstance(result, dict)
        assert "mean_confidence" in result
        assert result["n_samples"] == 100

    def test_confidence_range(self, dummy_model, target_data):
        from src.domain_adaptation.adabn import adabn_score_confidence
        result = adabn_score_confidence(dummy_model, target_data)
        assert 0.0 <= result["mean_confidence"] <= 1.0
        assert 0.0 <= result["low_confidence_ratio"] <= 1.0
