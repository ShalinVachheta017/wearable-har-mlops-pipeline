# Cell 11 - Model architecture, augmentation, and evaluation helpers

# Goal:
# Build a clean production-contract 1D-CNN-BiLSTM model.
#
# Input:
#   (200, 6)
#
# Meaning:
#   X[i, t, :] = [Ax, Ay, Az, Gx, Gy, Gz]
#
# Output:
#   11 activity classes

# Mild training-only augmentation. Validation and User 7 are never augmented.
USE_TRAIN_AUGMENTATION = True
AUGMENT_COPIES = 1
AUGMENT_NOISE_STD_FRACTION = 0.02
AUGMENT_MAGNITUDE_SCALE_STD = 0.04
AUGMENT_MAX_TIME_SHIFT = 8

AUGMENTATION_CONFIG = {
    "use_train_augmentation": USE_TRAIN_AUGMENTATION,
    "copies": AUGMENT_COPIES,
    "noise_std_fraction_of_channel_std": AUGMENT_NOISE_STD_FRACTION,
    "magnitude_scale_std": AUGMENT_MAGNITUDE_SCALE_STD,
    "max_time_shift_samples": AUGMENT_MAX_TIME_SHIFT,
    "applies_to": "training windows only",
    "not_applied_to": "validation windows or User 7 external test",
}


def augment_windows(
    X,
    seed=SEED,
    noise_std_fraction=AUGMENT_NOISE_STD_FRACTION,
    magnitude_scale_std=AUGMENT_MAGNITUDE_SCALE_STD,
    max_time_shift=AUGMENT_MAX_TIME_SHIFT,
):
    """Mild IMU augmentation for training windows only."""
    if len(X) == 0:
        return X.copy()

    rng = np.random.default_rng(seed)
    X_aug = X.copy().astype(np.float32)

    channel_std = X.reshape(-1, X.shape[-1]).std(axis=0)
    channel_std = np.maximum(channel_std, 1e-6)

    noise = rng.normal(
        loc=0.0,
        scale=noise_std_fraction * channel_std.reshape(1, 1, -1),
        size=X_aug.shape,
    ).astype(np.float32)
    X_aug = X_aug + noise

    scales = rng.normal(
        loc=1.0,
        scale=magnitude_scale_std,
        size=(len(X_aug), 1, X_aug.shape[-1]),
    ).astype(np.float32)
    X_aug = X_aug * scales

    if max_time_shift > 0:
        shifts = rng.integers(-max_time_shift, max_time_shift + 1, size=len(X_aug))
        for i, shift in enumerate(shifts):
            if shift != 0:
                X_aug[i] = np.roll(X_aug[i], shift=shift, axis=0)

    return X_aug.astype(np.float32)


def make_augmented_training_set(X, y, copies=AUGMENT_COPIES, seed=SEED):
    if not USE_TRAIN_AUGMENTATION or copies <= 0:
        return X, y

    X_parts = [X]
    y_parts = [y]

    for copy_idx in range(copies):
        X_parts.append(augment_windows(X, seed=seed + copy_idx + 1))
        y_parts.append(y.copy())

    X_out = np.concatenate(X_parts, axis=0).astype(np.float32)
    y_out = np.concatenate(y_parts, axis=0).astype(np.int64)

    print("Augmentation enabled")
    print("Original windows:", X.shape)
    print("Augmented training windows:", X_out.shape)

    return X_out, y_out


def build_1dcnn_bilstm_model(
    window_size=WINDOW_SIZE,
    n_channels=N_CHANNELS,
    n_classes=N_CLASSES,
    conv_filters_1=32,
    conv_filters_2=64,
    lstm_units=48,
    dense_units=48,
    dropout_rate=0.45,
    l2_strength=5e-4,
    learning_rate=5e-4,
):
    inputs = keras.Input(
        shape=(window_size, n_channels),
        name="imu_window",
    )

    x = layers.Conv1D(
        filters=conv_filters_1,
        kernel_size=5,
        padding="same",
        activation="relu",
        kernel_regularizer=regularizers.l2(l2_strength),
        name="conv1",
    )(inputs)
    x = layers.BatchNormalization(name="bn1")(x)
    x = layers.MaxPooling1D(pool_size=2, name="pool1")(x)
    x = layers.Dropout(dropout_rate, name="dropout1")(x)

    x = layers.Conv1D(
        filters=conv_filters_2,
        kernel_size=5,
        padding="same",
        activation="relu",
        kernel_regularizer=regularizers.l2(l2_strength),
        name="conv2",
    )(x)
    x = layers.BatchNormalization(name="bn2")(x)
    x = layers.MaxPooling1D(pool_size=2, name="pool2")(x)
    x = layers.Dropout(dropout_rate, name="dropout2")(x)

    x = layers.Bidirectional(
        layers.LSTM(
            lstm_units,
            return_sequences=False,
            dropout=0.30,
            recurrent_dropout=0.0,
        ),
        name="bilstm",
    )(x)

    x = layers.Dense(
        dense_units,
        activation="relu",
        kernel_regularizer=regularizers.l2(l2_strength),
        name="dense_features",
    )(x)
    x = layers.BatchNormalization(name="bn_dense")(x)
    x = layers.Dropout(dropout_rate, name="dropout_dense")(x)

    outputs = layers.Dense(
        n_classes,
        activation="softmax",
        name="activity_softmax",
    )(x)

    model = keras.Model(
        inputs=inputs,
        outputs=outputs,
        name="production_contract_1dcnn_bilstm",
    )

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    return model


def make_class_weights(y):
    classes_present = np.unique(y)

    weights = compute_class_weight(
        class_weight="balanced",
        classes=classes_present,
        y=y,
    )

    return {
        int(cls): float(weight)
        for cls, weight in zip(classes_present, weights)
    }


def make_callbacks(run_name, monitor="val_accuracy", patience=15):
    run_dir = MODEL_DIR / run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_path = run_dir / "best_model.keras"
    mode = "min" if "loss" in monitor else "max"

    callbacks = [
        keras.callbacks.ModelCheckpoint(
            filepath=str(checkpoint_path),
            monitor=monitor,
            save_best_only=True,
            mode=mode,
            verbose=1,
        ),
        keras.callbacks.EarlyStopping(
            monitor=monitor,
            patience=patience,
            restore_best_weights=True,
            mode=mode,
            verbose=1,
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor=monitor,
            factor=0.5,
            patience=max(4, patience // 3),
            min_lr=1e-6,
            mode=mode,
            verbose=1,
        ),
    ]

    return callbacks, checkpoint_path


def evaluate_model(model, X, y, dataset_name, save_prefix=None):
    proba = model.predict(X, verbose=0)
    pred = proba.argmax(axis=1)

    metrics = {
        "dataset": dataset_name,
        "accuracy": float(accuracy_score(y, pred)),
        "macro_f1": float(f1_score(y, pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y, pred, average="weighted", zero_division=0)),
        "mean_confidence": float(proba.max(axis=1).mean()),
        "median_confidence": float(np.median(proba.max(axis=1))),
        "n_predicted_classes": int(len(np.unique(pred))),
        "dominant_class": ID_TO_LABEL[int(pd.Series(pred).value_counts().idxmax())],
        "dominant_class_pct": float(pd.Series(pred).value_counts(normalize=True).max()),
    }

    print("=" * 90)
    print(dataset_name)
    print(metrics)

    print("Prediction distribution:")
    pred_dist = (
        pd.Series(pred)
        .map(ID_TO_LABEL)
        .value_counts()
        .reindex(CLASS_NAMES, fill_value=0)
    )
    display(pred_dist)

    print("True distribution:")
    true_dist = (
        pd.Series(y)
        .map(ID_TO_LABEL)
        .value_counts()
        .reindex(CLASS_NAMES, fill_value=0)
    )
    display(true_dist)

    print("Classification report:")
    report_text = classification_report(
        y,
        pred,
        labels=np.arange(N_CLASSES),
        target_names=CLASS_NAMES,
        zero_division=0,
    )
    print(report_text)

    cm = confusion_matrix(y, pred, labels=np.arange(N_CLASSES))
    cm_df = pd.DataFrame(cm, index=CLASS_NAMES, columns=CLASS_NAMES)
    display(cm_df)

    if save_prefix is not None:
        metrics_path = REPORT_DIR / f"{save_prefix}_metrics.json"
        cm_path = REPORT_DIR / f"{save_prefix}_confusion.csv"
        pred_path = REPORT_DIR / f"{save_prefix}_predictions.csv"

        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)

        cm_df.to_csv(cm_path)

        pd.DataFrame({
            "true_id": y,
            "true_label": [ID_TO_LABEL[int(i)] for i in y],
            "pred_id": pred,
            "pred_label": [ID_TO_LABEL[int(i)] for i in pred],
            "confidence": proba.max(axis=1),
        }).to_csv(pred_path, index=False)

        print("Saved metrics:", metrics_path)
        print("Saved confusion:", cm_path)
        print("Saved predictions:", pred_path)

    return metrics, cm_df, pred, proba


# Quick architecture check.
model = build_1dcnn_bilstm_model()
model.summary()

adamsense_class_weights = make_class_weights(y_adamsense_train)
garmin_class_weights = make_class_weights(y_garmin_train)

print("ADAMSense class weights:")
print(adamsense_class_weights)

print("Garmin fine-tuning class weights:")
print(garmin_class_weights)
print("Augmentation config:")
print(AUGMENTATION_CONFIG)
