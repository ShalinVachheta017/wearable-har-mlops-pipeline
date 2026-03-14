"""
Post-Inference Monitoring Module

Performs 3-layer monitoring:
1. Confidence Analysis - detect low confidence predictions
2. Temporal Analysis - detect anomalous temporal patterns
3. Drift Analysis - detect distribution drift from baseline
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class MonitoringReport:
    """Container for monitoring results."""
    
    def __init__(self):
        self.overall_status = "PASS"
        self.layer1_confidence = {}
        self.layer2_temporal = {}
        self.layer3_drift = {}
        self.alerts = []
        self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_status,
            "layer1_confidence": self.layer1_confidence,
            "layer2_temporal": self.layer2_temporal,
            "layer3_drift": self.layer3_drift,
            "alerts": self.alerts,
            "metadata": self.metadata
        }


class PostInferenceMonitor:
    """
    Three-layer monitoring system for production inference results.
    """
    
    def __init__(
        self,
        confidence_threshold: float = 0.5,
        uncertain_threshold_pct: float = 10.0,
        drift_threshold: float = 2.0,
        calibration_temperature: float = 1.0,
    ):
        """
        Args:
            confidence_threshold: Minimum confidence for valid predictions
            uncertain_threshold_pct: Max % of uncertain predictions allowed
            drift_threshold: Max z-score drift allowed (2σ ≈ 95th pct null;
                           Gama et al. 2014 DDM, Page 1954 CUSUM)
            calibration_temperature: Temperature T from Stage 11 (CalibrationUncertainty).
                When T != 1.0, confidence scores are re-scaled via:
                  p_cal ≈ p^(1/T) / (p^(1/T) + (1-p)^(1/T))
                This sharpens (T>1) or dampens (T<1) overconfident predictions before
                monitoring thresholds are applied.
        """
        self.confidence_threshold = confidence_threshold
        self.uncertain_threshold_pct = uncertain_threshold_pct
        self.drift_threshold = drift_threshold
        self.calibration_temperature = float(calibration_temperature)
        self.logger = logging.getLogger(__name__)
    
    def run(
        self,
        predictions_path: Path,
        production_data_path: Optional[Path] = None,
        baseline_path: Optional[Path] = None,
        model_path: Optional[Path] = None,
        output_dir: Path = Path("outputs/monitoring"),
    ) -> MonitoringReport:
        """
        Run complete monitoring pipeline.
        
        Args:
            predictions_path: Path to predictions CSV
            production_data_path: Path to production data .npy (for drift)
            baseline_path: Path to baseline stats JSON (for drift)
            model_path: Path to model file
            output_dir: Directory for monitoring outputs
            
        Returns:
            MonitoringReport with results
        """
        self.logger.info("=" * 60)
        self.logger.info("MONITORING PIPELINE - START")
        self.logger.info("=" * 60)
        
        report = MonitoringReport()
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load predictions
        self.logger.info(f"Loading predictions: {predictions_path}")
        predictions_df = pd.read_csv(predictions_path)

        # 6b — Apply post-hoc temperature scaling when T != 1.0
        # (approximation from max-confidence only; Stage 11 provides the temperature)
        if self.calibration_temperature != 1.0 and 'confidence' in predictions_df.columns:
            T = self.calibration_temperature
            p = predictions_df['confidence'].clip(1e-10, 1.0 - 1e-10).values
            p_cal = p ** (1.0 / T) / (p ** (1.0 / T) + (1.0 - p) ** (1.0 / T))
            predictions_df = predictions_df.copy()
            predictions_df['confidence'] = p_cal
            self.logger.info(
                "Temperature scaling applied: T=%.3f — mean confidence %.4f → %.4f",
                T, float(p.mean()), float(p_cal.mean()),
            )
        
        # Layer 1: Confidence Analysis
        self.logger.info("\n" + "=" * 60)
        self.logger.info("LAYER 1: CONFIDENCE ANALYSIS")
        self.logger.info("=" * 60)
        report.layer1_confidence = self._analyze_confidence(predictions_df)
        
        # Layer 2: Temporal Analysis
        self.logger.info("\n" + "=" * 60)
        self.logger.info("LAYER 2: TEMPORAL PATTERN ANALYSIS")
        self.logger.info("=" * 60)
        report.layer2_temporal = self._analyze_temporal_patterns(predictions_df)
        
        # Layer 3: Drift Analysis (optional - requires baseline)
        if production_data_path and baseline_path and Path(baseline_path).exists():
            self.logger.info("\n" + "=" * 60)
            self.logger.info("LAYER 3: DRIFT ANALYSIS")
            self.logger.info("=" * 60)
            report.layer3_drift = self._analyze_drift(
                production_data_path, baseline_path
            )
        else:
            self.logger.info("\n" + "=" * 60)
            self.logger.info("LAYER 3: DRIFT ANALYSIS - SKIPPED")
            self.logger.info("=" * 60)
            if not baseline_path:
                self.logger.warning("⚠️ No baseline provided - drift analysis skipped")
            elif not Path(baseline_path).exists():
                self.logger.warning(f"⚠️ Baseline not found: {baseline_path}")
            report.layer3_drift = {"status": "SKIPPED", "reason": "No baseline available"}
        
        # Determine overall status
        report.overall_status = self._determine_overall_status(report)
        report.metadata = {
            "total_predictions": len(predictions_df),
            "predictions_path": str(predictions_path),
            "baseline_path": str(baseline_path) if baseline_path else None,
        }
        
        # Save report
        report_path = output_dir / "monitoring_report.json"
        with open(report_path, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        self.logger.info(f"\n📄 Monitoring report saved: {report_path}")
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info(f"MONITORING RESULT: {report.overall_status}")
        self.logger.info("=" * 60)
        
        if report.alerts:
            self.logger.warning(f"⚠️ {len(report.alerts)} alert(s) generated:")
            for alert in report.alerts:
                self.logger.warning(f"   - {alert}")
        
        return report
    
    def _analyze_confidence(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Layer 1: Analyze prediction confidence."""
        results = {}
        
        # Overall statistics
        mean_conf = df['confidence'].mean()
        std_conf = df['confidence'].std()
        min_conf = df['confidence'].min()
        max_conf = df['confidence'].max()
        
        results['mean_confidence'] = float(mean_conf)
        results['std_confidence'] = float(std_conf)
        results['min_confidence'] = float(min_conf)
        results['max_confidence'] = float(max_conf)
        
        # Count by confidence level
        if 'is_uncertain' in df.columns:
            uncertain_count = df['is_uncertain'].sum()
            uncertain_pct = 100 * uncertain_count / len(df)
        else:
            uncertain_count = (df['confidence'] < self.confidence_threshold).sum()
            uncertain_pct = 100 * uncertain_count / len(df)
        
        results['uncertain_count'] = int(uncertain_count)
        results['uncertain_percentage'] = float(uncertain_pct)

        # Entropy (approximated from confidence: multinomial, K=11 HAR classes)
        # H = -c*log(c) - (1-c)*log((1-c)/(K-1))  where K=11
        K = 11
        eps = 1e-10
        confs = df['confidence'].clip(eps, 1.0 - eps).values
        entropy_vals = -(confs * np.log(confs) + (1 - confs) * np.log((1 - confs) / (K - 1) + eps))
        mean_entropy = float(np.mean(entropy_vals))
        results['mean_entropy'] = mean_entropy
        self.logger.info(f"Mean entropy (approx): {mean_entropy:.4f}")

        self.logger.info(f"Uncertain predictions: {uncertain_count}/{len(df)} ({uncertain_pct:.1f}%)")
        
        # Check thresholds
        if uncertain_pct > self.uncertain_threshold_pct:
            alert = f"High uncertainty rate: {uncertain_pct:.1f}% > {self.uncertain_threshold_pct}%"
            results['status'] = 'ALERT'
            results['alert'] = alert
            self.logger.warning(f"⚠️ {alert}")
        else:
            results['status'] = 'PASS'
            self.logger.info(f"✅ Confidence check PASSED")
        
        return results
    
    def _analyze_temporal_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Layer 2: Analyze temporal patterns."""
        results = {}
        
        if 'predicted_activity' not in df.columns:
            results['status'] = 'SKIPPED'
            results['reason'] = 'No activity column found'
            return results
        
        # Calculate transitions
        activities = df['predicted_activity'].values
        transitions = np.sum(activities[1:] != activities[:-1])
        transition_rate = 100 * transitions / (len(activities) - 1) if len(activities) > 1 else 0
        
        results['total_windows'] = len(df)
        results['transitions'] = int(transitions)
        results['transition_rate'] = float(transition_rate)
        
        # Find longest sequences AND collect all dwell lengths
        sequences = {}
        dwell_lengths = []
        current_activity = activities[0]
        current_length = 1
        
        for i in range(1, len(activities)):
            if activities[i] == current_activity:
                current_length += 1
            else:
                dwell_lengths.append(current_length)
                if current_activity not in sequences:
                    sequences[current_activity] = 0
                sequences[current_activity] = max(sequences[current_activity], current_length)
                current_activity = activities[i]
                current_length = 1
        
        # Don't forget the last sequence
        dwell_lengths.append(current_length)
        if current_activity not in sequences:
            sequences[current_activity] = 0
        sequences[current_activity] = max(sequences[current_activity], current_length)
        
        results['longest_sequences'] = sequences

        # Dwell-time metrics (window duration = 200 samples @ 25 Hz = 8 s)
        WINDOW_DURATION_SECS = 8.0
        SHORT_DWELL_WINDOWS = 2  # <= 2 windows (16 s) is "short"
        if dwell_lengths:
            mean_dwell_secs = float(np.mean(dwell_lengths) * WINDOW_DURATION_SECS)
            short_dwell_ratio = float(
                sum(1 for d in dwell_lengths if d <= SHORT_DWELL_WINDOWS) / len(dwell_lengths)
            )
        else:
            mean_dwell_secs = 0.0
            short_dwell_ratio = 0.0
        results['mean_dwell_time_seconds'] = mean_dwell_secs
        results['short_dwell_ratio'] = short_dwell_ratio
        self.logger.info(
            f"Mean dwell time: {mean_dwell_secs:.1f}s  short_dwell_ratio: {short_dwell_ratio:.3f}"
        )

        self.logger.info(f"Activity transitions: {transitions} ({transition_rate:.1f}%)")
        self.logger.info(f"Longest sequences: {sequences}")
        
        # Simple check: very high transition rate might indicate noise
        if transition_rate > 50:
            alert = f"High transition rate: {transition_rate:.1f}% (possible noise)"
            results['status'] = 'WARNING'
            results['alert'] = alert
            self.logger.warning(f"⚠️ {alert}")
        else:
            results['status'] = 'PASS'
            self.logger.info(f"✅ Temporal pattern check PASSED")
        
        return results
    
    def _analyze_drift(
        self, production_data_path: Path, baseline_path: Path
    ) -> Dict[str, Any]:
        """Layer 3: Analyze distribution drift."""
        results = {}
        
        try:
            # Load production data
            production_data = np.load(production_data_path)
            
            # Load baseline stats
            with open(baseline_path, 'r') as f:
                baseline = json.load(f)
            
            # Schema guard: fail loudly if required keys are missing
            _required = {"mean", "std"}
            _missing  = _required - set(baseline.keys())
            if _missing:
                raise ValueError(
                    f"Baseline JSON is missing required keys: {_missing}. "
                    f"Available keys: {list(baseline.keys())}. "
                    f"Re-run Stage 10 (baseline update) to regenerate."
                )

            # Feature-space guard: Stage 6 expects transformed-space baseline
            # because production_data_path is loaded from production_X.npy
            # after preprocessing transform mode.
            metadata = baseline.get("metadata", {}) if isinstance(baseline, dict) else {}
            feature_space = metadata.get("feature_space")
            if feature_space != "transformed":
                raise ValueError(
                    "Baseline feature-space mismatch: expected metadata.feature_space='transformed' "
                    f"but got '{feature_space}'. Rebuild baseline via Stage 10."
                )

            # Calculate production statistics
            prod_mean = production_data.mean(axis=(0, 1))  # Average over windows and timesteps
            prod_std = production_data.std(axis=(0, 1))
            
            # Compare with baseline
            if 'mean' in baseline and 'std' in baseline:
                baseline_mean = np.array(baseline['mean'])
                baseline_std = np.array(baseline['std'])

                if baseline_mean.shape[0] != prod_mean.shape[0] or baseline_std.shape[0] != prod_std.shape[0]:
                    raise ValueError(
                        "Baseline channel-shape mismatch: "
                        f"baseline_mean={baseline_mean.shape[0]}, baseline_std={baseline_std.shape[0]}, "
                        f"production={prod_mean.shape[0]}"
                    )
                
                # Calculate drift metrics (simple: normalized difference)
                mean_diff = np.abs(prod_mean - baseline_mean) / (baseline_std + 1e-8)
                max_drift = float(np.max(mean_diff))
                
                results['production_mean'] = prod_mean.tolist()
                results['production_std'] = prod_std.tolist()
                results['baseline_mean'] = baseline_mean.tolist()
                results['baseline_std'] = baseline_std.tolist()
                results['max_drift'] = max_drift
                
                # Count drifted channels (drift > 1 sigma from baseline)
                DRIFT_CHANNEL_THRESHOLD = 1.0  # normalised Z-score units
                n_drifted_channels = int(np.sum(mean_diff > DRIFT_CHANNEL_THRESHOLD))
                results['n_drifted_channels'] = n_drifted_channels
                self.logger.info(
                    f"Max drift: {max_drift:.3f}  drifted channels: {n_drifted_channels}"
                )
                
                if max_drift > self.drift_threshold:
                    alert = f"Distribution drift detected: {max_drift:.3f} > {self.drift_threshold}"
                    results['status'] = 'ALERT'
                    results['alert'] = alert
                    self.logger.warning(f"⚠️ {alert}")
                else:
                    results['status'] = 'PASS'
                    self.logger.info(f"✅ Drift check PASSED")
            else:
                results['status'] = 'PASS'
                results['note'] = 'Baseline format incompatible - basic check only'
                self.logger.info("✅ Basic drift check PASSED")
                
        except Exception as e:
            results['status'] = 'ERROR'
            results['error'] = str(e)
            self.logger.error(f"❌ Drift analysis failed: {e}")
        
        return results
    
    def _determine_overall_status(self, report: MonitoringReport) -> str:
        """Determine overall monitoring status based on all layers."""
        alerts = []
        
        # Check each layer
        if report.layer1_confidence.get('status') == 'ALERT':
            alerts.append(report.layer1_confidence.get('alert'))
        
        if report.layer2_temporal.get('status') in ['ALERT', 'WARNING']:
            alerts.append(report.layer2_temporal.get('alert'))
        
        if report.layer3_drift.get('status') == 'ALERT':
            alerts.append(report.layer3_drift.get('alert'))
        
        report.alerts = alerts
        
        if alerts:
            return "ALERT"
        elif (report.layer2_temporal.get('status') == 'WARNING' or
              report.layer1_confidence.get('status') == 'WARNING'):
            return "WARNING"
        else:
            return "PASS"
