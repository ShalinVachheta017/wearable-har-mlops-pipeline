"""Utility Tests — Active Learning Export"""
#!/usr/bin/env python3
import numpy as np
import pandas as pd
import tempfile
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestUncertaintySampler:
    def test_least_confidence(self):
        from active_learning_export import UncertaintySampler
        sampler = UncertaintySampler()
        assert sampler.least_confidence(np.array([[0.4, 0.35, 0.25]]))[0] > \
               sampler.least_confidence(np.array([[0.95, 0.03, 0.02]]))[0]

    def test_entropy_sampling(self):
        from active_learning_export import UncertaintySampler
        sampler = UncertaintySampler()
        low_entropy = np.array([[0.99] + [0.01/10]*10])[:, :11]
        high_entropy = np.ones((1, 11)) / 11
        assert sampler.entropy_sampling(high_entropy)[0] > sampler.entropy_sampling(low_entropy)[0]

    def test_margin_sampling(self):
        from active_learning_export import UncertaintySampler
        sampler = UncertaintySampler()
        large_margin = np.array([[0.9] + [0.05/10]*10])[:, :11]
        small_margin = np.array([[0.35, 0.33] + [0.32/9]*9])[:, :11]
        assert sampler.margin_sampling(small_margin)[0] > sampler.margin_sampling(large_margin)[0]

    def test_select_samples(self):
        from active_learning_export import UncertaintySampler
        np.random.seed(42)
        probs = np.random.dirichlet(np.ones(11), size=500)
        indices, metadata = UncertaintySampler().select_uncertain_samples(
            probs, n_samples=50, predictions=np.argmax(probs, axis=1)
        )
        assert len(indices) <= 50
        assert metadata['n_selected'] == len(indices)
        assert 'mean_uncertainty' in metadata


class TestDiversitySampler:
    def test_temporal_diversity(self):
        from active_learning_export import DiversitySampler
        timestamps = np.arange(0, 86400, 100)
        indices = DiversitySampler().temporal_diversity(timestamps, n_samples=50)
        assert len(indices) <= 50
        assert np.std(timestamps[indices]) > 10000

    def test_prediction_diversity(self):
        from active_learning_export import DiversitySampler
        predictions = np.array([0] * 100 + [1] * 50 + [2] * 20 + list(range(3, 11)) * 10)
        indices = DiversitySampler().prediction_diversity(predictions, n_samples=50)
        assert len(indices) <= 50
        assert len(set(predictions[indices])) > 5


class TestActiveLearningExporter:
    def test_select_samples_uncertainty(self):
        from active_learning_export import ActiveLearningExporter, ActiveLearningConfig
        np.random.seed(42)
        data = pd.DataFrame({'acc_x': np.random.randn(200), 'acc_y': np.random.randn(200), 'acc_z': np.random.randn(200)})
        probs = np.random.dirichlet(np.ones(11), size=200)
        selected, metadata = ActiveLearningExporter(ActiveLearningConfig(strategy='uncertainty')).select_samples(
            data, probs, np.argmax(probs, axis=1), n_samples=30
        )
        assert len(selected) <= 30
        assert '_uncertainty_score' in selected.columns

    def test_select_samples_hybrid(self):
        from active_learning_export import ActiveLearningExporter, ActiveLearningConfig
        np.random.seed(42)
        data = pd.DataFrame({'feature': np.random.randn(200)})
        probs = np.random.dirichlet(np.ones(11), size=200)
        selected, metadata = ActiveLearningExporter(ActiveLearningConfig(strategy='hybrid')).select_samples(
            data, probs, np.argmax(probs, axis=1), n_samples=50
        )
        assert metadata['strategy'] == 'hybrid'
        assert 'n_uncertain' in metadata

    def test_export_for_labeling(self):
        from active_learning_export import ActiveLearningExporter, ActiveLearningConfig
        with tempfile.TemporaryDirectory() as tmpdir:
            np.random.seed(42)
            data = pd.DataFrame({'acc_x': np.random.randn(100), 'acc_y': np.random.randn(100)})
            probs = np.random.dirichlet(np.ones(11), size=100)
            exporter = ActiveLearningExporter(ActiveLearningConfig(export_dir=Path(tmpdir)))
            selected, metadata = exporter.select_samples(data, probs, np.argmax(probs, axis=1), n_samples=20)
            export_path = exporter.export_for_labeling(selected, metadata, batch_id='test_batch')
            assert export_path.exists()
            assert (export_path.parent / 'batch_metadata.json').exists()
            assert (export_path.parent / 'LABELING_INSTRUCTIONS.md').exists()

    def test_import_labeled_data(self):
        from active_learning_export import ActiveLearningExporter, ActiveLearningConfig
        with tempfile.TemporaryDirectory() as tmpdir:
            np.random.seed(42)
            data = pd.DataFrame({'acc_x': np.random.randn(50)})
            probs = np.random.dirichlet(np.ones(11), size=50)
            exporter = ActiveLearningExporter(ActiveLearningConfig(export_dir=Path(tmpdir)))
            selected, metadata = exporter.select_samples(data, probs, np.argmax(probs, axis=1), n_samples=20)
            export_path = exporter.export_for_labeling(selected, metadata, batch_id='import_test')
            labeled_df = pd.read_csv(export_path)
            labeled_df['human_label'] = np.random.randint(0, 11, size=len(labeled_df))
            labeled_df.to_csv(export_path, index=False)
            imported, stats = exporter.import_labeled_data(export_path.parent)
            assert stats['n_labeled'] == len(labeled_df)
            assert stats['completion_rate'] == 1.0
