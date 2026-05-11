"""ABC model-contract comparison runner.

Dry-run mode validates the frozen ABC registry contracts and writes runtime
verification artifacts under reports/abc_comparison/. It does not modify
runtime code, retrain models, change thresholds, overwrite model artifacts, or
rewrite the registry contracts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DATE = "2026-05-11"
OUTPUT_DIR = PROJECT_ROOT / "reports" / "abc_comparison"

CONTRACT_FILES = {
    "model_a": PROJECT_ROOT / "models" / "model_registry" / "model_a_clean_contract.json",
    "model_b": PROJECT_ROOT / "models" / "model_registry" / "model_b_legacy_contract.json",
    "model_c": PROJECT_ROOT / "models" / "model_registry" / "model_c_previous_pipeline_contract.json",
}

REQUIRED_SECTIONS = [
    "artifact_identity",
    "runtime_environment",
    "architecture_contract",
    "data_input_contract",
    "unit_contract",
    "input_layout_summary",
    "input_layout_compatible_with_final_pipeline",
    "input_tensor_contract",
    "window_boundary_contract",
    "scaler_contract",
    "monitoring_baseline_contract",
    "preprocessing_order",
    "preprocessing_risks",
    "output_contract",
    "evaluation_protocol",
    "monitoring_trigger_contract",
    "model_card_summary",
    "known_contract_risks",
    "verification_status",
]

PATH_SENTINELS = {
    "",
    "none",
    "not_applicable",
    "not_applicable_not_persisted",
    "not_persisted",
    "not_verified",
    "pending_abc_runner",
}


def repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def resolve_repo_path(value: Any) -> Optional[Path]:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if normalized.lower() in PATH_SENTINELS:
        return None
    path = Path(normalized)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def package_version(dist_name: str) -> str:
    try:
        return importlib.metadata.version(dist_name)
    except importlib.metadata.PackageNotFoundError:
        return "not_installed"


def capture_runtime_environment() -> Dict[str, Any]:
    tensorflow_available = False
    tensorflow_version = "not_installed"
    keras_version = package_version("keras")
    try:
        import tensorflow as tf  # type: ignore

        tensorflow_available = True
        tensorflow_version = getattr(tf, "__version__", "unknown")
        keras_version = getattr(tf.keras, "__version__", keras_version)
    except Exception as exc:  # pragma: no cover - depends on local environment
        tensorflow_version = f"not_available: {type(exc).__name__}: {exc}"

    return {
        "status": "captured_by_dry_run",
        "python_version": sys.version.replace("\n", " "),
        "tensorflow_available": tensorflow_available,
        "tensorflow_version": tensorflow_version,
        "keras_version": keras_version,
        "numpy_version": package_version("numpy"),
        "scikit_learn_version": package_version("scikit-learn"),
        "pandas_version": package_version("pandas"),
        "os": platform.platform(),
        "cuda_available": "not_verified_without_tensorflow"
        if not tensorflow_available
        else "pending_tensorflow_device_query",
        "execution_device": "not_verified",
        "fresh_model_load_verified": False,
        "environment_capture_source": "scripts/run_abc_model_comparison.py --mode dry-run",
    }


def tensorflow_module() -> Tuple[bool, Optional[Any], str]:
    try:
        import tensorflow as tf  # type: ignore

        return True, tf, getattr(tf, "__version__", "unknown")
    except Exception as exc:  # pragma: no cover - depends on local environment
        return False, None, f"{type(exc).__name__}: {exc}"


def normalize_shape(shape: Any) -> Any:
    if isinstance(shape, tuple):
        return [normalize_shape(x) for x in shape]
    if isinstance(shape, list):
        return [normalize_shape(x) for x in shape]
    return shape


def fresh_keras_load_check(
    model_path: Optional[Path],
    expected_input_shape: Any,
    expected_output_shape: Any,
    tf_available: bool,
    tf_module: Optional[Any],
) -> Dict[str, Any]:
    if model_path is None:
        return {"status": "skipped_no_model_path"}
    if not model_path.exists():
        return {"status": "skipped_model_missing", "path": repo_rel(model_path)}
    if not tf_available or tf_module is None:
        return {"status": "skipped_tensorflow_not_available", "path": repo_rel(model_path)}

    try:
        model = tf_module.keras.models.load_model(str(model_path), compile=False)
        input_shape = normalize_shape(model.input_shape)
        output_shape = normalize_shape(model.output_shape)
        return {
            "status": "loaded",
            "path": repo_rel(model_path),
            "input_shape": input_shape,
            "output_shape": output_shape,
            "parameter_count": int(model.count_params()),
            "input_shape_matches_contract": input_shape == expected_input_shape,
            "output_shape_matches_contract": output_shape == expected_output_shape,
        }
    except Exception as exc:  # pragma: no cover - depends on local environment/model
        return {
            "status": "load_failed",
            "path": repo_rel(model_path),
            "error": f"{type(exc).__name__}: {exc}",
        }


def check_optional_artifact(
    contract: Dict[str, Any],
    field_name: str,
    hash_field_name: str,
    allowed_missing: Iterable[str],
) -> Dict[str, Any]:
    identity = contract.get("artifact_identity", {})
    value = identity.get(field_name)
    expected_hash = identity.get(hash_field_name)
    allowed = set(allowed_missing)

    if isinstance(value, str) and value.lower() in allowed:
        return {
            "status": "allowed_missing",
            "field": field_name,
            "value": value,
            "expected_hash": expected_hash,
        }

    path = resolve_repo_path(value)
    if path is None:
        return {
            "status": "missing_unexpected",
            "field": field_name,
            "value": value,
            "expected_hash": expected_hash,
        }
    if not path.exists():
        return {
            "status": "file_missing",
            "field": field_name,
            "path": repo_rel(path),
            "expected_hash": expected_hash,
        }

    actual_hash = sha256_file(path)
    hash_matches = (
        isinstance(expected_hash, str)
        and expected_hash not in PATH_SENTINELS
        and actual_hash.upper() == expected_hash.upper()
    )
    return {
        "status": "file_found",
        "field": field_name,
        "path": repo_rel(path),
        "expected_hash": expected_hash,
        "actual_sha256": actual_hash,
        "hash_matches_contract": hash_matches,
    }


def label_order_check(contract: Dict[str, Any]) -> Dict[str, Any]:
    output_contract = contract.get("output_contract", {})
    label_order = output_contract.get("label_order")
    source = output_contract.get("label_order_source") or contract.get("artifact_identity", {}).get(
        "label_map_source"
    )
    result = {
        "status": "not_verified",
        "label_count": 0,
        "unique_label_count": 0,
        "label_order_source": source,
        "source_file_readable": False,
    }

    if isinstance(label_order, list):
        result["label_count"] = len(label_order)
        result["unique_label_count"] = len(set(label_order))
        result["status"] = (
            "verified_from_contract_values"
            if len(label_order) == 11 and len(set(label_order)) == 11
            else "invalid_contract_values"
        )

    source_path = resolve_repo_path(source)
    if source_path and source_path.exists():
        result["source_file_readable"] = True
        try:
            read_json(source_path)
            result["source_file_json_valid"] = True
        except Exception as exc:
            result["source_file_json_valid"] = False
            result["source_file_error"] = f"{type(exc).__name__}: {exc}"

    return result


def contract_check(
    model_id: str,
    contract_path: Path,
    tf_available: bool,
    tf_module: Optional[Any],
) -> Dict[str, Any]:
    check: Dict[str, Any] = {
        "model_id": model_id,
        "contract_path": repo_rel(contract_path),
        "contract_load_status": "not_run",
        "required_sections": {},
        "artifact_checks": {},
        "label_order_check": {},
        "fresh_keras_load": {},
        "critical_errors": [],
        "warnings": [],
    }

    try:
        contract = read_json(contract_path)
        check["contract_load_status"] = "loaded"
    except Exception as exc:
        check["contract_load_status"] = "failed"
        check["critical_errors"].append(f"contract_json_load_failed: {type(exc).__name__}: {exc}")
        return check

    missing_sections = [section for section in REQUIRED_SECTIONS if section not in contract]
    check["required_sections"] = {
        "missing": missing_sections,
        "all_present": not missing_sections,
    }
    if missing_sections:
        check["critical_errors"].append(f"missing_required_sections: {missing_sections}")

    model_check = check_optional_artifact(
        contract,
        field_name="model_path",
        hash_field_name="model_sha256",
        allowed_missing=set(),
    )
    check["artifact_checks"]["model"] = model_check
    if model_check["status"] != "file_found":
        check["critical_errors"].append(f"model_artifact_not_found_or_invalid: {model_check}")
    elif model_check.get("hash_matches_contract") is False:
        check["critical_errors"].append("model_sha256_mismatch")

    scaler_allowed = {"none", "not_persisted", "not_applicable", "not_applicable_not_persisted"}
    scaler_check = check_optional_artifact(
        contract,
        field_name="scaler_path",
        hash_field_name="scaler_sha256",
        allowed_missing=scaler_allowed,
    )
    check["artifact_checks"]["scaler"] = scaler_check
    if scaler_check["status"] in {"file_missing", "missing_unexpected"}:
        check["critical_errors"].append(f"scaler_artifact_invalid: {scaler_check}")
    elif scaler_check["status"] == "file_found" and scaler_check.get("hash_matches_contract") is False:
        check["critical_errors"].append("scaler_sha256_mismatch")

    baseline_contract = contract.get("monitoring_baseline_contract", {})
    baseline_value = baseline_contract.get("baseline_path")
    baseline_hash = baseline_contract.get("baseline_sha256")
    identity = {
        "artifact_identity": {
            "baseline_path": baseline_value,
            "baseline_sha256": baseline_hash,
        }
    }
    baseline_check = check_optional_artifact(
        identity,
        field_name="baseline_path",
        hash_field_name="baseline_sha256",
        allowed_missing={"not_verified", "pending_abc_runner", "none", "not_applicable"},
    )
    check["artifact_checks"]["monitoring_baseline"] = baseline_check
    if baseline_check["status"] in {"file_missing", "missing_unexpected"}:
        check["warnings"].append(f"monitoring_baseline_not_verified: {baseline_check}")
    elif baseline_check["status"] == "file_found" and baseline_check.get("hash_matches_contract") is False:
        check["critical_errors"].append("monitoring_baseline_sha256_mismatch")

    label_check = label_order_check(contract)
    check["label_order_check"] = label_check
    if label_check.get("status") == "invalid_contract_values":
        check["critical_errors"].append("label_order_invalid")

    expected_input = contract.get("architecture_contract", {}).get("input_shape")
    expected_output = contract.get("architecture_contract", {}).get("output_shape")
    model_path = resolve_repo_path(contract.get("artifact_identity", {}).get("model_path"))
    check["fresh_keras_load"] = fresh_keras_load_check(
        model_path,
        expected_input,
        expected_output,
        tf_available,
        tf_module,
    )

    return check


def check_threshold_sources() -> Dict[str, Any]:
    paths = [
        PROJECT_ROOT / "config" / "pipeline_config.yaml",
        PROJECT_ROOT / "config" / "pipeline_overrides.yaml",
        PROJECT_ROOT / "src" / "entity" / "config_entity.py",
    ]
    result: Dict[str, Any] = {
        "status": "pending_value_verification",
        "files": [],
        "values_loaded": False,
        "note": "Dry-run verifies source files exist; threshold values remain contract-pending until evaluation mode.",
    }
    for path in paths:
        result["files"].append(
            {
                "path": repo_rel(path),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else None,
            }
        )
    result["all_sources_found"] = all(item["exists"] for item in result["files"])
    return result


def ensure_output_dirs() -> Dict[str, Any]:
    dirs = [
        OUTPUT_DIR,
        OUTPUT_DIR / "model_a",
        OUTPUT_DIR / "model_a" / "predictions",
        OUTPUT_DIR / "model_b",
        OUTPUT_DIR / "model_b" / "predictions",
        OUTPUT_DIR / "model_c",
        OUTPUT_DIR / "model_c" / "predictions",
    ]
    result = {"created_or_exists": [], "errors": []}
    for path in dirs:
        try:
            path.mkdir(parents=True, exist_ok=True)
            result["created_or_exists"].append(repo_rel(path))
        except Exception as exc:
            result["errors"].append({"path": repo_rel(path), "error": f"{type(exc).__name__}: {exc}"})
    result["ok"] = not result["errors"]
    return result


def git_status(paths: List[str]) -> Dict[str, Any]:
    cmd = ["git", "status", "--short", "--"] + paths
    try:
        completed = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        return {
            "command": " ".join(cmd),
            "returncode": completed.returncode,
            "lines": lines,
            "clean": completed.returncode == 0 and not lines,
            "stderr": completed.stderr.strip(),
        }
    except Exception as exc:
        return {
            "command": " ".join(cmd),
            "returncode": "not_run",
            "lines": [],
            "clean": False,
            "stderr": f"{type(exc).__name__}: {exc}",
        }


def write_dry_run_outputs(verification: Dict[str, Any]) -> None:
    write_json(OUTPUT_DIR / "contract_runtime_verification.json", verification)

    summary = {
        "mode": "dry_run",
        "created_at": verification["created_at"],
        "contracts_checked": list(verification["contracts"].keys()),
        "critical_error_count": sum(
            len(item.get("critical_errors", [])) for item in verification["contracts"].values()
        ),
        "warning_count": sum(len(item.get("warnings", [])) for item in verification["contracts"].values()),
        "tensorflow_available": verification["runtime_environment"]["tensorflow_available"],
        "threshold_sources_found": verification["monitoring_threshold_sources"]["all_sources_found"],
        "output_dirs_ok": verification["output_directories"]["ok"],
        "runtime_code_clean": verification["runtime_code_status"]["clean"],
        "contract_dry_run_passed": verification["contract_dry_run_passed"],
        "ready_for_evaluation_mode": verification["ready_for_evaluation_mode"],
        "evaluation_mode_blockers": verification["evaluation_mode_blockers"],
        "note": "Dry-run only; no predictions or model evaluation were executed.",
    }
    write_json(OUTPUT_DIR / "comparison_summary.json", summary)

    results_json = {
        "mode": "dry_run",
        "evaluations": [],
        "note": "No ABC metrics are produced in dry-run mode.",
    }
    write_json(OUTPUT_DIR / "abc_results.json", results_json)

    with (OUTPUT_DIR / "abc_results.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "mode",
                "model_id",
                "evaluation_dataset",
                "contract_mode",
                "status",
                "note",
            ]
        )
        writer.writerow(
            [
                "dry_run",
                "all",
                "not_run",
                "not_run",
                "no_metrics",
                "Dry-run only; full ABC evaluation mode is not implemented yet.",
            ]
        )

    report = build_markdown_report(verification, summary)
    (OUTPUT_DIR / f"ABC_MODEL_COMPARISON_REPORT_{REPORT_DATE}.md").write_text(
        report,
        encoding="utf-8",
    )


def build_markdown_report(verification: Dict[str, Any], summary: Dict[str, Any]) -> str:
    lines = [
        f"# ABC Model Comparison Dry-Run Report - {REPORT_DATE}",
        "",
        "Status: dry-run validation only. No model evaluation, retraining, threshold change,",
        "runtime-code modification, or registry-contract rewrite was performed.",
        "",
        "## Summary",
        "",
        f"- Contracts checked: {', '.join(summary['contracts_checked'])}",
        f"- Critical errors: {summary['critical_error_count']}",
        f"- Warnings: {summary['warning_count']}",
        f"- TensorFlow available: {summary['tensorflow_available']}",
        f"- Threshold sources found: {summary['threshold_sources_found']}",
        f"- Output directories ready: {summary['output_dirs_ok']}",
        f"- Runtime code clean: {summary['runtime_code_clean']}",
        f"- Contract dry-run passed: {summary['contract_dry_run_passed']}",
        f"- Ready for evaluation mode: {summary['ready_for_evaluation_mode']}",
        f"- Evaluation-mode blockers: {summary['evaluation_mode_blockers']}",
        "",
        "## Contract Checks",
        "",
    ]

    for model_id, item in verification["contracts"].items():
        lines.extend(
            [
                f"### {model_id}",
                "",
                f"- Contract load: {item['contract_load_status']}",
                f"- Required sections present: {item['required_sections'].get('all_present')}",
                f"- Model artifact: {item['artifact_checks']['model']['status']}",
                f"- Scaler artifact: {item['artifact_checks']['scaler']['status']}",
                f"- Label order: {item['label_order_check']['status']}",
                f"- Fresh Keras load: {item['fresh_keras_load']['status']}",
                f"- Critical errors: {len(item.get('critical_errors', []))}",
                f"- Warnings: {len(item.get('warnings', []))}",
                "",
            ]
        )

    lines.extend(
        [
            "## Next Step",
            "",
            "Implement evaluation mode only after dry-run findings are acceptable. Evaluation mode",
            "should write results under `reports/abc_comparison/` and should not rewrite frozen",
            "registry contracts unless explicitly requested.",
            "",
        ]
    )
    return "\n".join(lines)


def dry_run() -> Dict[str, Any]:
    output_dirs = ensure_output_dirs()
    runtime_environment = capture_runtime_environment()
    tf_available, tf_module, tf_status = tensorflow_module()

    contracts: Dict[str, Any] = {}
    for model_id, contract_path in CONTRACT_FILES.items():
        contracts[model_id] = contract_check(model_id, contract_path, tf_available, tf_module)

    runtime_code_status = git_status(["src", "config", "docker", "run_pipeline.py"])
    script_status = git_status(["scripts/run_abc_model_comparison.py"])
    report_status = git_status(["reports/abc_comparison"])
    threshold_sources = check_threshold_sources()

    critical_error_count = sum(len(item.get("critical_errors", [])) for item in contracts.values())
    contract_dry_run_passed = (
        critical_error_count == 0
        and output_dirs["ok"]
        and bool(threshold_sources["all_sources_found"])
        and bool(runtime_code_status["clean"])
    )
    evaluation_mode_blockers: List[str] = []
    if not tf_available:
        evaluation_mode_blockers.append("tensorflow_not_available")
    ready_for_evaluation_mode = contract_dry_run_passed and not evaluation_mode_blockers

    verification = {
        "mode": "dry_run",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(PROJECT_ROOT),
        "contract_files": {k: repo_rel(v) for k, v in CONTRACT_FILES.items()},
        "runtime_environment": runtime_environment,
        "tensorflow_import": {
            "available": tf_available,
            "status": tf_status,
        },
        "contracts": contracts,
        "monitoring_threshold_sources": threshold_sources,
        "output_directories": output_dirs,
        "runtime_code_status": runtime_code_status,
        "script_status": script_status,
        "report_status": report_status,
        "contract_dry_run_passed": contract_dry_run_passed,
        "ready_for_evaluation_mode": ready_for_evaluation_mode,
        "evaluation_mode_blockers": evaluation_mode_blockers,
        "safety_guards": {
            "runtime_code_modified_by_runner": not runtime_code_status["clean"],
            "registry_contracts_rewritten": False,
            "models_retrained": False,
            "thresholds_changed": False,
            "model_artifacts_overwritten": False,
        },
    }
    write_dry_run_outputs(verification)
    return verification


def print_summary(verification: Dict[str, Any]) -> None:
    print("ABC model-contract dry-run")
    print(f"Output dir: {repo_rel(OUTPUT_DIR)}")
    print(f"TensorFlow available: {verification['tensorflow_import']['available']}")
    print(f"Threshold sources found: {verification['monitoring_threshold_sources']['all_sources_found']}")
    print(f"Output dirs OK: {verification['output_directories']['ok']}")
    print(f"Runtime code clean: {verification['runtime_code_status']['clean']}")
    print(f"Contract dry-run passed: {verification['contract_dry_run_passed']}")
    print(f"Ready for evaluation mode: {verification['ready_for_evaluation_mode']}")
    print(f"Evaluation-mode blockers: {verification['evaluation_mode_blockers']}")
    print()
    for model_id, item in verification["contracts"].items():
        errors = item.get("critical_errors", [])
        warnings = item.get("warnings", [])
        print(
            f"{model_id}: sections_ok={item['required_sections'].get('all_present')} "
            f"model={item['artifact_checks']['model']['status']} "
            f"scaler={item['artifact_checks']['scaler']['status']} "
            f"label_order={item['label_order_check']['status']} "
            f"keras_load={item['fresh_keras_load']['status']} "
            f"errors={len(errors)} warnings={len(warnings)}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["dry-run", "evaluate"],
        default="dry-run",
        help="Dry-run validates contracts. Evaluation mode is intentionally not implemented yet.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.mode == "evaluate":
        print(
            "Evaluation mode is not implemented yet. Run --mode dry-run first and review "
            "reports/abc_comparison/contract_runtime_verification.json.",
            file=sys.stderr,
        )
        return 2

    verification = dry_run()
    print_summary(verification)
    return 0 if verification["contract_dry_run_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
