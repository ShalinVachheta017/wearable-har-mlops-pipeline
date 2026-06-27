# Model & Data Versioning Guide — HAR MLOps Pipeline

This guide explains the versioning and registry layers of the ML platform as implemented
in this thesis project. It covers two orthogonal concerns:

| Concern | Tool | What it tracks |
|---|---|---|
| **Model versioning** | MLflow Tracking | Training runs, hyperparameters, metrics, model artifacts |
| **Model registry** | MLflow Model Registry | Promoted, named, staged model versions |
| **Data versioning** | DVC | Raw, prepared, and processed dataset snapshots |
| **Data registry** | DVC remote (S3 / local) | Shared content-addressable data store |

Both layers are already active in this repository. No new tooling is needed.

**Thesis reference:** Model registry and governance are discussed in Chapter 5 (pipeline
implementation) and Chapter 6 (monitoring and governance). Data versioning is covered in
Chapter 3 (MLOps architecture) and Chapter 4 (data and model development).

---

## Part 1 — Model Versioning with MLflow

### What is model versioning here?

Every time the training pipeline runs, MLflow records a new **run** under the experiment
`anxiety-activity-recognition`. A run captures:

- **Parameters** — learning rate, batch size, window size, dropout rate, optimizer
- **Metrics** — accuracy, loss, val_accuracy, val_loss, F1, precision, recall
- **Artifacts** — model weights (`.keras`), confusion matrix, classification report,
  training history, preprocessing config
- **Tags** — model type, project, author, git commit SHA (when set)

The run ID is the unique version handle. Two runs trained on the same code with different
hyperparameters are two separate, fully reproducible versions.

### Where the tracking is wired

| File | What it does |
|---|---|
| `config/mlflow_config.yaml` | Central config — tracking URI, experiment name, what to log |
| `src/pipeline/pipeline_mlflow_logger.py` | Adapter that owns run lifecycle and metric logging |
| `src/mlflow_tracking.py` | Low-level MLflow wrapper |

The tracking URI is currently `"mlruns"` — a local directory. Every run is stored there
automatically.

### How to inspect runs

```bash
# Start the MLflow UI (run from the repository root)
mlflow ui --backend-store-uri mlruns

# Open in browser
http://localhost:5000
```

The UI shows all runs, side-by-side metric comparison, parameter search, and artifact
download. Filter by tag or metric to find the best run before registering.

### Comparing runs from the CLI

```bash
# List all runs in the experiment
mlflow runs list --experiment-name anxiety-activity-recognition

# Fetch details for a specific run
mlflow runs describe --run-id <run-id>

# Download artifacts from a run
mlflow artifacts download --run-id <run-id> --artifact-path model_weights
```

### Linking a run to a git commit

Add a git tag before training so every run is reproducible from source:

```bash
git tag -a model-d1-v1 -m "1D-CNN-BiLSTM retrain May 2026"
mlflow run . -P git_sha=$(git rev-parse HEAD)
```

When `MLFLOW_GIT_COMMIT` is set in the environment, MLflow captures it automatically.

---

## Part 2 — Model Registry with MLflow

### What the registry is

The MLflow Model Registry is a named catalogue of promoted model versions. It sits on top
of the run store. A model is registered once a run has been validated and is considered
ready for deployment.

In this project the registered model name is **`har-1dcnn-bilstm`**, defined in
`config/mlflow_config.yaml` under `registry.model_name`.

### The four registry stages

| Stage | Meaning in this project |
|---|---|
| `None` | Registered but not yet reviewed |
| `Staging` | Passed offline evaluation (5-fold CV), waiting for LOUO review |
| `Production` | Approved for serving — becomes the runtime contract source |
| `Archived` | Superseded by a newer Production version |

Only one version should be in `Production` at any time. The currently deployed model is
`model_d1_final_20260528` (5-fold CV 93.61 %, LOUO 44.42 %).

### How registration happens in the pipeline

Registration is performed by **Stage 9 (ModelRegistration)**, not during normal inference.
This is intentional — see the comment in `pipeline_mlflow_logger.py:63`:

> Registration happens only in Stage 9 (ModelRegistration component). Calling
> register_model during normal inference would create unauthorized model versions on
> every production run.

The registration call in `pipeline_mlflow_logger.py:124` does:

```python
tracker.register_model(
    run_id=run_id,
    model_uri=f"runs:/{run_id}/model",
    registered_model_name="har-1dcnn-bilstm",
)
```

### Promoting a version through stages (CLI)

```bash
# Register a run manually (if not done by Stage 9)
mlflow models register \
  --model-uri runs:/<run-id>/model \
  --name har-1dcnn-bilstm

# Transition a version to Staging
mlflow models transition-version-stage \
  --name har-1dcnn-bilstm \
  --version 2 \
  --stage Staging

# Promote to Production after LOUO review passes
mlflow models transition-version-stage \
  --name har-1dcnn-bilstm \
  --version 2 \
  --stage Production \
  --archive-existing-versions   # automatically archives the old Production version

# Archive an old version manually
mlflow models transition-version-stage \
  --name har-1dcnn-bilstm \
  --version 1 \
  --stage Archived
```

### Adding model description and tags

Good registry hygiene: document every version before promoting it.

```bash
# Add a plain-text description
mlflow models update-version \
  --name har-1dcnn-bilstm \
  --version 2 \
  --description "Retrained May 2026. 5-fold 93.61%, LOUO 44.42%. Trained on 9 users."

# Tag the version with evaluation results
mlflow models set-version-tag \
  --name har-1dcnn-bilstm \
  --version 2 \
  --key louo_accuracy \
  --value 0.4442

mlflow models set-version-tag \
  --name har-1dcnn-bilstm \
  --version 2 \
  --key cv5_accuracy \
  --value 0.9361
```

### Loading a registered model for inference

```python
import mlflow.keras

# Load the current Production version
model = mlflow.keras.load_model("models:/har-1dcnn-bilstm/Production")

# Load a specific version by number
model = mlflow.keras.load_model("models:/har-1dcnn-bilstm/2")
```

The FastAPI serving layer does NOT use this path — it reads the frozen `.keras` file from
the runtime contract folder. The registry is used for audit, comparison, and promotion
decisions, not for hot-loading during inference.

### Registry on a remote MLflow server

To share the registry across a team, point the tracking URI at a remote server:

```bash
# In config/mlflow_config.yaml:
mlflow:
  tracking_uri: "http://your-mlflow-server:5000"
```

Or via environment variable (no config change needed):

```bash
export MLFLOW_TRACKING_URI=http://your-mlflow-server:5000
```

For AWS, deploy MLflow with an RDS backend and S3 artifact store:

```bash
mlflow server \
  --backend-store-uri postgresql://user:pass@rds-host:5432/mlflow \
  --default-artifact-root s3://your-bucket-name/mlflow-artifacts \
  --host 0.0.0.0 \
  --port 5000
```

---

## Part 3 — Data Versioning with DVC

### What DVC tracks in this project

DVC tracks large files and directories by replacing them with small `.dvc` pointer files
that live in git. The actual data is stored in the DVC cache (`.dvc/cache/`) and optionally
pushed to a remote.

| `.dvc` file | What it points to | Content |
|---|---|---|
| `data/raw.dvc` | `data/raw/` | Original Garmin sensor CSVs, one per user session |
| `data/prepared.dvc` | `data/prepared/` | Windowed, labelled segments |
| `data/processed.dvc` | `data/processed/` | Scaled features ready for training |
| `models/pretrained.dvc` | `models/pretrained/` | Pre-trained weights before fine-tuning |
| `models/runtime_contract/model_d1_final_20260528.dvc` | runtime contract folder | Deployed model bundle |
| `artifacts/<timestamp>.dvc` | `artifacts/<timestamp>/` | Full pipeline run outputs |

Because `.dvc` files are committed to git, every git commit captures the exact dataset
state — checking out an old commit and running `dvc checkout` restores the data exactly.

### How a `.dvc` file looks

```yaml
# data/raw.dvc
outs:
- md5: 69c45431805a9772975fa73c8811fb97.dir
  size: 4823041
  nfiles: 22
  hash: md5
  path: raw
```

The `md5` hash is the content fingerprint. DVC uses this to deduplicate storage — if two
datasets share the same files, they share cache entries.

### Core DVC commands

```bash
# Track a new or updated dataset folder
dvc add data/raw/

# Commit the pointer file to git
git add data/raw.dvc .gitignore
git commit -m "data: add raw session files for users 1-9"

# Push data to the DVC remote
dvc push

# Pull data (on a fresh clone or new machine)
dvc pull

# Restore files from the local DVC cache to the working directory
dvc checkout

# Show what changed since last commit
dvc diff

# Show the pipeline DAG and stage checksums
dvc dag
dvc status
```

### Reproducing an older dataset version

```bash
# Go back to an older git commit
git checkout <old-commit-sha>

# Restore the data that was tracked at that commit
dvc checkout

# The data/ folder now contains exactly what it did at that commit
```

This is how the thesis guarantees reproducibility: the git commit SHA + DVC commit hash
together define an exact, restorable experiment state.

### Comparing dataset versions

```bash
# Show data changes between two git commits
dvc diff <old-commit-sha> <new-commit-sha>

# Example output:
# Modified:
#   data/prepared/:
#     (md5: a1df11... -> 3bb89a...)
#     size: 3.1 MB -> 3.4 MB
#     nfiles: 18 -> 22
```

---

## Part 4 — Data Registry with DVC Remote

### What a DVC remote is

A DVC remote is a shared content-addressable storage location — the data equivalent of a
Docker registry or an artifact store. Instead of emailing datasets or committing large
files to git, team members push data to the remote once and pull exactly what they need.

### Remote types supported by DVC

| Remote type | URI format | Good for |
|---|---|---|
| Local folder | `/mnt/shared/dvc-store` | Single-machine or NFS share |
| S3 | `s3://bucket-name/dvc-data` | AWS deployment, large datasets |
| Azure Blob | `azure://container/dvc-data` | Azure deployment |
| GCS | `gs://bucket-name/dvc-data` | GCP deployment |
| SSH | `ssh://user@host/path` | On-premise servers |

### Setting up an S3 remote (AWS deployment scenario)

```bash
# Add the remote (one time)
dvc remote add production s3://your-bucket-name/dvc-data
dvc remote default production

# Store the remote config in git (not credentials)
git add .dvc/config
git commit -m "dvc: configure S3 remote"

# Push all cached data to S3
dvc push

# On another machine, pull the data
dvc pull
```

Credentials are handled by the AWS CLI profile or IAM role — DVC never stores them.

### Using a shared local remote for the thesis scenario

```bash
# Use a local folder as the "team" remote (e.g. an external drive or shared folder)
dvc remote add localshare /d/dvc-remote-store
dvc remote default localshare

# Push
dvc push -r localshare

# On another machine with access to the same drive
dvc pull -r localshare
```

### Tagging dataset versions for reproducibility

DVC does not have its own tagging concept — git tags serve that purpose:

```bash
# Tag the state of the data at model D1 training time
git tag -a data-d1-may2026 -m "Dataset state at Model D1 training (22 sessions, 9 users)"
git push origin data-d1-may2026

# To reproduce: checkout the tag, pull the data
git checkout data-d1-may2026
dvc pull
```

This is the equivalent of a "data version" in the registry sense: a named, restorable
snapshot of the full dataset.

---

## Part 5 — The Full MLOps Version Flow

This diagram shows how model and data versioning connect across the pipeline:

```
Raw sessions (Garmin CSV)
         |
    dvc add data/raw/
    git commit + dvc push          <-- DATA VERSION pinned in git
         |
    Stage 1-4: Ingest, Transform, Scale
         |
    dvc add data/processed/
    git commit + dvc push          <-- PROCESSED DATA VERSION pinned in git
         |
    Stage 5: Train 1D-CNN-BiLSTM
         |
    MLflow run logged              <-- RUN VERSION in MLflow (run_id)
    (params, metrics, artifacts)
         |
    Stage 6-7: Monitor + Trigger
         |
    Stage 9: ModelRegistration
         |
    mlflow register_model          <-- MODEL VERSION in MLflow Registry
    (har-1dcnn-bilstm, version N)
         |
    Manual review: LOUO check
    mlflow transition → Production <-- REGISTRY STAGE promoted
         |
    Runtime contract folder
    dvc add models/runtime_contract/<name>.dvc
    git commit + dvc push          <-- CONTRACT VERSION pinned in git
         |
    Docker image + K8s / ECS
    pulls contract at startup      <-- DEPLOYED VERSION serving requests
```

Each arrow introduces a version boundary. Going back to any point requires only two things:
the git commit SHA and `dvc pull`.

---

## Quick Reference

### Model versioning

| Task | Command |
|---|---|
| Start MLflow UI | `mlflow ui --backend-store-uri mlruns` |
| List all runs | `mlflow runs list --experiment-name anxiety-activity-recognition` |
| Register a run | `mlflow models register --model-uri runs:/<id>/model --name har-1dcnn-bilstm` |
| Promote to Production | `mlflow models transition-version-stage --name har-1dcnn-bilstm --version N --stage Production --archive-existing-versions` |
| Load Production model | `mlflow.keras.load_model("models:/har-1dcnn-bilstm/Production")` |

### Data versioning

| Task | Command |
|---|---|
| Track a dataset | `dvc add data/raw/` |
| Push to remote | `dvc push` |
| Pull from remote | `dvc pull` |
| Restore old dataset | `git checkout <sha> && dvc checkout` |
| Show diff | `dvc diff <old-sha> <new-sha>` |
| Set up S3 remote | `dvc remote add prod s3://bucket/dvc && dvc remote default prod` |
