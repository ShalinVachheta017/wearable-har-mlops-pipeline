# Inference Image Optimization & CI Pipeline — Detailed Report

This report covers two things you asked about:

1. **Reducing the size of the inference image** (the web/FastAPI image we build first) —
   with real measured sizes and the concrete benefits.
2. **A detailed, part-by-part explanation of the CI file** (`.github/workflows/ci.yml`).

---

## Part 1 — Reducing the Inference Image Size

### Where the size actually comes from (measured, not guessed)

The inference image is **2.64 GB**. Running `docker history` on it shows exactly which
layer is heavy:

| Layer | Size | What it is |
|---|---|---|
| `pip install -r requirements-runtime.txt` | **1.94 GB** | Python deps — TensorFlow-CPU dominates this |
| Base `python:3.11-slim` | ~140 MB | Python runtime + OS |
| `COPY src/` | 32 MB | Application code |
| `apt-get install curl` | 14 MB | Healthcheck tool |
| Everything else | < 1 MB | env vars, mkdir, config |

**The conclusion is clear:** one single layer — the Python packages — is **73 % of the
whole image**, and TensorFlow-CPU is the bulk of that layer. Nothing else is worth touching.

### The one change that matters: TensorFlow → ONNX Runtime

The model only needs to *predict* at serving time. The full TensorFlow framework is built
for *training* — it ships training ops, the Keras stack, and large bundled C++ libraries
the inference path never uses.

We can convert the frozen `.keras` model to the **ONNX** format and serve it with
**ONNX Runtime**, a lightweight engine built only for inference.

**The steps:**

```bash
# 1. Convert the deployed Keras model to ONNX (one-time, offline)
pip install tf2onnx
python -m tf2onnx.convert \
  --keras models/runtime_contract/model_d1_final_20260528/finetuned_1DCNNBILSTM_HAR_model.keras \
  --output models/runtime_contract/model_d1_final_20260528/model.onnx

# 2. Swap the dependency in requirements-runtime.txt
#    remove:  tensorflow-cpu>=2.14
#    add:     onnxruntime>=1.17

# 3. Small change in src/api/app.py — replace the Keras load + predict
#    with an onnxruntime InferenceSession (same input/output shapes)
```

### Before vs After (estimated)

| | Current (TensorFlow) | After (ONNX Runtime) |
|---|---|---|
| Serving engine | `tensorflow-cpu` | `onnxruntime` |
| pip layer size | ~1.94 GB | ~0.5–0.7 GB |
| **Total image size** | **2.64 GB** | **~1.3–1.5 GB** |
| Reduction | — | **~45–50 % smaller** |

> Sizes after conversion are estimates until the new image is built and measured. The
> 2.64 GB current size and 1.94 GB pip layer are **measured** via `docker history`.

### The benefits of a smaller inference image

1. **Faster deployments.** Every `docker pull` on ECS, Kubernetes, or a fresh server
   downloads ~1.3 GB instead of ~2.6 GB — roughly half the network transfer and time.

2. **Faster cold starts / autoscaling.** When Kubernetes spins up a new pod under load, a
   smaller image means the new pod is serving requests sooner. This directly improves the
   autoscaling responsiveness described in the Kubernetes guide.

3. **Lower storage and registry cost.** ECR (and any registry) bills by GB stored and
   transferred. Half the size means roughly half the cost, multiplied across every stored
   version.

4. **Smaller attack surface.** ONNX Runtime is a fraction of TensorFlow's code. Fewer
   libraries inside the container means fewer potential vulnerabilities to patch.

5. **Faster CI.** The `docker-build-check` job in CI builds this image on every push.
   A lighter image builds and caches faster, shortening the feedback loop.

6. **Often faster inference too.** ONNX Runtime is frequently quicker than TensorFlow for
   pure CPU inference — a side benefit on top of the size saving.

### Honest cost of the change

- A **one-time model conversion** step is added to the release process.
- A **small code change** in `app.py` (load + predict path).
- **Re-validation is mandatory:** confirm ONNX predictions match the Keras outputs on the
  user-7 probe before promoting. For a thesis with a frozen, defended model, only do this
  if image size is a real constraint — otherwise the current image is correct and safe.

### What is NOT worth doing

- **Alpine base image** — TensorFlow / numpy / scipy have no Alpine wheels; they would
  compile from source, breaking builds and often producing a *larger* image.
- **Removing `curl`** — saves only ~14 MB and costs you easy in-container debugging.
- **Multi-stage build** — the deps are pre-built wheels with no leftover build artifacts,
  so there is nothing for a builder stage to strip out.

---

## Part 2 — The CI File Explained in Detail

File: [.github/workflows/ci.yml](.github/workflows/ci.yml)

A CI file is a set of instructions for GitHub's robot (**GitHub Actions**). It runs
automatically and blocks broken code from merging. Below is every part, top to bottom.

### Block 1 — `name`

```yaml
name: CI
```

Just the display label. This is the name you see in the GitHub "Actions" tab and on the
green check / red X next to each commit.

### Block 2 — `on` (the triggers — *when* the robot wakes up)

```yaml
on:
  pull_request:
    branches: [main]
  push:
    branches: [main, develop]
```

- **`pull_request` into `main`** → runs when someone opens or updates a PR targeting `main`.
  This is the gate that protects your main branch *before* code merges.
- **`push` to `main` or `develop`** → runs when commits land directly on those branches.

In plain terms: *"Wake up whenever someone tries to put code into main, or pushes to main
or develop."*

### Block 3 — `permissions`

```yaml
permissions:
  contents: read
```

A safety setting. It tells the robot it may only **read** the repository, never modify it.
This follows the security principle of least privilege — the CI job has no power to push
code or change settings.

### Block 4 — `env` (shared settings)

```yaml
env:
  PYTHON_VERSION: "3.11"
```

A variable reused by every job, so the Python version is defined **once**. If you upgrade
Python later, you change it in one place instead of three.

### Block 5 — The three jobs

The work is split into three jobs. The key detail is `needs:`, which **chains them in
order** — each only starts if the previous one passed.

```
lint  →  unit-tests  →  docker-build-check
```

---

#### Job 1 — `lint` (is the code clean and correctly formatted?)

```yaml
lint:
  runs-on: ubuntu-latest
  timeout-minutes: 10
  steps:
    - uses: actions/checkout@v4              # download the repo code
    - uses: actions/setup-python@v5          # install Python 3.11
    - name: Install lint dependencies
      run: pip install flake8 black isort
    - name: Run flake8 ...
    - name: Run black (check) ...
    - name: Run isort (check) ...
```

Step by step:
- **`runs-on: ubuntu-latest`** → the robot uses a fresh Linux machine.
- **`timeout-minutes: 10`** → if it hangs past 10 minutes, kill it (prevents stuck jobs).
- **`checkout`** → downloads your repository onto that machine.
- **`setup-python`** → installs Python 3.11.
- **flake8** → scans `src/` for real errors (undefined names, bad syntax) and functions
  that are too complex. The first flake8 line (`--select=E9,F63,F7,F82`) catches *serious*
  errors; the second checks complexity and line length with a list of relaxed rules.
- **black `--check`** → verifies the code is auto-formatted. `--check` means *only report*,
  do not modify. Fails if any file would be reformatted.
- **isort `--check-only`** → verifies import statements are sorted correctly.

If any check fails, the job goes red and **nothing downstream runs**.

---

#### Job 2 — `unit-tests` (does the code actually work?)

```yaml
unit-tests:
  needs: lint                # <-- only runs if lint passed
  steps:
    - checkout / setup-python (with pip cache)
    - run: pip install -r config/requirements.txt && pip install pytest pytest-cov
    - run: pytest tests/ --junitxml=test-results.xml
    - upload test-results.xml as an artifact (if: always())
```

Step by step:
- **`needs: lint`** → this is the chain link. The tests only run **after** lint passes.
- **`cache: pip`** → reuses downloaded packages from previous runs, so installs are faster.
- **Install deps** → the full `requirements.txt` plus pytest.
- **`pytest tests/`** → runs *every* test file in `tests/` (validation, transformation,
  monitoring, trigger, registration, the API tests, etc.). `--junitxml` writes results to
  a structured file.
- **`upload-artifact` with `if: always()`** → saves the test report **even if tests fail**,
  so you can open it and see exactly which test broke.

If any test fails, the job goes red and the Docker job does not run.

---

#### Job 3 — `docker-build-check` (does it package into a working image?)

```yaml
docker-build-check:
  needs: unit-tests          # <-- only runs if tests passed
  steps:
    - checkout
    - uses: docker/setup-buildx-action@v3
    - uses: docker/build-push-action@v6
      with:
        file: docker/Dockerfile.inference
        push: false          # <-- build only, do NOT publish
        tags: har-inference:ci
```

Step by step:
- **`needs: unit-tests`** → only runs after tests pass.
- **`setup-buildx`** → enables Docker's modern builder.
- **`build-push-action`** → builds the inference image from `Dockerfile.inference`.
- **`push: false`** → this is the important part. It **builds but does not publish**
  anywhere. The goal is purely to confirm: *"Does the Dockerfile still assemble into a
  valid image?"* It catches packaging breakage (a missing file, a broken dependency)
  before it reaches a real deployment.

---

### The whole CI flow in one picture

```
Someone pushes code or opens a PR to main
                │
        ┌───────▼────────┐
        │   Job 1: lint  │   style + obvious errors (flake8, black, isort)
        └───────┬────────┘
                │ passed?
        ┌───────▼─────────────┐
        │ Job 2: unit-tests   │   pytest runs every test in tests/
        └───────┬─────────────┘
                │ passed?
        ┌───────▼──────────────────┐
        │ Job 3: docker-build-check │   builds inference image (no push)
        └───────┬──────────────────┘
                │ all green?
                ▼
     Safe to merge into main
```

**Why it is built in this order:** cheapest and fastest checks run first. Style checking
takes seconds; tests take a minute or two; building the Docker image is the slowest. There
is no point building a 2.64 GB image if a one-second formatting check already shows the code
is broken. Fail fast, fail cheap.
