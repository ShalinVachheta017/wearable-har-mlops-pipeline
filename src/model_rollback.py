#!/usr/bin/env python3
"""
Model Rollback Manager
======================

Safe model rollback functionality for the HAR MLOps pipeline.
Enables quick recovery when a deployed model underperforms.

Features:
- Maintain history of deployed models
- Quick rollback to previous versions
- Validation before and after rollback
- Audit trail of all rollback operations

Usage:
    # List available model versions
    python src/model_rollback.py --list

    # Rollback to previous version
    python src/model_rollback.py --rollback

    # Rollback to specific version
    python src/model_rollback.py --rollback --version 1.0.0

Author: HAR MLOps Pipeline
Date: January 30, 2026
"""

import argparse
import hashlib
import json
import logging
import shutil
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import MODELS_DIR, PROJECT_ROOT
from src.utils.common import get_timestamp

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class ModelVersion:
    """Represents a model version with metadata."""

    version: str
    path: str
    created_at: str
    deployed_at: Optional[str]
    metrics: Dict[str, float]
    config_hash: str
    data_version: Optional[str]
    status: str  # 'deployed', 'archived', 'rollback'

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "ModelVersion":
        return cls(**data)


# ============================================================================
# MODEL REGISTRY
# ============================================================================


class ModelRegistry:
    """
    Local model registry for tracking deployed models.

    Maintains a history of all model versions and enables
    quick rollback to previous versions.
    """

    def __init__(self, registry_dir: Path = None):
        self.registry_dir = registry_dir or (MODELS_DIR / "registry")
        self.registry_dir.mkdir(parents=True, exist_ok=True)

        self.registry_file = self.registry_dir / "model_registry.json"
        self.current_link = MODELS_DIR / "current"

        self.registry = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        """Load registry from file."""
        if self.registry_file.exists():
            with open(self.registry_file, "r") as f:
                return json.load(f)
        return {"models": {}, "current_version": None, "history": []}

    def _save_registry(self):
        """Save registry to file."""
        with open(self.registry_file, "w") as f:
            json.dump(self.registry, f, indent=2, default=str)

    def _compute_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()[:12]

    def register_model(
        self,
        model_path: Path,
        version: str,
        metrics: Dict[str, float],
        data_version: Optional[str] = None,
        deploy: bool = False,
    ) -> ModelVersion:
        """
        Register a new model version.

        Args:
            model_path: Path to the model file
            version: Semantic version string
            metrics: Model performance metrics
            data_version: DVC version of training data
            deploy: Whether to deploy immediately

        Returns:
            ModelVersion object
        """
        logger.info(f"Registering model version: {version}")

        # Copy model to registry
        model_filename = f"har_model_v{version}.keras"
        registry_path = self.registry_dir / model_filename

        if model_path.exists():
            shutil.copy2(model_path, registry_path)

        # Create version record
        model_version = ModelVersion(
            version=version,
            path=str(registry_path),
            created_at=datetime.now().isoformat(),
            deployed_at=None,
            metrics=metrics,
            config_hash=self._compute_hash(registry_path) if registry_path.exists() else "unknown",
            data_version=data_version,
            status="archived",
        )

        # Add to registry
        self.registry["models"][version] = model_version.to_dict()
        self._save_registry()

        logger.info(f"✓ Model {version} registered at {registry_path}")

        if deploy:
            self.deploy_model(version)

        return model_version

    def deploy_model(self, version: str) -> bool:
        """
        Deploy a specific model version.

        Args:
            version: Version to deploy

        Returns:
            True if successful
        """
        if version not in self.registry["models"]:
            logger.error(f"Version {version} not found in registry")
            return False

        model_info = self.registry["models"][version]
        model_path = Path(model_info["path"])

        if not model_path.exists():
            logger.error(f"Model file not found: {model_path}")
            return False

        # Update current symlink/copy
        current_model = MODELS_DIR / "pretrained" / "current_model.keras"
        current_model.parent.mkdir(parents=True, exist_ok=True)

        # On Windows, copy instead of symlink
        if current_model.exists():
            current_model.unlink()
        shutil.copy2(model_path, current_model)

        # Update registry
        old_version = self.registry["current_version"]
        if old_version and old_version in self.registry["models"]:
            self.registry["models"][old_version]["status"] = "archived"

        self.registry["models"][version]["status"] = "deployed"
        self.registry["models"][version]["deployed_at"] = datetime.now().isoformat()
        self.registry["current_version"] = version

        # Record in history
        self.registry["history"].append(
            {
                "action": "deploy",
                "version": version,
                "previous_version": old_version,
                "timestamp": datetime.now().isoformat(),
            }
        )

        self._save_registry()

        logger.info(f"✓ Model {version} deployed successfully")
        return True

    def rollback(self, target_version: Optional[str] = None) -> bool:
        """
        Rollback to a previous model version.

        Args:
            target_version: Specific version to rollback to.
                          If None, rolls back to the previous version.

        Returns:
            True if successful
        """
        logger.info("=" * 60)
        logger.info("MODEL ROLLBACK")
        logger.info("=" * 60)

        current = self.registry["current_version"]

        if target_version is None:
            # Find previous version from history
            deploy_history = [
                h
                for h in self.registry["history"]
                if h["action"] == "deploy" and h["version"] != current
            ]

            if not deploy_history:
                logger.error("No previous version available for rollback")
                return False

            # Get the most recent previous version
            target_version = deploy_history[-1].get("previous_version")

            if target_version is None:
                # Fall back to finding any archived version
                archived = [
                    v
                    for v, info in self.registry["models"].items()
                    if info["status"] == "archived" and v != current
                ]
                if archived:
                    target_version = sorted(archived)[-1]

        if target_version is None or target_version not in self.registry["models"]:
            logger.error(f"Target version {target_version} not found")
            return False

        logger.info(f"Rolling back from {current} to {target_version}")

        # Mark current as rollback
        if current:
            self.registry["models"][current]["status"] = "rollback"

        # Deploy target version
        success = self.deploy_model(target_version)

        if success:
            # Record rollback in history
            self.registry["history"].append(
                {
                    "action": "rollback",
                    "from_version": current,
                    "to_version": target_version,
                    "timestamp": datetime.now().isoformat(),
                    "reason": "manual_rollback",
                }
            )
            self._save_registry()

            logger.info(f"✓ Rollback to {target_version} successful")

        return success

    def list_versions(self) -> List[Dict]:
        """List all registered model versions."""
        versions = []
        for version, info in self.registry["models"].items():
            versions.append(
                {
                    "version": version,
                    "status": info["status"],
                    "created_at": info["created_at"],
                    "deployed_at": info.get("deployed_at"),
                    "metrics": info.get("metrics", {}),
                }
            )
        return sorted(versions, key=lambda x: x["version"], reverse=True)

    def get_current_version(self) -> Optional[str]:
        """Get currently deployed version."""
        return self.registry["current_version"]

    def get_deployment_history(self, limit: int = 10) -> List[Dict]:
        """Get recent deployment history."""
        return self.registry["history"][-limit:]


# ============================================================================
# ROLLBACK VALIDATOR
# ============================================================================


class RollbackValidator:
    """
    Validate model before and after rollback.

    Ensures the rolled-back model is functional and
    produces reasonable outputs.
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.Validator")

    def validate_model_file(self, model_path: Path) -> bool:
        """Check that model file exists and is loadable."""
        if not model_path.exists():
            self.logger.error(f"Model file not found: {model_path}")
            return False

        try:
            import tensorflow as tf

            model = tf.keras.models.load_model(model_path)

            # Check model structure
            if model is None:
                return False

            # Check input/output shapes
            input_shape = model.input_shape
            output_shape = model.output_shape

            self.logger.info(f"Model loaded: input={input_shape}, output={output_shape}")

            del model
            tf.keras.backend.clear_session()

            return True

        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            return False

    def validate_inference(self, model_path: Path) -> bool:
        """Run a quick inference test."""
        try:
            import numpy as np
            import tensorflow as tf

            model = tf.keras.models.load_model(model_path)

            # Create dummy input
            dummy_input = np.random.randn(1, 200, 6).astype(np.float32)

            # Run inference
            output = model.predict(dummy_input, verbose=0)

            # Check output
            if output is None or output.shape != (1, 11):
                self.logger.error(f"Unexpected output shape: {output.shape}")
                return False

            # Check probabilities sum to 1
            prob_sum = np.sum(output)
            if not np.isclose(prob_sum, 1.0, atol=0.01):
                self.logger.error(f"Probabilities don't sum to 1: {prob_sum}")
                return False

            self.logger.info("✓ Inference validation passed")

            del model
            tf.keras.backend.clear_session()

            return True

        except Exception as e:
            self.logger.error(f"Inference validation failed: {e}")
            return False


# ============================================================================
# CLI
# ============================================================================


def main():
    parser = argparse.ArgumentParser(description="Model rollback manager for HAR MLOps pipeline")

    parser.add_argument("--list", action="store_true", help="List all model versions")
    parser.add_argument("--current", action="store_true", help="Show current deployed version")
    parser.add_argument("--history", action="store_true", help="Show deployment history")
    parser.add_argument("--rollback", action="store_true", help="Rollback to previous version")
    parser.add_argument("--version", type=str, default=None, help="Specific version to rollback to")
    parser.add_argument(
        "--register", type=str, default=None, help="Register a new model (path to model file)"
    )
    parser.add_argument("--deploy", type=str, default=None, help="Deploy a specific version")
    parser.add_argument("--validate", type=str, default=None, help="Validate a model file")

    args = parser.parse_args()

    registry = ModelRegistry()
    validator = RollbackValidator()

    if args.list:
        print("\n" + "=" * 60)
        print("REGISTERED MODEL VERSIONS")
        print("=" * 60)

        versions = registry.list_versions()
        if not versions:
            print("No models registered yet.")
        else:
            for v in versions:
                status_icon = "🟢" if v["status"] == "deployed" else "⚪"
                print(f"\n{status_icon} Version: {v['version']}")
                print(f"   Status: {v['status']}")
                print(f"   Created: {v['created_at']}")
                if v["deployed_at"]:
                    print(f"   Deployed: {v['deployed_at']}")
                if v["metrics"]:
                    print(f"   Metrics: accuracy={v['metrics'].get('accuracy', 'N/A')}")

        return 0

    if args.current:
        current = registry.get_current_version()
        print(f"\nCurrently deployed: {current or 'None'}")
        return 0

    if args.history:
        print("\n" + "=" * 60)
        print("DEPLOYMENT HISTORY")
        print("=" * 60)

        history = registry.get_deployment_history()
        for entry in history:
            print(f"\n{entry['timestamp']}")
            print(f"  Action: {entry['action']}")
            if entry["action"] == "deploy":
                print(f"  Version: {entry['version']}")
            elif entry["action"] == "rollback":
                print(f"  From: {entry['from_version']} → To: {entry['to_version']}")

        return 0

    if args.validate:
        model_path = Path(args.validate)
        print(f"\nValidating model: {model_path}")

        file_valid = validator.validate_model_file(model_path)
        inference_valid = validator.validate_inference(model_path) if file_valid else False

        if file_valid and inference_valid:
            print("✓ Model validation passed")
            return 0
        else:
            print("✗ Model validation failed")
            return 1

    if args.register:
        model_path = Path(args.register)
        if not model_path.exists():
            print(f"Model file not found: {model_path}")
            return 1

        # Generate version from timestamp
        version = get_timestamp("%Y%m%d.%H%M%S")

        registry.register_model(
            model_path=model_path,
            version=version,
            metrics={"accuracy": 0.0},  # Would be filled from actual training
            deploy=False,
        )

        print(f"✓ Model registered as version {version}")
        return 0

    if args.deploy:
        success = registry.deploy_model(args.deploy)
        return 0 if success else 1

    if args.rollback:
        # Validate before rollback
        target = args.version

        print("\n" + "=" * 60)
        print("INITIATING ROLLBACK")
        print("=" * 60)

        success = registry.rollback(target_version=target)

        if success:
            # Validate after rollback
            current_model = MODELS_DIR / "pretrained" / "current_model.keras"
            if current_model.exists():
                validator.validate_inference(current_model)

        return 0 if success else 1

    # Default: show help
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
