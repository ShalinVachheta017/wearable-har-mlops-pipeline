#!/usr/bin/env python3
"""
MLOps Pipeline Audit Script (Core Edition)
Audits MasterArbeit_MLops repository across 10 MLOps dimensions.
Outputs: JSON + Markdown reports to reports/repo_audit/

Usage:
    python mlops_audit.py

Reports generated:
    - audit_TIMESTAMP.json
    - audit_TIMESTAMP.md
"""

import ast
import json
import re
from collections import defaultdict
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher
from typing import Dict, List, Tuple, Set, Iterable

# ============================================================================
# AUDIT CATEGORIES (10 Core MLOps Dimensions)
# ============================================================================

class MLOpsAuditor:
    """
    Complete repository auditor focused on practical MLOps readiness.

    Each category score is 0-10 and contributes equally to the overall score.
    """

    EXCLUDED_DIRS = {
        ".git",
        ".conda",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "node_modules",
        "artifacts",
        "mlruns",
        "logs",
        "outputs",
        "reports",
    }
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.timestamp = datetime.now().isoformat(timespec='minutes').replace(':', '')
        self.src_dir = repo_root / "src"
        self.tests_dir = repo_root / "tests"
        self.scripts_dir = repo_root / "scripts"
        self.reports_dir = repo_root / "reports" / "repo_audit"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        self.audit_results: Dict[str, Dict[str, object]] = {}
        self.all_issues: List[str] = []
        self.dead_code_issues: List[str] = []
        self.cleanup_insights: Dict[str, object] = {}
        self.category_check_catalog = self._build_category_check_catalog()

    @staticmethod
    def _normalize_rel(path: Path) -> str:
        return str(path).replace("\\", "/")

    def _is_excluded(self, path: Path) -> bool:
        return any(part in self.EXCLUDED_DIRS for part in path.parts)

    def _iter_repo_files(self, patterns: Iterable[str]) -> List[Path]:
        files: List[Path] = []
        for pattern in patterns:
            for path in self.repo_root.rglob(pattern):
                if path.is_file() and not self._is_excluded(path):
                    files.append(path)
        return files

    def _build_category_check_catalog(self) -> Dict[str, List[str]]:
        """Static checklist shown in reports so "no issues" still explains what was checked."""
        return {
            "1. Repo Structure & Code Quality": [
                "Expected modules under src/: api, components, core, data, deployment, entity, inference, logger, monitoring, pipeline, training, utils",
                "Python parsing + syntax scan across src/**/*.py",
                "Public docstring presence for functions/classes",
                "Public function return type annotation presence",
            ],
            "2. Reproducibility": [
                "Dependency manifests: pyproject.toml, requirements.txt, config/requirements.txt, config/requirements-lock.txt",
                "Container assets: docker-compose.yml and Dockerfile* in root/docker/",
                "Reproduction guide: REPRODUCE.md",
                "Seed controls in src/**/*.py and run_pipeline.py",
                "Repository hygiene: .gitignore and __pycache__ rule",
            ],
            "3. Data Pipeline & Validation": [
                "Data/preprocess/validation candidates in src/data/, src/, and scripts/",
                "Preprocess safeguards: NaN handling, scaling/normalization, windowing/segmentation",
                "Configuration anchor: config/pipeline_config.yaml",
            ],
            "4. Model Training & Experiment Tracking": [
                "Training entrypoints: src/training/trainer.py, src/train.py, run_pipeline.py",
                "Pipeline config files: **/pipeline_config*.yaml",
                "Experiment tracking token: mlflow in src/**/*.py and run_pipeline.py",
                "Model artifact directory: models/",
            ],
            "5. Inference & Deployment": [
                "Inference implementations in src/inference/, src/run_inference.py, scripts/inference_smoke.py",
                "Serving layer check in src/api/*.py with FastAPI/Flask token scan",
                "Deployment assets in src/deployment/, src/deployment_manager.py, docker/Dockerfile.inference",
            ],
            "6. Monitoring & Drift Detection": [
                "Monitoring/drift implementations in src/monitoring/, src/wasserstein_drift.py, src/trigger_policy.py, scripts/post_inference_monitoring.py",
                "Drift token scan: drift, ks_stat, wasserstein, zscore",
                "Logging setup in src/logger/__init__.py or logging*.{yaml,yml,ini}",
            ],
            "7. Testing & Robustness": [
                "Test discovery patterns: tests/test_*.py and tests/*_test.py",
                "Fixture reuse check: @pytest.fixture usage",
                "Shared setup check: tests/conftest.py",
                "Pytest config check: pytest.ini or [tool.pytest.ini_options] in pyproject.toml",
                "Coverage config check: .coveragerc or tool.coverage in pyproject.toml",
            ],
            "8. Infrastructure & Tooling": [
                "Packaging metadata: pyproject.toml or setup.py",
                "Docker orchestration: docker-compose.yml + Dockerfile*",
                "CI workflow check: .github/workflows/*.yml",
                "Lint/type tooling hints: .pylintrc, pyproject.toml, setup.cfg",
            ],
            "9. Documentation": [
                "Core docs: README.md, REPRODUCE.md, thesis_execution_plan_mar_jun_2026.md",
                "Topic coverage in docs/**/*.md: PIPELINE, RUNTIME, THESIS",
                "Work history traceability: WORKLOG.md",
                "Sprawl indicators: markdown and script volume for cleanup planning",
            ],
            "10. Scalability & Production Readiness": [
                "Batch script presence in scripts/",
                "Config-driven execution: config/pipeline_config.yaml",
                "Run persistence: artifacts/, logs/, reports/",
                "Serving readiness: src/api/app.py and framework token scan",
            ],
        }
        
    def run_full_audit(self):
        """Execute all audit checks and generate JSON + Markdown reports."""
        print("\n🔍 Starting MLOps Pipeline Audit...\n")
        
        # The 10 core dimensions are scored independently for easy prioritization.
        checks = [
            ("1. Repo Structure & Code Quality", self.audit_code_quality),
            ("2. Reproducibility", self.audit_reproducibility),
            ("3. Data Pipeline & Validation", self.audit_data_pipeline),
            ("4. Model Training & Experiment Tracking", self.audit_training),
            ("5. Inference & Deployment", self.audit_inference_deployment),
            ("6. Monitoring & Drift Detection", self.audit_monitoring),
            ("7. Testing & Robustness", self.audit_testing),
            ("8. Infrastructure & Tooling", self.audit_infrastructure),
            ("9. Documentation", self.audit_documentation),
            ("10. Scalability & Production Readiness", self.audit_scalability),
        ]
        
        for category_name, check_func in checks:
            print(f"Checking {category_name}...")
            score, issues = check_func()
            self.audit_results[category_name] = {"score": score, "issues": issues}
            self.all_issues.extend(issues)
        
        # Dead code + duplication detection
        print("Checking 11. Dead Code & Code Duplication...")
        self.detect_dead_code()

        # Repository sprawl insights feed cleanup guidance in reports.
        self.cleanup_insights = self.analyze_repo_sprawl()
        
        # Equal-weight average across the 10 main dimensions.
        overall_score = sum(v["score"] for v in self.audit_results.values()) / len(self.audit_results)
        
        # Generate reports
        self.generate_json_report(overall_score)
        self.generate_markdown_report(overall_score)
        
        print(f"\n✅ Audit complete! Overall Score: {overall_score:.1f}/10")
        print(f"📊 Reports saved to: {self.reports_dir}")
        
    # ========================================================================
    # CATEGORY 1: REPO STRUCTURE & CODE QUALITY
    # ========================================================================
    
    def audit_code_quality(self) -> Tuple[float, List[str]]:
        """
        Check source-code organization and maintainability hygiene.

        Why this matters:
        - Structure and naming consistency make the pipeline easier to maintain.
        - Docstrings/type hints improve handover quality and thesis defensibility.
        """
        issues: List[str] = []
        score = 10.0

        # Expected high-level modules for a thesis-scale MLOps codebase.
        expected_modules = [
            "api",
            "components",
            "core",
            "data",
            "deployment",
            "entity",
            "inference",
            "logger",
            "monitoring",
            "pipeline",
            "training",
            "utils",
        ]
        for mod in expected_modules:
            mod_path = self.src_dir / mod
            if not mod_path.exists():
                issues.append(f"Missing src/{mod}/ module")
                score -= 0.5

        py_files = list(self.src_dir.rglob("*.py"))
        if not py_files:
            issues.append("No Python files found in src/")
            score = 2.0
            return score, issues

        undocumented_funcs: List[str] = []
        missing_type_hints: List[str] = []

        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        # Public symbols should be documented for maintainability.
                        docstring = ast.get_docstring(node)
                        if not docstring and not node.name.startswith('_'):
                            undocumented_funcs.append(f"{py_file.name}::{node.name}")

                        # Return annotations help static analysis and code review.
                        if isinstance(node, ast.FunctionDef):
                            if not node.returns and not node.name.startswith('_'):
                                missing_type_hints.append(f"{py_file.name}::{node.name}")
            except SyntaxError as e:
                issues.append(f"Syntax error in {py_file}: {e}")
                score -= 1.0

        if undocumented_funcs:
            issues.append(f"Undocumented functions: {len(undocumented_funcs)} found")
            score -= min(1.0, len(undocumented_funcs) * 0.1)

        if missing_type_hints:
            issues.append(f"Missing type hints: {len(missing_type_hints)} functions")
            score -= min(0.5, len(missing_type_hints) * 0.05)

        return max(0.0, score), issues
    
    # ========================================================================
    # CATEGORY 2: REPRODUCIBILITY
    # ========================================================================
    
    def audit_reproducibility(self) -> Tuple[float, List[str]]:
        """
        Check dependency pinning, containers, and deterministic-run hygiene.

        Why this matters:
        - Reproducibility is mandatory for thesis claims and experiment comparison.
        - Environment drift should be minimized across machines.
        """
        issues: List[str] = []
        score = 10.0

        # Accept modern pyproject workflows and classic requirements workflows.
        dependency_files = [
            self.repo_root / "pyproject.toml",
            self.repo_root / "requirements.txt",
            self.repo_root / "config" / "requirements.txt",
            self.repo_root / "config" / "requirements-lock.txt",
        ]
        if not any(path.exists() for path in dependency_files):
            issues.append("No dependency manifest found (pyproject or requirements files)")
            score -= 2.0

        # Encourage lock or pinned file in addition to broad version ranges.
        if not (self.repo_root / "config" / "requirements-lock.txt").exists():
            issues.append("Missing lock-style dependency file (config/requirements-lock.txt)")
            score -= 0.5

        # Dockerfiles can live in root or docker/ in this repository.
        dockerfiles = list(self.repo_root.glob("Dockerfile*")) + \
                      list((self.repo_root / "docker").glob("Dockerfile*"))
        if not dockerfiles:
            issues.append("Missing Dockerfile for containerization")
            score -= 1.5

        if not (self.repo_root / "docker-compose.yml").exists():
            issues.append("Missing docker-compose.yml")
            score -= 0.5

        # Reproduction guide is critical for external verification.
        if not (self.repo_root / "REPRODUCE.md").exists():
            issues.append("Missing REPRODUCE.md")
            score -= 1.0

        # Heuristic seed scan across code paths.
        seed_tokens = ["random.seed(", "np.random.seed(", "tf.random.set_seed(", "torch.manual_seed("]
        seed_found = False
        scan_files = list(self.src_dir.rglob("*.py")) + [self.repo_root / "run_pipeline.py"]
        for py_file in scan_files:
            if not py_file.exists():
                continue
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
            if any(tok.lower() in content for tok in seed_tokens):
                seed_found = True
                break
        if not seed_found:
            issues.append("No explicit random seed control detected in code")
            score -= 0.5

        gitignore = self.repo_root / ".gitignore"
        if not gitignore.exists():
            issues.append("Missing .gitignore")
            score -= 0.5
        else:
            with open(gitignore, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
            if '__pycache__' not in content:
                issues.append(".gitignore missing __pycache__")
                score -= 0.2

        return max(0.0, score), issues
    
    # ========================================================================
    # CATEGORY 3: DATA PIPELINE & VALIDATION
    # ========================================================================
    
    def audit_data_pipeline(self) -> Tuple[float, List[str]]:
        """
        Check ingestion/preprocessing/validation readiness.

        Why this matters:
        - Data issues are the most common source of silent model failure.
        - Validation + preprocessing checks protect downstream training quality.
        """
        issues: List[str] = []
        score = 10.0

        data_dir = self.src_dir / "data"
        if not data_dir.exists():
            issues.append("Missing src/data/ module")
            score -= 1.0

        # Accept both package-style and script-style pipeline layouts.
        preprocess_candidates = [
            self.src_dir / "data" / "preprocessing.py",
            self.src_dir / "preprocess_data.py",
            self.repo_root / "scripts" / "preprocess.py",
        ]
        validation_candidates = [
            self.src_dir / "data" / "validation.py",
            self.src_dir / "data_validator.py",
            self.repo_root / "tests" / "test_data_validation.py",
        ]

        preprocess_file = next((p for p in preprocess_candidates if p.exists()), None)
        validation_file = next((p for p in validation_candidates if p.exists()), None)

        if not preprocess_file:
            issues.append("No preprocessing implementation found (src/data or src/scripts fallback)")
            score -= 1.0
        if not validation_file:
            issues.append("No validation implementation/tests found")
            score -= 1.0

        # Inspect preprocessing content for common data-quality safeguards.
        if preprocess_file:
            with open(preprocess_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
            checks = {
                "NaN handling": any(token in content for token in ["fillna", "dropna", "isnan", "isnull"]),
                "Scaling/Normalization": any(token in content for token in ["scale", "normalize", "standardscaler"]),
                "Windowing/Segmentation": any(token in content for token in ["window", "stride", "segment"]),
            }
            for check_name, found in checks.items():
                if not found:
                    issues.append(f"{preprocess_file.relative_to(self.repo_root)} may miss: {check_name}")
                    score -= 0.4

        # Config should exist to avoid hard-coded paths and constants.
        if not (self.repo_root / "config" / "pipeline_config.yaml").exists():
            issues.append("Missing config/pipeline_config.yaml for data pipeline settings")
            score -= 0.75

        return max(0.0, score), issues
    
    # ========================================================================
    # CATEGORY 4: MODEL TRAINING & EXPERIMENT TRACKING
    # ========================================================================
    
    def audit_training(self) -> Tuple[float, List[str]]:
        """
        Check training orchestration, experiment tracking, and model artifacts.

        Why this matters:
        - Training reproducibility requires config + tracked experiments.
        - Missing artifact paths/checkpoints make rollback impossible.
        """
        issues: List[str] = []
        score = 10.0

        training_dir = self.src_dir / "training"
        if not training_dir.exists():
            issues.append("Missing src/training/ module")
            score -= 1.0

        # Accept either modular trainer or script entrypoint style.
        training_candidates = [
            training_dir / "trainer.py",
            self.src_dir / "train.py",
            self.repo_root / "run_pipeline.py",
        ]
        if not any(path.exists() for path in training_candidates):
            issues.append("No training entrypoint found (trainer.py / src/train.py / run_pipeline.py)")
            score -= 1.5

        config_files = list(self.repo_root.glob("**/pipeline_config*.yaml"))
        if not config_files:
            issues.append("Missing pipeline configuration YAML files")
            score -= 1.0

        # MLflow presence is a strong signal for experiment traceability.
        mlflow_check = False
        for py_file in list(self.src_dir.rglob("*.py")) + [self.repo_root / "run_pipeline.py"]:
            if not py_file.exists():
                continue
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                if 'mlflow' in f.read().lower():
                    mlflow_check = True
                    break
        if not mlflow_check:
            issues.append("MLflow not detected - no experiment tracking found")
            score -= 1.5

        # Model directory is needed for saved checkpoints/fine-tuned artifacts.
        if not (self.repo_root / "models").exists():
            issues.append("Missing models/ directory")
            score -= 0.75

        return max(0.0, score), issues
    
    # ========================================================================
    # CATEGORY 5: INFERENCE & DEPLOYMENT
    # ========================================================================
    
    def audit_inference_deployment(self) -> Tuple[float, List[str]]:
        """
        Check serving layer, inference path, and deployment packaging.

        Why this matters:
        - A trained model is only useful if inference and serving are operational.
        - Deployment assets reduce friction for reproducible demos.
        """
        issues: List[str] = []
        score = 10.0

        inference_dir = self.src_dir / "inference"
        api_dir = self.src_dir / "api"
        deployment_dir = self.src_dir / "deployment"

        # Inference can be package-based or script-based.
        inference_candidates = [
            inference_dir,
            self.src_dir / "run_inference.py",
            self.repo_root / "scripts" / "inference_smoke.py",
        ]
        if not any(path.exists() for path in inference_candidates):
            issues.append("No inference implementation found")
            score -= 1.5

        if not api_dir.exists():
            issues.append("Missing src/api/ module for serving")
            score -= 1.5
        else:
            api_files = list(api_dir.glob("*.py"))
            if not api_files:
                issues.append("src/api/ is empty")
                score -= 1.0
            else:
                api_has_framework = False
                for f in api_files:
                    with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read().lower()
                    if 'fastapi' in content or 'flask' in content:
                        api_has_framework = True
                        break
                if not api_has_framework:
                    issues.append("API framework not detected (FastAPI/Flask)")
                    score -= 0.75

        # Deployment can live in src/deployment or docker/ scripts.
        deployment_candidates = [
            deployment_dir,
            self.src_dir / "deployment_manager.py",
            self.repo_root / "docker" / "Dockerfile.inference",
        ]
        if not any(path.exists() for path in deployment_candidates):
            issues.append("No deployment assets detected")
            score -= 0.75

        return max(0.0, score), issues
    
    # ========================================================================
    # CATEGORY 6: MONITORING & DRIFT DETECTION
    # ========================================================================
    
    def audit_monitoring(self) -> Tuple[float, List[str]]:
        """
        Check observability and drift-surveillance readiness.

        Why this matters:
        - Monitoring catches distribution shifts that degrade model quality.
        - Logging is required for post-hoc debugging and thesis traceability.
        """
        issues: List[str] = []
        score = 10.0

        monitoring_dir = self.src_dir / "monitoring"
        logger_dir = self.src_dir / "logger"

        if not monitoring_dir.exists():
            issues.append("Missing src/monitoring/ module")
            score -= 1.0

        # Drift checks may be implemented outside src/monitoring in this repo.
        drift_candidates = list(monitoring_dir.glob("*.py")) + [
            self.src_dir / "trigger_policy.py",
            self.repo_root / "scripts" / "post_inference_monitoring.py",
        ]
        drift_check = False
        for py_file in drift_candidates:
            if not py_file.exists():
                continue
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
            if any(token in content for token in ["drift", "ks_stat", "wasserstein", "zscore"]):
                drift_check = True
                break
        if not drift_check:
            issues.append("No drift detection logic found in monitoring-related modules")
            score -= 1.0

        if not logger_dir.exists():
            issues.append("Missing src/logger/ module")
            score -= 0.75

        # Logging can be config-file based or code-configured (e.g., src/logger).
        logging_config = (
            list(self.repo_root.glob("**/logging*.yaml"))
            + list(self.repo_root.glob("**/logging*.yml"))
            + list(self.repo_root.glob("**/logging*.ini"))
        )
        logger_module = self.src_dir / "logger" / "__init__.py"
        has_code_logging = False
        if logger_module.exists():
            with open(logger_module, 'r', encoding='utf-8', errors='ignore') as f:
                has_code_logging = "logging" in f.read().lower()
        if not logging_config and not has_code_logging:
            issues.append("No logging configuration detected (file-based or code-based)")
            score -= 0.5

        return max(0.0, score), issues
    
    # ========================================================================
    # CATEGORY 7: TESTING & ROBUSTNESS
    # ========================================================================
    
    def audit_testing(self) -> Tuple[float, List[str]]:
        """
        Check whether automated tests can catch regressions early.

        Why this matters:
        - Good test coverage reduces thesis-risk when you refactor pipeline stages.
        - Shared fixtures/conftest keep test behavior consistent across datasets.
        """
        issues = []
        score = 10.0
        
        if not self.tests_dir.exists():
            issues.append("Missing tests/ directory")
            score -= 3.0
            return max(0.0, score), issues
        
        # Accept both common pytest naming patterns.
        test_files = list(self.tests_dir.glob("test_*.py")) + list(self.tests_dir.glob("*_test.py"))
        if not test_files:
            issues.append("No test files found (test_*.py or *_test.py)")
            score -= 2.0
        else:
            # Fixtures indicate reusable setup and usually improve test quality.
            fixtures_found = False
            for test_file in test_files:
                with open(test_file, 'r', encoding='utf-8', errors='ignore') as f:
                    if '@pytest.fixture' in f.read():
                        fixtures_found = True
                        break
            if not fixtures_found:
                issues.append("No pytest fixtures detected")
                score -= 0.5
        
        if not (self.tests_dir / "conftest.py").exists():
            issues.append("Missing tests/conftest.py")
            score -= 0.5
        
        # Ensure pytest is configured either in pytest.ini or pyproject.toml.
        pytest_ini = self.repo_root / "pytest.ini"
        pyproject = self.repo_root / "pyproject.toml"
        has_pytest_config = pytest_ini.exists()
        if not has_pytest_config and pyproject.exists():
            with open(pyproject, 'r', encoding='utf-8', errors='ignore') as f:
                has_pytest_config = "[tool.pytest.ini_options]" in f.read()
        
        if not has_pytest_config:
            issues.append("No explicit pytest configuration found (pytest.ini or pyproject)")
            score -= 0.5
        
        # Coverage config helps ensure model/data code paths are actually exercised.
        coverage_files = [
            self.repo_root / ".coveragerc",
            self.repo_root / "pyproject.toml",
        ]
        coverage_found = False
        for cfg in coverage_files:
            if cfg.exists():
                with open(cfg, 'r', encoding='utf-8', errors='ignore') as f:
                    if "tool.coverage" in f.read() or "[run]" in f.read():
                        coverage_found = True
                        break
        if not coverage_found:
            issues.append("No coverage configuration found")
            score -= 0.5
        
        return max(0.0, score), issues

    # ========================================================================
    # CATEGORY 8: INFRASTRUCTURE & TOOLING
    # ========================================================================

    def audit_infrastructure(self) -> Tuple[float, List[str]]:
        """
        Check build/deployment/tooling assets.

        Why this matters:
        - Reproducible infra makes experiments repeatable on another machine.
        - CI and container assets reduce manual setup errors.
        """
        issues = []
        score = 10.0

        # Packaging metadata is the baseline for installable/reproducible projects.
        has_pyproject = (self.repo_root / "pyproject.toml").exists()
        has_setup = (self.repo_root / "setup.py").exists()
        if not (has_pyproject or has_setup):
            issues.append("Missing pyproject.toml/setup.py packaging metadata")
            score -= 1.5

        # Compose file usually captures local multi-service orchestration.
        if not (self.repo_root / "docker-compose.yml").exists():
            issues.append("Missing docker-compose.yml")
            score -= 1.0

        # Accept either root Dockerfile or docker/ Dockerfiles.
        docker_candidates = list(self.repo_root.glob("Dockerfile*")) + \
                            list((self.repo_root / "docker").glob("Dockerfile*"))
        if not docker_candidates:
            issues.append("No Dockerfile found (root or docker/)")
            score -= 1.0

        # CI workflow is optional, but strongly recommended for production readiness.
        ci_workflows = list((self.repo_root / ".github" / "workflows").glob("*.y*ml"))
        if not ci_workflows:
            issues.append("No CI workflow found in .github/workflows/")
            score -= 0.75

        # Lint/type config signals maintainability and code health discipline.
        has_lint_cfg = any([
            (self.repo_root / ".pylintrc").exists(),
            (self.repo_root / "pyproject.toml").exists(),
            (self.repo_root / "setup.cfg").exists(),
        ])
        if not has_lint_cfg:
            issues.append("No lint/type-check configuration detected")
            score -= 0.5

        return max(0.0, score), issues

    # ========================================================================
    # CATEGORY 9: DOCUMENTATION
    # ========================================================================

    def audit_documentation(self) -> Tuple[float, List[str]]:
        """
        Check if essential project docs exist.

        Why this matters:
        - Clear docs are required for thesis reproducibility and defense traceability.
        - Missing run/reproduce docs slows future maintenance.
        """
        issues = []
        score = 10.0

        required_docs = [
            "README.md",
            "REPRODUCE.md",
            "thesis_execution_plan_mar_jun_2026.md",
        ]

        for doc_name in required_docs:
            if not (self.repo_root / doc_name).exists():
                issues.append(f"Missing documentation file: {doc_name}")
                score -= 0.75

        docs_dir = self.repo_root / "docs"
        if not docs_dir.exists():
            issues.append("Missing docs/ directory")
            score -= 1.25
        else:
            # Check for architecture/pipeline docs expected in MLOps repositories.
            expected_topics = ["PIPELINE", "RUNTIME", "THESIS"]
            docs_files = [p.name.upper() for p in docs_dir.rglob("*.md")]
            for topic in expected_topics:
                if not any(topic in name for name in docs_files):
                    issues.append(f"docs/: no markdown file covering topic '{topic}'")
                    score -= 0.5

        # Change log / working log helps audit historical experiment decisions.
        if not (self.repo_root / "WORKLOG.md").exists():
            issues.append("Missing WORKLOG.md")
            score -= 0.5

        # Sprawl checks to encourage cleanup and long-term maintainability.
        md_files = self._iter_repo_files(["*.md"])
        script_files = self._iter_repo_files(["scripts/**/*.py"])

        if len(md_files) > 90:
            issues.append(
                f"Documentation sprawl: {len(md_files)} markdown files (consider consolidation/archive policy)"
            )
            score -= 0.5

        if len(script_files) > 45:
            issues.append(
                f"Script sprawl: {len(script_files)} python scripts under scripts/ (consider wrapper/core split cleanup)"
            )
            score -= 0.5

        return max(0.0, score), issues

    # ========================================================================
    # CATEGORY 10: SCALABILITY & PRODUCTION READINESS
    # ========================================================================

    def audit_scalability(self) -> Tuple[float, List[str]]:
        """
        Check operational readiness indicators.

        Why this matters:
        - A thesis pipeline should scale from single runs to repeated batch runs.
        - Production-readiness depends on config-driven behavior and artifacts.
        """
        issues = []
        score = 10.0

        # Batch utility scripts indicate multi-dataset scalability path.
        batch_scripts = [
            self.repo_root / "scripts" / "batch_process_all_datasets.py",
            self.repo_root / "scripts" / "per_dataset_inference.py",
        ]
        if not any(path.exists() for path in batch_scripts):
            issues.append("No batch-processing script detected in scripts/")
            score -= 1.0

        # Config-driven pipelines are easier to scale and tune without code edits.
        if not (self.repo_root / "config" / "pipeline_config.yaml").exists():
            issues.append("Missing config/pipeline_config.yaml")
            score -= 1.25

        # Artifacts directory indicates persisted outputs/versioned runs.
        artifacts_dir = self.repo_root / "artifacts"
        if not artifacts_dir.exists():
            issues.append("Missing artifacts/ directory for run outputs")
            score -= 1.0

        # Basic API readiness check for serving use-cases.
        api_app = self.src_dir / "api" / "app.py"
        if not api_app.exists():
            issues.append("Missing src/api/app.py for serving layer")
            score -= 1.0
        else:
            with open(api_app, 'r', encoding='utf-8', errors='ignore') as f:
                api_content = f.read().lower()
            if "fastapi" not in api_content and "flask" not in api_content:
                issues.append("Serving app exists but FastAPI/Flask not detected")
                score -= 0.5

        # Monitoring outputs/logs indicate observability in practice.
        has_logs = (self.repo_root / "logs").exists()
        has_reports = (self.repo_root / "reports").exists()
        if not (has_logs and has_reports):
            issues.append("Missing logs/ or reports/ directory for operational observability")
            score -= 0.75

        return max(0.0, score), issues

    # ========================================================================
    # CATEGORY 11: DEAD CODE & DUPLICATION
    # ========================================================================

    def detect_dead_code(self):
        """
        Heuristic checks for dead code and copy-paste duplication.

        Why this matters:
        - Dead modules increase maintenance cost and audit noise.
        - Duplicated logic often drifts over time and creates inconsistent behavior.
        """
        self.dead_code_issues = []

        candidate_roots = [path for path in [self.src_dir, self.scripts_dir] if path.exists()]
        py_files: List[Path] = []
        for root in candidate_roots:
            for py_file in root.rglob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                if self._is_excluded(py_file):
                    continue
                py_files.append(py_file)

        if not py_files:
            self.dead_code_issues.append("No Python source files found for dead-code scan")
            return

        module_from_path: Dict[Path, str] = {}
        file_text_cache: Dict[Path, str] = {}
        imported_modules: Set[str] = set()
        executable_modules: Set[str] = set()

        for py_file in py_files:
            rel = py_file.relative_to(self.repo_root).with_suffix("")
            module_name = ".".join(rel.parts)
            module_from_path[py_file] = module_name

            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                    file_text_cache[py_file] = text
            except OSError:
                continue

            if "if __name__ == \"__main__\"" in text or "if __name__ == '__main__'" in text:
                executable_modules.add(module_name)

            try:
                tree = ast.parse(text)
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith("src") or alias.name.startswith("scripts"):
                            imported_modules.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module and (node.module.startswith("src") or node.module.startswith("scripts")):
                        imported_modules.add(node.module)

        # Gather textual references from docs/config/scripts to avoid false dead-code flags.
        reference_files = self._iter_repo_files(
            ["*.md", "*.txt", "*.yaml", "*.yml", "*.toml", "*.ini", "*.json", "*.ps1", "*.sh", "*.bat", "*.py"]
        )

        token_map: Dict[Path, Dict[str, str]] = {}
        for py_file, module_name in module_from_path.items():
            rel = self._normalize_rel(py_file.relative_to(self.repo_root)).lower()
            token_map[py_file] = {
                "rel": rel,
                "name": py_file.name.lower(),
                "module": module_name.lower(),
            }

        referenced_files: Set[Path] = set()
        for ref_file in reference_files:
            try:
                with open(ref_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
            except OSError:
                continue

            for py_file, tokens in token_map.items():
                if ref_file == py_file:
                    continue
                if tokens["rel"] in content:
                    referenced_files.add(py_file)
                    continue
                if f"python {tokens['name']}" in content:
                    referenced_files.add(py_file)
                    continue
                if f"python -m {tokens['module']}" in content:
                    referenced_files.add(py_file)

        for py_file, module_name in module_from_path.items():
            is_imported = any(
                module_name == imported
                or module_name.startswith(imported + ".")
                or imported.startswith(module_name + ".")
                for imported in imported_modules
            )
            is_referenced = py_file in referenced_files
            is_executable = module_name in executable_modules

            in_src = "src" in py_file.parts
            in_scripts = "scripts" in py_file.parts

            if in_src and not is_imported and not is_referenced and not is_executable:
                self.dead_code_issues.append(
                    f"Potential dead module (src, no import/reference): {py_file.relative_to(self.repo_root)}"
                )
            elif in_scripts and not is_imported and not is_referenced and is_executable:
                self.dead_code_issues.append(
                    f"Orphan CLI script candidate (scripts, executable but unreferenced): {py_file.relative_to(self.repo_root)}"
                )
            elif in_scripts and not is_imported and not is_referenced and not is_executable:
                self.dead_code_issues.append(
                    f"Potential dead helper script (scripts, no import/reference): {py_file.relative_to(self.repo_root)}"
                )

        # File-level duplication detector (normalized text, src + scripts).
        normalized_texts: Dict[Path, str] = {}
        for py_file, text in file_text_cache.items():
            lines = []
            for raw in text.splitlines():
                stripped = raw.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                lines.append(stripped)
            normalized_texts[py_file] = "\n".join(lines)

        file_list = list(normalized_texts.keys())
        for i in range(len(file_list)):
            for j in range(i + 1, len(file_list)):
                a = file_list[i]
                b = file_list[j]
                ta = normalized_texts[a]
                tb = normalized_texts[b]

                if len(ta) < 600 or len(tb) < 600:
                    continue

                ratio = SequenceMatcher(None, ta, tb).ratio()
                if ratio >= 0.92:
                    self.dead_code_issues.append(
                        f"High file-level duplication ({ratio:.2f}) between "
                        f"{a.relative_to(self.repo_root)} and {b.relative_to(self.repo_root)}"
                    )

        # Function-level duplication detector for long public functions.
        function_groups: Dict[int, List[str]] = defaultdict(list)
        for py_file, text in file_text_cache.items():
            try:
                tree = ast.parse(text)
            except SyntaxError:
                continue

            lines = text.splitlines()
            for node in ast.walk(tree):
                if not isinstance(node, ast.FunctionDef):
                    continue
                if node.name.startswith("_"):
                    continue
                if not getattr(node, "lineno", None) or not getattr(node, "end_lineno", None):
                    continue

                span = node.end_lineno - node.lineno + 1
                if span < 18:
                    continue

                snippet_lines = lines[node.lineno - 1:node.end_lineno]
                normalized = []
                for raw in snippet_lines:
                    stripped = raw.strip()
                    if not stripped or stripped.startswith("#"):
                        continue
                    normalized.append(re.sub(r"\s+", " ", stripped))
                body = "\n".join(normalized)
                if len(body) < 400:
                    continue

                fingerprint = hash(body)
                function_groups[fingerprint].append(
                    f"{py_file.relative_to(self.repo_root)}::{node.name}"
                )

        duplicate_group_count = 0
        for locations in function_groups.values():
            if len(locations) < 2:
                continue
            duplicate_group_count += 1
            sample = ", ".join(locations[:3])
            more = "" if len(locations) <= 3 else f" (+{len(locations) - 3} more)"
            self.dead_code_issues.append(
                f"Duplicate function logic candidate ({len(locations)} locations): {sample}{more}"
            )
            if duplicate_group_count >= 12:
                self.dead_code_issues.append(
                    "Additional duplicate function groups omitted after 12 entries (see script-level refactor opportunity)"
                )
                break

    def analyze_repo_sprawl(self) -> Dict[str, object]:
        """Collect high-level repository volume signals to drive cleanup guidance."""
        md_files = self._iter_repo_files(["*.md"])
        txt_files = self._iter_repo_files(["*.txt"])
        src_py_files = self._iter_repo_files(["src/**/*.py"])
        scripts_py_files = self._iter_repo_files(["scripts/**/*.py"])

        docs_markdown = [p for p in md_files if "docs" in p.parts]
        thesis_markdown = [p for p in md_files if "thesis" in p.parts]
        root_notes = [
            p for p in (md_files + txt_files)
            if p.parent == self.repo_root
        ]

        stem_map: Dict[str, List[str]] = defaultdict(list)
        for md in md_files:
            rel = self._normalize_rel(md.relative_to(self.repo_root))
            stem_map[md.stem.lower()].append(rel)
        duplicate_stems = {
            stem: paths for stem, paths in stem_map.items() if len(paths) > 1
        }

        noisy_doc_candidates = []
        noisy_pattern = re.compile(r"audit|plan|cleanup|review|wave|report|notes", re.IGNORECASE)
        for md in md_files:
            if noisy_pattern.search(md.name):
                noisy_doc_candidates.append(self._normalize_rel(md.relative_to(self.repo_root)))

        return {
            "markdown_file_count": len(md_files),
            "root_note_file_count": len(root_notes),
            "docs_markdown_count": len(docs_markdown),
            "thesis_markdown_count": len(thesis_markdown),
            "src_python_file_count": len(src_py_files),
            "scripts_python_file_count": len(scripts_py_files),
            "duplicate_markdown_stem_count": len(duplicate_stems),
            "duplicate_markdown_stem_examples": {
                stem: paths[:3] for stem, paths in sorted(
                    duplicate_stems.items(), key=lambda x: len(x[1]), reverse=True
                )[:8]
            },
            "cleanup_named_markdown_examples": sorted(noisy_doc_candidates)[:20],
        }

    # ========================================================================
    # REPORT GENERATION
    # ========================================================================

    def generate_json_report(self, overall_score: float):
        """Write a machine-readable JSON report for downstream automation."""
        report = {
            "timestamp": self.timestamp,
            "repo_root": str(self.repo_root),
            "overall_score": round(overall_score, 2),
            "categories": self.audit_results,
            "checks_per_category": self.category_check_catalog,
            "dead_code_and_duplication": self.dead_code_issues,
            "cleanup_insights": self.cleanup_insights,
            "issue_count": len(self.all_issues) + len(self.dead_code_issues),
        }

        output_file = self.reports_dir / f"audit_{self.timestamp}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

    def generate_markdown_report(self, overall_score: float):
        """
        Write a human-readable Markdown report.

        Why this matters:
        - Easier to share in thesis notes, PRs, or supervisor updates.
        """
        output_file = self.reports_dir / f"audit_{self.timestamp}.md"

        lines = [
            "# MLOps Repository Audit Report",
            "",
            f"- **Timestamp:** {self.timestamp}",
            f"- **Repository:** `{self.repo_root.name}`",
            f"- **Overall Score:** **{overall_score:.1f}/10**",
            "",
            "## Category Scores",
            "",
            "| Category | Score |",
            "|---|---:|",
        ]

        for category_name, payload in self.audit_results.items():
            lines.append(f"| {category_name} | {payload['score']:.1f} |")

        lines.extend([
            "",
            "## Detailed Findings",
            "",
        ])

        for category_name, payload in self.audit_results.items():
            issues = payload.get("issues", [])
            lines.append(f"### {category_name}")
            lines.append("")

            # Always show what the audit checked, even when there are no issues.
            checks_performed = self.category_check_catalog.get(category_name, [])
            if checks_performed:
                lines.append("Checks performed:")
                for check in checks_performed:
                    lines.append(f"- [x] {check}")
                lines.append("")

            lines.append("Findings:")
            if issues:
                for issue in issues:
                    lines.append(f"- [ ] {issue}")
            else:
                lines.append("- [x] No issues detected")
            lines.append("")

        lines.extend([
            "## Dead Code & Duplication",
            "",
            "Scan scope and logic:",
            "- [x] Scanned both src/**/*.py and scripts/**/*.py",
            "- [x] Cross-checked import graph, CLI entrypoints, and textual references in docs/config/code",
            "- [x] Performed file-level and long-function duplication heuristics",
            "",
        ])

        if self.dead_code_issues:
            for issue in self.dead_code_issues:
                lines.append(f"- [ ] {issue}")
        else:
            lines.append("- [x] No major dead-code or duplication signals detected")

        cleanup = self.cleanup_insights or {}
        lines.extend([
            "",
            "## Cleanup Guide (Docs + Scripts)",
            "",
            f"- Markdown files (excluding generated/runtime dirs): {cleanup.get('markdown_file_count', 'n/a')}",
            f"- docs/ markdown files: {cleanup.get('docs_markdown_count', 'n/a')}",
            f"- thesis/ markdown files: {cleanup.get('thesis_markdown_count', 'n/a')}",
            f"- Python files in src/: {cleanup.get('src_python_file_count', 'n/a')}",
            f"- Python files in scripts/: {cleanup.get('scripts_python_file_count', 'n/a')}",
            f"- Duplicate markdown stem groups: {cleanup.get('duplicate_markdown_stem_count', 'n/a')}",
            "",
            "Recommended cleanup actions:",
            "1. Keep one canonical document per topic and archive superseded variants under internal/archive_docs/.",
            "2. Split scripts into two buckets: operational wrappers kept in scripts/, and one-off analysis moved to internal/scripts_archive/.",
            "3. For repeated docs (same stem/name theme), keep newest + reference it from README/docs index, then remove duplicates from active paths.",
            "4. Add a lightweight docs index table (topic -> canonical path -> owner) to reduce future sprawl.",
            "",
        ])

        duplicate_examples = cleanup.get("duplicate_markdown_stem_examples", {})
        if duplicate_examples:
            lines.append("Duplicate markdown stem examples:")
            for stem, paths in duplicate_examples.items():
                joined = ", ".join(paths)
                lines.append(f"- [ ] {stem}: {joined}")
            lines.append("")

        noisy_examples = cleanup.get("cleanup_named_markdown_examples", [])
        if noisy_examples:
            lines.append("Potential cleanup candidates by filename pattern (audit/plan/cleanup/review/notes):")
            for rel in noisy_examples:
                lines.append(f"- [ ] {rel}")
            lines.append("")

        lines.extend([
            "",
            "## Next Steps",
            "",
            "1. Fix high-impact findings first (missing modules, reproducibility gaps, and true dead code).",
            "2. Execute one docs/scripts cleanup pass using the guide above.",
            "3. Re-run this audit after cleanup and track score trend.",
            "",
        ])

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))


def main() -> int:
    """
    CLI entrypoint.

    Usage:
        python mlops_audit.py
    """
    repo_root = Path(__file__).resolve().parent
    auditor = MLOpsAuditor(repo_root)
    auditor.run_full_audit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
