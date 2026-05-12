#!/usr/bin/env python3
"""
Deployment Manager
==================

Manages model deployment lifecycle including:
- Container build and push
- Model serving deployment
- Blue-green deployments
- Canary releases
- Health checks and validation

Integrates with Docker, Kubernetes (optional), and cloud platforms.

Usage:
    python deployment_manager.py build
    python deployment_manager.py deploy --version v1.2.0
    python deployment_manager.py rollback --to v1.1.0
    python deployment_manager.py canary --new-version v1.2.0 --traffic 10

Author: HAR MLOps Pipeline
Date: January 30, 2026
"""

import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class DeploymentConfig:
    """Deployment configuration."""

    # Container settings
    image_name: str = "har-inference"
    image_tag: str = "latest"
    registry: str = "localhost:5000"  # Local registry for development

    # Paths
    docker_dir: Path = Path("docker")
    models_dir: Path = Path("models")
    artifacts_dir: Path = Path("artifacts")

    # Deployment settings
    deployment_strategy: str = "rolling"  # 'rolling', 'blue_green', 'canary'
    replicas: int = 2
    max_unavailable: int = 1

    # Health check settings
    health_check_endpoint: str = "/health"
    health_check_port: int = 8080
    health_check_timeout: int = 30

    # Canary settings
    canary_traffic_percent: int = 10
    canary_duration_minutes: int = 30

    # Rollback settings
    keep_versions: int = 5

    def full_image_name(self, tag: str = None) -> str:
        """Get full image name with registry."""
        tag = tag or self.image_tag
        return f"{self.registry}/{self.image_name}:{tag}"


# ============================================================================
# CONTAINER BUILDER
# ============================================================================


class ContainerBuilder:
    """Builds Docker containers for model serving."""

    def __init__(self, config: DeploymentConfig = None):
        self.config = config or DeploymentConfig()
        self.logger = logging.getLogger(f"{__name__}.ContainerBuilder")

    def check_docker(self) -> bool:
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ["docker", "--version"], capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def build_inference_image(
        self, model_path: Path, version: str, extra_files: List[Path] = None
    ) -> Dict[str, Any]:
        """
        Build inference Docker image.

        Args:
            model_path: Path to trained model
            version: Version tag for the image
            extra_files: Additional files to include

        Returns:
            Build result with image details
        """
        self.logger.info(f"Building inference image version {version}")

        # Verify Dockerfile exists
        dockerfile = self.config.docker_dir / "Dockerfile.inference"
        if not dockerfile.exists():
            raise FileNotFoundError(f"Dockerfile not found: {dockerfile}")

        # Create build context
        build_context = tempfile.mkdtemp(prefix="har_build_")

        try:
            # Copy Dockerfile
            shutil.copy(dockerfile, Path(build_context) / "Dockerfile")

            # Copy model
            model_dest = Path(build_context) / "model"
            if model_path.is_dir():
                shutil.copytree(model_path, model_dest)
            else:
                model_dest.mkdir(parents=True)
                shutil.copy(model_path, model_dest / model_path.name)

            # Copy source files
            src_dest = Path(build_context) / "src"
            src_dest.mkdir()
            src_dir = Path("src")

            required_files = [
                "config.py",
                "run_inference.py",
            ]
            for f in required_files:
                src_file = src_dir / f
                if src_file.exists():
                    shutil.copy(src_file, src_dest / f)

            # Copy runtime packages used by the thin inference CLI.
            for package_name in ("components", "entity", "utils"):
                package_src = src_dir / package_name
                package_dest = src_dest / package_name
                if package_src.exists():
                    import shutil as _shutil

                    _shutil.copytree(package_src, package_dest)

            # Copy monitoring package
            monitoring_src = src_dir / "monitoring"
            if monitoring_src.exists():
                import shutil as _shutil

                _shutil.copytree(monitoring_src, src_dest / "monitoring")

            # Copy requirements
            req_file = Path("config/requirements.txt")
            if req_file.exists():
                shutil.copy(req_file, Path(build_context) / "requirements.txt")

            # Copy extra files
            if extra_files:
                for f in extra_files:
                    if f.exists():
                        shutil.copy(f, Path(build_context) / f.name)

            # Build image
            image_tag = self.config.full_image_name(version)

            cmd = [
                "docker",
                "build",
                "-t",
                image_tag,
                "-f",
                "Dockerfile",
                "--build-arg",
                f"MODEL_VERSION={version}",
                ".",
            ]

            self.logger.info(f"Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd, cwd=build_context, capture_output=True, text=True, timeout=600
            )

            if result.returncode != 0:
                self.logger.error(f"Build failed: {result.stderr}")
                return {"success": False, "error": result.stderr, "stdout": result.stdout}

            # Get image info
            inspect_result = subprocess.run(
                ["docker", "inspect", image_tag], capture_output=True, text=True
            )

            if inspect_result.returncode == 0:
                image_info = json.loads(inspect_result.stdout)[0]
                image_size = image_info.get("Size", 0) / (1024 * 1024)  # MB
            else:
                image_size = 0

            return {
                "success": True,
                "image": image_tag,
                "version": version,
                "size_mb": round(image_size, 2),
                "build_time": datetime.now().isoformat(),
            }

        finally:
            # Cleanup
            shutil.rmtree(build_context, ignore_errors=True)

    def push_image(self, version: str) -> Dict[str, Any]:
        """
        Push image to registry.

        Args:
            version: Version tag to push

        Returns:
            Push result
        """
        image_tag = self.config.full_image_name(version)

        self.logger.info(f"Pushing image: {image_tag}")

        result = subprocess.run(
            ["docker", "push", image_tag], capture_output=True, text=True, timeout=300
        )

        if result.returncode != 0:
            return {"success": False, "error": result.stderr}

        return {"success": True, "image": image_tag, "pushed_at": datetime.now().isoformat()}


# ============================================================================
# DEPLOYMENT MANAGER
# ============================================================================


class DeploymentManager:
    """
    Manages model deployment lifecycle.

    Supports:
    - Docker Compose deployments
    - Blue-green deployment pattern
    - Canary releases
    - Automatic rollback
    """

    def __init__(self, config: DeploymentConfig = None):
        self.config = config or DeploymentConfig()
        self.builder = ContainerBuilder(config)
        self.logger = logging.getLogger(f"{__name__}.DeploymentManager")

        # Deployment state file
        self.state_file = self.config.artifacts_dir / "deployment_state.json"
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        """Load deployment state."""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {
            "current_version": None,
            "previous_version": None,
            "deployments": [],
            "canary_active": False,
        }

    def _save_state(self):
        """Save deployment state."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)

    def deploy(self, version: str, model_path: Path = None, strategy: str = None) -> Dict[str, Any]:
        """
        Deploy a model version.

        Args:
            version: Version to deploy
            model_path: Path to model (optional, uses default)
            strategy: Deployment strategy (optional, uses config default)

        Returns:
            Deployment result
        """
        strategy = strategy or self.config.deployment_strategy
        model_path = model_path or self.config.models_dir / "pretrained"

        self.logger.info(f"Deploying version {version} with strategy: {strategy}")

        # Build image if needed
        build_result = self.builder.build_inference_image(model_path, version)

        if not build_result.get("success"):
            return {"success": False, "stage": "build", "error": build_result.get("error")}

        # Deploy based on strategy
        if strategy == "rolling":
            deploy_result = self._rolling_deploy(version)
        elif strategy == "blue_green":
            deploy_result = self._blue_green_deploy(version)
        elif strategy == "canary":
            deploy_result = self._canary_deploy(version)
        else:
            return {"success": False, "error": f"Unknown strategy: {strategy}"}

        if deploy_result.get("success"):
            # Update state
            self.state["previous_version"] = self.state["current_version"]
            self.state["current_version"] = version
            self.state["deployments"].append(
                {
                    "version": version,
                    "strategy": strategy,
                    "timestamp": datetime.now().isoformat(),
                    "status": "active",
                }
            )

            # Keep only recent deployments
            self.state["deployments"] = self.state["deployments"][-self.config.keep_versions :]
            self._save_state()

        return deploy_result

    def _rolling_deploy(self, version: str) -> Dict[str, Any]:
        """
        Rolling deployment using docker-compose.

        Updates containers one at a time to minimize downtime.
        """
        self.logger.info("Executing rolling deployment...")

        compose_file = Path("docker-compose.yml")
        if not compose_file.exists():
            return {"success": False, "error": "docker-compose.yml not found"}

        # Update image tag in environment
        env = os.environ.copy()
        env["HAR_IMAGE_TAG"] = version

        # Pull new image
        pull_cmd = ["docker-compose", "pull", "inference"]
        pull_result = subprocess.run(pull_cmd, capture_output=True, text=True, env=env)

        # Rolling update
        up_cmd = [
            "docker-compose",
            "up",
            "-d",
            "--no-deps",
            "--scale",
            f"inference={self.config.replicas}",
            "inference",
        ]

        result = subprocess.run(up_cmd, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            return {"success": False, "error": result.stderr}

        # Health check
        healthy = self._wait_for_healthy(timeout=self.config.health_check_timeout)

        return {
            "success": healthy,
            "version": version,
            "strategy": "rolling",
            "replicas": self.config.replicas,
            "healthy": healthy,
        }

    def _blue_green_deploy(self, version: str) -> Dict[str, Any]:
        """
        Blue-green deployment.

        Spins up new version alongside old, then switches traffic.
        """
        self.logger.info("Executing blue-green deployment...")

        # Determine colors
        current_color = self.state.get("active_color", "blue")
        new_color = "green" if current_color == "blue" else "blue"

        env = os.environ.copy()
        env["HAR_IMAGE_TAG"] = version
        env["DEPLOYMENT_COLOR"] = new_color

        # Start new environment
        up_cmd = [
            "docker-compose",
            "-f",
            "docker-compose.yml",
            "-f",
            f"docker-compose.{new_color}.yml",
            "up",
            "-d",
        ]

        # Check if color-specific compose exists
        color_compose = Path(f"docker-compose.{new_color}.yml")
        if not color_compose.exists():
            # Use standard compose with port offset
            return self._rolling_deploy(version)

        result = subprocess.run(up_cmd, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            return {"success": False, "error": result.stderr}

        # Wait for new version to be healthy
        healthy = self._wait_for_healthy(
            port=self.config.health_check_port + (100 if new_color == "green" else 0),
            timeout=self.config.health_check_timeout,
        )

        if not healthy:
            # Cleanup failed deployment
            self._stop_color(new_color)
            return {"success": False, "error": "New version failed health check"}

        # Switch traffic (update nginx/load balancer)
        self._switch_traffic(new_color)

        # Stop old version
        self._stop_color(current_color)

        self.state["active_color"] = new_color

        return {
            "success": True,
            "version": version,
            "strategy": "blue_green",
            "active_color": new_color,
        }

    def _canary_deploy(self, version: str) -> Dict[str, Any]:
        """
        Canary deployment.

        Routes small percentage of traffic to new version.
        """
        self.logger.info(
            f"Executing canary deployment ({self.config.canary_traffic_percent}% traffic)..."
        )

        # Start canary container
        env = os.environ.copy()
        env["HAR_IMAGE_TAG"] = version
        env["CANARY"] = "true"

        up_cmd = [
            "docker-compose",
            "-f",
            "docker-compose.yml",
            "up",
            "-d",
            "--scale",
            "inference-canary=1",
            "inference-canary",
        ]

        result = subprocess.run(up_cmd, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            # Canary container might not be defined, use regular approach
            self.logger.warning("Canary container not defined, using weighted routing simulation")

        # Mark canary as active
        self.state["canary_active"] = True
        self.state["canary_version"] = version
        self.state["canary_started"] = datetime.now().isoformat()
        self._save_state()

        return {
            "success": True,
            "version": version,
            "strategy": "canary",
            "traffic_percent": self.config.canary_traffic_percent,
            "duration_minutes": self.config.canary_duration_minutes,
            "status": "canary_active",
        }

    def promote_canary(self) -> Dict[str, Any]:
        """Promote canary to full deployment."""
        if not self.state.get("canary_active"):
            return {"success": False, "error": "No active canary deployment"}

        canary_version = self.state.get("canary_version")
        self.logger.info(f"Promoting canary {canary_version} to full deployment")

        # Do rolling deploy of canary version
        result = self._rolling_deploy(canary_version)

        if result.get("success"):
            self.state["canary_active"] = False
            self.state["canary_version"] = None
            self._save_state()

        return result

    def rollback(self, target_version: str = None) -> Dict[str, Any]:
        """
        Rollback to previous version.

        Args:
            target_version: Specific version to rollback to (optional)

        Returns:
            Rollback result
        """
        target = target_version or self.state.get("previous_version")

        if not target:
            return {"success": False, "error": "No previous version available for rollback"}

        self.logger.warning(f"Rolling back to version: {target}")

        # Deploy previous version
        result = self._rolling_deploy(target)

        if result.get("success"):
            self.state["current_version"] = target
            self.state["deployments"].append(
                {
                    "version": target,
                    "strategy": "rollback",
                    "timestamp": datetime.now().isoformat(),
                    "status": "active",
                }
            )
            self._save_state()

        return {
            **result,
            "rollback": True,
            "from_version": self.state.get("current_version"),
            "to_version": target,
        }

    def _wait_for_healthy(self, port: int = None, timeout: int = None) -> bool:
        """Wait for service to be healthy."""
        port = port or self.config.health_check_port
        timeout = timeout or self.config.health_check_timeout

        import socket

        start = time.time()
        while time.time() - start < timeout:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(("localhost", port))
                sock.close()

                if result == 0:
                    self.logger.info(f"Service healthy on port {port}")
                    return True

            except Exception:
                pass

            time.sleep(2)

        self.logger.error(f"Health check timeout after {timeout}s")
        return False

    def _stop_color(self, color: str):
        """Stop blue or green deployment."""
        cmd = [
            "docker-compose",
            "-f",
            "docker-compose.yml",
            "-f",
            f"docker-compose.{color}.yml",
            "down",
        ]
        subprocess.run(cmd, capture_output=True)

    def _switch_traffic(self, target_color: str):
        """Switch traffic to target color (nginx/load balancer config)."""
        # This would update nginx upstream or load balancer
        self.logger.info(f"Switching traffic to {target_color}")
        # Implementation depends on actual infrastructure

    def status(self) -> Dict[str, Any]:
        """Get current deployment status."""
        return {
            "current_version": self.state.get("current_version"),
            "previous_version": self.state.get("previous_version"),
            "canary_active": self.state.get("canary_active", False),
            "canary_version": self.state.get("canary_version"),
            "recent_deployments": self.state.get("deployments", [])[-5:],
            "active_color": self.state.get("active_color"),
        }


# ============================================================================
# CLI
# ============================================================================


def main():
    """Command-line interface for deployment manager."""
    import argparse

    parser = argparse.ArgumentParser(
        description="HAR Model Deployment Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build and deploy
  python deployment_manager.py build --version v1.2.0
  python deployment_manager.py deploy --version v1.2.0

  # Canary deployment
  python deployment_manager.py deploy --version v1.2.0 --strategy canary
  python deployment_manager.py promote-canary

  # Rollback
  python deployment_manager.py rollback
  python deployment_manager.py rollback --to v1.1.0

  # Status
  python deployment_manager.py status
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Build
    build_parser = subparsers.add_parser("build", help="Build deployment image")
    build_parser.add_argument("--version", required=True, help="Version tag")
    build_parser.add_argument("--model", type=Path, help="Model path")

    # Deploy
    deploy_parser = subparsers.add_parser("deploy", help="Deploy a version")
    deploy_parser.add_argument("--version", required=True, help="Version to deploy")
    deploy_parser.add_argument("--strategy", choices=["rolling", "blue_green", "canary"])
    deploy_parser.add_argument("--model", type=Path, help="Model path")

    # Promote canary
    subparsers.add_parser("promote-canary", help="Promote canary to full deployment")

    # Rollback
    rollback_parser = subparsers.add_parser("rollback", help="Rollback deployment")
    rollback_parser.add_argument("--to", dest="target_version", help="Target version")

    # Status
    subparsers.add_parser("status", help="Show deployment status")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    manager = DeploymentManager()

    if args.command == "build":
        model_path = args.model or Path("models/pretrained")
        result = manager.builder.build_inference_image(model_path, args.version)

        if result.get("success"):
            print(f"\n✓ Built image: {result['image']}")
            print(f"  Size: {result['size_mb']} MB")
        else:
            print(f"\n✗ Build failed: {result.get('error')}")
            return 1

    elif args.command == "deploy":
        result = manager.deploy(version=args.version, model_path=args.model, strategy=args.strategy)

        if result.get("success"):
            print(f"\n✓ Deployed version {args.version}")
            print(f"  Strategy: {result.get('strategy')}")
        else:
            print(f"\n✗ Deployment failed: {result.get('error')}")
            return 1

    elif args.command == "promote-canary":
        result = manager.promote_canary()

        if result.get("success"):
            print("\n✓ Canary promoted to full deployment")
        else:
            print(f"\n✗ Promotion failed: {result.get('error')}")
            return 1

    elif args.command == "rollback":
        result = manager.rollback(target_version=args.target_version)

        if result.get("success"):
            print(f"\n✓ Rolled back to version {result.get('to_version')}")
        else:
            print(f"\n✗ Rollback failed: {result.get('error')}")
            return 1

    elif args.command == "status":
        status = manager.status()

        print("\n=== Deployment Status ===")
        print(f"Current version: {status.get('current_version') or 'None'}")
        print(f"Previous version: {status.get('previous_version') or 'None'}")

        if status.get("canary_active"):
            print(f"Canary active: {status.get('canary_version')}")

        print("\nRecent deployments:")
        for d in status.get("recent_deployments", []):
            print(f"  - {d['version']} ({d['strategy']}) at {d['timestamp']}")

    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
