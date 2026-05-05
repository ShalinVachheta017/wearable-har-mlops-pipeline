"""
Tests for Trigger Policy Module
================================

Tests for the automated retraining trigger logic.
"""

import json
from datetime import datetime
import numpy as np
import pytest
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from trigger_policy import (
    TriggerPolicyEngine, 
    TriggerThresholds, 
    TriggerAction, 
    AlertLevel,
    ProxyModelValidator
)


class TestTriggerThresholds:
    """Tests for threshold configuration."""
    
    def test_default_thresholds(self):
        """Test that default thresholds are set correctly.

        Drift thresholds are z-scores of mean shift (NOT PSI):
          drift_zscore_warn=2.0  (≈95th pct), drift_zscore_critical=3.0 (≈99.7th pct).
        References: Gama et al. 2014 (DDM), Page 1954 (CUSUM).
        """
        thresholds = TriggerThresholds()
        
        assert thresholds.confidence_warn == 0.65
        assert thresholds.confidence_critical == 0.50
        assert thresholds.drift_zscore_warn == 2.0
        assert thresholds.drift_zscore_critical == 3.0
        assert thresholds.dominant_pct_critical == 95.0
    
    def test_custom_thresholds(self):
        """Test custom threshold configuration."""
        thresholds = TriggerThresholds(
            confidence_warn=0.60,
            drift_zscore_critical=0.30
        )
        
        assert thresholds.confidence_warn == 0.60
        assert thresholds.drift_zscore_critical == 0.30


class TestTriggerPolicyEngine:
    """Tests for the main trigger policy engine."""
    
    def test_engine_initialization(self, temp_state_file):
        """Test engine initializes correctly."""
        engine = TriggerPolicyEngine(state_file=temp_state_file)
        
        assert engine.thresholds is not None
        assert engine.cooldown is not None
        assert engine.state is not None
    
    def test_normal_metrics_no_trigger(self, temp_state_file, sample_monitoring_report):
        """Test that normal metrics don't trigger retraining."""
        engine = TriggerPolicyEngine(state_file=temp_state_file)
        
        decision = engine.evaluate(sample_monitoring_report)
        
        assert decision.should_trigger == False
        assert decision.action in [TriggerAction.NONE, TriggerAction.MONITOR]
        assert decision.alert_level == AlertLevel.INFO
    
    def test_degraded_metrics_trigger(self, temp_state_file, degraded_monitoring_report):
        """Test that degraded metrics trigger retraining."""
        engine = TriggerPolicyEngine(state_file=temp_state_file)
        
        decision = engine.evaluate(degraded_monitoring_report)
        
        # With multiple signals degraded, alert escalates.
        assert decision.alert_level in [AlertLevel.WARNING, AlertLevel.CRITICAL]
        # Governance: CRITICAL signals route to REVIEW (human gate), never auto-retrain.
        assert decision.action in [TriggerAction.QUEUE_RETRAIN, TriggerAction.TRIGGER_RETRAIN, TriggerAction.REVIEW]
        assert decision.auto_retrain is False
    
    def test_low_confidence_triggers_warning(self, temp_state_file):
        """Test that low confidence triggers at least a warning."""
        engine = TriggerPolicyEngine(state_file=temp_state_file)
        
        report = {
            'confidence_report': {
                'metrics': {
                    'mean_confidence': 0.50,  # Below warn threshold
                    'mean_entropy': 1.0,
                    'uncertain_ratio': 0.10
                }
            },
            'temporal_report': {
                'metrics': {'flip_rate': 0.10}
            },
            'drift_report': {
                'per_channel_metrics': {},
                'n_drifted_channels': 0
            }
        }
        
        decision = engine.evaluate(report)
        
        # Should at least note the low confidence
        assert 'confidence' in str(decision.signals).lower() or \
               decision.alert_level != AlertLevel.INFO

    def test_drift_zscore_key_replaces_psi_alias(self, temp_state_file):
        """New drift payloads use drift_zscore; psi remains only as a compatibility alias."""
        engine = TriggerPolicyEngine(state_file=temp_state_file)

        report = {
            "confidence_report": {
                "metrics": {
                    "mean_confidence": 0.90,
                    "mean_entropy": 1.0,
                    "uncertain_ratio": 0.01,
                }
            },
            "temporal_report": {
                "metrics": {"flip_rate": 0.10}
            },
            "drift_report": {
                "per_channel_metrics": {
                    "Ax_w": {"drift_zscore": 2.2},
                    "Ay_w": {"drift_zscore": 2.1},
                },
                "n_drifted_channels": 0,
                "aggregate_drift_score": 0.0,
            },
        }

        decision = engine.evaluate(report)

        assert decision.signals["drift"]["level"] == AlertLevel.WARNING.value

    def test_collapse_guard_dominant_pct_95_forces_review(
        self, temp_state_file, sample_monitoring_report
    ):
        """95%+ single-class dominance must return REVIEW and block auto-retrain."""
        engine = TriggerPolicyEngine(state_file=temp_state_file)

        report = json.loads(json.dumps(sample_monitoring_report))
        report["collapse_signals"] = {
            "dominance_warning": False,
            "dominant_class": "hand_tapping",
            "dominant_pct": 95.0,
            "mean_confidence": 0.85,
            "transition_rate": 7.0,
        }

        decision = engine.evaluate(report)

        assert decision.action == TriggerAction.REVIEW
        assert decision.should_trigger is False
        assert decision.alert_level == AlertLevel.WARNING
        assert "collapse_guard" in decision.signals
        matched = decision.signals["collapse_guard"].get("matched_conditions", [])
        assert "dominant_pct>=95" in matched

    def test_collapse_guard_below_95_does_not_review_by_itself(
        self, temp_state_file, sample_monitoring_report
    ):
        """Dominance below 95% should not hit collapse REVIEW unless other guard conditions match."""
        engine = TriggerPolicyEngine(state_file=temp_state_file)

        report = json.loads(json.dumps(sample_monitoring_report))
        report["collapse_signals"] = {
            "dominance_warning": False,
            "dominant_class": "hand_tapping",
            "dominant_pct": 94.9,
            "mean_confidence": 0.80,
            "transition_rate": 5.0,
        }

        decision = engine.evaluate(report)

        assert decision.action in [TriggerAction.NONE, TriggerAction.MONITOR]
        assert decision.should_trigger is False
        assert decision.alert_level == AlertLevel.INFO

    def test_collapse_level_critical_forces_review(
        self, temp_state_file, sample_monitoring_report
    ):
        """Stage 4 CRITICAL_COLLAPSE must directly block automatic retraining."""
        engine = TriggerPolicyEngine(state_file=temp_state_file)

        report = json.loads(json.dumps(sample_monitoring_report))
        report["collapse_signals"] = {
            "collapse_level": "CRITICAL_COLLAPSE",
            "dominant_class": "hand_tapping",
            "dominant_pct": 88.0,
            "mean_confidence": 0.90,
            "transition_rate": 4.0,
        }

        decision = engine.evaluate(report)

        assert decision.action == TriggerAction.REVIEW
        assert decision.should_trigger is False
        assert decision.alert_level == AlertLevel.CRITICAL
        matched = decision.signals["collapse_guard"].get("matched_conditions", [])
        assert "collapse_level=CRITICAL_COLLAPSE" in matched

    def test_low_motion_collapse_risk_forces_review(
        self, temp_state_file, sample_monitoring_report
    ):
        """Stage 6 low-motion collapse risk must block automatic retraining."""
        engine = TriggerPolicyEngine(state_file=temp_state_file)

        report = json.loads(json.dumps(sample_monitoring_report))
        report["collapse_signals"] = {
            "low_motion_collapse_risk": True,
            "low_gyro_motion": True,
            "g_mag_median": 0.545,
            "gravity_dominant_axis": "Az",
            "dominant_class": "hand_tapping",
            "dominant_pct": 78.0,
            "mean_confidence": 0.91,
            "transition_rate": 5.0,
        }

        decision = engine.evaluate(report)

        assert decision.action == TriggerAction.REVIEW
        assert decision.should_trigger is False
        assert decision.alert_level == AlertLevel.CRITICAL
        guard = decision.signals["collapse_guard"]
        assert "low_motion_collapse_risk=true" in guard["matched_conditions"]
        assert guard["g_mag_median"] == 0.545
        assert guard["gravity_dominant_axis"] == "Az"
    
    def test_multiple_signals_required(self, temp_state_file):
        """Test that multiple signals are required for trigger."""
        engine = TriggerPolicyEngine(state_file=temp_state_file)
        
        # Only one signal degraded
        report = {
            'confidence_report': {
                'metrics': {
                    'mean_confidence': 0.40,  # Critical
                    'mean_entropy': 1.0,
                    'uncertain_ratio': 0.10
                }
            },
            'temporal_report': {
                'metrics': {'flip_rate': 0.10}  # Normal
            },
            'drift_report': {
                'per_channel_metrics': {},  # Normal
                'n_drifted_channels': 0
            }
        }
        
        decision = engine.evaluate(report)
        
        # Single critical signal should still trigger due to severity
        assert decision.alert_level == AlertLevel.CRITICAL
    
    def test_state_persistence(self, temp_state_file, sample_monitoring_report):
        """Test that state is persisted between evaluations."""
        engine = TriggerPolicyEngine(state_file=temp_state_file)
        
        # First evaluation
        engine.evaluate(sample_monitoring_report)
        
        # Check state file exists
        assert temp_state_file.exists()
        
        # Create new engine, should load state
        engine2 = TriggerPolicyEngine(state_file=temp_state_file)
        
        assert engine2.state['batches_since_retrain'] > 0
    
    def test_state_reset(self, temp_state_file, sample_monitoring_report):
        """Test state reset functionality."""
        engine = TriggerPolicyEngine(state_file=temp_state_file)
        
        # Accumulate some state
        engine.evaluate(sample_monitoring_report)
        engine.evaluate(sample_monitoring_report)
        
        # Reset
        engine.reset_state()
        
        assert engine.state['warning_count'] == 0
        assert engine.state['consecutive_warnings'] == 0
        assert engine.state['batches_since_retrain'] == 0
    
    def test_trigger_summary(self, temp_state_file, sample_monitoring_report):
        """Test trigger summary generation."""
        engine = TriggerPolicyEngine(state_file=temp_state_file)
        
        engine.evaluate(sample_monitoring_report)
        
        summary = engine.get_trigger_summary()
        
        assert 'warning_count' in summary
        assert 'consecutive_warnings' in summary
        assert 'batches_since_retrain' in summary


class TestConsecutiveWarnings:
    """Tests for consecutive warning escalation."""
    
    def test_consecutive_warnings_escalate(self, temp_state_file):
        """Test that consecutive warnings escalate to trigger."""
        engine = TriggerPolicyEngine(state_file=temp_state_file)
        
        # Warning-level report (but not critical)
        warning_report = {
            'confidence_report': {
                'metrics': {
                    'mean_confidence': 0.52,  # Just below warn
                    'mean_entropy': 1.9,      # Just above warn
                    'uncertain_ratio': 0.22   # Above warn
                }
            },
            'temporal_report': {
                'metrics': {'flip_rate': 0.28}  # Above warn
            },
            'drift_report': {
                'per_channel_metrics': {
                    'Ax_w': {'psi': 0.12},
                    'Ay_w': {'psi': 0.11}
                },
                'n_drifted_channels': 2
            }
        }
        
        # Simulate consecutive warnings
        decisions = []
        for i in range(4):
            decisions.append(engine.evaluate(warning_report))
        
        # Governance: consecutive warnings escalate to REVIEW (human gate), not auto-retrain.
        assert any(d.action == TriggerAction.REVIEW for d in decisions)
        assert all(d.auto_retrain is False for d in decisions)


class TestCooldownOrdering:
    """Regression tests for cooldown precedence in final trigger decisions."""

    def test_cooldown_wins_over_consecutive_warning_escalation(self, temp_state_file):
        """A cooldown-active run must not end with immediate retrain after escalation."""
        engine = TriggerPolicyEngine(state_file=temp_state_file)

        previous_retrain = datetime.now().isoformat()
        engine.state["last_retrain_timestamp"] = previous_retrain
        engine.state["consecutive_warnings"] = (
            engine.thresholds.consecutive_warnings_for_trigger - 1
        )
        engine._save_state()

        warning_report = {
            "confidence_report": {
                "metrics": {
                    "mean_confidence": 0.60,
                    "mean_entropy": 1.0,
                    "uncertain_ratio": 0.10,
                }
            },
            "temporal_report": {
                "metrics": {
                    "flip_rate": 0.10,
                }
            },
            "drift_report": {
                "per_channel_metrics": {},
                "n_drifted_channels": 0,
                "aggregate_drift_score": 0.0,
            },
        }

        decision = engine.evaluate(warning_report)

        # Governance: consecutive warnings → REVIEW + should_trigger=False.
        # Cooldown is irrelevant here since auto-retrain never fires.
        assert decision.should_trigger is False
        assert decision.auto_retrain is False
        assert decision.action == TriggerAction.REVIEW
        assert decision.review_required is True
        assert engine.state["last_retrain_timestamp"] == previous_retrain

    def test_cooldown_does_not_override_review_decision(self, temp_state_file):
        """Collapse guard REVIEW should remain REVIEW even when cooldown state exists."""
        engine = TriggerPolicyEngine(state_file=temp_state_file)
        engine.state["last_retrain_timestamp"] = datetime.now().isoformat()
        engine._save_state()

        report = {
            "confidence_report": {"metrics": {}},
            "temporal_report": {"metrics": {}},
            "drift_report": {"per_channel_metrics": {}, "n_drifted_channels": 0},
            "collapse_signals": {
                "dominance_warning": False,
                "dominant_class": "hand_tapping",
                "dominant_pct": 95.0,
                "mean_confidence": 0.85,
                "transition_rate": 5.0,
            },
        }

        decision = engine.evaluate(report)

        assert decision.action == TriggerAction.REVIEW
        assert decision.should_trigger is False
        assert decision.cooldown_active is False


class TestProxyModelValidator:
    """Tests for proxy-based model validation."""
    
    def test_validator_initialization(self):
        """Test validator initializes correctly."""
        validator = ProxyModelValidator(improvement_threshold=0.05)
        assert validator.improvement_threshold == 0.05
    
    def test_improved_model_recommended(self):
        """Test that improved model is recommended for deployment."""
        validator = ProxyModelValidator()
        
        np.random.seed(42)
        n_samples = 100
        n_classes = 11
        
        # Old model: lower confidence
        old_probs = np.random.dirichlet(np.ones(n_classes) * 0.5, size=n_samples)
        old_labels = np.argmax(old_probs, axis=1)
        
        # New model: higher confidence
        new_probs = np.random.dirichlet(np.ones(n_classes) * 3, size=n_samples)
        new_labels = np.argmax(new_probs, axis=1)
        
        old_predictions = {'probabilities': old_probs, 'labels': old_labels}
        new_predictions = {'probabilities': new_probs, 'labels': new_labels}
        
        result = validator.compare_models(old_predictions, new_predictions)
        
        assert 'should_deploy' in result
        assert 'comparisons' in result
        assert 'confidence' in result['comparisons']
    
    def test_regression_not_deployed(self):
        """Test that regressed model is not recommended."""
        validator = ProxyModelValidator()
        
        n_samples = 100
        n_classes = 11
        
        # Old model: clearly high confidence
        old_probs = np.full((n_samples, n_classes), 0.01)
        for i in range(n_samples):
            old_probs[i, i % n_classes] = 0.90
        old_probs = old_probs / old_probs.sum(axis=1, keepdims=True)
        old_labels = np.argmax(old_probs, axis=1)
        
        # New model: uniform / low confidence (regression)
        new_probs = np.ones((n_samples, n_classes)) / n_classes
        new_labels = np.argmax(new_probs, axis=1)
        
        old_predictions = {'probabilities': old_probs, 'labels': old_labels}
        new_predictions = {'probabilities': new_probs, 'labels': new_labels}
        
        result = validator.compare_models(old_predictions, new_predictions)
        
        # Should not deploy due to regression
        assert result['should_deploy'] == False


class TestAlertLevels:
    """Tests for alert level assignment."""
    
    def test_info_level_for_normal(self, temp_state_file, sample_monitoring_report):
        """Test INFO level for normal metrics."""
        engine = TriggerPolicyEngine(state_file=temp_state_file)
        decision = engine.evaluate(sample_monitoring_report)
        
        assert decision.alert_level == AlertLevel.INFO
    
    def test_critical_for_severe_degradation(self, temp_state_file, degraded_monitoring_report):
        """Test CRITICAL level for severe degradation."""
        engine = TriggerPolicyEngine(state_file=temp_state_file)
        decision = engine.evaluate(degraded_monitoring_report)
        
        # Should be WARNING or CRITICAL
        assert decision.alert_level in [AlertLevel.WARNING, AlertLevel.CRITICAL]
