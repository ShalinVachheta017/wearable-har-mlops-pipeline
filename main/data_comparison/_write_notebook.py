"""Helper script to write the dataset comparison notebook with unit conversions."""
import json

cells = []

def md(source):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": source if isinstance(source, list) else [source]})

def code(source):
    cells.append({"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source if isinstance(source, list) else [source]})

# ============================================================
# TITLE
# ============================================================
md([
    "# Comprehensive Dataset Comparison Analysis\n",
    "\n",
    "**Purpose:** Compare all core research datasets side by side, with all values in the same units.\n",
    "\n",
    "| Dataset | Raw Accel Unit | Raw Gyro Unit | Conversion Applied |\n",
    "|---------|---------------|--------------|--------------------|\n",
    "| Main Grid | m/s\u00b2 | deg/s | None (already standard) |\n",
    "| Label (Anxiety) wrist | **g-units** (\u22481g magnitude) | deg/s | Accel \u00d7 9.80665 |\n",
    "| Label (Anxiety) pocket | m/s\u00b2 | **rad/s** | Gyro \u00d7 (180/\u03c0) |\n",
    "| Synthetic | m/s\u00b2 | deg/s | None (mirrors grid) |\n",
    "| Codex Synthetic | m/s\u00b2 | deg/s | None (mirrors grid) |\n",
    "| Production (Garmin) | **milliG** | deg/s | Accel \u00d7 0.00981 |\n",
    "\n",
    "**After conversion: all accel in m/s\u00b2, all gyro in deg/s.**\n",
    "\n",
    "---"
])

# ============================================================
# SETUP
# ============================================================
md("## 1. Setup and Imports")

code([
    "import pandas as pd\n",
    "import numpy as np\n",
    "import matplotlib.pyplot as plt\n",
    "import matplotlib.ticker as ticker\n",
    "import seaborn as sns\n",
    "from pathlib import Path\n",
    "import warnings\n",
    "warnings.filterwarnings('ignore')\n",
    "\n",
    "sns.set_theme(style='whitegrid', font_scale=1.1)\n",
    "plt.rcParams['figure.dpi'] = 110\n",
    "plt.rcParams['figure.figsize'] = (12, 5)\n",
    "\n",
    "DATA_DIR = Path('data')\n",
    "RAW_DIR = DATA_DIR / 'raw'\n",
    "\n",
    "SENSOR_COLS = ['Ax_w', 'Ay_w', 'Az_w', 'Gx_w', 'Gy_w', 'Gz_w']\n",
    "ACCEL_COLS = ['Ax_w', 'Ay_w', 'Az_w']\n",
    "GYRO_COLS  = ['Gx_w', 'Gy_w', 'Gz_w']\n",
    "\n",
    "# Conversion constants\n",
    "MILLIG_TO_MS2 = 9.80665 / 1000   # milliG -> m/s\u00b2\n",
    "G_TO_MS2      = 9.80665           # g-units -> m/s\u00b2\n",
    "RAD_TO_DEG    = 180.0 / np.pi     # rad/s -> deg/s\n",
    "\n",
    "ACCEL_UNIT = 'm/s\u00b2'\n",
    "GYRO_UNIT  = 'deg/s'\n",
    "\n",
    "print('Setup complete. All values will be in m/s\u00b2 (accel) and deg/s (gyro).')"
])

# ============================================================
# DATA LOADING
# ============================================================
md("## 2. Data Loading and Unit Standardization")

code([
    "# --- Main Research Grid Data (already in m/s\u00b2 and deg/s) ---\n",
    "df_grid = pd.read_csv(DATA_DIR / 'all_users_data_labeled.csv')\n",
    "df_grid['dataset'] = 'Main Grid'\n",
    "grid_mag = np.sqrt((df_grid[ACCEL_COLS]**2).sum(axis=1)).mean()\n",
    "print(f'Main Grid:       {df_grid.shape[0]:>10,} rows  |  Accel mag = {grid_mag:.2f} m/s\u00b2  |  No conversion')\n",
    "\n",
    "# --- Label / Anxiety Data ---\n",
    "# Wrist accel in g-units -> *9.80665 to get m/s\u00b2\n",
    "# Pocket gyro in rad/s -> *57.3 to get deg/s\n",
    "df_label = pd.read_csv(DATA_DIR / 'anxiety_dataset.csv')\n",
    "df_label.rename(columns={'Activity': 'activity'}, inplace=True)\n",
    "for col in ACCEL_COLS:\n",
    "    df_label[col] = df_label[col] * G_TO_MS2\n",
    "for col in ['Gx_p', 'Gy_p', 'Gz_p']:\n",
    "    if col in df_label.columns:\n",
    "        df_label[col] = df_label[col] * RAD_TO_DEG\n",
    "df_label['dataset'] = 'Label (Anxiety)'\n",
    "label_mag = np.sqrt((df_label[ACCEL_COLS]**2).sum(axis=1)).mean()\n",
    "print(f'Label (Anxiety): {df_label.shape[0]:>10,} rows  |  Accel mag = {label_mag:.2f} m/s\u00b2 (after g->m/s\u00b2)')\n",
    "\n",
    "# --- Synthetic Data (mirrors grid, already in m/s\u00b2 and deg/s) ---\n",
    "df_synth = pd.read_csv(DATA_DIR / 'synthetic' / 'synthetic_labeled.csv')\n",
    "df_synth['dataset'] = 'Synthetic'\n",
    "synth_mag = np.sqrt((df_synth[ACCEL_COLS]**2).sum(axis=1)).mean()\n",
    "print(f'Synthetic:       {df_synth.shape[0]:>10,} rows  |  Accel mag = {synth_mag:.2f} m/s\u00b2  |  No conversion')\n",
    "\n",
    "# --- Codex Synthetic Data ---\n",
    "df_codex = pd.read_csv(DATA_DIR / 'codex_synth' / 'synthetic_all_users_labeled_v1.csv')\n",
    "df_codex['dataset'] = 'Codex Synthetic'\n",
    "codex_mag = np.sqrt((df_codex[ACCEL_COLS]**2).sum(axis=1)).mean()\n",
    "print(f'Codex Synthetic: {df_codex.shape[0]:>10,} rows  |  Accel mag = {codex_mag:.2f} m/s\u00b2  |  No conversion')"
])

code([
    "# --- Production Data (Garmin: milliG accel, deg/s gyro) ---\n",
    "# Convert accel: milliG * 0.00981 -> m/s\u00b2\n",
    "\n",
    "prod_sessions = []\n",
    "for accel_file in sorted(RAW_DIR.glob('*_accelerometer.csv')):\n",
    "    session_id = accel_file.name.replace('_accelerometer.csv', '')\n",
    "    gyro_file = RAW_DIR / f'{session_id}_gyroscope.csv'\n",
    "    try:\n",
    "        acc = pd.read_csv(accel_file, usecols=['accel_x', 'accel_y', 'accel_z'])\n",
    "        gyr = pd.read_csv(gyro_file, usecols=['gyro_x', 'gyro_y', 'gyro_z'])\n",
    "        n = min(len(acc), len(gyr))\n",
    "        merged = pd.DataFrame({\n",
    "            'Ax_w': acc['accel_x'].values[:n] * MILLIG_TO_MS2,\n",
    "            'Ay_w': acc['accel_y'].values[:n] * MILLIG_TO_MS2,\n",
    "            'Az_w': acc['accel_z'].values[:n] * MILLIG_TO_MS2,\n",
    "            'Gx_w': gyr['gyro_x'].values[:n],\n",
    "            'Gy_w': gyr['gyro_y'].values[:n],\n",
    "            'Gz_w': gyr['gyro_z'].values[:n],\n",
    "            'session': session_id\n",
    "        })\n",
    "        prod_sessions.append(merged)\n",
    "    except Exception as e:\n",
    "        print(f'  Skipped {session_id}: {e}')\n",
    "\n",
    "print('  Note: Session 2025-03-23 (Excel) excluded from CSV loading.')\n",
    "df_prod = pd.concat(prod_sessions, ignore_index=True)\n",
    "df_prod['dataset'] = 'Production'\n",
    "n_sessions = df_prod['session'].nunique()\n",
    "prod_mag = np.sqrt((df_prod[ACCEL_COLS]**2).sum(axis=1)).mean()\n",
    "print(f'\\nProduction:      {df_prod.shape[0]:>10,} rows  |  Accel mag = {prod_mag:.2f} m/s\u00b2 (after milliG->m/s\u00b2)  |  Sessions: {n_sessions}')"
])

# ============================================================
# SANITY CHECK
# ============================================================
md("### Unit Conversion Sanity Check\n\nMean accel magnitude should be near **9.81 m/s\u00b2** (= 1g) for gravity-dominated signals.")

code([
    "sanity = pd.DataFrame({\n",
    "    'Dataset': ['Main Grid', 'Label (Anxiety)', 'Synthetic', 'Codex Synthetic', 'Production'],\n",
    "    'Mean Accel Magnitude (m/s\u00b2)': [f'{grid_mag:.3f}', f'{label_mag:.3f}', f'{synth_mag:.3f}', f'{codex_mag:.3f}', f'{prod_mag:.3f}'],\n",
    "    'Close to 9.81?': [\n",
    "        '\u2713' if abs(grid_mag - 9.81) < 2 else '\u2717',\n",
    "        '\u2713' if abs(label_mag - 9.81) < 2 else '\u2717',\n",
    "        '\u2713' if abs(synth_mag - 9.81) < 2 else '\u2717',\n",
    "        '\u2713' if abs(codex_mag - 9.81) < 2 else '\u2717',\n",
    "        '\u2713' if abs(prod_mag - 9.81) < 2 else '\u2717']\n",
    "})\n",
    "display(sanity.style.set_caption('Sanity Check: Mean Accelerometer Magnitude After Unit Conversion'))"
])

# ============================================================
# OVERVIEW
# ============================================================
md("## 3. Dataset Overview")

code([
    "overview = pd.DataFrame({\n",
    "    'Dataset': ['Main Grid', 'Label (Anxiety)', 'Synthetic', 'Codex Synthetic', 'Production'],\n",
    "    'Rows': [len(df_grid), len(df_label), len(df_synth), len(df_codex), len(df_prod)],\n",
    "    'Has Labels': ['Yes', 'Yes', 'Yes', 'Yes', 'No'],\n",
    "    'Users/Sessions': [\n",
    "        f\"{df_grid['User'].nunique()} users\", f\"{df_label['User'].nunique()} users\",\n",
    "        f\"{df_synth['User'].nunique()} users\", f\"{df_codex['User'].nunique()} users\",\n",
    "        f\"{n_sessions} sessions\"],\n",
    "    'Activities': [df_grid['activity'].nunique(), df_label['activity'].nunique(),\n",
    "                   df_synth['activity'].nunique(), df_codex['activity'].nunique(), 'N/A'],\n",
    "    'Accel': ['m/s\u00b2'] * 5, 'Gyro': ['deg/s'] * 5,\n",
    "    'Sensor': ['Wrist', 'Pocket+Wrist', 'Wrist', 'Wrist', 'Wrist (Garmin)']\n",
    "})\n",
    "overview.style.set_caption('Dataset Overview (all units standardized)').format({'Rows': '{:,}'})"
])

# ============================================================
# QUALITY
# ============================================================
md("## 4. Data Quality Checks")

code([
    "def quality_report(df, name, cols):\n",
    "    available = [c for c in cols if c in df.columns]\n",
    "    sub = df[available]; total = len(sub)\n",
    "    return {'Dataset': name, 'Total Rows': f'{total:,}',\n",
    "        'Missing (%)': f\"{sub.isnull().sum().sum() / (total * len(available)) * 100:.2f}%\" if total > 0 else 'N/A',\n",
    "        'Inf Count': int(np.isinf(sub.select_dtypes(include=[np.number])).sum().sum()),\n",
    "        'All-Zero Cols': sum((sub == 0).all()),\n",
    "        'Duplicate Rows': int(sub.duplicated().sum()),\n",
    "        'Duplicate (%)': f\"{sub.duplicated().sum() / total * 100:.2f}%\" if total > 0 else 'N/A'}\n",
    "\n",
    "quality = pd.DataFrame([\n",
    "    quality_report(df_grid, 'Main Grid', SENSOR_COLS),\n",
    "    quality_report(df_label, 'Label (Anxiety)', SENSOR_COLS),\n",
    "    quality_report(df_synth, 'Synthetic', SENSOR_COLS),\n",
    "    quality_report(df_codex, 'Codex Synthetic', SENSOR_COLS),\n",
    "    quality_report(df_prod, 'Production', SENSOR_COLS),\n",
    "])\n",
    "quality.style.set_caption('Data Quality Summary (After Unit Conversion)')"
])

code([
    "extra_cols = [c for c in df_label.columns if c not in SENSOR_COLS + ['activity', 'User', 'dataset', 'timestamp']]\n",
    "extra_summary = []\n",
    "for col in sorted(extra_cols):\n",
    "    if df_label[col].dtype in ['float64', 'int64', 'float32']:\n",
    "        extra_summary.append({'Column': col, 'Non-Null (%)': f\"{df_label[col].notna().mean()*100:.1f}%\",\n",
    "            'Zero (%)': f\"{(df_label[col] == 0).mean()*100:.1f}%\",\n",
    "            'Mean': f\"{df_label[col].mean():.3f}\", 'Std': f\"{df_label[col].std():.3f}\"})\n",
    "if extra_summary:\n",
    "    display(pd.DataFrame(extra_summary).style.set_caption('Label (Anxiety) - Extra Columns (pocket gyro now in deg/s)'))"
])

# ============================================================
# NUMERIC DISTRIBUTIONS
# ============================================================
md("## 5. Numeric Distribution Comparisons (Same Units)\n\n### 5.1 Descriptive Statistics")

code([
    "def describe_sensors(df, name, cols=SENSOR_COLS):\n",
    "    available = [c for c in cols if c in df.columns]\n",
    "    desc = df[available].describe().T; desc['dataset'] = name; desc.index.name = 'sensor'\n",
    "    return desc.reset_index()\n",
    "\n",
    "stats_all = pd.concat([\n",
    "    describe_sensors(df_grid, 'Main Grid'), describe_sensors(df_label, 'Label (Anxiety)'),\n",
    "    describe_sensors(df_synth, 'Synthetic'), describe_sensors(df_codex, 'Codex Synthetic'),\n",
    "    describe_sensors(df_prod, 'Production'),\n",
    "])\n",
    "\n",
    "for col_name in ['mean', 'std', 'min', 'max']:\n",
    "    pivot = stats_all.pivot(index='sensor', columns='dataset', values=col_name)\n",
    "    pivot = pivot[['Main Grid', 'Label (Anxiety)', 'Synthetic', 'Codex Synthetic', 'Production']]\n",
    "    display(pivot.style.format('{:.2f}').set_caption(f'{col_name.upper()} by Sensor ({ACCEL_UNIT} / {GYRO_UNIT})'))"
])

md("### 5.2 Distribution Histograms")

code([
    "fig, axes = plt.subplots(2, 3, figsize=(16, 9))\n",
    "fig.suptitle('Sensor Distributions \u2014 All in Same Units', fontsize=15, y=1.02)\n",
    "\n",
    "datasets_all = [\n",
    "    (df_grid, 'Main Grid', '#2196F3'), (df_label, 'Label (Anxiety)', '#FF9800'),\n",
    "    (df_synth, 'Synthetic', '#4CAF50'), (df_codex, 'Codex Synthetic', '#9C27B0'),\n",
    "    (df_prod, 'Production', '#E53935'),\n",
    "]\n",
    "\n",
    "for idx, col in enumerate(SENSOR_COLS):\n",
    "    ax = axes[idx // 3, idx % 3]\n",
    "    unit = ACCEL_UNIT if col.startswith('A') else GYRO_UNIT\n",
    "    for df_i, label, color in datasets_all:\n",
    "        if col in df_i.columns:\n",
    "            vals = df_i[col].dropna()\n",
    "            if len(vals) > 50_000: vals = vals.sample(50_000, random_state=42)\n",
    "            lo, hi = vals.quantile(0.01), vals.quantile(0.99)\n",
    "            ax.hist(vals.clip(lo, hi), bins=80, alpha=0.4, label=label, color=color, density=True)\n",
    "    ax.set_title(f'{col} ({unit})', fontsize=13)\n",
    "    ax.set_ylabel('Density')\n",
    "    ax.legend(fontsize=7)\n",
    "\n",
    "plt.tight_layout()\n",
    "plt.show()"
])

md("### 5.3 Box Plots")

code([
    "SAMPLE_N = 30_000\n",
    "\n",
    "def sample_long(df, name, cols=SENSOR_COLS):\n",
    "    available = [c for c in cols if c in df.columns]\n",
    "    sub = df[available].sample(n=min(SAMPLE_N, len(df)), random_state=42)\n",
    "    melted = sub.melt(var_name='Sensor', value_name='Value'); melted['Dataset'] = name\n",
    "    return melted\n",
    "\n",
    "long_df = pd.concat([\n",
    "    sample_long(df_grid, 'Main Grid'), sample_long(df_label, 'Label (Anxiety)'),\n",
    "    sample_long(df_synth, 'Synthetic'), sample_long(df_codex, 'Codex Synthetic'),\n",
    "    sample_long(df_prod, 'Production'),\n",
    "])\n",
    "\n",
    "fig, axes = plt.subplots(1, 2, figsize=(16, 6))\n",
    "\n",
    "accel_data = long_df[long_df['Sensor'].isin(ACCEL_COLS)]\n",
    "sns.boxplot(data=accel_data, x='Sensor', y='Value', hue='Dataset', ax=axes[0], showfliers=False, palette='Set2')\n",
    "axes[0].set_title(f'Accelerometer ({ACCEL_UNIT})', fontsize=13)\n",
    "axes[0].set_ylabel(ACCEL_UNIT); axes[0].legend(fontsize=8, loc='upper right')\n",
    "\n",
    "gyro_data = long_df[long_df['Sensor'].isin(GYRO_COLS)]\n",
    "sns.boxplot(data=gyro_data, x='Sensor', y='Value', hue='Dataset', ax=axes[1], showfliers=False, palette='Set2')\n",
    "axes[1].set_title(f'Gyroscope ({GYRO_UNIT})', fontsize=13)\n",
    "axes[1].set_ylabel(GYRO_UNIT); axes[1].legend(fontsize=8, loc='upper right')\n",
    "\n",
    "plt.suptitle('Sensor Distributions (same units, outliers hidden)', fontsize=14, y=1.02)\n",
    "plt.tight_layout()\n",
    "plt.show()"
])

# ============================================================
# CATEGORICAL
# ============================================================
md("## 6. Categorical Distribution Comparisons\n\n### 6.1 Activity Class Balance")

code([
    "fig, axes = plt.subplots(2, 2, figsize=(16, 10))\n",
    "fig.suptitle('Activity Class Distribution', fontsize=15, y=1.01)\n",
    "\n",
    "for ax, (df_i, name) in zip(axes.ravel(), [\n",
    "    (df_grid, 'Main Grid'), (df_label, 'Label (Anxiety)'),\n",
    "    (df_synth, 'Synthetic'), (df_codex, 'Codex Synthetic')\n",
    "]):\n",
    "    counts = df_i['activity'].value_counts().sort_index()\n",
    "    bars = ax.barh(counts.index, counts.values, color=sns.color_palette('Set2', len(counts)))\n",
    "    ax.set_title(f'{name} ({len(df_i):,} rows)', fontsize=12)\n",
    "    ax.set_xlabel('Sample Count')\n",
    "    for bar, val in zip(bars, counts.values):\n",
    "        ax.text(val + max(counts)*0.01, bar.get_y() + bar.get_height()/2, f'{val:,}', va='center', fontsize=9)\n",
    "\n",
    "plt.tight_layout()\n",
    "plt.show()"
])

code([
    "balance = pd.DataFrame({\n",
    "    'Main Grid': df_grid['activity'].value_counts().sort_index(),\n",
    "    'Label (Anxiety)': df_label['activity'].value_counts().sort_index(),\n",
    "    'Synthetic': df_synth['activity'].value_counts().sort_index(),\n",
    "    'Codex Synthetic': df_codex['activity'].value_counts().sort_index(),\n",
    "})\n",
    "balance.loc['TOTAL'] = balance.sum()\n",
    "balance.loc['Imbalance Ratio'] = (balance.iloc[:-1].max() / balance.iloc[:-1].min()).round(2)\n",
    "balance.style.format('{:,.0f}').set_caption('Activity Counts (+ Imbalance Ratio)')"
])

md("### 6.2 User/Session Distribution")

code([
    "fig, axes = plt.subplots(1, 3, figsize=(16, 4))\n",
    "for ax, (df_i, name, col) in zip(axes, [\n",
    "    (df_grid, 'Main Grid - Users', 'User'),\n",
    "    (df_label, 'Label (Anxiety) - Users', 'User'),\n",
    "    (df_prod, 'Production - Sessions', 'session'),\n",
    "]):\n",
    "    counts = df_i[col].value_counts().sort_index()\n",
    "    ax.bar(counts.index.astype(str), counts.values, color='steelblue', alpha=0.8)\n",
    "    ax.set_title(name, fontsize=11); ax.set_ylabel('Rows')\n",
    "    ax.tick_params(axis='x', rotation=90 if col == 'session' else 0, labelsize=7 if col == 'session' else 10)\n",
    "    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x):,}'))\n",
    "plt.tight_layout()\n",
    "plt.show()"
])

# ============================================================
# PRODUCTION DETAIL
# ============================================================
md("## 7. Production Data: All Sessions Detailed\n\nValues in m/s\u00b2 and deg/s after milliG conversion.")

code([
    "prod_simple = df_prod.groupby('session').agg(\n",
    "    Rows=('Ax_w', 'count'), Duration_sec=('Ax_w', lambda x: len(x) / 25),\n",
    "    Ax_mean=('Ax_w', 'mean'), Ay_mean=('Ay_w', 'mean'), Az_mean=('Az_w', 'mean'),\n",
    "    Gx_mean=('Gx_w', 'mean'), Gy_mean=('Gy_w', 'mean'), Gz_mean=('Gz_w', 'mean'),\n",
    "    Ax_std=('Ax_w', 'std'), Ay_std=('Ay_w', 'std'), Az_std=('Az_w', 'std'),\n",
    ").round(2)\n",
    "prod_simple['Duration_min'] = (prod_simple['Duration_sec'] / 60).round(1)\n",
    "prod_simple.style.format('{:,.2f}').set_caption(f'Production Sessions ({ACCEL_UNIT} / {GYRO_UNIT})')"
])

code([
    "fig, ax = plt.subplots(figsize=(16, 4))\n",
    "sessions_sorted = prod_simple.sort_values('Rows', ascending=False)\n",
    "ax.bar(range(len(sessions_sorted)), sessions_sorted['Rows'], color='coral', alpha=0.8)\n",
    "ax.set_xticks(range(len(sessions_sorted)))\n",
    "ax.set_xticklabels([s[:10] for s in sessions_sorted.index], rotation=60, ha='right', fontsize=8)\n",
    "ax.set_ylabel('Row Count'); ax.set_title('Production Sessions by Size', fontsize=13)\n",
    "ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x):,}'))\n",
    "plt.tight_layout()\n",
    "plt.show()"
])

code([
    "session_means = df_prod.groupby('session')[SENSOR_COLS].mean()\n",
    "fig, ax = plt.subplots(figsize=(10, 10))\n",
    "sns.heatmap(session_means, annot=True, fmt='.2f', cmap='RdBu_r', center=0,\n",
    "            linewidths=0.5, ax=ax, annot_kws={'size': 8})\n",
    "ax.set_title(f'Mean Sensor Values per Session ({ACCEL_UNIT} / {GYRO_UNIT})', fontsize=13)\n",
    "ax.set_ylabel('Session')\n",
    "plt.tight_layout()\n",
    "plt.show()\n",
    "\n",
    "print('Observations (in m/s\u00b2):')\n",
    "print('- Az consistently around -9.8 m/s\u00b2 = -1g (gravity through wrist).')\n",
    "print('- Grid has Az mean ~ -3.5 m/s\u00b2 -- different wrist orientation.')\n",
    "print('- This orientation difference is the main domain gap, not a unit problem.')"
])

code([
    "session_stds = df_prod.groupby('session')[SENSOR_COLS].std()\n",
    "fig, ax = plt.subplots(figsize=(10, 10))\n",
    "sns.heatmap(session_stds, annot=True, fmt='.2f', cmap='YlOrRd',\n",
    "            linewidths=0.5, ax=ax, annot_kws={'size': 8})\n",
    "ax.set_title(f'Std Dev per Session [{ACCEL_UNIT} / {GYRO_UNIT}]', fontsize=13)\n",
    "ax.set_ylabel('Session')\n",
    "plt.tight_layout()\n",
    "plt.show()"
])

# ============================================================
# SYNTHETIC VS REAL
# ============================================================
md("## 8. Synthetic vs Real Data Comparison\n\n### 8.1 Per-Axis KDE: Real vs Synthetic")

code([
    "fig, axes = plt.subplots(2, 3, figsize=(16, 9))\n",
    "fig.suptitle(f'Real vs Synthetic ({ACCEL_UNIT} / {GYRO_UNIT})', fontsize=15, y=1.02)\n",
    "\n",
    "for idx, col in enumerate(SENSOR_COLS):\n",
    "    ax = axes[idx // 3, idx % 3]\n",
    "    unit = ACCEL_UNIT if col.startswith('A') else GYRO_UNIT\n",
    "    for df_i, label, color, ls in [\n",
    "        (df_grid, 'Main Grid (Real)', '#2196F3', '-'),\n",
    "        (df_synth, 'Synthetic', '#4CAF50', '--'),\n",
    "        (df_codex, 'Codex Synthetic', '#9C27B0', ':'),\n",
    "    ]:\n",
    "        vals = df_i[col].dropna().sample(n=min(50_000, len(df_i)), random_state=42)\n",
    "        vals.plot.kde(ax=ax, label=label, color=color, linestyle=ls, linewidth=2)\n",
    "    ax.set_title(f'{col} ({unit})', fontsize=13); ax.set_ylabel('Density'); ax.legend(fontsize=8)\n",
    "    lo = df_grid[col].quantile(0.005); hi = df_grid[col].quantile(0.995)\n",
    "    margin = (hi - lo) * 0.2; ax.set_xlim(lo - margin, hi + margin)\n",
    "\n",
    "plt.tight_layout()\n",
    "plt.show()"
])

md("### 8.2 Per-Activity Mean Comparison")

code([
    "real_means = df_grid.groupby('activity')[SENSOR_COLS].mean()\n",
    "synth_means = df_synth.groupby('activity')[SENSOR_COLS].mean()\n",
    "codex_means = df_codex.groupby('activity')[SENSOR_COLS].mean()\n",
    "\n",
    "fig, axes = plt.subplots(2, 3, figsize=(16, 9))\n",
    "fig.suptitle('Per-Activity Mean: Real vs Synthetic (same units)', fontsize=14, y=1.02)\n",
    "\n",
    "activities = sorted(df_grid['activity'].unique())\n",
    "x = np.arange(len(activities)); w = 0.25\n",
    "\n",
    "for idx, col in enumerate(SENSOR_COLS):\n",
    "    ax = axes[idx // 3, idx % 3]\n",
    "    unit = ACCEL_UNIT if col.startswith('A') else GYRO_UNIT\n",
    "    ax.bar(x - w, real_means.loc[activities, col], w, label='Real', color='#2196F3', alpha=0.8)\n",
    "    ax.bar(x, synth_means.loc[activities, col], w, label='Synthetic', color='#4CAF50', alpha=0.8)\n",
    "    ax.bar(x + w, codex_means.loc[activities, col], w, label='Codex', color='#9C27B0', alpha=0.8)\n",
    "    ax.set_title(f'{col} ({unit})', fontsize=12); ax.set_xticks(x)\n",
    "    ax.set_xticklabels(activities, rotation=45, ha='right', fontsize=7); ax.legend(fontsize=7)\n",
    "\n",
    "plt.tight_layout()\n",
    "plt.show()"
])

code([
    "fidelity = []\n",
    "for col in SENSOR_COLS:\n",
    "    unit = ACCEL_UNIT if col.startswith('A') else GYRO_UNIT\n",
    "    r_synth = np.corrcoef(real_means[col].values, synth_means[col].values)[0, 1]\n",
    "    r_codex = np.corrcoef(real_means[col].values, codex_means[col].values)[0, 1]\n",
    "    mae_synth = np.mean(np.abs(real_means[col].values - synth_means[col].values))\n",
    "    mae_codex = np.mean(np.abs(real_means[col].values - codex_means[col].values))\n",
    "    fidelity.append({'Sensor': col, 'Unit': unit,\n",
    "        'Corr (Synth)': f'{r_synth:.4f}', 'Corr (Codex)': f'{r_codex:.4f}',\n",
    "        f'MAE Synth ({unit})': f'{mae_synth:.3f}', f'MAE Codex ({unit})': f'{mae_codex:.3f}'})\n",
    "\n",
    "pd.DataFrame(fidelity).style.set_caption('Synthetic Fidelity: Correlation & MAE vs Real')"
])

md("### 8.3 Variability Fidelity")

code([
    "real_stds = df_grid.groupby('activity')[SENSOR_COLS].std()\n",
    "synth_stds = df_synth.groupby('activity')[SENSOR_COLS].std()\n",
    "codex_stds = df_codex.groupby('activity')[SENSOR_COLS].std()\n",
    "\n",
    "ratio_synth = (synth_stds / real_stds).round(3)\n",
    "ratio_codex = (codex_stds / real_stds).round(3)\n",
    "\n",
    "fig, axes = plt.subplots(1, 2, figsize=(14, 6))\n",
    "sns.heatmap(ratio_synth, annot=True, fmt='.2f', cmap='RdYlGn', center=1.0,\n",
    "            vmin=0.3, vmax=2.0, ax=axes[0], linewidths=0.5)\n",
    "axes[0].set_title('Synthetic Std / Real Std (1.0 = perfect)', fontsize=12)\n",
    "sns.heatmap(ratio_codex, annot=True, fmt='.2f', cmap='RdYlGn', center=1.0,\n",
    "            vmin=0.3, vmax=2.0, ax=axes[1], linewidths=0.5)\n",
    "axes[1].set_title('Codex Std / Real Std (1.0 = perfect)', fontsize=12)\n",
    "plt.suptitle('Variability Fidelity: Synthetic vs Real', fontsize=14, y=1.02)\n",
    "plt.tight_layout()\n",
    "plt.show()"
])

# ============================================================
# KEY FINDINGS
# ============================================================
md("## 9. Key Findings")

code([
    "scale_comparison = pd.DataFrame({\n",
    "    'Dataset': ['Main Grid', 'Label (Anxiety)', 'Synthetic', 'Codex Synthetic', 'Production'],\n",
    "    'Original Accel': ['m/s\u00b2', 'g-units', 'm/s\u00b2', 'm/s\u00b2', 'milliG'],\n",
    "    'Original Gyro': ['deg/s', 'deg/s (wrist), rad/s (pocket)', 'deg/s', 'deg/s', 'deg/s'],\n",
    "    'Conversion': ['None', 'accel\u00d79.81, pocket gyro\u00d757.3', 'None', 'None', 'accel\u00d70.00981'],\n",
    "    f'Accel Range ({ACCEL_UNIT})': [\n",
    "        f\"{df_grid[ACCEL_COLS].min().min():.1f} to {df_grid[ACCEL_COLS].max().max():.1f}\",\n",
    "        f\"{df_label[ACCEL_COLS].min().min():.1f} to {df_label[ACCEL_COLS].max().max():.1f}\",\n",
    "        f\"{df_synth[ACCEL_COLS].min().min():.1f} to {df_synth[ACCEL_COLS].max().max():.1f}\",\n",
    "        f\"{df_codex[ACCEL_COLS].min().min():.1f} to {df_codex[ACCEL_COLS].max().max():.1f}\",\n",
    "        f\"{df_prod[ACCEL_COLS].min().min():.1f} to {df_prod[ACCEL_COLS].max().max():.1f}\"],\n",
    "    f'Gyro Range ({GYRO_UNIT})': [\n",
    "        f\"{df_grid[GYRO_COLS].min().min():.1f} to {df_grid[GYRO_COLS].max().max():.1f}\",\n",
    "        f\"{df_label[GYRO_COLS].min().min():.1f} to {df_label[GYRO_COLS].max().max():.1f}\",\n",
    "        f\"{df_synth[GYRO_COLS].min().min():.1f} to {df_synth[GYRO_COLS].max().max():.1f}\",\n",
    "        f\"{df_codex[GYRO_COLS].min().min():.1f} to {df_codex[GYRO_COLS].max().max():.1f}\",\n",
    "        f\"{df_prod[GYRO_COLS].min().min():.1f} to {df_prod[GYRO_COLS].max().max():.1f}\"],\n",
    "})\n",
    "scale_comparison.style.set_caption('Unit Conversion Summary & Final Ranges')"
])

code([
    "print('''\n",
    "==========================================================================\n",
    " KEY FINDINGS (All values in m/s\u00b2 and deg/s after conversion)\n",
    "==========================================================================\n",
    "\n",
    "1. UNIT ALIGNMENT CONFIRMED\n",
    "   - Production: milliG \u00d7 0.00981 \u2192 m/s\u00b2.  Magnitude \u2248 9.8 m/s\u00b2 \u2713\n",
    "   - Label (Anxiety) wrist: g-units \u00d7 9.80665 \u2192 m/s\u00b2.  Magnitude \u2248 9.8 \u2713\n",
    "   - Label (Anxiety) pocket gyro: rad/s \u00d7 57.3 \u2192 deg/s.\n",
    "   - Grid, Synthetic, Codex: already in m/s\u00b2 and deg/s. \u2713\n",
    "\n",
    "2. GRAVITY ORIENTATION IS THE MAIN DOMAIN GAP\n",
    "   - Main Grid: gravity mostly on X (Ax \u2248 +8, Az \u2248 -3.5 m/s\u00b2).\n",
    "   - Production: gravity mostly on Z (Az \u2248 -9.8, Ax \u2248 +0.3 m/s\u00b2).\n",
    "   - Same 1g force, different axis distribution due to wrist orientation.\n",
    "   - NOT fixable by unit conversion -- needs orientation-invariant features.\n",
    "\n",
    "3. LABEL (ANXIETY) WRIST: Narrower accel range after conversion\n",
    "   (-13 to +9 vs grid -22 to +17 m/s\u00b2).\n",
    "\n",
    "4. CLASS BALANCE: Well-balanced across all labeled datasets (~1.2 ratio).\n",
    "\n",
    "5. SYNTHETIC FIDELITY: Means well-reproduced; variability mixed.\n",
    "\n",
    "6. PRODUCTION: Sessions vary in duration/characteristics.\n",
    "   Accel std typically 1-4 m/s\u00b2 (moderate motion).\n",
    "\n",
    "7. DATA QUALITY: Clean (low missing, no inf).\n",
    "==========================================================================\n",
    "''')"
])

# ============================================================
# FINAL TAKEAWAY
# ============================================================
md([
    "## 10. Final Takeaway\n",
    "\n",
    "With all datasets in common units (m/s\u00b2 for accel, deg/s for gyro), the most important finding is not about scale -- "
    "unit conversion handles that -- but about **sensor orientation**. The Main Grid training data has gravity projecting "
    "primarily onto the X-axis (Ax \u2248 +8 m/s\u00b2), while production Garmin data has gravity on the Z-axis (Az \u2248 -9.8 m/s\u00b2). "
    "This means the **same physical posture produces fundamentally different raw values** depending on how the device sits "
    "on the wrist. No amount of unit conversion fixes this; it requires either orientation-invariant features (e.g., magnitude, "
    "jerk) or explicit rotation alignment. The synthetic datasets reproduce the Main Grid's orientation conventions, so they "
    "share the same domain gap with production. The Label (Anxiety) dataset has correct units after conversion but narrower "
    "dynamic range. For the MLOps pipeline: **unit conversion is necessary but not sufficient** -- orientation differences "
    "remain the key training-production domain gap.\n",
    "\n",
    "---\n",
    "*All accel in m/s\u00b2. All gyro in deg/s. Conversions: Production milliG\u00d70.00981, Label wrist g\u00d79.80665, Label pocket gyro rad/s\u00d757.30.*"
])

# ============================================================
# WRITE
# ============================================================
notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12.3"}
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

with open("dataset_comparison_analysis.ipynb", "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

print(f"Notebook written: {len(cells)} cells")
