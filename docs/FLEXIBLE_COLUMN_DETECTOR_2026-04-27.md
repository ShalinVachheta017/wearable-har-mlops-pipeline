# Flexible Column Detector — Accept Any Sensor Naming Convention

**Date**: 2026-04-27  
**What**: Pipeline now automatically detects and standardizes sensor column names from any convention.  
**Why**: Training data, production data, and synthetic data may use different column naming schemes (Ax_w vs Ax vs accel_x). The detector handles all of them without manual remapping.

---

## Problem Solved

Before this change:
- Training data: `Ax_w, Ay_w, Az_w, Gx_w, Gy_w, Gz_w` (wrist convention)
- Production data: `Ax, Ay, Az, Gx, Gy, Gz` (standard convention)
- Synthetic data: `accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z` (generic convention)

**Result**: Pipeline would reject production/synthetic data with "unknown data format" error.

After this change:
- **One detector handles all three**, automatically renaming columns to internal standard `[Ax, Ay, Az, Gx, Gy, Gz]`.
- **No manual remapping needed** — each data source just works.
- **Errors are clear** — if any sensor is truly missing, the error message lists what was found vs what was needed.

---

## How It Works

### 1. Detection Phase
The detector looks for any of these patterns per axis (case-insensitive):

| Axis | Acceptable patterns |
|---|---|
| **Ax** | `Ax`, `AX`, `ax`, `Ax_w`, `accel_x`, `accel_X`, `accel-x` |
| **Ay** | `Ay`, `AY`, `ay`, `Ay_w`, `accel_y`, `accel_Y`, `accel-y` |
| **Az** | `Az`, `AZ`, `az`, `Az_w`, `accel_z`, `accel_Z`, `accel-z` |
| **Gx** | `Gx`, `GX`, `gx`, `Gx_w`, `gyro_x`, `gyro_X`, `gyro-x` |
| **Gy** | `Gy`, `GY`, `gy`, `Gy_w`, `gyro_y`, `gyro_Y`, `gyro-y` |
| **Gz** | `Gz`, `GZ`, `gz`, `Gz_w`, `gyro_z`, `gyro_Z`, `gyro-z` |

### 2. Matching Strategy
1. Iterate over available columns in the DataFrame.
2. For each axis (Ax, Ay, Az, Gx, Gy, Gz), try to match one of the regex patterns.
3. First successful match wins.
4. After matching, rename the original column to the canonical name.

### 3. Standardization Phase
Once all 6 axes are found, the detector renames columns in-place:
```
Original columns: [Ax_w, Ay_w, Az_w, Gx_w, Gy_w, Gz_w]
       ↓ (rename)
Canonical form:  [Ax,   Ay,   Az,   Gx,   Gy,   Gz]
```

The renamed DataFrame is then used for all downstream processing (unit conversion, normalization, scaler application, model inference).

---

## Data Sources Tested

| Source | Naming Convention | Status |
|---|---|---|
| Training (ADAM-SENSE labeled) | `Ax_w, Ay_w, Az_w, Gx_w, Gy_w, Gz_w` | ✓ Passes |
| Production (calibrated accel+gyro) | `Ax, Ay, Az, Gx, Gy, Gz` | ✓ Passes |
| Synthetic production | `accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z` | ✓ Passes |
| Mixed case | `AX, aY, Az, GX, gY, GZ` | ✓ Passes |
| Labeled production (synthetic) | `Ax, Ay, Az, Gx, Gy, Gz` + `activity` column | ✓ Passes |

---

## Implementation Details

### Code Location
[src/preprocess_data.py](../src/preprocess_data.py) — `UnifiedPreprocessor._detect_sensor_columns()`

### Key Methods

#### `detect_data_format(df: pd.DataFrame) -> (str, List[str])`
**Public API** — called by the pipeline.

- Accepts DataFrame with any sensor column naming.
- **Modifies DataFrame in-place**: renames sensor columns to canonical form.
- Returns `(format, canonical_columns)` where format is `"labeled"` or `"unlabeled"`.

```python
data_format, sensor_cols = preprocessor.detect_data_format(df)
# df now has columns [Ax, Ay, Az, Gx, Gy, Gz, ...]
# sensor_cols = ['Ax', 'Ay', 'Az', 'Gx', 'Gy', 'Gz']
```

#### `_detect_sensor_columns(df: pd.DataFrame) -> (List[str], str)`
**Internal method** — pattern matching logic.

- Tries to find all 6 sensor axes.
- Returns original column names in canonical axis order + pattern description.

---

## Error Handling

If any sensor axis is missing:
```
ValueError: Could not detect all sensor columns. Missing: [Gy, Gz]. 
Found: [Ax, Ay, Az, Gx]. Available columns: ['Ax', 'Ay', 'Az', 'Gx', 'timestamp', ...]
```

Clear, actionable error messages help diagnose column issues.

---

## Usage Examples

### Example 1: Production data (standard naming)
```python
import pandas as pd
from src.preprocess_data import UnifiedPreprocessor, PreprocessLogger

df = pd.read_csv("data/raw/accel_gyro_2025_07_16.csv")
# Columns: ['Ax', 'Ay', 'Az', 'Gx', 'Gy', 'Gz', 'timestamp']

prep_logger = PreprocessLogger().get_logger()
preprocessor = UnifiedPreprocessor(logger=prep_logger, window_size=200, overlap=0.5)

fmt, cols = preprocessor.detect_data_format(df)
# fmt = 'unlabeled'
# cols = ['Ax', 'Ay', 'Az', 'Gx', 'Gy', 'Gz']
# df is now renamed (columns are standardized)
```

### Example 2: Training data (wrist naming)
```python
df_train = pd.read_csv("27 april meet/all_users_data_labeled.csv")
# Columns: ['Ax_w', 'Ay_w', 'Az_w', 'Gx_w', 'Gy_w', 'Gz_w', 'activity', 'User']

fmt, cols = preprocessor.detect_data_format(df_train)
# fmt = 'labeled'  (because activity column exists)
# cols = ['Ax', 'Ay', 'Az', 'Gx', 'Gy', 'Gz']
# df_train now has columns ['Ax', 'Ay', 'Az', 'Gx', 'Gy', 'Gz', 'activity', 'User']
```

### Example 3: Synthetic data (generic naming)
```python
df_synth = pd.read_csv("data/synthetic_production/synthetic_production_01.csv")
# Columns: ['accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y', 'gyro_z', 'timestamp']

fmt, cols = preprocessor.detect_data_format(df_synth)
# fmt = 'unlabeled'
# cols = ['Ax', 'Ay', 'Az', 'Gx', 'Gy', 'Gz']
# df_synth now has columns ['Ax', 'Ay', 'Az', 'Gx', 'Gy', 'Gz', 'timestamp']
```

---

## Pipeline Flow

```
Raw Data (any naming convention)
         ↓
detect_data_format()  ← FLEXIBLE DETECTION
         ↓
Standardized columns [Ax, Ay, Az, Gx, Gy, Gz]
         ↓
Unit detection & conversion (milliG → m/s²)
         ↓
Gravity removal (optional)  OR  Domain calibration (optional)
         ↓
Normalization (z-score or robust)
         ↓
Windowing (4 s @ 50 Hz)
         ↓
Model inference
```

---

## Backwards Compatibility

This change is **fully backwards compatible**:
- Existing code that expects `[Ax, Ay, Az, Gx, Gy, Gz]` still works — the detector produces exactly those names.
- Code that passed in already-canonical data sees no difference.
- The renaming happens silently in-place.

---

## Future Extensions

Possible enhancements (not yet implemented):
1. **Custom mappings**: accept user-provided column mapping dict.
2. **Partial sensor sets**: handle data with only accelerometer (3 axes) or gyroscope (3 axes).
3. **Auto-detection of units**: detect if columns are already normalized or still raw.
4. **Sensor fusion**: accept multi-IMU setups with multiple sensor suites.

---

## Testing

Test cases in [src/preprocess_data.py](../src/preprocess_data.py):
- ✓ Standard naming (Ax, Ay, Az, Gx, Gy, Gz)
- ✓ Wrist naming (Ax_w, Ay_w, Az_w, Gx_w, Gy_w, Gz_w)
- ✓ Generic naming (accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z)
- ✓ Mixed case (AX, aY, Az, GX, gY, GZ)
- ✓ Labeled production (sensors + activity column)

Run tests:
```bash
python -c "from src.preprocess_data import ...; ..."  # See test code above
```

---

## Summary

The pipeline is now **smart about column names**:
- ✓ No manual remapping per data source
- ✓ Clear error messages if sensors are missing
- ✓ Works with training, production, and synthetic data
- ✓ Backwards compatible

**Result**: Model receives correctly standardized, properly scaled inputs regardless of the original data source's naming convention.
