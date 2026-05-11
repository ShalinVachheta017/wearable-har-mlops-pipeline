# Cell 16 - Save final deployable model package and contract

# Goal:
# Save the final model with explicit contract files and provenance metadata.
# This is the package a production pipeline should load.

from datetime import datetime
import hashlib
import joblib

required_for_cell_16 = ["finetune_model"]
missing = [name for name in required_for_cell_16 if name not in globals()]
if missing:
    raise RuntimeError(
        "Run Cell 13 successfully before Cell 16. Missing variables: "
        + ", ".join(missing)
    )


def sha256_file(path, chunk_size=1024 * 1024):
    path = Path(path)
    if not path.exists():
        return None

    digest = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def file_fingerprint(path):
    path = Path(path)
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "size_bytes": None,
            "sha256": None,
            "modified_time": None,
        }

    stat = path.stat()
    return {
        "path": str(path),
        "exists": True,
        "size_bytes": int(stat.st_size),
        "sha256": sha256_file(path),
        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
    }


FINAL_RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
TRAINING_DATE = datetime.now().isoformat()
FINAL_PACKAGE_DIR = MODEL_DIR / f"clean_contract_{SCALER_MODE}_{FINAL_RUN_ID}"
FINAL_PACKAGE_DIR.mkdir(parents=True, exist_ok=True)

final_model_path = FINAL_PACKAGE_DIR / "fine_tuned_clean_model.keras"
finetune_model.save(final_model_path)

label_order_path = FINAL_PACKAGE_DIR / "label_order.json"
feature_order_path = FINAL_PACKAGE_DIR / "feature_order.json"
model_contract_path = FINAL_PACKAGE_DIR / "model_contract.json"
metrics_summary_path = FINAL_PACKAGE_DIR / "metrics_summary.json"
provenance_path = FINAL_PACKAGE_DIR / "training_provenance.json"

with open(label_order_path, "w") as f:
    json.dump(CLASS_NAMES, f, indent=2)

with open(feature_order_path, "w") as f:
    json.dump(COMMON_FEATURES, f, indent=2)

scaler_package_path = None
if production_scaler is not None:
    scaler_package_path = FINAL_PACKAGE_DIR / "scaler.joblib"
    joblib.dump(production_scaler, scaler_package_path)

metrics_summary = {
    "pretrain_val_metrics": globals().get("pretrain_val_metrics"),
    "garmin_val_metrics": globals().get("garmin_val_metrics"),
    "user7_final_metrics": globals().get("user7_final_metrics"),
}

with open(metrics_summary_path, "w") as f:
    json.dump(metrics_summary, f, indent=2)

scaler_fit_scope = "none"
if SCALER_MODE == "train_only_standard":
    scaler_fit_scope = "ADAMSense train windows + Garmin all_users train windows only"

training_provenance = {
    "run_id": FINAL_RUN_ID,
    "training_date": TRAINING_DATE,
    "random_seed": SEED,
    "tensorflow_version": tf.__version__,
    "keras_version": keras.__version__,
    "numpy_version": np.__version__,
    "pandas_version": pd.__version__,
    "scaler_mode": SCALER_MODE,
    "scaler_fit_scope": scaler_fit_scope,
    "augmentation_config": globals().get("AUGMENTATION_CONFIG"),
    "data_fingerprints": {
        "adamsense_pretraining": file_fingerprint(ADAMSENSE_PATH),
        "garmin_all_users_finetuning": file_fingerprint(GARMIN_FINETUNE_PATH),
        "user7_external_test": file_fingerprint(USER7_EXTERNAL_TEST_PATH),
    },
    "model_fingerprint": file_fingerprint(final_model_path),
    "label_order_fingerprint": file_fingerprint(label_order_path),
    "feature_order_fingerprint": file_fingerprint(feature_order_path),
    "scaler_fingerprint": file_fingerprint(scaler_package_path) if scaler_package_path is not None else None,
}

with open(provenance_path, "w") as f:
    json.dump(training_provenance, f, indent=2)

model_contract = {
    "model_name": "fine_tuned_clean_model",
    "model_path": str(final_model_path),
    "input_shape": [WINDOW_SIZE, N_CHANNELS],
    "features": COMMON_FEATURES,
    "feature_order_path": str(feature_order_path),
    "class_names": CLASS_NAMES,
    "label_order_path": str(label_order_path),
    "window_size": WINDOW_SIZE,
    "stride": STRIDE,
    "tensor_layout": TENSOR_LAYOUT,
    "mentor_legacy_reshape": False,
    "scaler_mode": SCALER_MODE,
    "scaler_fit_scope": scaler_fit_scope,
    "augmentation_config": globals().get("AUGMENTATION_CONFIG"),
    "scaler_path": str(scaler_package_path) if scaler_package_path is not None else None,
    "accelerometer_unit": TARGET_ACCEL_UNIT,
    "gyroscope_unit": TARGET_GYRO_UNIT,
    "adamsense_unit_decision": globals().get("unit_conversion_decision"),
    "training_data": {
        "pretraining": str(ADAMSENSE_PATH),
        "fine_tuning": str(GARMIN_FINETUNE_PATH),
        "external_test": str(USER7_EXTERNAL_TEST_PATH),
    },
    "split_summary_path": str(REPORT_DIR / "clean_model_group_split_summary.csv"),
    "metrics_summary_path": str(metrics_summary_path),
    "provenance_path": str(provenance_path),
    "random_seed": SEED,
    "tensorflow_version": tf.__version__,
    "keras_version": keras.__version__,
    "training_date": TRAINING_DATE,
    "production_rule": (
        "Production inference must apply the same feature order, unit conversion, scaler mode, "
        "window size, stride, and normal row-wise tensor layout. Do not use mentor legacy reshape."
    ),
}

with open(model_contract_path, "w") as f:
    json.dump(model_contract, f, indent=2)

# Update provenance after model_contract exists.
training_provenance["model_contract_fingerprint"] = file_fingerprint(model_contract_path)
with open(provenance_path, "w") as f:
    json.dump(training_provenance, f, indent=2)

print("Saved final model:", final_model_path)
print("Saved model contract:", model_contract_path)
print("Saved provenance:", provenance_path)
print("Saved label order:", label_order_path)
print("Saved feature order:", feature_order_path)
print("Saved metrics summary:", metrics_summary_path)
if scaler_package_path is not None:
    print("Saved scaler:", scaler_package_path)
else:
    print("No scaler saved because SCALER_MODE = none")
