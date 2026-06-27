"""MLflow logging adapter for ProductionPipeline."""

from __future__ import annotations

from src.logger import logging

logger = logging.getLogger(__name__)


class PipelineMLflowLogger:
    """Owns non-fatal MLflow lifecycle, metrics, and model registration."""

    def __init__(self, artifacts_manager):
        self.artifacts_manager = artifacts_manager

    def init_run(self, run_id: str):
        """
        Method Name :   init_run
        Description :   Start an MLflow run for the production pipeline.

        Output      :   Returns MLflowTracker or None.
        On Failure  :   Logs the error and continues without tracking.
        """
        try:
            from src.mlflow_tracking import MLflowTracker

            tracker = MLflowTracker(experiment_name="har-production-pipeline")
            tracker._run_context = tracker.start_run(
                run_name=f"pipeline_{run_id}",
                tags={"pipeline": "production", "version": "2.0"},
            )
            tracker._active_run = tracker._run_context.__enter__()
            return tracker
        except Exception as exc:
            logger.warning("MLflow initialization failed (continuing without tracking): %s", exc)
            return None

    def log_stage(self, tracker, stage: str, result) -> None:
        """
        Method Name :   log_stage
        Description :   Log per-stage metrics and artifacts to MLflow.

        Output      :   Writes MLflow metrics/artifacts when tracking is active.
        On Failure  :   Logs the error and continues.
        """
        try:
            metrics = self._stage_metrics(stage, result)
            if metrics:
                tracker.log_metrics(metrics)
                logger.debug("Logged %d metrics to MLflow for stage: %s", len(metrics), stage)
            self._log_stage_artifacts(tracker, stage, result)
        except Exception as exc:
            logger.warning("Failed to log stage '%s' to MLflow: %s", stage, exc)

    def end_run(self, tracker, result) -> None:
        """
        Method Name :   end_run
        Description :   Finalize MLflow params and artifacts.

        Output      :   Ends the MLflow run.
        On Failure  :   Logs the error and continues.

        NOTE: Model registration is intentionally NOT called here.
        Registration happens only in Stage 9 (ModelRegistration component).
        Calling register_model during normal inference would create unauthorized
        model versions on every production run.
        """
        try:
            retrain_ran = "retraining" in result.stages_completed
            trigger_requested = bool(result.trigger and result.trigger.should_retrain)
            tracker.log_params(
                {
                    "stages_completed": ",".join(result.stages_completed),
                    "stages_failed": ",".join(result.stages_failed),
                    "overall_status": result.overall_status,
                    "n_stages_completed": len(result.stages_completed),
                    "n_stages_failed": len(result.stages_failed),
                    "retrain_ran": str(retrain_ran),
                    "retrain_trigger_initiated": str(trigger_requested),
                    "retrain_forced_by_cli": str(retrain_ran and not trigger_requested),
                }
            )
            run_info_path = self.artifacts_manager.run_dir / "run_info.json"
            if run_info_path.exists():
                tracker.log_artifact(run_info_path, "pipeline")
            # register_model is NOT called here — Stage 9 owns registration.
            if hasattr(tracker, "_run_context"):
                tracker._run_context.__exit__(None, None, None)
        except Exception as exc:
            logger.warning("Failed to finalize MLflow run: %s", exc)
        finally:
            try:
                if hasattr(tracker, "_run_context"):
                    tracker._run_context.__exit__(None, None, None)
            except Exception:
                pass

    def register_model(self, tracker, result) -> None:
        """
        Method Name :   register_model
        Description :   Register the active production model in MLflow Model Registry.

        Output      :   Logs/registers the model when possible.
        On Failure  :   Logs the error and continues.
        """
        try:
            from src.config import DEFAULT_MODEL_PATH

            if result.retraining and result.retraining.retrained_model_path:
                model_path = result.retraining.retrained_model_path
            elif result.inference and result.inference.active_model_path:
                model_path = result.inference.active_model_path
            else:
                model_path = DEFAULT_MODEL_PATH
            if not model_path.exists():
                logger.warning("Model file not found at %s - skipping registration.", model_path)
                return
            loaded_model = self.load_keras_model(model_path)
            input_example = self._input_example(loaded_model)
            tracker.log_keras_model(
                model=loaded_model,
                artifact_path="model",
                input_example=input_example,
                registered_model_name="har-1dcnn-bilstm",
            )
            conf_mean = 0.0
            if result.inference and result.inference.confidence_stats:
                conf_mean = result.inference.confidence_stats.get("mean", 0.0)
            tracker.log_metrics({"registered_model_confidence": conf_mean})
            logger.info("Model registered in MLflow Model Registry as 'har-1dcnn-bilstm'")
        except Exception as exc:
            logger.warning("Model registration failed (non-fatal): %s", exc)

    @staticmethod
    def load_keras_model(path):
        """Load a Keras model with lazy TensorFlow import."""
        from tensorflow import keras

        return keras.models.load_model(path)

    @staticmethod
    def _input_example(loaded_model):
        try:
            import numpy as np

            input_shape = loaded_model.input_shape
            return np.zeros((1,) + tuple(input_shape[1:]), dtype=np.float32)
        except Exception:
            return None

    def _stage_metrics(self, stage: str, result) -> dict:
        builders = {
            "ingestion": self._ingestion_metrics,
            "validation": self._validation_metrics,
            "transformation": self._transformation_metrics,
            "inference": self._inference_metrics,
            "monitoring": self._monitoring_metrics,
            "trigger": self._trigger_metrics,
            "retraining": self._retraining_metrics,
        }
        builder = builders.get(stage)
        return builder(result) if builder else {}

    @staticmethod
    def _ingestion_metrics(result) -> dict:
        if not result.ingestion:
            return {}
        return {
            "ingestion_n_rows": result.ingestion.n_rows,
            "ingestion_n_columns": result.ingestion.n_columns,
        }

    @staticmethod
    def _validation_metrics(result) -> dict:
        if not result.validation:
            return {}
        return {
            "validation_is_valid": 1.0 if result.validation.is_valid else 0.0,
        }

    @staticmethod
    def _transformation_metrics(result) -> dict:
        if not result.transformation:
            return {}
        return {
            "transformation_n_windows": result.transformation.n_windows,
        }

    @staticmethod
    def _inference_metrics(result) -> dict:
        if not result.inference:
            return {}
        conf = result.inference.confidence_stats or {}
        metrics = {
            "inference_time_seconds": result.inference.inference_time_seconds,
            "inference_mean_confidence": conf.get("mean", 0.0),
            "inference_uncertain_pct": conf.get("n_uncertain", 0)
            / max(result.inference.n_predictions, 1)
            * 100,
        }
        if result.inference.activity_distribution:
            total = sum(result.inference.activity_distribution.values())
            max_count = max(result.inference.activity_distribution.values())
            metrics["inference_dominant_activity_pct"] = (max_count / max(total, 1)) * 100
        return metrics

    @staticmethod
    def _monitoring_metrics(result) -> dict:
        if not result.monitoring:
            return {}
        layer2 = result.monitoring.layer2_temporal or {}
        layer3 = result.monitoring.layer3_drift or {}
        return {
            "monitoring_overall_healthy": (
                1.0 if result.monitoring.overall_status == "HEALTHY" else 0.0
            ),
            "monitoring_transition_rate": layer2.get("transition_rate", 0.0),
            "monitoring_drift_score": layer3.get("max_drift", 0.0),
        }

    @staticmethod
    def _trigger_metrics(result) -> dict:
        if not result.trigger:
            return {}
        alert_map = {"INFO": 0, "WARNING": 1, "ALERT": 2, "CRITICAL": 3}
        return {
            "trigger_should_retrain": 1.0 if result.trigger.should_retrain else 0.0,
            "trigger_alert_level": alert_map.get(result.trigger.alert_level, 0),
        }

    @staticmethod
    def _retraining_metrics(result) -> dict:
        if not result.retraining:
            return {}
        metrics = {
            f"retrain_{key}": value
            for key, value in result.retraining.metrics.items()
            if isinstance(value, (int, float))
        }
        metrics["retrain_n_source_samples"] = result.retraining.n_source_samples
        metrics["retrain_n_target_samples"] = result.retraining.n_target_samples
        return metrics

    def _log_stage_artifacts(self, tracker, stage: str, result) -> None:
        if stage == "inference" and result.inference:
            summary = self.artifacts_manager.run_dir / "inference" / "inference_summary.json"
            if summary.exists():
                tracker.log_artifact(summary, "inference")
        elif stage == "evaluation" and result.evaluation:
            if result.evaluation.report_json_path and result.evaluation.report_json_path.exists():
                tracker.log_artifact(result.evaluation.report_json_path, "evaluation")
        elif stage == "monitoring" and result.monitoring:
            if result.monitoring.report_path and result.monitoring.report_path.exists():
                tracker.log_artifact(result.monitoring.report_path, "monitoring")
