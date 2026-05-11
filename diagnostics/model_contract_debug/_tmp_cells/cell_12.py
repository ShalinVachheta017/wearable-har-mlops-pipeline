# Cell 12 - Pretrain model on ADAMSense

# Goal:
# Learn general wrist-IMU HAR features from ADAMSense first.
#
# Important:
# - Uses only ADAMSense train/validation split.
# - Does not use Garmin all_users for this pretraining step.
# - Does not use User 7.
# - Uses the clean production tensor contract: normal row-wise (time, channel).

PRETRAIN_EPOCHS = 80
PRETRAIN_BATCH_SIZE = 64
PRETRAIN_RUN_NAME = f"pretrain_adamsense_scaler_{SCALER_MODE}_regularized"

required_for_cell_12 = [
    "X_adamsense_train_model",
    "X_adamsense_val_model",
    "y_adamsense_train",
    "y_adamsense_val",
    "adamsense_class_weights",
]

missing = [name for name in required_for_cell_12 if name not in globals()]
if missing:
    raise RuntimeError(
        "Run Cells 10 and 11 successfully before Cell 12. Missing variables: "
        + ", ".join(missing)
    )

print("Pretraining run:", PRETRAIN_RUN_NAME)
print("X train:", X_adamsense_train_model.shape)
print("y train:", y_adamsense_train.shape)
print("X val:", X_adamsense_val_model.shape)
print("y val:", y_adamsense_val.shape)

# Fresh model for pretraining.
pretrain_model = build_1dcnn_bilstm_model(
    learning_rate=5e-4,
    dropout_rate=0.45,
    l2_strength=5e-4,
)

pretrain_callbacks, pretrain_checkpoint_path = make_callbacks(
    run_name=PRETRAIN_RUN_NAME,
    monitor="val_accuracy",
    patience=15,
)

X_adamsense_train_fit, y_adamsense_train_fit = make_augmented_training_set(
    X_adamsense_train_model,
    y_adamsense_train,
    copies=AUGMENT_COPIES,
    seed=SEED,
)

adamsense_class_weights_fit = make_class_weights(y_adamsense_train_fit)

pretrain_history = pretrain_model.fit(
    X_adamsense_train_fit,
    y_adamsense_train_fit,
    validation_data=(X_adamsense_val_model, y_adamsense_val),
    epochs=PRETRAIN_EPOCHS,
    batch_size=PRETRAIN_BATCH_SIZE,
    class_weight=adamsense_class_weights_fit,
    callbacks=pretrain_callbacks,
    verbose=1,
)

# Save training history.
pretrain_history_df = pd.DataFrame(pretrain_history.history)
pretrain_history_path = REPORT_DIR / "clean_model_pretrain_adamsense_history.csv"
pretrain_history_df.to_csv(pretrain_history_path, index=False)

print("Saved pretraining history:", pretrain_history_path)
print("Best pretraining checkpoint:", pretrain_checkpoint_path)

# Evaluate best in-memory weights after EarlyStopping restore_best_weights=True.
pretrain_val_metrics, pretrain_val_cm, pretrain_val_pred, pretrain_val_proba = evaluate_model(
    pretrain_model,
    X_adamsense_val_model,
    y_adamsense_val,
    dataset_name="ADAMSense validation after pretraining",
    save_prefix="clean_model_pretrain_adamsense_val",
)

# Save pretrained model.
pretrained_model_path = MODEL_DIR / "pretrained_adamsense_clean_contract.keras"
pretrain_model.save(pretrained_model_path)

print("Saved pretrained ADAMSense model:", pretrained_model_path)
