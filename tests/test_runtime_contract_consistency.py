from src.config import (
    DEFAULT_MODEL_PATH,
    FINAL_MODEL_A_PATH,
    FINAL_MODEL_A_SCALER_JSON,
    MILLIG_TO_MS2,
    PROJECT_ROOT,
    SCALER_CANONICAL,
)


FINAL_MODEL_REL = "models/runtime_contract/model_a_final_20260508/fine_tuned_clean_model.keras"
FINAL_SCALER_REL = "models/runtime_contract/model_a_final_20260508/garmin_train_scaler.json"
FINAL_BASELINE_REL = (
    "models/runtime_contract/model_a_final_20260508/garmin_train_scaled_baseline.json"
)
LEGACY_MODEL_REL = "models/pretrained/fine_tuned_model_1dcnnbilstm.keras"


def _read_repo_file(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def test_runtime_defaults_use_final_model_a_contract():
    assert DEFAULT_MODEL_PATH == FINAL_MODEL_A_PATH
    assert DEFAULT_MODEL_PATH.as_posix().endswith(FINAL_MODEL_REL)
    assert SCALER_CANONICAL == FINAL_MODEL_A_SCALER_JSON
    assert SCALER_CANONICAL.as_posix().endswith(FINAL_SCALER_REL)


def test_docker_compose_does_not_override_to_legacy_model():
    compose = _read_repo_file("docker-compose.yml")
    assert f"MODEL_PATH=/app/{LEGACY_MODEL_REL}" not in compose
    assert "- MODEL_PATH=" not in compose
    assert f"SCALER_CONFIG_PATH=/app/{FINAL_SCALER_REL}" in compose
    assert f"BASELINE_PATH=/app/{FINAL_BASELINE_REL}" in compose


def test_reproduce_doc_names_final_runtime_prerequisites():
    reproduce = _read_repo_file("REPRODUCE.md")
    assert FINAL_MODEL_REL in reproduce
    assert FINAL_SCALER_REL in reproduce
    assert FINAL_BASELINE_REL in reproduce
    assert LEGACY_MODEL_REL not in reproduce
    assert "models/normalized_baseline.json" not in reproduce


def test_api_upload_path_uses_saved_scaler_not_runtime_fit():
    app_source = _read_repo_file("src/api/app.py")
    assert "from sklearn.preprocessing" not in app_source
    assert "StandardScaler(" not in app_source
    assert ".fit(" not in app_source
    assert ".fit_transform(" not in app_source
    assert "SCALER_CONFIG_PATH" in app_source
    assert "FINAL_MODEL_A_SCALER_JSON" in app_source


def test_unit_conversion_constant_is_shared_by_api_and_preprocess():
    assert MILLIG_TO_MS2 == 0.00980665
    api_source = _read_repo_file("src/api/app.py")
    preprocess_source = _read_repo_file("src/preprocess_data.py")
    assert "_MILLIG_TO_MS2" in api_source
    assert "CONVERSION_FACTOR = MILLIG_TO_MS2" in preprocess_source
    assert "0.00981" not in api_source
    assert "0.00981" not in preprocess_source
