"""Single source of truth for label-column detection constants."""

LABEL_COLUMN_CANDIDATES = (
    "activity",
    "label",
    "labels",
    "activity_label",
    "activity_id",
    "target",
    "target_label",
    "ground_truth",
    "y_true",
    "class",
    "class_id",
)

NON_GROUND_TRUTH_COLUMNS = {
    "predicted_activity",
    "predicted_class",
    "confidence",
    "confidence_level",
    "is_uncertain",
}
