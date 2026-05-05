# %% [markdown]
# # MLOps Pipeline Testing & Model Evaluation
#
# This notebook supports both single CSV and two-file (accel+gyro) input modes.
# It auto-detects labels, applies configurable preprocessing, loads two models for comparison,
# generates sliding windows, performs inference, and displays all metrics and visualizations inline.

# %% [markdown]
# ## Configuration
# Set input paths, preprocessing switches, memory controls, and model paths here. Unit conversion is only for accelerometer data when it is still in milliG.

# %%
# ===== CONFIGURATION SECTION =====
# Adjust these settings before running

# Data Input: Choose ONE mode
# Mode 1: Single CSV with both accel and gyro columns
DATA_PATH = r'D:\study apply\ML Ops\MasterArbeit_MLops\notebooks\synthetic_labeled.csv'  # e.g., r'data/sample_data.csv'

# Mode 2: Separate accel and gyro files (two-file merge)
ACCEL_FILE = None
GYRO_FILE  = None

# Label column name (or None if no labels)
LABEL_COLUMN = 'activity'  # Will auto-detect if this column exists

# Preprocessing toggles
# Unit conversion is for accelerometer values only: milliG -> m/s^2.
# Gyroscope values are expected to stay in degrees/second and are never scaled here.
UNIT_CONVERSION      = False
GRAVITY_REMOVAL      = False  # Remove gravity component from acceleration
ZSCORE_NORMALIZATION = False  # Apply z-score normalization per sensor axis

# Memory controls
WINDOW_DTYPE       = 'float32'  # numpy-compatible string; resolved when used
PREDICT_BATCH_SIZE = 128
MAX_WINDOWS        = None  # Optional safety cap while debugging, e.g. 5000

# Model paths (set manually)
PRETRAINED_MODEL_PATH = r"D:\study apply\ML Ops\MasterArbeit_MLops\models\pretrained\fine_tuned_model_1dcnnbilstm.keras"
TRAINED_MODEL_PATH    = None  # e.g., r'models/trained_model.keras'
SCALER_PATH           = None  # e.g., r'models/scaler.pkl' (optional)

# Window parameters (matching production pipeline)
WINDOW_SIZE    = 200
WINDOW_OVERLAP = 0.5
WINDOW_STEP    = int(WINDOW_SIZE * (1 - WINDOW_OVERLAP))

# Activity class mapping - 11 classes matching production label_mapping.py
ACTIVITY_MAPPING = {
    'ear_rubbing':       0,
    'forehead_rubbing':  1,
    'hair_pulling':      2,
    'hand_scratching':   3,
    'hand_tapping':      4,
    'knuckles_cracking': 5,
    'nail_biting':       6,
    'nape_rubbing':      7,
    'sitting':           8,
    'smoking':           9,
    'standing':         10,
}

print('=== Configuration Loaded ===')
print(f'Single CSV:  {DATA_PATH}')
print(f'Accel File:  {ACCEL_FILE}')
print(f'Gyro File:   {GYRO_FILE}')
print(f'Preprocessing: unit={UNIT_CONVERSION}, gravity={GRAVITY_REMOVAL}, zscore={ZSCORE_NORMALIZATION}')
print(f'Window dtype: {WINDOW_DTYPE}, predict batch size: {PREDICT_BATCH_SIZE}, max windows: {MAX_WINDOWS}')
print(f'Pretrained:  {PRETRAINED_MODEL_PATH}')
print(f'Trained:     {TRAINED_MODEL_PATH}')
print(f'Classes ({len(ACTIVITY_MAPPING)}): {list(ACTIVITY_MAPPING.keys())}')

# %%
# ===== IMPORTS =====
import pandas as pd
import numpy as np
import json
import pickle
import warnings
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report
import tensorflow as tf
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings('ignore')
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (12, 6)

print('All imports successful')

# %%
# Quick preview of raw file columns (informational only)
import pandas as pd
if ACCEL_FILE:
    _a = pd.read_csv(ACCEL_FILE, nrows=2)
    _g = pd.read_csv(GYRO_FILE,  nrows=2)
    print("Accel columns:", _a.columns.tolist())
    print("Gyro  columns:", _g.columns.tolist())
    del _a, _g
elif DATA_PATH:
    _d = pd.read_csv(DATA_PATH, nrows=2)
    print("Data columns:", _d.columns.tolist())
    del _d

# %% [markdown]
# ## Data Loading
# Loads either one prepared CSV or separate accelerometer/gyroscope files. Numeric values are downcast after loading to reduce memory use.

# %%
# ===== STEP 1: DATA INGESTION (Single CSV or Two-File Merge) =====

def optimize_dataframe_memory(df, exclude_cols=None):
    """Downcast numeric columns in-place to reduce notebook RAM use."""
    exclude_cols = set(exclude_cols or [])
    before_mb = df.memory_usage(deep=True).sum() / 1024**2
    for col in df.columns:
        if col in exclude_cols:
            continue
        if pd.api.types.is_float_dtype(df[col]):
            df[col] = pd.to_numeric(df[col], downcast='float')
        elif pd.api.types.is_integer_dtype(df[col]):
            df[col] = pd.to_numeric(df[col], downcast='integer')
    after_mb = df.memory_usage(deep=True).sum() / 1024**2
    print(f'Memory optimized: {before_mb:.1f} MB -> {after_mb:.1f} MB')
    return df

def _build_precise_time(df):
    """
    Build a precise datetime index from:
      timestamp          -> string "2025-08-12 22:41:37" (second-level)
      timestamp_ms       -> int 0-999 (milliseconds within that second)
      sample_time_offset -> int/float sub-sample offset in ms
    """
    base = pd.to_datetime(df['timestamp'])
    ms = pd.to_numeric(df['timestamp_ms'], errors='coerce')
    off = pd.to_numeric(df['sample_time_offset'], errors='coerce')
    return base + pd.to_timedelta(ms + off, unit='ms')

def load_data():
    if DATA_PATH:
        print(f'Loading single CSV: {DATA_PATH}')
        df = pd.read_csv(DATA_PATH, low_memory=False)
        df = optimize_dataframe_memory(df, exclude_cols=[LABEL_COLUMN] if LABEL_COLUMN else None)
        print(f'Loaded {len(df)} rows, columns: {df.columns.tolist()}')
        return df

    if ACCEL_FILE and GYRO_FILE:
        print(f'Loading accel: {ACCEL_FILE}')
        print(f'Loading gyro:  {GYRO_FILE}')

        accel_df = pd.read_csv(ACCEL_FILE, low_memory=False)
        gyro_df  = pd.read_csv(GYRO_FILE, low_memory=False)
        accel_df = optimize_dataframe_memory(accel_df)
        gyro_df  = optimize_dataframe_memory(gyro_df)

        # Build precise absolute timestamps.
        accel_df['_t'] = _build_precise_time(accel_df)
        gyro_df['_t']  = _build_precise_time(gyro_df)

        accel_df = accel_df.sort_values('_t').reset_index(drop=True)
        gyro_df  = gyro_df.sort_values('_t').reset_index(drop=True)

        print(f"Accel time range: {accel_df['_t'].iloc[0]}  ->  {accel_df['_t'].iloc[-1]}")
        print(f"Gyro  time range: {gyro_df['_t'].iloc[0]}  ->  {gyro_df['_t'].iloc[-1]}")

        # Drop duplicate metadata cols from gyro before merge to keep the merge narrow.
        gyro_drop = [c for c in ['timestamp', 'timestamp_ms', 'sample_index', 'sample_time_offset']
                     if c in gyro_df.columns]
        gyro_slim = gyro_df.drop(columns=gyro_drop)

        # Merge on precise timestamp, 20ms tolerance (covers accel/gyro phase offset).
        df = pd.merge_asof(
            accel_df,
            gyro_slim,
            left_on='_t', right_on='_t',
            tolerance=pd.Timedelta('20ms'),
            direction='nearest'
        )

        # Drop rows where gyro did not match.
        gyro_sensor_cols = [c for c in df.columns if c.lower().startswith(('gyro_', 'g'))]
        before = len(df)
        df = df.dropna(subset=gyro_sensor_cols).reset_index(drop=True)
        print(f'Rows before dropna: {before}  after: {len(df)}')

        df = df.rename(columns={'_t': 'timestamp'})
        df = df.drop(columns=[c for c in ['timestamp_ms', 'sample_index', 'sample_time_offset'] if c in df.columns])
        df = optimize_dataframe_memory(df, exclude_cols=['timestamp', LABEL_COLUMN] if LABEL_COLUMN else ['timestamp'])

        print(f'Final merged shape: {df.shape}')
        print(f'Columns: {df.columns.tolist()}')
        return df

    raise ValueError('Must set either DATA_PATH or both ACCEL_FILE and GYRO_FILE')

df_raw = load_data()
print(f'\nRaw data shape: {df_raw.shape}')
print(df_raw.head())

# %% [markdown]
# ## Column and Label Detection
# Detects accelerometer, gyroscope, and activity-label columns before preprocessing.

# %%
# ===== STEP 2: DATA VALIDATION & LABEL AUTO-DETECTION =====

def detect_sensor_columns(df):
    """
    Auto-detect accelerometer and gyroscope columns.
    Supports: Ax/Ay/Az, Gx/Gy/Gz, Ax_w/Ay_w/Az_w, Gx_w/Gy_w/Gz_w, calibrated names, accel_x/gyro_x, etc.
    """
    cols = df.columns.str.lower()
    
    # Accel patterns
    accel_patterns = [
        ('ax', 'ay', 'az'),  # Standard
        ('ax_w', 'ay_w', 'az_w'),  # Wrist convention
        ('accel_x', 'accel_y', 'accel_z'),  # Canonical
        ('acceleration_x', 'acceleration_y', 'acceleration_z'),  # Full name
    ]
    
    gyro_patterns = [
        ('gx', 'gy', 'gz'),  # Standard
        ('gx_w', 'gy_w', 'gz_w'),  # Wrist convention
        ('gyro_x', 'gyro_y', 'gyro_z'),  # Canonical
        ('angular_x', 'angular_y', 'angular_z'),  # Full name
    ]
    
    accel_cols = None
    gyro_cols = None
    
    for pattern in accel_patterns:
        if all(col in cols for col in pattern):
            accel_cols = pattern
            break
    
    for pattern in gyro_patterns:
        if all(col in cols for col in pattern):
            gyro_cols = pattern
            break
    
    if not accel_cols or not gyro_cols:
        raise ValueError(f'Could not detect sensor columns. Available: {df.columns.tolist()}')
    
    # Map back to original case
    accel_actual = [df.columns[np.where(cols == c)[0][0]] for c in accel_cols]
    gyro_actual = [df.columns[np.where(cols == c)[0][0]] for c in gyro_cols]
    
    return accel_actual, gyro_actual

def detect_labels(df):
    """
    Auto-detect label column if it exists.
    Returns column name if found, None otherwise.
    """
    if LABEL_COLUMN and LABEL_COLUMN in df.columns:
        return LABEL_COLUMN
    
    # Try common label column names
    for col in ['activity', 'label', 'activity_type', 'action']:
        if col in df.columns:
            return col
    
    return None

# Detect columns
accel_cols, gyro_cols = detect_sensor_columns(df_raw)
label_col = detect_labels(df_raw)

print(f'Detected accel columns: {accel_cols}')
print(f'Detected gyro columns: {gyro_cols}')
print(f'Detected label column: {label_col}')
print(f'Has labels: {label_col is not None}')

if label_col:
    print(f'Unique labels: {df_raw[label_col].unique()}')
    print(f'Label value counts:\n{df_raw[label_col].value_counts()}')

# Check for missing values
print(f'\nMissing values per column:')
print(df_raw.isnull().sum())

# %% [markdown]
# ## Unit Check and Preprocessing
# Checks whether acceleration looks like milliG or m/s^2. Conversion is applied only to accelerometer columns; gyroscope stays in degrees/second.

# %%
# ===== STEP 3: DATA PREPROCESSING =====

def infer_accel_unit_need(df, accel_cols):
    """
    Estimate whether acceleration needs milliG -> m/s^2 conversion.

    Practical rule:
    - If the median acceleration magnitude is near 9.81, data is already m/s^2.
    - If it is near 1000, data is likely milliG and should be converted.
    - In between, inspect the source/export settings before enabling conversion.
    """
    accel = df[accel_cols].apply(pd.to_numeric, errors='coerce').dropna()
    if accel.empty:
        return {'decision': 'unknown', 'median_norm': np.nan, 'message': 'No valid accelerometer rows found.'}

    sample = accel.sample(min(len(accel), 50_000), random_state=42) if len(accel) > 50_000 else accel
    norms = np.linalg.norm(sample.to_numpy(dtype=np.float32, copy=False), axis=1)
    median_norm = float(np.nanmedian(norms))

    if median_norm > 100:
        decision = 'convert'
        message = 'Acceleration looks like milliG; enable UNIT_CONVERSION=True.'
    elif 3 <= median_norm <= 30:
        decision = 'do_not_convert'
        message = 'Acceleration looks like m/s^2; keep UNIT_CONVERSION=False.'
    else:
        decision = 'ambiguous'
        message = 'Scale is ambiguous; verify units from the data logger/export.'

    return {'decision': decision, 'median_norm': median_norm, 'message': message}

def preprocess_data(df, accel_cols, gyro_cols):
    """
    Apply configurable preprocessing:
    1. Unit conversion: milliG to m/s^2 for accelerometer columns only.
    2. Gravity removal: subtract gravity vector from accelerometer columns only.
    3. Z-score normalization: per-axis standardization across accel + gyro.

    Gyroscope values are expected in degrees/second and are not unit-converted.
    """
    df = df.copy()
    all_sensor_cols = accel_cols + gyro_cols
    df[all_sensor_cols] = df[all_sensor_cols].apply(pd.to_numeric, errors='coerce').astype(np.float32)

    unit_report = infer_accel_unit_need(df, accel_cols)
    print(f"Acceleration unit check: median |a|={unit_report['median_norm']:.3f}; {unit_report['message']}")

    gyro_before = df[gyro_cols].copy(deep=True)

    # Step 1: Unit Conversion. Acceleration only; gyroscope stays in degrees/second.
    if UNIT_CONVERSION:
        print('Converting accelerometer from milliG to m/s^2. Gyroscope columns are not converted.')
        milli_g_to_mps2 = 9.81 / 1000.0
        df.loc[:, accel_cols] = df[accel_cols] * np.float32(milli_g_to_mps2)

    if not np.allclose(gyro_before.to_numpy(), df[gyro_cols].to_numpy(), equal_nan=True):
        raise AssertionError('Gyroscope values changed during unit conversion. Check preprocessing code.')

    # Step 2: Gravity Removal.
    if GRAVITY_REMOVAL:
        print('Removing gravity component from acceleration...')
        window_size = 50  # about 1 second at 50Hz
        for col in accel_cols:
            gravity = df[col].rolling(window=window_size, center=True, min_periods=1).mean().astype(np.float32)
            df[col] = (df[col] - gravity).astype(np.float32)

    # Step 3: Z-score Normalization.
    if ZSCORE_NORMALIZATION:
        print('Applying z-score normalization...')
        scaler = StandardScaler()
        df.loc[:, all_sensor_cols] = scaler.fit_transform(df[all_sensor_cols]).astype(np.float32)

    return optimize_dataframe_memory(df, exclude_cols=[label_col] if label_col else None)

df_processed = preprocess_data(df_raw, accel_cols, gyro_cols)
print(f'\nProcessed data shape: {df_processed.shape}')
show_cols = accel_cols[0:3] + gyro_cols[0:3]
print(df_processed[show_cols].head())

# %% [markdown]
# ## Window Generation
# Builds model windows with a float32 strided view to avoid copying every overlapping window into RAM.

# %%
# ===== STEP 4: SLIDING WINDOW GENERATION =====

def create_windows(df, accel_cols, gyro_cols, window_size=200, step=100, label_col=None, max_windows=None):
    """
    Generate sliding windows without building a large Python list.

    The sensor matrix is float32 and windows are created as a NumPy strided view.
    This avoids the main RAM spike from list-of-arrays -> float64 ndarray conversion.
    """
    all_sensor_cols = accel_cols + gyro_cols
    sensor_values = np.ascontiguousarray(df[all_sensor_cols].to_numpy(dtype=np.float32, copy=False))

    if len(sensor_values) < window_size:
        empty = np.empty((0, window_size, len(all_sensor_cols)), dtype=np.float32)
        return empty, None if label_col is None else np.array([]), np.array([], dtype=np.int64)

    all_windows = np.lib.stride_tricks.sliding_window_view(
        sensor_values,
        window_shape=(window_size, len(all_sensor_cols))
    )[:, 0, :, :]
    windows = all_windows[::step]

    if max_windows is not None:
        windows = windows[:max_windows]

    indices = np.arange(0, len(windows) * step, step, dtype=np.int64)

    labels = None
    if label_col is not None:
        label_values = df[label_col].to_numpy()
        labels = []
        for i in indices:
            window_labels = pd.Series(label_values[i:i + window_size])
            most_common = window_labels.mode(dropna=True)
            labels.append(most_common.iloc[0] if len(most_common) > 0 else window_labels.iloc[0])
        labels = np.asarray(labels)

    return windows, labels, indices

X, y, indices = create_windows(
    df_processed,
    accel_cols,
    gyro_cols,
    window_size=WINDOW_SIZE,
    step=WINDOW_STEP,
    label_col=label_col,
    max_windows=MAX_WINDOWS
)

print(f'Windows shape: {X.shape}')  # (n_windows, 200, 6)
print(f'Windows dtype: {X.dtype}; view-backed: {X.base is not None}')
print(f'Approx window storage if copied: {X.nbytes / 1024**2:.1f} MB')
print(f'Label shape: {y.shape if y is not None else "None"}')
print(f'Window indices shape: {indices.shape}')

if y is not None:
    print(f'\nLabel distribution in windows:')
    unique, counts = np.unique(y, return_counts=True)
    for u, c in zip(unique, counts):
        print(f'  {u}: {c}')

# %% [markdown]
# ## Model Loading
# Loads the configured Keras model files.

# %%
# ===== STEP 5: MODEL LOADING =====

def load_model(model_path):
    """
    Load a TensorFlow/Keras model from .h5 file.
    """
    if not model_path:
        return None
    
    print(f'Loading model: {model_path}')
    model = tf.keras.models.load_model(model_path)
    print(f'Model loaded successfully. Input shape: {model.input_shape}, Output shape: {model.output_shape}')
    return model

pretrained_model = load_model(PRETRAINED_MODEL_PATH)
trained_model = load_model(TRAINED_MODEL_PATH)

if not pretrained_model and not trained_model:
    raise ValueError('At least one model path must be set')

print('\nModels loaded successfully')

# %% [markdown]
# ## Inference and Confidence Analysis
# Runs batched prediction and summarizes confidence, entropy, margin, and class-level uncertainty.

# %%
# ===== STEP 6: INFERENCE & DEEP CONFIDENCE ANALYSIS =====
#
# Confidence score = max softmax probability (top-1).
#   > 0.80          → high confidence, model is decisive
#   0.50 – 0.80     → moderate, treat with caution
#   < 0.50          → low confidence (random baseline for 11 classes = 0.09)
#
# Metrics computed:
#   mean/std/min/max confidence
#   low_conf_rate       — % windows below threshold
#   entropy             — H = -sum(p*log(p)); 0=certain, 2.40=uniform random
#   margin              — top1 prob – top2 prob; small = ambiguous
#   per-class confidence — which activity is predicted most/least confidently
#   confidence buckets  — 5 bands: [0–0.3, 0.3–0.5, 0.5–0.7, 0.7–0.9, 0.9–1.0]
#   rolling confidence  — temporal heatmap, shows if model degrades mid-recording

CONFIDENCE_THRESHOLD = 0.5

def run_inference(model, X, activity_mapping):
    if len(X) == 0:
        print("Warning: No windows to run inference on.")
        return None
    print(f'Running inference on {len(X)} windows...')
    probs = model.predict(X, batch_size=PREDICT_BATCH_SIZE, verbose=0).astype(np.float32, copy=False)

    confidences    = np.max(probs, axis=1)
    pred_class_idx = np.argmax(probs, axis=1)
    idx_to_act     = {v: k for k, v in activity_mapping.items()}
    pred_activities = np.array([idx_to_act.get(i, f'class_{i}') for i in pred_class_idx])

    eps     = 1e-9
    entropy = -np.sum(probs * np.log(probs + eps), axis=1)
    sp      = np.sort(probs, axis=1)[:, ::-1]
    margin  = sp[:, 0] - sp[:, 1]

    top5_idx   = np.argsort(probs, axis=1)[:, -5:][:, ::-1]
    top5_probs = np.take_along_axis(probs, top5_idx, axis=1)
    top5_names = np.vectorize(idx_to_act.get)(top5_idx)

    return dict(confidences=confidences, pred_class_idx=pred_class_idx,
                pred_activities=pred_activities, probs=probs,
                entropy=entropy, margin=margin,
                top5_idx=top5_idx, top5_probs=top5_probs, top5_names=top5_names)


def deep_confidence_analysis(results, model_name):
    c   = results['confidences']
    ent = results['entropy']
    mar = results['margin']
    acts = results['pred_activities']
    n   = len(c)
    low = (c < CONFIDENCE_THRESHOLD).mean()
    max_ent = -np.log(1 / len(ACTIVITY_MAPPING))

    # ── printed summary ──────────────────────────────────────────────────────
    print(f'\n{"="*65}')
    print(f'  {model_name}  —  Confidence & Uncertainty')
    print(f'{"="*65}')
    print(f'  Windows              : {n}')
    print(f'  Confidence mean±std  : {c.mean():.4f} ± {c.std():.4f}')
    print(f'  Confidence min/max   : {c.min():.4f} / {c.max():.4f}')
    print(f'  Low-conf (<{CONFIDENCE_THRESHOLD:.2f})     : {low:.2%}  ({int(low*n)} windows)')
    print(f'  Entropy  mean±std    : {ent.mean():.4f} ± {ent.std():.4f}  (max={max_ent:.2f})')
    print(f'  Margin   mean±std    : {mar.mean():.4f} ± {mar.std():.4f}')
    print(f'  Ambiguous (mar<0.10) : {(mar < 0.10).mean():.2%}')

    # per-class confidence
    print(f'\n  Per-class mean confidence:')
    for act in sorted(set(acts)):
        mask = acts == act
        mc = c[mask].mean() if mask.sum() > 0 else 0.0
        bar = '█' * int(mc * 20)
        print(f'    {act:<22} {mc:.3f}  {bar}')

    # confidence buckets
    buckets = [(0.0,0.3,'<0.30  very low'),
               (0.3,0.5,'0.30–0.50 low'),
               (0.5,0.7,'0.50–0.70 moderate'),
               (0.7,0.9,'0.70–0.90 good'),
               (0.9,1.0,'0.90–1.00 high')]
    print(f'\n  Confidence bucket distribution:')
    for lo, hi, label in buckets:
        cnt = ((c >= lo) & (c < hi)).sum()
        pct = cnt / n
        bar = '█' * int(pct * 40)
        print(f'    {label:<22} {cnt:>5} ({pct:>5.1%})  {bar}')

    # ── plots ─────────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(2, 3, figsize=(18, 9))
    fig.suptitle(f'{model_name}  —  Confidence Deep Dive', fontsize=13, fontweight='bold')

    # 1. Confidence histogram
    ax = axes[0, 0]
    ax.hist(c, bins=40, color='steelblue', alpha=0.75, edgecolor='white')
    ax.axvline(c.mean(), color='red',    linestyle='--', lw=2, label=f'Mean {c.mean():.3f}')
    ax.axvline(CONFIDENCE_THRESHOLD, color='orange', linestyle=':', lw=2,
               label=f'Threshold {CONFIDENCE_THRESHOLD}')
    ax.set_title('Confidence Distribution')
    ax.set_xlabel('Confidence'); ax.set_ylabel('Count')
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    # 2. Entropy histogram
    ax = axes[0, 1]
    ax.hist(ent, bins=40, color='mediumpurple', alpha=0.75, edgecolor='white')
    ax.axvline(ent.mean(), color='red', linestyle='--', lw=2, label=f'Mean {ent.mean():.3f}')
    ax.axvline(max_ent,    color='black', linestyle=':', lw=1.5, label=f'Max (uniform) {max_ent:.2f}')
    ax.set_title('Prediction Entropy Distribution')
    ax.set_xlabel('Entropy H'); ax.set_ylabel('Count')
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    # 3. Margin histogram
    ax = axes[0, 2]
    ax.hist(mar, bins=40, color='seagreen', alpha=0.75, edgecolor='white')
    ax.axvline(mar.mean(), color='red', linestyle='--', lw=2, label=f'Mean {mar.mean():.3f}')
    ax.axvline(0.10, color='orange', linestyle=':', lw=1.5, label='Ambiguous < 0.10')
    ax.set_title('Decision Margin (top1 – top2)')
    ax.set_xlabel('Margin'); ax.set_ylabel('Count')
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    # 4. Per-class mean confidence bar
    ax = axes[1, 0]
    act_labels = sorted(set(acts))
    per_class_conf = [c[acts == a].mean() if (acts == a).sum() > 0 else 0 for a in act_labels]
    colors_pc = ['#2196F3' if v >= CONFIDENCE_THRESHOLD else '#FF5722' for v in per_class_conf]
    bars = ax.barh(act_labels, per_class_conf, color=colors_pc, alpha=0.8, edgecolor='black')
    ax.axvline(CONFIDENCE_THRESHOLD, color='orange', linestyle='--', lw=1.5,
               label=f'Threshold {CONFIDENCE_THRESHOLD}')
    ax.set_xlim(0, 1); ax.set_title('Per-Class Mean Confidence')
    ax.set_xlabel('Mean Confidence'); ax.legend(fontsize=8); ax.grid(axis='x', alpha=0.3)
    for bar, val in zip(bars, per_class_conf):
        ax.text(val + 0.01, bar.get_y() + bar.get_height()/2,
                f'{val:.3f}', va='center', fontsize=8)

    # 5. Confidence buckets pie
    ax = axes[1, 1]
    bucket_counts = [((c >= lo) & (c < hi)).sum() for lo, hi, _ in buckets]
    bucket_labels = [lbl for _, _, lbl in buckets]
    bucket_colors = ['#d32f2f','#ff7043','#ffd54f','#81c784','#2e7d32']
    wedges, texts, autotexts = ax.pie(
        bucket_counts, labels=bucket_labels, colors=bucket_colors,
        autopct='%1.1f%%', startangle=90, textprops={'fontsize': 8})
    ax.set_title('Confidence Bucket Distribution')

    # 6. Rolling confidence over time (window=50)
    ax = axes[1, 2]
    roll_w = 50
    rolling_conf = pd.Series(c).rolling(roll_w, min_periods=1).mean().values
    rolling_ent  = pd.Series(ent).rolling(roll_w, min_periods=1).mean().values
    ax.fill_between(range(n), rolling_conf, alpha=0.4, color='steelblue', label='Conf (rolling)')
    ax.plot(range(n), rolling_conf, color='steelblue', lw=1.2)
    ax2 = ax.twinx()
    ax2.plot(range(n), rolling_ent, color='mediumpurple', lw=1.2, alpha=0.7, label='Entropy (rolling)')
    ax2.set_ylabel('Entropy', color='mediumpurple', fontsize=9)
    ax.axhline(CONFIDENCE_THRESHOLD, color='orange', linestyle='--', lw=1.2)
    ax.set_ylim(0, 1); ax.set_title(f'Rolling Confidence & Entropy (w={roll_w})')
    ax.set_xlabel('Window index'); ax.set_ylabel('Confidence')
    ax.legend(loc='upper left', fontsize=8)
    ax2.legend(loc='upper right', fontsize=8)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.show()


# Run inference
results_pretrained = None
results_trained    = None

if pretrained_model:
    print('\n=== PRETRAINED MODEL ===')
    results_pretrained = run_inference(pretrained_model, X, ACTIVITY_MAPPING)
    if results_pretrained:
        deep_confidence_analysis(results_pretrained, 'Pretrained Model')

if trained_model:
    print('\n=== TRAINED MODEL ===')
    results_trained = run_inference(trained_model, X, ACTIVITY_MAPPING)
    if results_trained:
        deep_confidence_analysis(results_trained, 'Trained Model')

# %%
# ===== STEP 6b: FLIP RATE ANALYSIS =====
#
# Flip rate = how often the predicted class changes between consecutive windows.
# Consecutive windows share 50% of their samples (overlap=0.5), so the signal
# barely changes. A stable model should predict the same class for many windows
# in a row. Frequent flipping indicates the model is uncertain or the activity
# itself is genuinely ambiguous near boundaries.
#
# Metrics:
#   flip_rate         → fraction of consecutive window pairs where prediction changed
#   mean_run_length   → average number of windows in a row with the same prediction
#                       (longer = more stable)
#   flip_after_low_conf → do flips happen more often after a low-confidence window?
#                         yes → model flips when it's uncertain (expected, normal)
#                         no  → model flips even when confident (bad sign)

def compute_flip_rate(results, model_name, conf_threshold=0.5):
    acts = results['pred_activities']   # (n_windows,)
    confs = results['confidences']

    if len(acts) < 2:
        print(f'{model_name}: not enough windows for flip analysis')
        return

    # --- flip rate ---
    flips      = acts[1:] != acts[:-1]          # True where class changes
    flip_rate  = flips.mean()

    # --- run length (consecutive same-class windows) ---
    run_lengths = []
    run = 1
    for f in flips:
        if f:
            run_lengths.append(run)
            run = 1
        else:
            run += 1
    run_lengths.append(run)
    mean_run = np.mean(run_lengths)
    max_run  = np.max(run_lengths)

    # --- flip after low-conf ---
    low_conf_before_flip = flips & (confs[:-1] < conf_threshold)
    flip_after_low  = low_conf_before_flip.sum()
    flip_after_high = (flips & (confs[:-1] >= conf_threshold)).sum()
    total_flips = flips.sum()

    print(f'\n{"="*60}')
    print(f'  {model_name} — Flip Rate Analysis')
    print(f'{"="*60}')
    print(f'  Total windows          : {len(acts)}')
    print(f'  Consecutive pairs      : {len(flips)}')
    print(f'  Flip rate              : {flip_rate:.2%}  ({total_flips} flips)')
    print(f'  Mean run length        : {mean_run:.1f} windows  (stable streak)')
    print(f'  Max run length         : {max_run} windows')
    print(f'  Flips after low-conf   : {flip_after_low} / {total_flips}  ({flip_after_low/max(total_flips,1):.0%})')
    print(f'  Flips after high-conf  : {flip_after_high} / {total_flips}  ({flip_after_high/max(total_flips,1):.0%})')

    if flip_rate < 0.05:
        verdict = "Very stable — model is consistent across overlapping windows."
    elif flip_rate < 0.20:
        verdict = "Moderately stable — some transitions, likely near activity boundaries."
    elif flip_rate < 0.50:
        verdict = "Unstable — frequent class changes, model may be uncertain."
    else:
        verdict = "Highly unstable — model is flipping on nearly every window."
    print(f'\n  Verdict: {verdict}')

    # --- plot: flip map ---
    fig, axes = plt.subplots(2, 1, figsize=(14, 5), sharex=True)

    # Top: prediction sequence
    act_codes = np.array([ACTIVITY_MAPPING.get(a, -1) for a in acts])
    axes[0].step(range(len(act_codes)), act_codes, where='post', linewidth=1.2, color='steelblue')
    axes[0].set_yticks(list(ACTIVITY_MAPPING.values()))
    axes[0].set_yticklabels(list(ACTIVITY_MAPPING.keys()), fontsize=7)
    axes[0].set_ylabel('Predicted class')
    axes[0].set_title(f'{model_name} — Prediction sequence & flips  (flip rate={flip_rate:.1%})')
    axes[0].grid(alpha=0.3)

    # Mark flips as red dots on the top plot
    flip_positions = np.where(flips)[0] + 1
    axes[0].scatter(flip_positions, act_codes[flip_positions],
                    color='red', s=20, zorder=5, label=f'Flip ({total_flips})')
    axes[0].legend(fontsize=8)

    # Bottom: confidence with low-conf threshold line
    axes[1].fill_between(range(len(confs)), confs, alpha=0.5, color='steelblue')
    axes[1].axhline(conf_threshold, color='orange', linestyle='--', linewidth=1.5,
                    label=f'Threshold={conf_threshold}')
    axes[1].set_ylim(0, 1)
    axes[1].set_ylabel('Confidence')
    axes[1].set_xlabel('Window index')
    axes[1].legend(fontsize=8)
    axes[1].grid(alpha=0.3)

    plt.tight_layout()
    plt.show()

if results_pretrained:
    compute_flip_rate(results_pretrained, 'Pretrained Model', conf_threshold=CONFIDENCE_THRESHOLD)

if results_trained:
    compute_flip_rate(results_trained, 'Trained Model', conf_threshold=CONFIDENCE_THRESHOLD)

# %%
# ===== STEP 7: SAMPLE PREDICTIONS (Top-5 per window) =====

def show_top5_predictions(results, model_name, n_samples=5):
    """
    Display top-5 predicted activities for a sample of windows.
    """
    print(f'\n{model_name} - Top-5 Predictions (sample of {n_samples} windows):')
    print('=' * 80)
    
    for window_idx in range(min(n_samples, len(results['pred_activities']))):
        print(f'\nWindow {window_idx}:')
        print(f'  Predicted (main): {results["pred_activities"][window_idx]} (confidence: {results["confidences"][window_idx]:.4f})')
        print(f'  Top-5:')
        for rank, (activity, prob) in enumerate(zip(
            results['top5_names'][window_idx],
            results['top5_probs'][window_idx]
        ), 1):
            print(f'    {rank}. {activity}: {prob:.4f}')

if results_pretrained:
    show_top5_predictions(results_pretrained, 'PRETRAINED MODEL')

if results_trained:
    show_top5_predictions(results_trained, 'TRAINED MODEL')

# %% [markdown]
# ## Evaluation Metrics
# Computes accuracy, macro metrics, and confusion matrix values when labels are available.

# %%
# ===== STEP 8: EVALUATION METRICS (if labels available) =====

def compute_metrics(y_true, y_pred_activities, y_confidences, model_name, activity_mapping):
    """
    Compute accuracy, precision, recall, F1 (macro and per-class).
    Returns dict with all metrics.
    """
    # Convert activity names to indices for sklearn
    y_pred_idx = np.array([activity_mapping.get(act, -1) for act in y_pred_activities])
    y_true_idx = np.array([activity_mapping.get(act, -1) for act in y_true])
    
    # Filter out unmapped classes
    valid = (y_pred_idx != -1) & (y_true_idx != -1)
    y_true_idx = y_true_idx[valid]
    y_pred_idx = y_pred_idx[valid]
    y_confidences = y_confidences[valid]
    
    accuracy = accuracy_score(y_true_idx, y_pred_idx)
    precision_macro = precision_score(y_true_idx, y_pred_idx, average='macro', zero_division=0)
    recall_macro = recall_score(y_true_idx, y_pred_idx, average='macro', zero_division=0)
    f1_macro = f1_score(y_true_idx, y_pred_idx, average='macro', zero_division=0)
    
    # Per-class metrics
    report = classification_report(y_true_idx, y_pred_idx, output_dict=True, zero_division=0)
    
    # Confusion matrix
    cm = confusion_matrix(y_true_idx, y_pred_idx, labels=list(activity_mapping.values()))
    
    return {
        'model': model_name,
        'accuracy': accuracy,
        'precision_macro': precision_macro,
        'recall_macro': recall_macro,
        'f1_macro': f1_macro,
        'confidence_mean': y_confidences.mean(),
        'confidence_std': y_confidences.std(),
        'per_class_report': report,
        'confusion_matrix': cm,
        'y_true': y_true_idx,
        'y_pred': y_pred_idx,
        'confidences': y_confidences
    }

metrics_pretrained = None
metrics_trained = None

if y is not None:
    print('\n=== EVALUATION METRICS ===')
    
    if results_pretrained:
        print('\nPRETRAINED MODEL:')
        metrics_pretrained = compute_metrics(y, results_pretrained['pred_activities'],
                                              results_pretrained['confidences'],
                                              'Pretrained', ACTIVITY_MAPPING)
        print(f"  Accuracy: {metrics_pretrained['accuracy']:.4f}")
        print(f"  Precision (macro): {metrics_pretrained['precision_macro']:.4f}")
        print(f"  Recall (macro): {metrics_pretrained['recall_macro']:.4f}")
        print(f"  F1 (macro): {metrics_pretrained['f1_macro']:.4f}")
        print(f"  Confidence mean: {metrics_pretrained['confidence_mean']:.4f}")
        print(f"  Confidence std: {metrics_pretrained['confidence_std']:.4f}")
    
    if results_trained:
        print('\nTRAINED MODEL:')
        metrics_trained = compute_metrics(y, results_trained['pred_activities'],
                                           results_trained['confidences'],
                                           'Trained', ACTIVITY_MAPPING)
        print(f"  Accuracy: {metrics_trained['accuracy']:.4f}")
        print(f"  Precision (macro): {metrics_trained['precision_macro']:.4f}")
        print(f"  Recall (macro): {metrics_trained['recall_macro']:.4f}")
        print(f"  F1 (macro): {metrics_trained['f1_macro']:.4f}")
        print(f"  Confidence mean: {metrics_trained['confidence_mean']:.4f}")
        print(f"  Confidence std: {metrics_trained['confidence_std']:.4f}")
else:
    print('\nNo labels available - skipping evaluation metrics')

# %%
# ===== STEP 9: CONFUSION MATRICES =====

available = []
if metrics_pretrained:
    available.append((metrics_pretrained, 'Pretrained'))
if metrics_trained:
    available.append((metrics_trained, 'Trained'))

if available:
    fig, axes = plt.subplots(1, len(available), figsize=(7 * len(available), 6), squeeze=False)
    axes = axes.flatten()

    for ax, (metrics, name) in zip(axes, available):
        cm = metrics['confusion_matrix']
        cm_normalized = cm.astype('float') / (cm.sum(axis=1)[:, np.newaxis] + 1e-8)

        sns.heatmap(cm_normalized, annot=True, fmt='.2f', cmap='Blues',
                    xticklabels=list(ACTIVITY_MAPPING.keys()),
                    yticklabels=list(ACTIVITY_MAPPING.keys()),
                    cbar=True, ax=ax)
        ax.set_title(f'{name} Model - Normalized Confusion Matrix')
        ax.set_ylabel('True Label')
        ax.set_xlabel('Predicted Label')
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

    plt.tight_layout()
    plt.show()
else:
    print('No metrics available for confusion matrices')

# %%
# ===== STEP 10: CONFIDENCE DISTRIBUTIONS =====

available = []
if results_pretrained:
    available.append((results_pretrained, 'Pretrained'))
if results_trained:
    available.append((results_trained, 'Trained'))

if available:
    fig, axes = plt.subplots(1, len(available), figsize=(7 * len(available), 5), squeeze=False)
    axes = axes.flatten()

    for ax, (results, name) in zip(axes, available):
        ax.hist(results['confidences'], bins=30, alpha=0.7, edgecolor='black', color='steelblue')
        ax.axvline(results['confidences'].mean(), color='red', linestyle='--', linewidth=2,
                   label=f'Mean: {results["confidences"].mean():.3f}')
        ax.set_title(f'{name} Model - Confidence Distribution')
        ax.set_xlabel('Confidence Score')
        ax.set_ylabel('Frequency')
        ax.legend()
        ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.show()
else:
    print('No results available for confidence distributions')

# %%
# ===== STEP 11: PER-CLASS F1 SCORES =====

available = []
if metrics_pretrained:
    available.append((metrics_pretrained, 'Pretrained'))
if metrics_trained:
    available.append((metrics_trained, 'Trained'))

if available:
    fig, axes = plt.subplots(1, len(available), figsize=(7 * len(available), 6), squeeze=False)
    axes = axes.flatten()

    for ax, (metrics, name) in zip(axes, available):
        report = metrics['per_class_report']
        activities = list(ACTIVITY_MAPPING.keys())
        f1_scores = [report.get(act, {}).get('f1-score', 0) for act in activities]

        colors = ['#1f77b4' if f > 0 else '#d62728' for f in f1_scores]
        bars = ax.bar(activities, f1_scores, color=colors, alpha=0.7, edgecolor='black')
        ax.set_title(f'{name} Model - Per-Class F1 Scores')
        ax.set_ylabel('F1 Score')
        ax.set_ylim([0, 1])
        ax.grid(axis='y', alpha=0.3)
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

        for bar, score in zip(bars, f1_scores):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{score:.2f}', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.show()
else:
    print('No metrics available for per-class F1 scores')

# %%
# ===== STEP 12: PREDICTION TIMELINE (temporal sequence of predictions) =====

available = []
if results_pretrained:
    available.append((results_pretrained, 'Pretrained'))
if results_trained:
    available.append((results_trained, 'Trained'))

if available:
    activity_to_code = ACTIVITY_MAPPING

    fig, axes = plt.subplots(len(available), 1, figsize=(14, 4 * len(available)), squeeze=False)
    axes = axes.flatten()

    for ax, (results, name) in zip(axes, available):
        # Limit timeline to first 100 windows for readability
        window_range = min(100, len(results['pred_activities']))
        pred_codes = np.array([activity_to_code.get(act, -1) for act in results['pred_activities'][:window_range]])
        confidences = results['confidences'][:window_range]

        scatter = ax.scatter(range(window_range), pred_codes, c=confidences, cmap='RdYlGn',
                             s=100, alpha=0.7, edgecolor='black', vmin=0, vmax=1)
        ax.set_title(f'{name} Model - Prediction Timeline (first {window_range} windows, colored by confidence)')
        ax.set_ylabel('Predicted Activity (class code)')
        ax.set_xlabel('Window Index')
        ax.set_yticks(list(activity_to_code.values()))
        ax.set_yticklabels(list(activity_to_code.keys()), fontsize=8)
        ax.grid(alpha=0.3)

        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Confidence')

    plt.tight_layout()
    plt.show()
else:
    print('No results available for prediction timeline')

# %% [markdown]
# ## Data Drift Analysis
# Compares the current recording against training reference data using PSI, JSD, Z-mean, and Wasserstein distance.

# %%
# ===== DATA DRIFT ANALYSIS =====
# Compares training distribution (all_users_data_labeled.csv) vs current recording.
#
# Three complementary metrics — each answers a different question:
#
#  1. Z-score of means (grounded in YOUR training scaler)
#     — How many std-devs is this recording's mean away from training mean?
#     — Uses saved scaler from config.json (fit on users 1–4)
#     — |z| < 1.0 = normal,  1–2 = watch,  > 2 = flag
#
#  2. Population Stability Index (PSI)  ← PRIMARY metric
#     — Industry standard (banking/MLOps). Compares full distributions via bins.
#     — PSI < 0.10 = no drift,  0.10–0.20 = moderate,  > 0.20 = significant
#     — Formula: PSI = sum((actual% – expected%) * ln(actual%/expected%))
#
#  3. Jensen-Shannon Divergence (JSD)   ← SECONDARY metric
#     — Symmetric, bounded [0,1].  0=identical, 1=completely different.
#     — More stable than Wasserstein for mixed-scale sensor data.
#
#  4. Wasserstein distance kept as reference (raw scale, unbounded).

import json as _json
import matplotlib.gridspec as gridspec
from scipy.stats import wasserstein_distance
from scipy.spatial.distance import jensenshannon

# ── Load reference data ───────────────────────────────────────────────────────
REFERENCE_DATA_PATH = r"D:\study apply\ML Ops\MasterArbeit_MLops\data\all_users_data_labeled.csv"
PIPELINE_CONFIG     = r"D:\study apply\ML Ops\MasterArbeit_MLops\data\prepared\config.json"

print("Loading reference (training) data...")
ref_df  = pd.read_csv(REFERENCE_DATA_PATH)
cfg     = _json.loads(open(PIPELINE_CONFIG, encoding='utf-8').read())
TRAIN_MEAN  = np.array(cfg['scaler_mean'])   # per-axis mean from users 1-4
TRAIN_SCALE = np.array(cfg['scaler_scale'])  # per-axis std  from users 1-4
print(f"  Reference shape : {ref_df.shape}")
print(f"  Scaler mean     : {np.round(TRAIN_MEAN, 3)}")
print(f"  Scaler scale    : {np.round(TRAIN_SCALE, 3)}")

REF_COLS = ['Ax_w', 'Ay_w', 'Az_w', 'Gx_w', 'Gy_w', 'Gz_w']
CUR_COLS = list(accel_cols) + list(gyro_cols)
axis_pairs = list(zip(REF_COLS, CUR_COLS))

# ── PSI helper ────────────────────────────────────────────────────────────────
def compute_psi(expected, actual, n_bins=20):
    """Population Stability Index."""
    mn = min(expected.min(), actual.min())
    mx = max(expected.max(), actual.max())
    bins = np.linspace(mn, mx, n_bins + 1)
    exp_hist, _ = np.histogram(expected, bins=bins)
    act_hist, _ = np.histogram(actual,   bins=bins)
    eps = 1e-8
    exp_pct = (exp_hist + eps) / (exp_hist.sum() + eps)
    act_pct = (act_hist + eps) / (act_hist.sum() + eps)
    psi = np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct))
    return float(psi), bins, exp_pct, act_pct

def psi_label(p):
    if p < 0.10:  return 'NO DRIFT',       'green'
    if p < 0.20:  return 'MODERATE DRIFT', 'orange'
    return             'SIGNIFICANT',       'red'

def jsd_label(j):
    if j < 0.10:  return 'LOW',      'green'
    if j < 0.25:  return 'MODERATE', 'orange'
    return             'HIGH',       'red'

# ── Compute all metrics ───────────────────────────────────────────────────────
drift_results = {}
RNG = np.random.default_rng(42)

for i, (ref_col, cur_col) in enumerate(axis_pairs):
    ref_vals = ref_df[ref_col].dropna().values
    cur_vals = df_processed[cur_col].dropna().values
    if len(ref_vals) > 60_000:
        ref_vals = RNG.choice(ref_vals, 60_000, replace=False)

    psi_val, bins, exp_pct, act_pct = compute_psi(ref_vals, cur_vals)
    jsd_lo = float(min(ref_vals.min(), cur_vals.min()))
    jsd_hi = float(max(ref_vals.max(), cur_vals.max()))
    shared_bins = np.linspace(jsd_lo, jsd_hi, 51)
    jsd_val  = float(jensenshannon(
        np.histogram(ref_vals, bins=shared_bins, density=True)[0] + 1e-8,
        np.histogram(cur_vals, bins=shared_bins, density=True)[0] + 1e-8))
    wass_val = wasserstein_distance(ref_vals, cur_vals)
    zmean    = abs(cur_vals.mean() - TRAIN_MEAN[i]) / TRAIN_SCALE[i]

    psi_lbl, psi_clr = psi_label(psi_val)
    jsd_lbl, jsd_clr = jsd_label(jsd_val)
    z_lbl   = 'OK' if zmean < 1 else ('WATCH' if zmean < 2 else 'FLAG')
    z_clr   = 'green' if zmean < 1 else ('orange' if zmean < 2 else 'red')

    drift_results[ref_col] = dict(
        ref_col=ref_col, cur_col=cur_col,
        ref_mean=ref_vals.mean(), cur_mean=cur_vals.mean(),
        ref_std=ref_vals.std(),   cur_std=cur_vals.std(),
        psi=psi_val, psi_lbl=psi_lbl, psi_clr=psi_clr,
        jsd=jsd_val, jsd_lbl=jsd_lbl, jsd_clr=jsd_clr,
        wass=wass_val,
        zmean=zmean, z_lbl=z_lbl, z_clr=z_clr,
        ref_vals=ref_vals, cur_vals=cur_vals,
        bins=bins, exp_pct=exp_pct, act_pct=act_pct,
    )

# ── Print summary table ───────────────────────────────────────────────────────
print(f'\n{"="*90}')
print(f'{"Axis":<12} {"PSI":>8} {"PSI Status":<18} {"JSD":>6} {"JSD Status":<14} {"Z-mean":>8} {"Z Status":<8} {"Wasserstein":>12}')
print(f'{"-"*90}')
for col, r in drift_results.items():
    print(f'{col:<12} {r["psi"]:>8.4f} {r["psi_lbl"]:<18} '
          f'{r["jsd"]:>6.4f} {r["jsd_lbl"]:<14} '
          f'{r["zmean"]:>8.3f} {r["z_lbl"]:<8} '
          f'{r["wass"]:>12.4f}')

overall_psi  = np.mean([r['psi']  for r in drift_results.values()])
overall_jsd  = np.mean([r['jsd']  for r in drift_results.values()])
overall_wass = np.mean([r['wass'] for r in drift_results.values()])
overall_z    = np.mean([r['zmean'] for r in drift_results.values()])
print(f'{"-"*90}')
print(f'{"OVERALL":<12} {overall_psi:>8.4f} {psi_label(overall_psi)[0]:<18} '
      f'{overall_jsd:>6.4f} {jsd_label(overall_jsd)[0]:<14} '
      f'{overall_z:>8.3f} {"OK" if overall_z<1 else "WATCH":<8} '
      f'{overall_wass:>12.4f}')

# ── Plot 1: KDE overlay 2×3 grid ─────────────────────────────────────────────
fig = plt.figure(figsize=(17, 10))
fig.suptitle('Data Drift — Training vs Current  (KDE per axis)', fontsize=13, fontweight='bold')
gs = gridspec.GridSpec(2, 3, hspace=0.45, wspace=0.35)

for idx, (ref_col, _) in enumerate(axis_pairs):
    r  = drift_results[ref_col]
    ax = fig.add_subplot(gs[idx // 3, idx % 3])
    for vals, lbl, clr, alp in [
        (r['ref_vals'], 'Reference (train)', '#2196F3', 0.45),
        (r['cur_vals'], 'Current',           '#FF5722', 0.45),
    ]:
        counts, bins_ = np.histogram(vals, bins=80, density=True)
        bc = (bins_[:-1] + bins_[1:]) / 2
        ax.fill_between(bc, counts, alpha=alp, color=clr, label=lbl)
        ax.plot(bc, counts, color=clr, lw=1.1)
    ax.set_title(
        f'{ref_col}  |  PSI={r["psi"]:.3f} ({r["psi_lbl"]})',
        color=r['psi_clr'], fontweight='bold', fontsize=9)
    ax.set_xlabel('Value', fontsize=8); ax.set_ylabel('Density', fontsize=8)
    ax.legend(fontsize=7); ax.grid(alpha=0.3)
plt.show()

# ── Plot 2: PSI bar chart (primary) ──────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(18, 4))
fig.suptitle('Drift Metrics per Axis', fontsize=12, fontweight='bold')

for ax, (metric, thresh_lo, thresh_hi, ylabel, title) in zip(axes, [
    ('psi',  0.10, 0.20, 'PSI',  'PSI  (primary — industry standard)'),
    ('jsd',  0.10, 0.25, 'JSD',  'Jensen-Shannon Divergence  [0–1]'),
    ('zmean',1.0,  2.0,  '|Z|',  'Z-score of means  (vs training scaler)'),
]):
    vals   = [drift_results[k][metric] for k in REF_COLS]
    colors = [drift_results[k]['psi_clr' if metric=='psi' else
                               'jsd_clr' if metric=='jsd' else 'z_clr']
              for k in REF_COLS]
    bars = ax.bar(REF_COLS, vals, color=colors, alpha=0.8, edgecolor='black')
    ax.axhline(thresh_lo, color='orange', linestyle='--', lw=1.5,
               label=f'Moderate >{thresh_lo}')
    ax.axhline(thresh_hi, color='red',    linestyle='--', lw=1.5,
               label=f'Significant >{thresh_hi}')
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.002,
                f'{val:.3f}', ha='center', va='bottom', fontsize=8)
    ax.set_title(title, fontsize=9); ax.set_ylabel(ylabel)
    ax.legend(fontsize=7); ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.show()

# ── Legend ────────────────────────────────────────────────────────────────────
print('\nDrift Thresholds:')
print('  PSI  < 0.10  → No drift       | 0.10–0.20 → Moderate | > 0.20 → Significant')
print('  JSD  < 0.10  → Low            | 0.10–0.25 → Moderate | > 0.25 → High')
print('  |Z|  < 1.0   → Normal         | 1.0–2.0   → Watch    | > 2.0  → Flag')
print('  Wasserstein  kept for reference (raw scale, compare axes only within this run)')

# %% [markdown]
# ## Final Summary
# Prints the key preprocessing, model, evaluation, and drift results in one place.

# %%
# ===== FINAL SUMMARY REPORT =====

print('\n' + '='*80)
print('FINAL SUMMARY REPORT')
print('='*80)

print(f'\n[Data]')
print(f'  Raw shape          : {df_raw.shape}')
print(f'  Processed shape    : {df_processed.shape}')
print(f'  Windows generated  : {X.shape[0]}')
print(f'  Window size        : {WINDOW_SIZE} samples  |  Overlap: {WINDOW_OVERLAP*100:.0f}%')

print(f'\n[Preprocessing]')
print(f'  Unit conversion    : {UNIT_CONVERSION}')
print(f'  Gravity removal    : {GRAVITY_REMOVAL}')
print(f'  Z-score norm       : {ZSCORE_NORMALIZATION}')
print(f'  Accel cols         : {accel_cols}')
print(f'  Gyro  cols         : {gyro_cols}')
print(f'  Labels             : {label_col}  (has_labels={y is not None})')

for res, name in [(results_pretrained,'PRETRAINED'), (results_trained,'TRAINED')]:
    if res is None:
        continue
    c, ent, mar = res['confidences'], res['entropy'], res['margin']
    low = (c < CONFIDENCE_THRESHOLD).mean()
    print(f'\n[{name} MODEL — Confidence]')
    print(f'  Mean±std           : {c.mean():.4f} ± {c.std():.4f}')
    print(f'  Min / Max          : {c.min():.4f} / {c.max():.4f}')
    print(f'  Low-conf rate      : {low:.2%}  (threshold={CONFIDENCE_THRESHOLD})')
    print(f'  Entropy mean       : {ent.mean():.4f}  |  Margin mean: {mar.mean():.4f}')
    print(f'  Ambiguous windows  : {(mar < 0.10).mean():.2%}')

for mets, name in [(metrics_pretrained,'PRETRAINED'), (metrics_trained,'TRAINED')]:
    if mets is None:
        continue
    print(f'\n[{name} MODEL — Evaluation]')
    print(f'  Accuracy           : {mets["accuracy"]:.4f}')
    print(f'  Precision (macro)  : {mets["precision_macro"]:.4f}')
    print(f'  Recall (macro)     : {mets["recall_macro"]:.4f}')
    print(f'  F1 (macro)         : {mets["f1_macro"]:.4f}')

if metrics_pretrained and metrics_trained:
    print(f'\n[MODEL COMPARISON]')
    print(f'  Accuracy Δ         : {metrics_trained["accuracy"]  - metrics_pretrained["accuracy"]:+.4f}')
    print(f'  F1 Δ               : {metrics_trained["f1_macro"]  - metrics_pretrained["f1_macro"]:+.4f}')

if drift_results:
    print(f'\n[DATA DRIFT SUMMARY]')
    print(f'  {"Axis":<12} {"PSI":>8}  {"PSI Status":<18} {"JSD":>6}  {"Z-mean":>7}  {"Z Status"}')
    print(f'  {"-"*65}')
    for col, r in drift_results.items():
        print(f'  {col:<12} {r["psi"]:>8.4f}  {r["psi_lbl"]:<18} {r["jsd"]:>6.4f}  {r["zmean"]:>7.3f}  {r["z_lbl"]}')
    overall_psi = np.mean([r['psi'] for r in drift_results.values()])
    overall_jsd = np.mean([r['jsd'] for r in drift_results.values()])
    overall_z   = np.mean([r['zmean'] for r in drift_results.values()])
    p_lbl = psi_label(overall_psi)[0]
    j_lbl = jsd_label(overall_jsd)[0]
    z_lbl = 'OK' if overall_z < 1 else ('WATCH' if overall_z < 2 else 'FLAG')
    print(f'  {"-"*65}')
    print(f'  {"OVERALL":<12} {overall_psi:>8.4f}  {p_lbl:<18} {overall_jsd:>6.4f}  {overall_z:>7.3f}  {z_lbl}')

print(f'\n' + '='*80)
