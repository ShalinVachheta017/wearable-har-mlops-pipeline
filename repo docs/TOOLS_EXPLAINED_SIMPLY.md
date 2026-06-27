# Tools Explained Simply — HAR MLOps Pipeline

This document explains every major tool in this project in plain language:
what it is, why we use it, and exactly where you see it in this codebase.

---

## 1. Docker

### What it is — simple version

Imagine you write code on your laptop. It works perfectly. You send it to someone else
and they say "it doesn't work." The reason is almost always that their machine has a
different Python version, different libraries, or different settings.

Docker solves this by putting your code, its Python version, and all its libraries
inside a sealed box called a **container**. When you send someone that box, it runs
exactly the same on their machine as on yours — because everything it needs is already
inside.

### Why we use it

- Anyone can run the inference API without installing Python, TensorFlow, or anything else
- The same container runs locally on a laptop, on AWS ECS, or on Kubernetes — zero changes
- The container is small and predictable — no "works on my machine" problems

### Where you see it in this project

| File | What it does |
|---|---|
| `docker/Dockerfile.inference` | Builds the serving image — Python 3.11, FastAPI, TensorFlow-CPU, your `src/` code |
| `docker/Dockerfile.training` | Builds the full training image — includes MLflow, DVC, Jupyter, everything |
| `docker-compose.yml` | Runs both images together locally with one command |

The inference image is deliberately kept small. The comment in `Dockerfile.inference:31`
explains why:

> Uses `requirements-runtime.txt` (NOT `requirements.txt`) so dev tooling (jupyterlab,
> pytest, black) and training-side packages (mlflow, dvc) stay out of the inference image.
> tensorflow-cpu also avoids ~900 MB of CUDA libraries.

**In one sentence:** Docker is a shipping box for your code. What goes in always comes out
the same on any computer.

---

## 2. CI/CD Pipeline

### What it is — simple version

CI/CD stands for **Continuous Integration / Continuous Delivery**.

Think of it like an automatic safety guard that runs every time you push code to GitHub.
Before your code is allowed to merge, a robot (GitHub Actions) runs a checklist:

1. Is the code formatted correctly?
2. Do all the tests pass?
3. Does the Docker image build without errors?

If anything fails, the push is blocked. You fix it and try again. This means broken code
never reaches the `main` branch.

### Why we use it

- Catches mistakes automatically — you don't have to remember to run tests before every push
- Keeps `main` always in a working state
- Makes it safe for multiple people to work on the same project
- Documents the quality bar in code, not just in conversation

### Where you see it in this project

The entire CI pipeline lives in one file: `.github/workflows/ci.yml`

It runs three jobs in order — each one must pass before the next starts:

```
push to main or PR
        |
  Job 1: lint        ← checks code style (flake8, black, isort)
        |
  Job 2: unit-tests  ← runs all tests in tests/ with pytest
        |
  Job 3: docker-build-check  ← builds the inference Docker image (does not push)
```

The `lint` job uses three tools:
- **flake8** — finds Python errors and complexity problems
- **black** — checks that code is auto-formatted consistently
- **isort** — checks that import statements are in the right order

**In one sentence:** CI/CD is a robot that checks your code automatically every time you
push, so bugs and style errors never reach the main branch.

---

## 3. Inference API (FastAPI)

### What it is — simple version

An API (Application Programming Interface) is a door that lets other programs talk to
your code. FastAPI is the framework that builds that door for Python.

In this project, the API is the front door of the entire pipeline. You send it a CSV file
of sensor data, and it runs all 7 pipeline stages and sends back the activity predictions
plus monitoring signals — all through a standard web request.

### Why we use it

- Any tool (web browser, Python script, mobile app, Grafana) can call it over HTTP
- FastAPI is fast — it uses async Python so it can handle multiple uploads at once
- It automatically generates interactive docs at `/docs` so you can test the API in the
  browser without writing any code
- It validates every request and response automatically using Pydantic (see section 4)

### Where you see it in this project

The entire serving layer lives in `src/api/app.py`.

The two main endpoints:

```
POST /upload/labeled    ← CSV with activity labels (for evaluation + monitoring)
POST /upload/unlabeled  ← CSV without labels (for live monitoring only)
```

Both endpoints do the same thing internally:
1. Parse the uploaded CSV
2. Detect sensor columns and label column
3. Window the data (128 samples per window)
4. Scale features using the training scaler
5. Run the 1D-CNN-BiLSTM model
6. Apply temporal smoothing (k=3)
7. Run 3-layer monitoring (confidence, temporal, drift)
8. Return predictions + monitoring signals as JSON

The health check endpoint:

```
GET /health   ← returns model_loaded, baseline_loaded, uptime
```

This is what Kubernetes and Docker use to check that the container is alive and ready.

**In one sentence:** FastAPI is the web door to your model — you send a CSV file in, and
it runs the whole pipeline and sends predictions back.

---

## 4. Pydantic

### What it is — simple version

Pydantic is a library that checks whether data has the right shape and type.

Imagine someone sends your API a request, but they forget to include the confidence field
in the response, or they accidentally send a string where a number is expected. Without
Pydantic, this crashes in an unpredictable way. With Pydantic, it is caught immediately
with a clear error message.

You describe the shape of your data once, as a Python class. Pydantic enforces it
automatically — both when data comes in and when it goes out.

### Why we use it

- Catches wrong data types before they reach the model — no silent crashes
- Self-documents what the API expects and returns
- FastAPI uses Pydantic models directly to generate the `/docs` page automatically
- Forces you to think clearly about what fields are required vs optional

### Where you see it in this project

In `src/api/app.py:676`, the `UploadResult` class describes every field in the API
response:

```python
class UploadResult(BaseModel):
    filename: str
    upload_mode: str = "fused_csv"
    total_rows: int
    sensor_columns: List[str]
    has_labels: bool = False
    windows_created: int
    processing_time_ms: float
    predictions: List[Dict]
    activity_summary: Dict[str, int]
    monitoring: Dict
    evaluation: Optional[Dict] = None   # only present on labeled uploads
    confidence_stats: Dict
```

And the health check response in `src/api/app.py:695`:

```python
class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    baseline_loaded: bool
    timestamp: str
    uptime_seconds: float
```

If FastAPI tries to return a response that is missing `model_loaded`, Pydantic raises an
error immediately instead of sending broken JSON to the caller.

**In one sentence:** Pydantic is a data shape checker — it makes sure every input and
output matches exactly the structure you declared, and complains loudly when it does not.

---

## 5. Pytest

### What it is — simple version

Pytest is the testing framework for Python. You write small functions that check whether
your code does what it is supposed to do. Then you run `pytest` and it tells you which
ones passed and which ones failed.

Think of it like writing a list of questions:

- "If I feed this sensor CSV into `_detect_columns`, does it find `accel_x`?"
- "If the mean confidence is 0.60, does Layer 1 return WARNING?"
- "If I register a model, does it appear in the MLflow registry?"

Pytest runs all those questions automatically in seconds.

### Why we use it

- Catches regressions — when you change something, tests immediately tell you if you broke
  something else
- Documents how your code is supposed to behave — a test is a runnable spec
- Required before the Docker build runs in CI (see section 2) — tests must pass first
- Lets you refactor confidently because you know the outputs are still correct

### Where you see it in this project

All tests live in `tests/`. Each file tests one pipeline stage:

| Test file | What it tests |
|---|---|
| `tests/test_stage2_validation.py` | Data validation rules |
| `tests/test_stage3_transformation.py` | Windowing and feature extraction |
| `tests/test_stage6_monitoring.py` | 3-layer monitoring signals |
| `tests/test_stage7_trigger.py` | Retraining trigger logic |
| `tests/test_stage9_registration.py` | Model registration in MLflow |
| `tests/test_api_upload_modes.py` | All upload paths through FastAPI |
| `tests/test_runtime_contract_consistency.py` | Runtime contract integrity hashes |

An example from `tests/test_api_upload_modes.py:36`:

```python
def test_detect_fused_columns_and_label():
    df = pd.DataFrame({
        "accel_x": [1.0], "accel_y": [2.0], "accel_z": [3.0],
        "gyro_x": [4.0],  "gyro_y": [5.0],  "gyro_z": [6.0],
        "activity": ["walking"],
    })
    assert _detect_columns(df) == ["accel_x", "accel_y", "accel_z",
                                    "gyro_x", "gyro_y", "gyro_z"]
```

Run all tests locally:

```bash
pytest tests/ -v
```

Run one specific test file:

```bash
pytest tests/test_stage6_monitoring.py -v
```

**In one sentence:** Pytest lets you write questions about your code and automatically
checks that all the answers are still correct every time you make a change.

---

## 6. DVC (Data Version Control)

### What it is — simple version

Git tracks code changes perfectly. But Git is bad at tracking large files — it was never
designed for gigabyte CSV datasets or 50 MB model weights.

DVC solves this. It works alongside Git. Instead of storing the actual data in Git, DVC
stores a tiny fingerprint (an MD5 hash) called a `.dvc` file. The real data sits in the
DVC cache (a local folder) or on a remote (like S3). When you need the data, DVC fetches
it using the fingerprint.

The result: `git checkout` + `dvc pull` restores the exact code AND data state of any
past moment — fully reproducible experiments.

### Why we use it

- Data reproducibility — you can always get back the exact dataset that trained a specific model
- Team sharing — push data to S3 once, anyone can `dvc pull` it
- Dataset history — `dvc diff` shows what changed between two versions of a dataset
- Works with the existing Git workflow — you still commit, branch, and tag as normal

### Where you see it in this project

These `.dvc` pointer files live in the repository:

| `.dvc` file | What it tracks |
|---|---|
| `data/raw.dvc` | 22 original Garmin sensor CSV files |
| `data/prepared.dvc` | Windowed, labelled segments |
| `data/processed.dvc` | Scaled features ready for training |
| `models/pretrained.dvc` | Pre-trained model weights |
| `models/runtime_contract/model_d1_final_20260528.dvc` | The deployed model bundle |
| `artifacts/<timestamp>.dvc` | Full outputs of each pipeline run |

Each `.dvc` file looks like this:

```yaml
outs:
- md5: 69c45431805a9772975fa73c8811fb97.dir
  size: 4823041
  nfiles: 22
  path: raw
```

That `md5` is the fingerprint of the entire folder. If even one byte changes, the hash
changes — making silent data corruption impossible.

Essential commands:

```bash
dvc pull          # download data from remote to your machine
dvc push          # upload local data changes to the remote
dvc checkout      # restore data files after a git checkout
dvc diff          # show what dataset files changed between commits
```

**In one sentence:** DVC is Git for data — it stores fingerprints of large files in Git
and keeps the actual data in a separate store, so experiments are fully reproducible and
data can be shared without bloating the repository.

---

## 7. MLflow

### What it is — simple version

When you train a machine learning model, you try many things: different learning rates,
different window sizes, different dropout rates. Without a tool, you quickly lose track of
which experiment gave which result.

MLflow is an experiment diary. Every time you run training, it automatically records:

- What settings (hyperparameters) you used
- What results (metrics) you got
- The actual model file that produced those results

Later you can open the MLflow UI, see all your experiments side by side, pick the best
one, and promote it to the model registry for deployment.

### Why we use it

- Never lose an experiment result — every run is stored with its exact parameters
- Compare runs visually — one graph showing 10 experiments at once
- Model registry — gives each model a named version with a stage (Staging / Production /
  Archived) so you always know what is deployed and what is superseded
- Reproducibility — a run ID is a permanent link to the code + data + settings that
  produced a specific model

### Where you see it in this project

**Experiment tracking:**

The config is in `config/mlflow_config.yaml`. Metrics logged on every training run:
accuracy, loss, val_accuracy, val_loss, F1, precision, recall.

The adapter that owns the MLflow run lifecycle is `src/pipeline/pipeline_mlflow_logger.py`.
It wraps every pipeline stage: when a stage finishes, its metrics are logged automatically.

**Model registry:**

The registered model name is `har-1dcnn-bilstm`. The currently deployed version
(`model_d1_final_20260528`) has:

- 5-fold CV accuracy: 93.61 %
- LOUO accuracy: 44.42 % (the honest leave-one-user-out number)

Registration only happens in **Stage 9 (ModelRegistration)** — not during normal
inference. This is intentional: if registration happened on every inference call, a new
model version would be created every time someone uploads a CSV file.

Promotion flow:

```
Training run
     |
  None     ← just registered, not yet reviewed
     |
  Staging  ← passed offline evaluation
     |
  Production  ← approved for serving, used to build the runtime contract
     |
  Archived ← superseded by a newer Production version
```

**Viewing experiments:**

```bash
mlflow ui --backend-store-uri mlruns
# Open http://localhost:5000
```

**In one sentence:** MLflow is an experiment diary and model catalogue — it records every
training run automatically so you can compare results, pick the best model, and track
exactly what version is in production.

---

## How They All Connect

Here is the full picture — how each tool plays its role in one complete cycle:

```
You write code
      |
  Pytest           ← checks that the logic is correct
      |
  CI pipeline      ← runs Pytest + lint + Docker build automatically on every push
      |
  Docker           ← packages the API into a portable, sealed container
      |
  FastAPI          ← the web door — accepts CSV uploads, runs the pipeline, returns JSON
      |
  Pydantic         ← enforces that every input and output has exactly the right shape
      |
  DVC              ← ensures the training data is the exact same version every run
      |
  MLflow           ← records every training run and tracks which model is in Production
```

None of these tools does the same job as another. Each one guards a different failure mode:

| Without this tool | What would go wrong |
|---|---|
| Docker | Works on your machine, fails on the server |
| CI pipeline | Broken code silently reaches main |
| FastAPI | No standard interface — callers need direct Python access |
| Pydantic | Wrong data types cause silent crashes deep in the pipeline |
| Pytest | Refactoring breaks things and nobody notices until production |
| DVC | Cannot reproduce which dataset trained which model |
| MLflow | Cannot compare experiments or find out which settings produced the best model |
