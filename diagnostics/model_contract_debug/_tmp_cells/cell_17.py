# Cell 17 - Write final thesis/MLOps training report

# Goal:
# Create one readable markdown report for the clean production-contract model.
# This cell does not train and does not modify production code.

from datetime import datetime


def safe_get(name, default=None):
    return globals().get(name, default)


def format_metric_block(title, metrics):
    if metrics is None:
        return f"## {title}\n\nNot available yet.\n"

    lines = [f"## {title}", ""]
    for key, value in metrics.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def shape_line(name, X, y=None):
    if X is None:
        return f"- `{name}`: not available"
    if y is None:
        return f"- `{name}`: X `{X.shape}`"
    return f"- `{name}`: X `{X.shape}`, y `{y.shape}`"


def dataframe_to_markdown_or_text(df):
    try:
        return df.to_markdown(index=False)
    except Exception:
        return "```text\n" + df.to_string(index=False) + "\n```"


report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

pretrain_metrics = safe_get("pretrain_val_metrics")
garmin_metrics = safe_get("garmin_val_metrics")
user7_metrics = safe_get("user7_final_metrics")

report_lines = [
    "# Clean Production-Contract HAR Model Training Report",
    "",
    f"Generated: `{report_time}`",
    "",
    "## Purpose",
    "",
    "This notebook trains a thesis-defendable HAR model using the same input contract expected by the production pipeline.",
    "",
    "The main goal is to avoid the previous training-serving mismatch where the deployed checkpoint expected a hidden mentor notebook contract.",
    "",
    "## Production Contract",
    "",
    f"- Features: `{COMMON_FEATURES}`",
    f"- Window size: `{WINDOW_SIZE}`",
    f"- Stride: `{STRIDE}`",
    f"- Tensor layout: `{TENSOR_LAYOUT}`",
    f"- Number of classes: `{N_CLASSES}`",
    f"- Class order: `{CLASS_NAMES}`",
    f"- Scaler mode: `{SCALER_MODE}`",
    f"- Accelerometer target unit: `{TARGET_ACCEL_UNIT}`",
    f"- Gyroscope handling: `{TARGET_GYRO_UNIT}`",
    "- Mentor legacy reshape: `not used`",
    "- User 7: held out for external testing only",
    "",
    "## Training Augmentation",
    "",
]

if "AUGMENTATION_CONFIG" in globals():
    for key, value in AUGMENTATION_CONFIG.items():
        report_lines.append(f"- `{key}`: `{value}`")
else:
    report_lines.append("Augmentation config not available.")

report_lines.extend([
    "",
    "## Datasets",
    "",
    f"- ADAMSense pretraining: `{ADAMSENSE_PATH}`",
    f"- Garmin all_users fine-tuning: `{GARMIN_FINETUNE_PATH}`",
    f"- User 7 external test: `{USER7_EXTERNAL_TEST_PATH}`",
    "",
    "## Tensor Shapes",
    "",
    shape_line("ADAMSense train", safe_get("X_adamsense_train_model"), safe_get("y_adamsense_train")),
    shape_line("ADAMSense validation", safe_get("X_adamsense_val_model"), safe_get("y_adamsense_val")),
    shape_line("Garmin train", safe_get("X_garmin_train_model"), safe_get("y_garmin_train")),
    shape_line("Garmin validation", safe_get("X_garmin_val_model"), safe_get("y_garmin_val")),
    shape_line("User 7 external", safe_get("X_user7_model"), safe_get("y_user7")),
    "",
    "## Split Summary",
    "",
])

if "split_summary" in globals():
    report_lines.append(dataframe_to_markdown_or_text(split_summary))
else:
    report_lines.append("Split summary not available.")

report_lines.extend(["", "## Unit Conversion Decision", ""])

if "unit_conversion_decision" in globals():
    for key, value in unit_conversion_decision.items():
        report_lines.append(f"- `{key}`: `{value}`")
else:
    report_lines.append("Unit conversion decision not available.")

report_lines.extend([
    "",
    format_metric_block("ADAMSense Pretraining Validation Metrics", pretrain_metrics),
    format_metric_block("Garmin Fine-Tuning Validation Metrics", garmin_metrics),
    format_metric_block("User 7 External Final Metrics", user7_metrics),
    "## Saved Artifacts",
    "",
    f"- Final package directory: `{safe_get('FINAL_PACKAGE_DIR')}`",
    f"- Final model: `{safe_get('final_model_path')}`",
    f"- Model contract: `{safe_get('model_contract_path')}`",
    f"- Scaler contract: `{safe_get('scaler_contract_path')}`",
    f"- Model directory: `{MODEL_DIR}`",
    f"- Report directory: `{REPORT_DIR}`",
    "",
    "## Interpretation",
    "",
    "This model is trained under a clean production contract: normal row-wise `(time, channel)` windows and explicit scaler behavior.",
    "",
    "The mentor legacy tensor layout is not used for this clean model. If mentor-layout results are discussed, they should be reported separately as a legacy compatibility benchmark, not as the production model contract.",
    "",
    "User 7 should be interpreted as external deployment-style evidence. It must not be used to tune the model after seeing the result.",
    "",
])

training_report_path = REPORT_DIR / "clean_production_contract_training_report.md"

with open(training_report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))

print("Saved training report:", training_report_path)
