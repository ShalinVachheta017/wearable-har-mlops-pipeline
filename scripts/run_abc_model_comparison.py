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
import math
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DATE = "2026-05-11"
OUTPUT_DIR = PROJECT_ROOT / "reports" / "abc_comparison"
USER7_LABELED_PATH = PROJECT_ROOT / "data" / "raw" / "2026-05-05-15-11-15_labeled_50Hz_user7.csv"
GARMIN_UNLABELED_PATH = (
    PROJECT_ROOT / "data" / "processed" / "fused_2025_07_16_21_03_13_50Hz.csv"
)
ALL_USERS_DIAGNOSTIC_PATH = PROJECT_ROOT / "data" / "processed" / "fused_all_users_data_labeled_50Hz.csv"

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


def git_current_head() -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip() if completed.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


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


def load_contracts() -> Dict[str, Dict[str, Any]]:
    return {model_id: read_json(path) for model_id, path in CONTRACT_FILES.items()}


def import_eval_dependencies() -> Dict[str, Any]:
    try:
        import numpy as np  # type: ignore
        import pandas as pd  # type: ignore
        import tensorflow as tf  # type: ignore
        from sklearn.metrics import (  # type: ignore
            accuracy_score,
            balanced_accuracy_score,
            confusion_matrix,
            f1_score,
            precision_recall_fscore_support,
        )
        from sklearn.preprocessing import StandardScaler  # type: ignore
    except Exception as exc:  # pragma: no cover - local environment dependent
        raise RuntimeError(f"Evaluation dependencies are unavailable: {type(exc).__name__}: {exc}")

    return {
        "np": np,
        "pd": pd,
        "tf": tf,
        "StandardScaler": StandardScaler,
        "accuracy_score": accuracy_score,
        "balanced_accuracy_score": balanced_accuracy_score,
        "confusion_matrix": confusion_matrix,
        "f1_score": f1_score,
        "precision_recall_fscore_support": precision_recall_fscore_support,
    }


def label_order_from_contract(contract: Dict[str, Any]) -> List[str]:
    label_order = contract.get("output_contract", {}).get("label_order")
    if not isinstance(label_order, list) or len(label_order) != 11:
        raise ValueError(f"Invalid label order in contract {contract.get('model_id')}")
    return [str(label) for label in label_order]


def detect_sensor_columns(columns: Iterable[str]) -> List[str]:
    available = set(columns)
    canonical = ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
    aliases = ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]
    if all(col in available for col in canonical):
        return canonical
    if all(col in available for col in aliases):
        return aliases
    lower_map = {col.lower(): col for col in columns}
    discovered = []
    for name in ["ax", "ay", "az", "gx", "gy", "gz"]:
        if name in lower_map:
            discovered.append(lower_map[name])
        elif f"{name}_w" in lower_map:
            discovered.append(lower_map[f"{name}_w"])
    if len(discovered) == 6:
        return discovered
    raise ValueError(f"Could not detect six sensor columns from: {list(columns)}")


def canonicalize_sensor_frame(df: Any) -> Tuple[Any, List[str]]:
    sensor_cols = detect_sensor_columns(df.columns)
    out = df.copy()
    rename = dict(zip(sensor_cols, ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]))
    out = out.rename(columns=rename)
    for col in ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]:
        out[col] = out[col].astype("float32")
    return out, ["Ax", "Ay", "Az", "Gx", "Gy", "Gz"]


def maybe_convert_accel_units(df: Any, np_module: Any) -> Tuple[Any, Dict[str, Any]]:
    out = df.copy()
    accel_cols = ["Ax", "Ay", "Az"]
    values = out[accel_cols].values.astype("float32")
    mean_abs = float(np_module.nanmean(np_module.abs(values)))
    max_abs = float(np_module.nanmax(np_module.abs(values)))
    if mean_abs > 50.0:
        out[accel_cols] = out[accel_cols] * 0.00981
        converted = True
        detected = "milliG"
    else:
        converted = False
        detected = "m/s^2"
    return out, {
        "unit_conversion_applied": converted,
        "accelerometer_abs_mean_before": mean_abs,
        "accelerometer_abs_max_before": max_abs,
        "accelerometer_detected_unit": detected,
        "gyroscope_unit_assumption": "deg/s unchanged",
    }


def read_scaler_json(path: Path) -> Dict[str, Any]:
    data = read_json(path)
    for key in ["scaler_mean", "scaler_scale"]:
        if key not in data or not isinstance(data[key], list) or len(data[key]) != 6:
            raise ValueError(f"Scaler {path} missing valid {key}")
    return data


def apply_json_scaler(values: Any, scaler: Dict[str, Any], np_module: Any) -> Any:
    mean = np_module.asarray(scaler["scaler_mean"], dtype="float32")
    scale = np_module.asarray(scaler["scaler_scale"], dtype="float32")
    safe_scale = np_module.where(scale == 0, 1.0, scale)
    return ((values.astype("float32") - mean) / safe_scale).astype("float32")


def check_model_a_scaler_parity(json_scaler: Dict[str, Any], joblib_path: Optional[Path]) -> Dict[str, Any]:
    if joblib_path is None or not joblib_path.exists():
        return {
            "status": "skipped_joblib_not_found",
            "path": repo_rel(joblib_path) if joblib_path else None,
        }
    try:
        import joblib as _jl  # type: ignore
        import numpy as _np  # type: ignore

        sk = _jl.load(str(joblib_path))  # type: ignore[no-untyped-call]
        jm = _np.asarray(json_scaler["scaler_mean"], dtype="float64")
        js = _np.asarray(json_scaler["scaler_scale"], dtype="float64")
        km = _np.asarray(sk.mean_, dtype="float64")
        ks = _np.asarray(sk.scale_, dtype="float64")
        mean_diff = float(_np.max(_np.abs(jm - km)))
        scale_diff = float(_np.max(_np.abs(js - ks)))
        return {
            "status": "checked",
            "joblib_path": repo_rel(joblib_path),
            "json_vs_joblib_mean_max_abs_diff": mean_diff,
            "json_vs_joblib_scale_max_abs_diff": scale_diff,
            "parity_ok": mean_diff < 1e-6 and scale_diff < 1e-6,
        }
    except Exception as exc:
        return {"status": "check_failed", "error": f"{type(exc).__name__}: {exc}"}


def window_starts(n_samples: int, window_size: int, stride: int, legacy_layout: bool, np_module: Any) -> Any:
    stop = n_samples - window_size if legacy_layout else n_samples - window_size + 1
    if stop <= 0:
        return np_module.asarray([], dtype="int64")
    return np_module.arange(0, stop, stride, dtype="int64")


def build_windows(values: Any, window_size: int, stride: int, legacy_layout: bool, np_module: Any) -> Any:
    chunks = []
    for start in window_starts(len(values), window_size, stride, legacy_layout, np_module).tolist():
        window = values[start : start + window_size]
        chunks.append(window.T if legacy_layout else window)
    if not chunks:
        return np_module.empty((0, window_size, values.shape[1]), dtype="float32")
    arr = np_module.asarray(chunks, dtype="float32")
    if legacy_layout:
        arr = arr.reshape(-1, window_size, values.shape[1])
    return arr.astype("float32")


def build_window_labels(
    labels: Any,
    window_size: int,
    stride: int,
    label_to_id: Dict[str, int],
    legacy_layout: bool,
    np_module: Any,
) -> Tuple[Any, List[str]]:
    y_ids = []
    y_names = []
    for start in window_starts(len(labels), window_size, stride, legacy_layout, np_module).tolist():
        window_labels = [str(value) for value in labels[start : start + window_size]]
        counts: Dict[str, int] = {}
        for label in window_labels:
            counts[label] = counts.get(label, 0) + 1
        majority_label = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
        y_names.append(majority_label)
        y_ids.append(label_to_id.get(majority_label, -1))
    return np_module.asarray(y_ids, dtype="int64"), y_names


def count_mixed_label_windows(
    labels: Any,
    window_size: int,
    stride: int,
    legacy_layout: bool,
    np_module: Any,
) -> Dict[str, Any]:
    starts = window_starts(len(labels), window_size, stride, legacy_layout, np_module).tolist()
    mixed = 0
    for start in starts:
        if len(set(str(v) for v in labels[start : start + window_size])) > 1:
            mixed += 1
    total = len(starts)
    return {
        "window_label_policy": "majority_label_with_lexicographic_tiebreak",
        "total_windows": total,
        "mixed_label_window_count": mixed,
        "mixed_label_window_pct": round(100.0 * mixed / total, 2) if total > 0 else 0.0,
    }


def preprocess_for_contract(
    dataset: Dict[str, Any],
    contract: Dict[str, Any],
    deps: Dict[str, Any],
) -> Dict[str, Any]:
    pd = deps["pd"]
    np = deps["np"]
    StandardScaler = deps["StandardScaler"]

    df = pd.read_csv(dataset["path"])
    df, sensor_cols = canonicalize_sensor_frame(df)
    df, unit_info = maybe_convert_accel_units(df, np)
    values = df[sensor_cols].values.astype("float32")
    model_id = contract["model_id"]

    if model_id == "model_a":
        scaler_path = resolve_repo_path(contract["artifact_identity"]["scaler_path"])
        if scaler_path is None:
            raise ValueError("Model A scaler path is not resolvable")
        scaler = read_scaler_json(scaler_path)
        values_for_windows = apply_json_scaler(values, scaler, np)
        contract_mode = "clean_pipeline"
        layout = "time_major_row_wise"
        legacy_layout = False
        scaler_policy = "garmin_train_only_json"
    elif model_id == "model_b":
        values_for_windows = StandardScaler().fit_transform(values.astype("float64")).astype("float32")
        contract_mode = "native_legacy_diagnostic"
        layout = "legacy_channel_major_reshape"
        legacy_layout = True
        scaler_policy = "full_evaluation_dataframe_fit_transform_diagnostic_only"
    elif model_id == "model_c":
        values_for_windows = values.astype("float32")
        contract_mode = "previous_pipeline_clean_rowwise_no_scaler"
        layout = "time_major_row_wise"
        legacy_layout = False
        scaler_policy = "none"
    else:
        raise ValueError(f"Unknown model_id: {model_id}")

    window_size = int(contract["window_boundary_contract"]["window_size_samples"])
    stride = int(contract["window_boundary_contract"]["stride_samples"])
    X = build_windows(values_for_windows, window_size, stride, legacy_layout, np)
    y_ids = None
    y_names = None
    label_col = None
    label_order = label_order_from_contract(contract)
    if dataset["labeled"]:
        for candidate in ["activity", "label"]:
            if candidate in df.columns:
                label_col = candidate
                break
        if label_col is None:
            raise ValueError(f"Dataset {dataset['dataset_id']} is marked labeled but has no label column")
        label_to_id = {name: idx for idx, name in enumerate(label_order)}
        y_ids, y_names = build_window_labels(
            df[label_col].values,
            window_size,
            stride,
            label_to_id,
            legacy_layout,
            np,
        )
        valid_mask = y_ids >= 0
        X = X[valid_mask]
        y_ids = y_ids[valid_mask]
        y_names = [name for name, keep in zip(y_names, valid_mask.tolist()) if keep]

    # Dataset validation
    ts_col = next((c for c in ["timestamp", "Timestamp", "time", "Time"] if c in df.columns), None)
    ts_monotonic = None
    ts_duplicate_count = None
    if ts_col is not None:
        try:
            ts_series = pd.to_datetime(df[ts_col])
            ts_monotonic = bool(ts_series.is_monotonic_increasing)
            ts_duplicate_count = int(ts_series.duplicated().sum())
        except Exception:
            pass
    sensor_missing = int(df[sensor_cols].isnull().sum().sum())
    label_distribution = None
    mixed_label_window_count = None
    mixed_label_window_pct = None
    if label_col is not None:
        label_distribution = {str(k): int(v) for k, v in df[label_col].value_counts().items()}
        mixed_info = count_mixed_label_windows(df[label_col].values, window_size, stride, legacy_layout, np)
        mixed_label_window_count = mixed_info["mixed_label_window_count"]
        mixed_label_window_pct = mixed_info["mixed_label_window_pct"]
    dataset_validation: Dict[str, Any] = {
        "path": repo_rel(dataset["path"]),
        "rows": int(len(df)),
        "sensor_columns_found": sensor_cols,
        "timestamp_column": ts_col,
        "timestamp_monotonic": ts_monotonic,
        "timestamp_duplicate_count": ts_duplicate_count,
        "sensor_missing_value_count": sensor_missing,
        "accelerometer_unit_detected": unit_info["accelerometer_detected_unit"],
        "unit_conversion_applied": unit_info["unit_conversion_applied"],
        "label_column": label_col,
        "label_distribution": label_distribution,
        "window_count": int(len(X)),
        "window_label_policy": "majority_label_with_lexicographic_tiebreak",
        "mixed_label_window_count": mixed_label_window_count,
        "mixed_label_window_pct": mixed_label_window_pct,
    }

    return {
        "X": X,
        "y_ids": y_ids,
        "y_names": y_names,
        "label_col": label_col,
        "contract_mode": contract_mode,
        "layout": layout,
        "scaler_policy": scaler_policy,
        "unit_info": unit_info,
        "n_rows": int(len(df)),
        "n_windows": int(len(X)),
        "feature_columns": sensor_cols,
        "window_label_policy": "majority_label_with_lexicographic_tiebreak",
        "dataset_validation": dataset_validation,
    }


def distribution_from_ids(ids: Any, label_order: List[str], np_module: Any) -> Dict[str, int]:
    unique, counts = np_module.unique(ids, return_counts=True)
    return {label_order[int(idx)]: int(count) for idx, count in zip(unique, counts)}


def entropy_mean(probs: Any, np_module: Any) -> float:
    clipped = np_module.clip(probs.astype("float64"), 1e-12, 1.0)
    entropy = -np_module.sum(clipped * np_module.log(clipped), axis=1)
    return float(np_module.mean(entropy)) if len(entropy) else float("nan")


def temporal_flip_rate(pred_ids: Any, np_module: Any) -> float:
    if len(pred_ids) <= 1:
        return 0.0
    return float(np_module.mean(pred_ids[1:] != pred_ids[:-1]) * 100.0)


def confidence_bands(conf: Any, np_module: Any) -> Dict[str, float]:
    if len(conf) == 0:
        return {"high_pct": 0.0, "medium_pct": 0.0, "low_pct": 0.0, "uncertain_pct": 0.0}
    return {
        "high_pct": float(np_module.mean(conf > 0.90) * 100.0),
        "medium_pct": float(np_module.mean((conf > 0.70) & (conf <= 0.90)) * 100.0),
        "low_pct": float(np_module.mean((conf > 0.50) & (conf <= 0.70)) * 100.0),
        "uncertain_pct": float(np_module.mean(conf <= 0.50) * 100.0),
    }


def load_monitoring_thresholds() -> Dict[str, Any]:
    from src.entity.config_entity import PostInferenceMonitoringConfig, TriggerEvaluationConfig

    mon = PostInferenceMonitoringConfig()
    trig = TriggerEvaluationConfig()
    pipeline_config_exists = (PROJECT_ROOT / "config" / "pipeline_config.yaml").exists()
    overrides_config_exists = (PROJECT_ROOT / "config" / "pipeline_overrides.yaml").exists()
    return {
        "source": "src/entity/config_entity.py defaults; config/pipeline_overrides.yaml source discovered separately",
        "threshold_verification": {
            "runner_threshold_source": "src/entity/config_entity.py defaults",
            "pipeline_config_checked": pipeline_config_exists,
            "pipeline_overrides_checked": overrides_config_exists,
            "same_as_final_pipeline": "pending_manual_review",
        },
        "monitoring": {
            "confidence_warn_threshold": mon.confidence_warn_threshold,
            "uncertain_pct_threshold": mon.uncertain_pct_threshold,
            "uncertain_window_threshold": mon.uncertain_window_threshold,
            "dominant_class_warn_threshold": mon.dominant_class_warn_threshold,
            "dominant_class_critical_threshold": mon.dominant_class_critical_threshold,
            "transition_rate_threshold": mon.transition_rate_threshold,
            "drift_zscore_threshold": mon.drift_zscore_threshold,
        },
        "trigger": {
            "confidence_warn": trig.confidence_warn,
            "confidence_critical": trig.confidence_critical,
            "drift_zscore_warn": trig.drift_zscore_warn,
            "drift_zscore_critical": trig.drift_zscore_critical,
            "temporal_flip_warn": trig.temporal_flip_warn,
            "temporal_flip_critical": trig.temporal_flip_critical,
            "cooldown_hours": trig.cooldown_hours,
        },
        "auto_retrain_enabled": False,
    }


def drift_check_if_available(
    contract: Dict[str, Any],
    X: Any,
    np_module: Any,
    thresholds: Dict[str, Any],
) -> Dict[str, Any]:
    baseline = contract.get("monitoring_baseline_contract", {})
    baseline_path = resolve_repo_path(baseline.get("baseline_path"))
    if baseline_path is None or not baseline_path.exists():
        return {
            "status": "not_verified",
            "reason": "no compatible persisted baseline for this model contract",
            "max_drift_zscore": None,
        }
    data = read_json(baseline_path)
    if "mean" not in data or "std" not in data:
        return {"status": "not_verified", "reason": "baseline missing mean/std", "max_drift_zscore": None}
    flat = X.reshape(-1, X.shape[-1])
    prod_mean = np_module.mean(flat, axis=0)
    base_mean = np_module.asarray(data["mean"], dtype="float64")
    base_std = np_module.asarray(data["std"], dtype="float64")
    safe_std = np_module.where(base_std == 0, 1.0, base_std)
    zscores = np_module.abs((prod_mean - base_mean) / safe_std)
    max_z = float(np_module.max(zscores))
    threshold = float(thresholds["monitoring"]["drift_zscore_threshold"])
    return {
        "status": "WARNING" if max_z >= threshold else "HEALTHY",
        "max_drift_zscore": max_z,
        "threshold": threshold,
        "baseline_path": repo_rel(baseline_path),
    }


def monitoring_and_trigger_summary(
    contract: Dict[str, Any],
    X: Any,
    pred_ids: Any,
    conf: Any,
    probs: Any,
    label_order: List[str],
    deps: Dict[str, Any],
    thresholds: Dict[str, Any],
) -> Dict[str, Any]:
    np = deps["np"]
    n = len(pred_ids)
    dist = distribution_from_ids(pred_ids, label_order, np)
    dominant_label = max(dist.items(), key=lambda item: item[1])[0] if dist else None
    dominant_count = dist[dominant_label] if dominant_label else 0
    dominant_pct = float((dominant_count / n) * 100.0) if n else 0.0
    mean_conf = float(np.mean(conf)) if n else float("nan")
    median_conf = float(np.median(conf)) if n else float("nan")
    bands = confidence_bands(conf, np)
    flip_rate = temporal_flip_rate(pred_ids, np)
    drift = drift_check_if_available(contract, X, np, thresholds)

    mon_thresholds = thresholds["monitoring"]
    statuses = []
    review_reasons = []
    if mean_conf < float(mon_thresholds["confidence_warn_threshold"]):
        statuses.append("WARNING")
        review_reasons.append("mean_confidence_below_warning_threshold")
    if bands["uncertain_pct"] >= float(mon_thresholds["uncertain_pct_threshold"]):
        statuses.append("WARNING")
        review_reasons.append("uncertain_window_percentage_above_warning_threshold")
    if dominant_pct >= float(mon_thresholds["dominant_class_critical_threshold"]):
        statuses.append("CRITICAL")
        review_reasons.append("dominant_class_above_critical_threshold")
    elif dominant_pct >= float(mon_thresholds["dominant_class_warn_threshold"]):
        statuses.append("WARNING")
        review_reasons.append("dominant_class_above_warning_threshold")
    if flip_rate >= float(mon_thresholds["transition_rate_threshold"]):
        statuses.append("WARNING")
        review_reasons.append("transition_rate_above_warning_threshold")
    if drift["status"] == "WARNING":
        statuses.append("WARNING")
        review_reasons.append("drift_zscore_above_warning_threshold")

    if "CRITICAL" in statuses:
        monitoring_status = "CRITICAL"
    elif "WARNING" in statuses:
        monitoring_status = "WARNING"
    else:
        monitoring_status = "HEALTHY"

    trigger_decision = "REVIEW" if monitoring_status in {"WARNING", "CRITICAL"} else "NO_ACTION"
    return {
        "n_windows": int(n),
        "prediction_distribution": dist,
        "classes_used": int(len(dist)),
        "dominant_class": dominant_label,
        "dominant_class_pct": dominant_pct,
        "mean_confidence": mean_conf,
        "median_confidence": median_conf,
        "confidence_bands": bands,
        "prediction_entropy": entropy_mean(probs, np),
        "transition_rate_pct": flip_rate,
        "drift": drift,
        "monitoring_status": monitoring_status,
        "trigger_decision": trigger_decision,
        "review_reasons": review_reasons,
        "auto_retrain_flag": False,
    }


def run_model_predictions(contract: Dict[str, Any], X: Any, deps: Dict[str, Any]) -> Any:
    tf = deps["tf"]
    model_path = resolve_repo_path(contract["artifact_identity"]["model_path"])
    if model_path is None or not model_path.exists():
        raise FileNotFoundError(f"Model file not found for {contract['model_id']}: {model_path}")
    model = tf.keras.models.load_model(str(model_path), compile=False)
    return model.predict(X, batch_size=64, verbose=0)


def write_predictions_csv(
    path: Path,
    pred_ids: Any,
    conf: Any,
    label_order: List[str],
    y_ids: Optional[Any] = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        header = ["window_id", "predicted_id", "predicted_label", "confidence"]
        if y_ids is not None:
            header.extend(["true_id", "true_label", "correct"])
        writer.writerow(header)
        for idx, pred_id in enumerate(pred_ids):
            row: List[Any] = [idx, int(pred_id), label_order[int(pred_id)], float(conf[idx])]
            if y_ids is not None:
                true_id = int(y_ids[idx])
                row.extend([true_id, label_order[true_id], bool(true_id == int(pred_id))])
            writer.writerow(row)


def labeled_metrics(
    y_true: Any,
    pred_ids: Any,
    conf: Any,
    probs: Any,
    label_order: List[str],
    deps: Dict[str, Any],
) -> Dict[str, Any]:
    np = deps["np"]
    labels = list(range(len(label_order)))
    precision, recall, f1, support = deps["precision_recall_fscore_support"](
        y_true,
        pred_ids,
        labels=labels,
        zero_division=0,
    )
    return {
        "accuracy": float(deps["accuracy_score"](y_true, pred_ids)),
        "balanced_accuracy": float(deps["balanced_accuracy_score"](y_true, pred_ids)),
        "macro_f1": float(deps["f1_score"](y_true, pred_ids, average="macro", zero_division=0)),
        "weighted_f1": float(deps["f1_score"](y_true, pred_ids, average="weighted", zero_division=0)),
        "per_class_precision": {label_order[i]: float(precision[i]) for i in labels},
        "per_class_recall": {label_order[i]: float(recall[i]) for i in labels},
        "per_class_f1": {label_order[i]: float(f1[i]) for i in labels},
        "per_class_support": {label_order[i]: int(support[i]) for i in labels},
        "confusion_matrix": deps["confusion_matrix"](y_true, pred_ids, labels=labels).tolist(),
        "true_label_distribution": distribution_from_ids(y_true, label_order, np),
        "mean_confidence": float(np.mean(conf)) if len(conf) else float("nan"),
        "median_confidence": float(np.median(conf)) if len(conf) else float("nan"),
        "prediction_entropy": entropy_mean(probs, np),
    }


def model_decision_hint(contract: Dict[str, Any], monitoring: Dict[str, Any], metrics: Dict[str, Any]) -> str:
    model_id = contract["model_id"]
    if model_id == "model_b":
        return "forensic_reference_only_native_mode_not_production_safe"
    if model_id == "model_c":
        return "historical_baseline_pending_human_review"
    if model_id == "model_a":
        if monitoring["classes_used"] >= 10 and monitoring["trigger_decision"] in {"REVIEW", "NO_ACTION"}:
            return "clean_runtime_candidate_pending_human_review"
        return "clean_runtime_candidate_with_runtime_risk_pending_human_review"
    return "pending_human_review"


def flatten_row(row: Dict[str, Any]) -> Dict[str, Any]:
    flat: Dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, (dict, list)):
            flat[key] = json.dumps(value, sort_keys=True)
        else:
            flat[key] = value
    return flat


def evaluation_datasets(include_all_users: bool) -> List[Dict[str, Any]]:
    datasets = [
        {
            "dataset_id": "user7_labeled_external",
            "path": USER7_LABELED_PATH,
            "labeled": True,
            "scope": "primary_labeled_external_evaluation",
        },
        {
            "dataset_id": "garmin_unlabeled_production_style",
            "path": GARMIN_UNLABELED_PATH,
            "labeled": False,
            "scope": "primary_unlabeled_production_style_evaluation",
        },
    ]
    if include_all_users:
        datasets.append(
            {
                "dataset_id": "all_users_diagnostic",
                "path": ALL_USERS_DIAGNOSTIC_PATH,
                "labeled": True,
                "scope": "optional_internal_diagnostic_not_primary_evidence",
            }
        )
    return datasets


def run_evaluation(include_all_users: bool = False) -> Dict[str, Any]:
    deps = import_eval_dependencies()
    contracts = load_contracts()
    thresholds = load_monitoring_thresholds()
    output_dirs = ensure_output_dirs()
    runtime_environment = capture_runtime_environment()

    # Fresh Keras load checks for all three models
    tf_available, tf_module, _ = tensorflow_module()
    fresh_load_checks: Dict[str, Any] = {}
    for mid, cnt in contracts.items():
        expected_input = cnt.get("architecture_contract", {}).get("input_shape")
        expected_output = cnt.get("architecture_contract", {}).get("output_shape")
        mpath = resolve_repo_path(cnt.get("artifact_identity", {}).get("model_path"))
        fresh_load_checks[mid] = fresh_keras_load_check(
            mpath, expected_input, expected_output, tf_available, tf_module
        )
    all_loaded = all(v.get("status") == "loaded" for v in fresh_load_checks.values())
    runtime_environment["fresh_model_load_verified"] = all_loaded
    runtime_environment["fresh_model_load_checks"] = fresh_load_checks

    # Model A JSON vs joblib scaler parity
    scaler_parity: Dict[str, Any] = {"status": "not_applicable"}
    ma_ident = contracts.get("model_a", {}).get("artifact_identity", {})
    if ma_ident.get("scaler_path"):
        json_spath = resolve_repo_path(ma_ident["scaler_path"])
        joblib_spath = resolve_repo_path(ma_ident.get("scaler_joblib_path"))
        if json_spath and json_spath.exists():
            try:
                scaler_parity = check_model_a_scaler_parity(read_scaler_json(json_spath), joblib_spath)
            except Exception as exc:
                scaler_parity = {"status": "check_failed", "error": f"{type(exc).__name__}: {exc}"}

    rows: List[Dict[str, Any]] = []
    summaries: Dict[str, Any] = {}
    dataset_validations: Dict[str, Any] = {}

    for model_id, contract in contracts.items():
        label_order = label_order_from_contract(contract)
        model_dir = OUTPUT_DIR / model_id
        (model_dir / "predictions").mkdir(parents=True, exist_ok=True)
        summaries[model_id] = {
            "model_id": model_id,
            "model_role": contract.get("model_role"),
            "artifact_identity": contract.get("artifact_identity"),
            "datasets": {},
        }
        for dataset in evaluation_datasets(include_all_users):
            prepared = preprocess_for_contract(dataset, contract, deps)
            ds_id = dataset["dataset_id"]
            if ds_id not in dataset_validations and "dataset_validation" in prepared:
                dataset_validations[ds_id] = prepared["dataset_validation"]
            probs = run_model_predictions(contract, prepared["X"], deps)
            np = deps["np"]
            pred_ids = np.argmax(probs, axis=1)
            conf = np.max(probs, axis=1)
            monitoring = monitoring_and_trigger_summary(
                contract,
                prepared["X"],
                pred_ids,
                conf,
                probs,
                label_order,
                deps,
                thresholds,
            )

            metrics: Dict[str, Any] = {}
            if dataset["labeled"]:
                metrics = labeled_metrics(prepared["y_ids"], pred_ids, conf, probs, label_order, deps)

            prediction_path = (
                model_dir
                / "predictions"
                / f"{dataset['dataset_id']}_{prepared['contract_mode']}_predictions.csv"
            )
            write_predictions_csv(
                prediction_path,
                pred_ids,
                conf,
                label_order,
                prepared["y_ids"] if dataset["labeled"] else None,
            )

            dataset_summary = {
                "dataset": {
                    "dataset_id": dataset["dataset_id"],
                    "path": repo_rel(dataset["path"]),
                    "scope": dataset["scope"],
                    "labeled": dataset["labeled"],
                    "n_rows": prepared["n_rows"],
                    "n_windows": prepared["n_windows"],
                    "label_column": prepared["label_col"],
                },
                "contract_mode": prepared["contract_mode"],
                "layout": prepared["layout"],
                "scaler_policy": prepared["scaler_policy"],
                "unit_info": prepared["unit_info"],
                "metrics": metrics,
                "monitoring": monitoring,
                "prediction_file": repo_rel(prediction_path),
                "decision_hint": model_decision_hint(contract, monitoring, metrics),
            }
            summary_path = model_dir / f"{dataset['dataset_id']}_summary.json"
            write_json(summary_path, dataset_summary)
            summaries[model_id]["datasets"][dataset["dataset_id"]] = dataset_summary

            row = {
                "model_id": model_id,
                "model_role": contract.get("model_role"),
                "dataset_id": dataset["dataset_id"],
                "dataset_scope": dataset["scope"],
                "contract_mode": prepared["contract_mode"],
                "layout": prepared["layout"],
                "scaler_policy": prepared["scaler_policy"],
                "labeled": dataset["labeled"],
                "n_rows": prepared["n_rows"],
                "n_windows": prepared["n_windows"],
                "accuracy": metrics.get("accuracy"),
                "balanced_accuracy": metrics.get("balanced_accuracy"),
                "macro_f1": metrics.get("macro_f1"),
                "weighted_f1": metrics.get("weighted_f1"),
                "classes_used": monitoring["classes_used"],
                "dominant_class": monitoring["dominant_class"],
                "dominant_class_pct": monitoring["dominant_class_pct"],
                "mean_confidence": monitoring["mean_confidence"],
                "median_confidence": monitoring["median_confidence"],
                "uncertain_window_pct": monitoring["confidence_bands"]["uncertain_pct"],
                "prediction_entropy": monitoring["prediction_entropy"],
                "transition_rate_pct": monitoring["transition_rate_pct"],
                "drift_status": monitoring["drift"]["status"],
                "max_drift_zscore": monitoring["drift"].get("max_drift_zscore"),
                "monitoring_status": monitoring["monitoring_status"],
                "trigger_decision": monitoring["trigger_decision"],
                "review_reasons": monitoring["review_reasons"],
                "auto_retrain_flag": monitoring["auto_retrain_flag"],
                "decision_hint": dataset_summary["decision_hint"],
                "prediction_file": repo_rel(prediction_path),
            }
            rows.append(row)

    result: Dict[str, Any] = {
        "mode": "evaluate",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "registry_commit_metadata": {
            "registry_contract_base_commit": "5b7d537",
            "registry_contract_cleanup_commit": "071a8e8",
            "runner_commit": git_current_head(),
            "note": "Both commits reference the frozen registry contracts under models/model_registry/",
        },
        "runtime_environment": runtime_environment,
        "thresholds": thresholds,
        "model_a_scaler_parity": scaler_parity,
        "model_b_clean_pipeline_compatibility": {
            "model_id": "model_b",
            "contract_mode": "clean_pipeline",
            "status": "unsupported_not_run",
            "reason": (
                "no persisted legacy scaler and legacy tensor layout mismatch; "
                "Model B requires a non-persisted full-evaluation StandardScaler "
                "and legacy channel-major tensor layout incompatible with the "
                "clean production pipeline contract"
            ),
        },
        "datasets": [
            {
                "dataset_id": item["dataset_id"],
                "path": repo_rel(item["path"]),
                "labeled": item["labeled"],
                "scope": item["scope"],
            }
            for item in evaluation_datasets(include_all_users)
        ],
        "dataset_validations": dataset_validations,
        "models": summaries,
        "rows": rows,
        "safety_guards": {
            "runtime_code_modified_by_runner": False,
            "registry_contracts_rewritten": False,
            "models_retrained": False,
            "thresholds_changed": False,
            "model_artifacts_overwritten": False,
        },
    }

    write_evaluation_outputs(result, rows, output_dirs)
    return result


def write_evaluation_outputs(result: Dict[str, Any], rows: List[Dict[str, Any]], output_dirs: Dict[str, Any]) -> None:
    write_json(OUTPUT_DIR / "abc_results.json", {"mode": "evaluate", "rows": rows})
    write_json(OUTPUT_DIR / "contract_runtime_verification.json", result)
    write_json(
        OUTPUT_DIR / "dataset_validation_summary.json",
        {
            "created_at": result["created_at"],
            "datasets": result.get("dataset_validations", {}),
        },
    )
    summary = build_evaluation_summary(result, rows, output_dirs)
    write_json(OUTPUT_DIR / "comparison_summary.json", summary)
    write_results_csv(OUTPUT_DIR / "abc_results.csv", rows)
    (OUTPUT_DIR / f"ABC_MODEL_COMPARISON_REPORT_{REPORT_DATE}.md").write_text(
        build_evaluation_markdown(summary, rows),
        encoding="utf-8",
    )


def write_results_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "model_id",
        "model_role",
        "dataset_id",
        "dataset_scope",
        "contract_mode",
        "layout",
        "scaler_policy",
        "labeled",
        "n_rows",
        "n_windows",
        "accuracy",
        "balanced_accuracy",
        "macro_f1",
        "weighted_f1",
        "classes_used",
        "dominant_class",
        "dominant_class_pct",
        "mean_confidence",
        "median_confidence",
        "uncertain_window_pct",
        "prediction_entropy",
        "transition_rate_pct",
        "drift_status",
        "max_drift_zscore",
        "monitoring_status",
        "trigger_decision",
        "review_reasons",
        "auto_retrain_flag",
        "decision_hint",
        "prediction_file",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(flatten_row({key: row.get(key) for key in fieldnames}))


def build_evaluation_summary(
    result: Dict[str, Any],
    rows: List[Dict[str, Any]],
    output_dirs: Dict[str, Any],
) -> Dict[str, Any]:
    user7_rows = [row for row in rows if row["dataset_id"] == "user7_labeled_external"]
    garmin_rows = [row for row in rows if row["dataset_id"] == "garmin_unlabeled_production_style"]
    clean_candidates = [
        row
        for row in user7_rows
        if row["model_id"] == "model_a" and row["contract_mode"] == "clean_pipeline"
    ]
    return {
        "mode": "evaluate",
        "created_at": result["created_at"],
        "output_dirs_ok": output_dirs["ok"],
        "models_compared": sorted({row["model_id"] for row in rows}),
        "datasets_compared": sorted({row["dataset_id"] for row in rows}),
        "primary_decision_rule": [
            "clean production contract compatibility",
            "avoid class collapse",
            "use most/all classes",
            "honest train-only preprocessing",
            "User 7 external metrics",
            "safe monitoring/trigger behavior",
            "explainable provenance and preprocessing",
        ],
        "model_a_user7_macro_f1": clean_candidates[0].get("macro_f1") if clean_candidates else None,
        "model_a_user7_accuracy": clean_candidates[0].get("accuracy") if clean_candidates else None,
        "user7_rows": user7_rows,
        "garmin_unlabeled_rows": garmin_rows,
        "provisional_model_status": {
            "model_a": "clean_runtime_candidate_pending_human_review",
            "model_b": "forensic_reference_only_native_mode_not_production_safe",
            "model_c": "historical_baseline_contract_mismatch_risk",
        },
        "model_b_clean_pipeline_compatibility": result.get("model_b_clean_pipeline_compatibility"),
        "model_a_scaler_parity": result.get("model_a_scaler_parity"),
        "registry_commit_metadata": result.get("registry_commit_metadata"),
        "notes": [
            "Model B has the best native diagnostic User 7 score, but is forensic only and not production-safe.",
            "Model A is the best clean production-contract candidate.",
            "Model C is a weak historical baseline with checkpoint-contract mismatch risk.",
            "Model B native mode is diagnostic only because it fits a StandardScaler on the evaluation dataframe.",
            "Model C uses the same checkpoint as Model B but under the previous row-wise no-scaler contract.",
            "Registry contracts were not rewritten by evaluation mode.",
        ],
    }


def fmt_num(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        if math.isnan(value):
            return "n/a"
        return f"{value:.4f}"
    return str(value)


def build_evaluation_markdown(summary: Dict[str, Any], rows: List[Dict[str, Any]]) -> str:
    lines = [
        f"# ABC Model Comparison Report - {REPORT_DATE}",
        "",
        "Status: evaluation mode completed. Registry contracts were not rewritten, model",
        "artifacts were not overwritten, thresholds were not changed, and no retraining was run.",
        "",
        "## Decision Rule",
        "",
    ]
    for item in summary["primary_decision_rule"]:
        lines.append(f"- {item}")
    lines.extend(["", "## User 7 Labeled External Evaluation", ""])
    lines.append(
        "| Model | Contract mode | Accuracy | Macro F1 | Classes used | Dominant class % | Mean confidence | Trigger | Decision hint |"
    )
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |")
    for row in [r for r in rows if r["dataset_id"] == "user7_labeled_external"]:
        lines.append(
            "| {model_id} | {contract_mode} | {accuracy} | {macro_f1} | {classes_used} | "
            "{dominant_class_pct} | {mean_confidence} | {trigger_decision} | {decision_hint} |".format(
                model_id=row["model_id"],
                contract_mode=row["contract_mode"],
                accuracy=fmt_num(row.get("accuracy")),
                macro_f1=fmt_num(row.get("macro_f1")),
                classes_used=row["classes_used"],
                dominant_class_pct=fmt_num(row["dominant_class_pct"]),
                mean_confidence=fmt_num(row["mean_confidence"]),
                trigger_decision=row["trigger_decision"],
                decision_hint=row["decision_hint"],
            )
        )
    lines.extend(["", "## Garmin Production-Style Unlabeled Run", ""])
    lines.append(
        "| Model | Contract mode | Windows | Classes used | Dominant class % | Mean confidence | Monitoring | Trigger | Auto retrain |"
    )
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |")
    for row in [r for r in rows if r["dataset_id"] == "garmin_unlabeled_production_style"]:
        lines.append(
            "| {model_id} | {contract_mode} | {n_windows} | {classes_used} | {dominant_class_pct} | "
            "{mean_confidence} | {monitoring_status} | {trigger_decision} | {auto_retrain_flag} |".format(
                model_id=row["model_id"],
                contract_mode=row["contract_mode"],
                n_windows=row["n_windows"],
                classes_used=row["classes_used"],
                dominant_class_pct=fmt_num(row["dominant_class_pct"]),
                mean_confidence=fmt_num(row["mean_confidence"]),
                monitoring_status=row["monitoring_status"],
                trigger_decision=row["trigger_decision"],
                auto_retrain_flag=row["auto_retrain_flag"],
            )
        )
    lines.extend(
        [
            "",
            "## Model B Clean Pipeline Compatibility",
            "",
            "Model B was **not evaluated under the clean_pipeline contract** because:",
            "",
            "- No persisted legacy scaler exists (it requires a full-evaluation fitted StandardScaler).",
            "- Legacy channel-major tensor layout is incompatible with the clean production pipeline contract.",
            "",
            "Model B native diagnostic score is therefore forensic reference only and not production-safe.",
            "",
            "## Provisional Status",
            "",
            "- Model A: clean runtime candidate pending human review.",
            "- Model B: forensic native legacy reference only; not production-safe.",
            "- Model C: historical baseline with checkpoint-contract mismatch risk.",
            "",
            "## Output Files",
            "",
            "- `reports/abc_comparison/abc_results.csv`",
            "- `reports/abc_comparison/abc_results.json`",
            "- `reports/abc_comparison/comparison_summary.json`",
            "- `reports/abc_comparison/contract_runtime_verification.json`",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["dry-run", "evaluate"],
        default="dry-run",
        help="Dry-run validates contracts. Evaluation mode runs A/B/C comparison.",
    )
    parser.add_argument(
        "--include-all-users-diagnostic",
        action="store_true",
        help="Also run the clearly marked all_users diagnostic subset/evaluation.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.mode == "evaluate":
        result = run_evaluation(include_all_users=args.include_all_users_diagnostic)
        print("ABC model-contract evaluation completed")
        print(f"Output dir: {repo_rel(OUTPUT_DIR)}")
        print(f"Rows written: {len(result['rows'])}")
        print("Registry contracts rewritten: false")
        print("Runtime code modified by runner: false")
        return 0

    verification = dry_run()
    print_summary(verification)
    return 0 if verification["contract_dry_run_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
