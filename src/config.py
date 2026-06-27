"""
Path Configuration for MLOps Pipeline
Simplified structure without numbered prefixes
"""

from pathlib import Path

# Base directory is the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW = DATA_DIR / "raw"
DATA_PROCESSED = DATA_DIR / "processed"
DATA_PREPARED = DATA_DIR / "prepared"  # Windowed data ready for training

# Source code directories
SRC_DIR = PROJECT_ROOT / "src"

# Model directories
MODELS_DIR = PROJECT_ROOT / "models"
MODELS_PRETRAINED = MODELS_DIR / "pretrained"
# Model D1 final freeze (deployed default since 2026-05-26). The superseded
# Model A package is retained as offline rollback/evidence in
# _archive/presubmission_2026-06-27/models/runtime_contract/model_a_final_20260508.
MODEL_D1_FINAL_DIR = MODELS_DIR / "runtime_contract" / "model_d1_final_20260528"

# API
API_DIR = PROJECT_ROOT / "api"

# Notebooks
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"

# Logs
LOGS_DIR = PROJECT_ROOT / "logs"

# Outputs
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# Docs
DOCS_DIR = PROJECT_ROOT / "docs"

# Config
CONFIG_DIR = PROJECT_ROOT / "config"

# Tests
TESTS_DIR = PROJECT_ROOT / "tests"

# Docker
DOCKER_DIR = PROJECT_ROOT / "docker"

# Specific file paths (commonly used)
LABELED_DATA_FILE = DATA_RAW / "all_users_data_labeled.csv"
PROCESSED_SENSOR_FUSED = DATA_PROCESSED / "sensor_fused_50Hz.csv"
LEGACY_PRETRAINED_MODEL = MODELS_PRETRAINED / "fine_tuned_model_1dcnnbilstm.keras"

# Model D1 final freeze (2026-05-28): ADAMSense-pretrained 1D-CNN + BiLSTM,
# frozen on Garmin users 1-6 and exported from Keras 3 in thesis-mlops. The
# native .keras artifact is the pipeline/API default. The matching scaler and
# baseline must stay in the same runtime_contract folder.
FINAL_MODEL_D1_PATH = MODEL_D1_FINAL_DIR / "finetuned_1DCNNBILSTM_HAR_model.keras"
FINAL_MODEL_D1_SAVEDMODEL_DIR = (
    MODEL_D1_FINAL_DIR / "finetuned_1DCNNBILSTM_HAR_model_savedmodel"
)
FINAL_MODEL_D1_SCALER_JSON = MODEL_D1_FINAL_DIR / "garmin_train_scaler.json"
FINAL_MODEL_D1_SCALER_JOBLIB = MODEL_D1_FINAL_DIR / "garmin_train_scaler.joblib"
FINAL_MODEL_D1_CONTRACT = MODEL_D1_FINAL_DIR / "model_contract.json"

# Default runtime model: Model D1 final freeze (since 2026-05-26).
# Rollback target: the archived Model A package under
# _archive/presubmission_2026-06-27/models/runtime_contract/model_a_final_20260508
# (restore it into models/runtime_contract/ if D1 integration regresses).
PRETRAINED_MODEL = FINAL_MODEL_D1_PATH
DEFAULT_MODEL_PATH = FINAL_MODEL_D1_PATH
MODEL_INFO_JSON = MODELS_PRETRAINED / "model_info.json"
SCALER_CANONICAL = FINAL_MODEL_D1_SCALER_JSON
# Backward-compatible alias used by older modules.
SCALER_CONFIG = SCALER_CANONICAL

# Model configuration
WINDOW_SIZE = 200  # 4 seconds at 50Hz
OVERLAP = 0.5  # 50% overlap
NUM_SENSORS = 6  # Ax, Ay, Az, Gx, Gy, Gz
NUM_CLASSES = 11  # 11 activity types
MILLIG_TO_MS2 = 0.00980665  # exact standard gravity / 1000

# Activity labels (from labeled dataset)
ACTIVITY_LABELS = [
    "ear_rubbing",
    "forehead_rubbing",
    "hair_pulling",
    "hand_scratching",
    "hand_tapping",
    "knuckles_cracking",
    "nail_biting",
    "nape_rubbing",
    "sitting",
    "smoking",
    "standing",
]

# Sensor columns
SENSOR_COLUMNS = ["Ax_w", "Ay_w", "Az_w", "Gx_w", "Gy_w", "Gz_w"]

# Formal exclusion record for the externally-produced pretrained checkpoint.
# Consumers (train.py, inference, evaluation, registration) must treat
# status == "EXCLUDED_*" as a hard gate against using this artifact for any
# reported-number comparison.
PRETRAINED_MODEL_STATUS = {
    "path": "models/pretrained/fine_tuned_model_1dcnnbilstm.keras",
    "status": "EXCLUDED_UNDOCUMENTED_PROVENANCE",
    "reported_accuracy": 0.870,
    "reported_source": "Oleh & Obermaisser, ICTH 2025",
    "exclusion_reason": (
        "Forensic analysis confirms model was trained on a different dataset "
        "than all_users_data_labeled.csv. BN running variance=363.7 encodes "
        "different activation distribution. Az orientation mismatch: "
        "training=-7.2, current=-3.53. 20+ preprocessing configurations "
        "tested, max accuracy 18.5% vs reported 87.0%. Original training "
        "data and scaler not provided. See PIPELINE_DIAGNOSTIC_CHECKLIST.md "
        "and docs/pretrained_model_exclusion_report.md for full evidence."
    ),
    "investigation_date": "2026-04-24",
    "investigation_script": "_archive/scripts/forensic_investigation.py",
}

# data/prepared/config.json is retained only as historical evidence of the
# previous all-users scaler.

# Usage:
# from src.config import PROJECT_ROOT, PRETRAINED_MODEL, WINDOW_SIZE
