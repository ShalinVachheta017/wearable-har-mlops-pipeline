# Cell 13 - Fine-tune pretrained model on Garmin all_users

# Goal:
# Adapt the ADAMSense-pretrained model to Garmin Venu 3 / all_users data.
#
# Important:
# - Uses Garmin all_users train/validation split.
# - Does not use User 7.
# - Keeps the same clean production tensor contract.
# - Fine-tunes in two phases:
#   Phase A: freeze feature extractor, train classification head.
#   Phase B: unfreeze all layers, fine-tune with small learning rate.

FINETUNE_HEAD_EPOCHS = 40
FINETUNE_FULL_EPOCHS = 60
FINETUNE_BATCH_SIZE = 64
FINETUNE_RUN_NAME = f"finetune_garmin_scaler_{SCALER_MODE}_regularized"

required_for_cell_13 = [
    "pretrain_model",
    "X_garmin_train_model",
    "X_garmin_val_model",
    "y_garmin_train",
    "y_garmin_val",
    "garmin_class_weights",
]

missing = [name for name in required_for_cell_13 if name not in globals()]
if missing:
    raise RuntimeError(
        "Run Cell 12 successfully before Cell 13. Missing variables: "
        + ", ".join(missing)
    )

print("Fine-tuning run:", FINETUNE_RUN_NAME)
print("X Garmin train:", X_garmin_train_model.shape)
print("y Garmin train:", y_garmin_train.shape)
print("X Garmin val:", X_garmin_val_model.shape)
print("y Garmin val:", y_garmin_val.shape)

# Start from pretrained ADAMSense weights.
finetune_model = keras.models.clone_model(pretrain_model)
finetune_model.set_weights(pretrain_model.get_weights())

# Phase A: freeze early layers and train the head.
for layer in finetune_model.layers:
    layer.trainable = False

for layer_name in ["dense_features", "bn_dense", "dropout_dense", "activity_softmax"]:
    finetune_model.get_layer(layer_name).trainable = True

finetune_model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=3e-4),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)

head_callbacks, head_checkpoint_path = make_callbacks(
    run_name=FINETUNE_RUN_NAME + "_head",
    monitor="val_accuracy",
    patience=12,
)

print("Trainable layers during Phase A:")
for layer in finetune_model.layers:
    if layer.trainable:
        print(layer.name)

X_garmin_train_fit, y_garmin_train_fit = make_augmented_training_set(
    X_garmin_train_model,
    y_garmin_train,
    copies=AUGMENT_COPIES,
    seed=SEED + 1000,
)

garmin_class_weights_fit = make_class_weights(y_garmin_train_fit)

head_history = finetune_model.fit(
    X_garmin_train_fit,
    y_garmin_train_fit,
    validation_data=(X_garmin_val_model, y_garmin_val),
    epochs=FINETUNE_HEAD_EPOCHS,
    batch_size=FINETUNE_BATCH_SIZE,
    class_weight=garmin_class_weights_fit,
    callbacks=head_callbacks,
    verbose=1,
)

# Phase B: unfreeze all layers and fine-tune with a smaller learning rate.
for layer in finetune_model.layers:
    layer.trainable = True

finetune_model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=5e-5),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)

full_callbacks, full_checkpoint_path = make_callbacks(
    run_name=FINETUNE_RUN_NAME + "_full",
    monitor="val_accuracy",
    patience=15,
)

full_history = finetune_model.fit(
    X_garmin_train_fit,
    y_garmin_train_fit,
    validation_data=(X_garmin_val_model, y_garmin_val),
    epochs=FINETUNE_FULL_EPOCHS,
    batch_size=FINETUNE_BATCH_SIZE,
    class_weight=garmin_class_weights_fit,
    callbacks=full_callbacks,
    verbose=1,
)

# Save histories.
head_history_df = pd.DataFrame(head_history.history)
full_history_df = pd.DataFrame(full_history.history)

head_history_path = REPORT_DIR / "clean_model_finetune_garmin_head_history.csv"
full_history_path = REPORT_DIR / "clean_model_finetune_garmin_full_history.csv"

head_history_df.to_csv(head_history_path, index=False)
full_history_df.to_csv(full_history_path, index=False)

print("Saved head fine-tuning history:", head_history_path)
print("Saved full fine-tuning history:", full_history_path)

# Evaluate on Garmin validation.
garmin_val_metrics, garmin_val_cm, garmin_val_pred, garmin_val_proba = evaluate_model(
    finetune_model,
    X_garmin_val_model,
    y_garmin_val,
    dataset_name="Garmin all_users validation after fine-tuning",
    save_prefix="clean_model_finetune_garmin_val",
)

# Save fine-tuned model.
fine_tuned_model_path = MODEL_DIR / "fine_tuned_garmin_clean_contract.keras"
finetune_model.save(fine_tuned_model_path)

print("Saved fine-tuned Garmin model:", fine_tuned_model_path)
print("Best head checkpoint:", head_checkpoint_path)
print("Best full checkpoint:", full_checkpoint_path)
